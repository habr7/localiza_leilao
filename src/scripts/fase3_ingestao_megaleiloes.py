"""Ingestão do agregador Mega Leilões (Fase 3).

Coleta imóveis em SP no Mega Leilões, resolve a UF do leiloeiro pelo cadastro
(Fase 2) e faz upsert idempotente em `leiloes`/`lotes`/`lote_fontes`. Ao final,
mostra quantos lotes SP têm leiloeiro **não-SP** — o sinal central da tese.

Uso:
    uv run python -m src.scripts.fase3_ingestao_megaleiloes --limite 20
"""

from __future__ import annotations

import argparse
import asyncio
import logging

import structlog
from sqlalchemy import func, select

from src.core.config import settings
from src.core.db import get_session
from src.core.models import Leilao, Lote
from src.ingestao.agregadores.megaleiloes import MegaLeiloesScraper
from src.ingestao.base import LoteRaw
from src.ingestao.persistencia import IngestaoStats, persistir_lote
from src.leiloeiros.cadastro import carregar_cadastro
from src.leiloeiros.resolver import LeiloeiroResolver

log = structlog.get_logger()


async def coletar(limite: int | None) -> list[LoteRaw]:
    """Coleta os lotes de imóveis SP do Mega Leilões (com limite opcional)."""
    async with MegaLeiloesScraper() as scraper:
        lotes = await scraper.listar_lotes_sp(limite=limite)
    log.info("mega_coletado", lotes=len(lotes))
    return lotes


def ingerir(lotes: list[LoteRaw]) -> IngestaoStats:
    """Resolve o leiloeiro de cada lote e persiste de forma idempotente."""
    stats = IngestaoStats()
    with get_session() as session:
        resolver = LeiloeiroResolver(carregar_cadastro(session))
        for lote in lotes:
            resolucao = resolver.resolver_multiplas(
                nome=lote.leiloeiro_nome, matriculas=lote.leiloeiro_matriculas
            )
            persistir_lote(session, lote, resolucao)
            stats.processados += 1
            if resolucao.fora_sp is True:
                stats.fora_sp += 1
            elif resolucao.fora_sp is False:
                stats.sp += 1
            else:
                stats.uf_indefinida += 1
            log.info(
                "lote_ingerido",
                fonte_url=lote.fonte_url,
                leiloeiro=lote.leiloeiro_nome,
                uf=resolucao.uf,
                fora_sp=resolucao.fora_sp,
                confianca=resolucao.confianca,
            )
    return stats


def main() -> None:
    """Orquestra a coleta + resolução + carga idempotente do Mega Leilões."""
    parser = argparse.ArgumentParser(description="Ingestão do Mega Leilões (Fase 3).")
    parser.add_argument(
        "--limite",
        type=int,
        default=20,
        help="Quantos lotes (detalhes) coletar. Use 0 para todos da 1ª página.",
    )
    args = parser.parse_args()
    limite = None if args.limite == 0 else args.limite

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        )
    )
    log.info("fase3_iniciada", fonte="megaleiloes", limite=limite)

    lotes = asyncio.run(coletar(limite))
    stats = ingerir(lotes)

    with get_session() as session:
        total_lotes = session.scalar(select(func.count()).select_from(Lote))
        total_leiloes = session.scalar(select(func.count()).select_from(Leilao))
        leiloes_fora_sp = session.scalar(
            select(func.count())
            .select_from(Leilao)
            .where(Leilao.uf_leiloeiro.isnot(None), Leilao.uf_leiloeiro != "SP")
        )

    print(
        f"\nIngestão Mega Leilões: {stats.processados} lotes processados "
        f"({stats.fora_sp} com leiloeiro NÃO-SP, {stats.sp} SP, "
        f"{stats.uf_indefinida} UF indefinida)."
    )
    print(
        f"Banco: {total_leiloes} leilões ({leiloes_fora_sp} com leiloeiro não-SP), "
        f"{total_lotes} lotes."
    )


if __name__ == "__main__":
    main()
