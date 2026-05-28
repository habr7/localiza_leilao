"""Persistência idempotente de lotes coletados (Fase 3).

Converte um `LoteRaw` (cru, de um scraper) em registros no banco: `leiloes` (um
por anúncio/URL), `lotes` (o imóvel em SP) e `lote_fontes` (a origem). Tudo
idempotente: rodar a coleta 2x não duplica (chaves naturais: `fonte_url` do
leilão, `hash_dedup` do lote, `(lote_id, fonte_url)` da fonte).
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from decimal import Decimal

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.models import Leilao, Lote, LoteFonte
from src.ingestao.base import LoteRaw

log = structlog.get_logger()


@dataclass
class LoteStats:
    inseridos: int = 0
    atualizados: int = 0
    ignorados: int = 0


def _hash_dedup(lote: LoteRaw) -> str:
    """Chave de deduplicação: matrícula do imóvel se houver, senão a URL da fonte."""
    base = lote.fonte_url
    return hashlib.sha1(base.encode("utf-8")).hexdigest()  # noqa: S324 — só dedup, não cripto


def _dec(valor: float | None) -> Decimal | None:
    return Decimal(str(valor)) if valor is not None else None


def upsert_lote(
    session: Session,
    lote: LoteRaw,
    leiloeiro_id: uuid.UUID | None,
    uf_leiloeiro: str | None,
) -> str:
    """Insere/atualiza um lote (e seu leilão e fonte). Retorna o status da operação.

    Pré-condição: `lote.uf == 'SP'` e `lote.cidade` preenchida (constraints da
    tabela `lotes`). Lotes sem cidade são ignorados pelo chamador.
    """
    # 1) Leilão (um por URL de anúncio) — idempotente por fonte_url.
    leilao = session.scalar(select(Leilao).where(Leilao.fonte_url == lote.fonte_url))
    if leilao is None:
        leilao = Leilao(
            leiloeiro_id=leiloeiro_id,
            uf_leiloeiro=uf_leiloeiro,
            tipo=lote.tipo_leilao or "extrajudicial",
            fonte_origem=lote.fonte_origem,
            fonte_tipo=lote.fonte_tipo,
            fonte_url=lote.fonte_url,
            status="aberto",
        )
        session.add(leilao)
        session.flush()
    else:
        leilao.leiloeiro_id = leiloeiro_id
        leilao.uf_leiloeiro = uf_leiloeiro
        if lote.tipo_leilao:
            leilao.tipo = lote.tipo_leilao

    # 2) Lote — idempotente por hash_dedup.
    hash_dedup = _hash_dedup(lote)
    existente = session.scalar(select(Lote).where(Lote.hash_dedup == hash_dedup))
    campos = {
        "numero_lote": lote.numero_lote,
        "tipo_imovel": lote.tipo_imovel,
        "endereco_completo": lote.endereco_completo,
        "cidade": lote.cidade,
        "uf": lote.uf,
        "bairro": lote.bairro,
        "area_m2": _dec(lote.area_m2),
        "avaliacao": _dec(lote.avaliacao),
        "lance_minimo_1": _dec(lote.lance_minimo_1),
        "lance_minimo_2": _dec(lote.lance_minimo_2),
        "descricao": lote.descricao,
    }
    if existente is None:
        novo = Lote(leilao_id=leilao.id, hash_dedup=hash_dedup, **campos)
        session.add(novo)
        session.flush()
        lote_obj = novo
        status = "inserido"
    else:
        for k, v in campos.items():
            setattr(existente, k, v)
        lote_obj = existente
        status = "atualizado"

    # 3) Fonte do lote — idempotente por (lote_id, fonte_url).
    ja = session.scalar(
        select(LoteFonte).where(
            LoteFonte.lote_id == lote_obj.id, LoteFonte.fonte_url == lote.fonte_url
        )
    )
    if ja is None:
        session.add(
            LoteFonte(
                lote_id=lote_obj.id,
                fonte_origem=lote.fonte_origem,
                fonte_tipo=lote.fonte_tipo,
                fonte_url=lote.fonte_url,
                dados_extras=lote.dados_extras,
            )
        )
        session.flush()  # garante visibilidade na checagem do próximo lote
    return status


def upsert_lotes(
    session: Session,
    lotes: list[LoteRaw],
    leiloeiro_id: uuid.UUID | None,
    uf_leiloeiro: str | None,
) -> LoteStats:
    """Upsert de uma leva de lotes do mesmo leiloeiro. Ignora lotes sem cidade/UF."""
    stats = LoteStats()
    vistos: set[str] = set()
    for lote in lotes:
        if lote.uf != "SP" or not lote.cidade or lote.fonte_url in vistos:
            stats.ignorados += 1
            continue
        vistos.add(lote.fonte_url)
        status = upsert_lote(session, lote, leiloeiro_id, uf_leiloeiro)
        if status == "inserido":
            stats.inseridos += 1
        else:
            stats.atualizados += 1
    return stats
