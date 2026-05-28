"""Fase 2 — popula o cadastro de leiloeiros a partir das listas públicas das Juntas.

Roda os scrapers de Junta que já têm `url_lista` implementada (hoje: JUCEPAR e
JUCEG, ambas não-SP, com **site oficial** de cada leiloeiro) e faz upsert
idempotente em `leiloeiros`. As Juntas ainda sem parser ao vivo são puladas com
aviso (caminho LAI/CSV continua disponível).

O site oficial é o que destrava a Fase 3 (sites próprios): é nele que o leiloeiro
de fora de SP anuncia imóveis paulistas.

Uso:
    uv run python -m src.scripts.fase2_cadastrar_leiloeiros
"""

from __future__ import annotations

import asyncio

import structlog

from src.core.db import get_session
from src.leiloeiros.cadastro import LeiloeiroRaw, upsert_leiloeiros
from src.leiloeiros.juntas import JUNTAS_DISPONIVEIS

log = structlog.get_logger()


async def _coletar_todas() -> dict[str, list[LeiloeiroRaw]]:
    """Coleta de cada Junta com `url_lista` configurada (pula as pendentes)."""
    resultado: dict[str, list[LeiloeiroRaw]] = {}
    for nome, cls in JUNTAS_DISPONIVEIS.items():
        scraper = cls()
        if not scraper.url_lista:
            log.info("junta_pulada", junta=nome, motivo="sem_url_lista")
            continue
        try:
            registros = await scraper.coletar()
        except Exception as exc:  # noqa: BLE001 — uma Junta falha não derruba as demais
            log.warning("junta_erro", junta=nome, erro=type(exc).__name__, msg=str(exc)[:120])
            continue
        com_site = sum(1 for r in registros if r.site_oficial)
        log.info("junta_coletada", junta=nome, encontrados=len(registros), com_site=com_site)
        resultado[nome] = registros
    return resultado


def main() -> None:
    por_junta = asyncio.run(_coletar_todas())
    todos = [r for registros in por_junta.values() for r in registros]

    with get_session() as session:
        stats = upsert_leiloeiros(session, todos)

    com_site = sum(1 for r in todos if r.site_oficial)
    nao_sp = sum(1 for r in todos if (r.uf_matricula or "").upper() != "SP")
    print("\n=== Cadastro de leiloeiros (Fase 2) ===")
    for nome, registros in por_junta.items():
        print(
            f"  {nome}: {len(registros)} leiloeiros "
            f"({sum(1 for r in registros if r.site_oficial)} com site)"
        )
    print(f"Total coletado: {len(todos)} | não-SP: {nao_sp} | com site oficial: {com_site}")
    print(
        f"Upsert: inseridos={stats.inseridos} atualizados={stats.atualizados} "
        f"ignorados={stats.ignorados}"
    )


if __name__ == "__main__":
    main()
