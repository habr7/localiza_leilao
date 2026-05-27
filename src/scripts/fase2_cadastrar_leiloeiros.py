"""Carga do cadastro de leiloeiros (Fase 2).

Roda os scrapers das Juntas Comerciais com lista pública configurada, opcionalmente
carrega CSVs de respostas de LAI/e-SIC (Juntas sem lista navegável) e faz upsert
idempotente em `leiloeiros`. Ao final, imprime um resumo com a contagem de
leiloeiros não-SP, que é a base utilizável para o matching da tese.

Uso:
    uv run python -m src.scripts.fase2_cadastrar_leiloeiros
    uv run python -m src.scripts.fase2_cadastrar_leiloeiros --csv JUCEMG=data/lai_jucemg.csv
"""

from __future__ import annotations

import argparse
import asyncio
import logging

import structlog
from sqlalchemy import func, select

from src.core.config import settings
from src.core.db import get_session
from src.core.models import Leiloeiro
from src.leiloeiros.cadastro import LeiloeiroRaw, upsert_leiloeiros
from src.leiloeiros.juntas import JUNTAS_DISPONIVEIS, JuntaScraper

log = structlog.get_logger()


async def coletar_junta(scraper: JuntaScraper) -> list[LeiloeiroRaw]:
    """Coleta os leiloeiros de uma Junta com lista pública, tolerando falhas.

    Retorna lista vazia (e loga) se a Junta não tiver lista pública configurada
    ou se a coleta ao vivo falhar — assim uma Junta indisponível não derruba a
    carga das demais.
    """
    try:
        registros = await scraper.coletar()
        log.info("junta_coletada", junta=scraper.junta, encontrados=len(registros))
        return registros
    except NotImplementedError:
        log.info("junta_sem_lista_publica", junta=scraper.junta)
        return []
    except Exception as exc:  # noqa: BLE001
        log.warning("junta_falhou", junta=scraper.junta, erro=str(exc))
        return []


async def coletar_todas(csv_por_junta: dict[str, str]) -> list[LeiloeiroRaw]:
    """Coleta de todas as Juntas registradas (lista pública) + CSVs informados."""
    registros: list[LeiloeiroRaw] = []
    for sigla, cls in JUNTAS_DISPONIVEIS.items():
        scraper = cls()
        if caminho := csv_por_junta.get(sigla):
            csv_regs = scraper.coletar_csv(caminho)
            log.info("junta_csv_carregado", junta=sigla, registros=len(csv_regs))
            registros.extend(csv_regs)
        else:
            registros.extend(await coletar_junta(scraper))
    return registros


def resumo_por_uf(registros: list[LeiloeiroRaw]) -> dict[str, int]:
    """Conta quantos registros coletados há por UF de matrícula."""
    contagem: dict[str, int] = {}
    for r in registros:
        uf = (r.uf_matricula or "??").upper()
        contagem[uf] = contagem.get(uf, 0) + 1
    return contagem


def main() -> None:
    """Orquestra a coleta das Juntas e a carga idempotente do cadastro."""
    parser = argparse.ArgumentParser(description="Carga do cadastro de leiloeiros (Fase 2).")
    parser.add_argument(
        "--csv",
        action="append",
        default=[],
        metavar="JUNTA=caminho.csv",
        help="Carrega uma Junta a partir de CSV (resposta de LAI) em vez do site.",
    )
    args = parser.parse_args()
    csv_por_junta = dict(par.split("=", 1) for par in args.csv)

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        )
    )
    log.info("fase2_iniciada", juntas=list(JUNTAS_DISPONIVEIS), csv=list(csv_por_junta))

    registros = asyncio.run(coletar_todas(csv_por_junta))
    contagem = resumo_por_uf(registros)
    print(f"\nColetados {len(registros)} leiloeiros (cru) por UF: {contagem}")

    with get_session() as session:
        stats = upsert_leiloeiros(session, registros)
        total_db = session.scalar(select(func.count()).select_from(Leiloeiro))
        nao_sp_db = session.scalar(
            select(func.count()).select_from(Leiloeiro).where(Leiloeiro.uf_matricula != "SP")
        )

    print(
        f"Upsert: {stats.inseridos} inseridos, {stats.atualizados} atualizados, "
        f"{stats.ignorados} ignorados."
    )
    print(f"Cadastro no banco: {total_db} leiloeiros, dos quais {nao_sp_db} não-SP.")


if __name__ == "__main__":
    main()
