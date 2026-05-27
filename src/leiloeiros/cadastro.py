"""Consolidação do cadastro de leiloeiros (Fase 2).

Recebe registros crus (de scrapers de Juntas ou de CSV — ex.: resposta de LAI) e
faz upsert idempotente em `leiloeiros`. Também carrega o cadastro em memória no
formato que o resolvedor consome.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.core.models import Leiloeiro
from src.leiloeiros.matricula import parse_matricula
from src.leiloeiros.resolver import LeiloeiroRef

log = structlog.get_logger()


@dataclass
class LeiloeiroRaw:
    """Registro cru de leiloeiro vindo de uma Junta ou CSV."""

    nome: str
    matricula: str
    uf_matricula: str | None = None  # derivada da matrícula se ausente
    junta_comercial: str | None = None  # idem
    cpf: str | None = None
    site_oficial: str | None = None
    plataformas: list[str] | None = None
    aliases: list[str] | None = None
    fonte_cadastro: str | None = None


@dataclass
class UpsertStats:
    """Contagem do resultado de um upsert."""

    inseridos: int = 0
    atualizados: int = 0
    ignorados: int = 0

    @property
    def total(self) -> int:
        return self.inseridos + self.atualizados


def _normalizar(raw: LeiloeiroRaw) -> dict[str, object] | None:
    """Valida e completa um registro cru; retorna None se a UF for indeterminável."""
    m = parse_matricula(raw.matricula)
    uf = raw.uf_matricula or m.uf
    junta = raw.junta_comercial or m.junta
    if not uf:
        log.warning("leiloeiro_uf_indeterminada", nome=raw.nome, matricula=raw.matricula)
        return None
    return {
        "nome": raw.nome.strip(),
        "matricula": raw.matricula.strip(),
        "uf_matricula": uf.upper(),
        "junta_comercial": (junta or uf).upper(),
        "cpf": raw.cpf,
        "site_oficial": raw.site_oficial,
        "plataformas": raw.plataformas,
        "aliases": raw.aliases,
        "fonte_cadastro": raw.fonte_cadastro,
        "visto_em": datetime.now(UTC),
    }


def upsert_leiloeiros(session: Session, registros: list[LeiloeiroRaw]) -> UpsertStats:
    """Insere/atualiza leiloeiros de forma idempotente (chave matrícula+UF).

    Rodar duas vezes com os mesmos dados não duplica registros.
    """
    stats = UpsertStats()
    valores = []
    for raw in registros:
        normalizado = _normalizar(raw)
        if normalizado is None:
            stats.ignorados += 1
            continue
        valores.append(normalizado)

    if not valores:
        return stats

    # Quais (matricula, uf) já existem? Para contar inseridos vs. atualizados.
    chaves = {(v["matricula"], v["uf_matricula"]) for v in valores}
    existentes_q = select(Leiloeiro.matricula, Leiloeiro.uf_matricula).where(
        Leiloeiro.matricula.in_({m for m, _ in chaves})
    )
    existentes = {(m, uf) for m, uf in session.execute(existentes_q).all()}

    for v in valores:
        if (v["matricula"], v["uf_matricula"]) in existentes:
            stats.atualizados += 1
        else:
            stats.inseridos += 1

    stmt = insert(Leiloeiro).values(valores)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_leiloeiros_matricula_uf",
        set_={
            "nome": stmt.excluded.nome,
            "junta_comercial": stmt.excluded.junta_comercial,
            "cpf": stmt.excluded.cpf,
            "site_oficial": stmt.excluded.site_oficial,
            "plataformas": stmt.excluded.plataformas,
            "aliases": stmt.excluded.aliases,
            "fonte_cadastro": stmt.excluded.fonte_cadastro,
            "visto_em": stmt.excluded.visto_em,
            "atualizado_em": datetime.now(UTC),
        },
    )
    session.execute(stmt)
    log.info(
        "leiloeiros_upsert",
        inseridos=stats.inseridos,
        atualizados=stats.atualizados,
        ignorados=stats.ignorados,
    )
    return stats


def importar_csv(path: str | Path) -> list[LeiloeiroRaw]:
    """Lê leiloeiros de um CSV (ex.: resposta de pedido LAI).

    Colunas reconhecidas: nome, matricula, uf_matricula, junta_comercial, cpf,
    site_oficial, plataformas (separadas por ';'), aliases (separados por ';').
    """
    path = Path(path)
    registros: list[LeiloeiroRaw] = []
    with path.open(encoding="utf-8") as fh:
        for linha in csv.DictReader(fh):
            registros.append(
                LeiloeiroRaw(
                    nome=(linha.get("nome") or "").strip(),
                    matricula=(linha.get("matricula") or "").strip(),
                    uf_matricula=(linha.get("uf_matricula") or "").strip() or None,
                    junta_comercial=(linha.get("junta_comercial") or "").strip() or None,
                    cpf=(linha.get("cpf") or "").strip() or None,
                    site_oficial=(linha.get("site_oficial") or "").strip() or None,
                    plataformas=_split(linha.get("plataformas")),
                    aliases=_split(linha.get("aliases")),
                    fonte_cadastro=(linha.get("fonte_cadastro") or "").strip() or None,
                )
            )
    log.info("csv_importado", arquivo=str(path), registros=len(registros))
    return registros


def _split(valor: str | None) -> list[str] | None:
    """Quebra um campo multivalorado separado por ';' em lista (ou None)."""
    if not valor or not valor.strip():
        return None
    return [parte.strip() for parte in valor.split(";") if parte.strip()]


def carregar_cadastro(session: Session, apenas_ativos: bool = True) -> list[LeiloeiroRef]:
    """Carrega o cadastro em memória no formato que o resolvedor consome."""
    query = select(Leiloeiro)
    if apenas_ativos:
        query = query.where(Leiloeiro.ativo.is_(True))
    refs: list[LeiloeiroRef] = []
    for leiloeiro in session.scalars(query):
        refs.append(
            LeiloeiroRef(
                id=leiloeiro.id,
                nome=leiloeiro.nome,
                matricula=leiloeiro.matricula,
                uf_matricula=leiloeiro.uf_matricula,
                junta_comercial=leiloeiro.junta_comercial,
                aliases=list(leiloeiro.aliases or []),
            )
        )
    return refs
