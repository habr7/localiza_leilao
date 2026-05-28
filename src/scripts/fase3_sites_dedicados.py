"""Fase 3 — coleta estruturada dos sites próprios com parser dedicado.

Para cada scraper dedicado (`SCRAPERS_DEDICADOS`): resolve o leiloeiro dono do
site no cadastro (pelo domínio), coleta os imóveis em SP, faz **upsert no banco**
(leiloes/lotes/lote_fontes) e exporta um CSV estruturado em
``data/imoveis_sp_sites_proprios.csv`` para análise manual.

Diferente do scanner heurístico (`fase3_sites_proprios`), aqui o resultado é um
lote estruturado (tipo, cidade, bairro, lance, praça, link), pronto para ranquear.

Uso:
    uv run python -m src.scripts.fase3_sites_dedicados
"""

from __future__ import annotations

import asyncio
import csv
import uuid
from pathlib import Path

import structlog
from sqlalchemy import select

from src.core.db import get_session
from src.core.models import Leiloeiro
from src.ingestao.base import LoteRaw
from src.ingestao.persistencia import upsert_lotes
from src.ingestao.sites_proprios import SCRAPERS_DEDICADOS

log = structlog.get_logger()

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
COLUNAS = [
    "fonte",
    "leiloeiro",
    "uf_leiloeiro",
    "tipo_imovel",
    "cidade",
    "bairro",
    "uf_imovel",
    "lance_minimo",
    "tipo_leilao",
    "praca",
    "url",
]


def _resolver_dono(dominio: str) -> tuple[uuid.UUID | None, str | None, str | None]:
    """Acha no cadastro o leiloeiro dono do site (id, nome, uf) pelo domínio."""
    with get_session() as session:
        leil = session.scalar(select(Leiloeiro).where(Leiloeiro.site_oficial.ilike(f"%{dominio}%")))
        if leil is None:
            return None, None, None
        return leil.id, leil.nome, leil.uf_matricula


async def _coletar(scraper_cls: type) -> list[LoteRaw]:
    async with scraper_cls() as scraper:
        return await scraper.listar_lotes_sp()


def _linha(lote: LoteRaw, nome: str | None, uf: str | None) -> dict[str, object]:
    return {
        "fonte": lote.fonte_origem,
        "leiloeiro": nome or "",
        "uf_leiloeiro": uf or "",
        "tipo_imovel": lote.tipo_imovel or "",
        "cidade": lote.cidade or "",
        "bairro": lote.bairro or "",
        "uf_imovel": lote.uf or "",
        "lance_minimo": lote.lance_minimo_1 or "",
        "tipo_leilao": lote.tipo_leilao or "",
        "praca": lote.descricao or "",
        "url": lote.fonte_url,
    }


def main() -> None:
    linhas: list[dict[str, object]] = []
    total_ins = total_atu = 0
    for scraper_cls in SCRAPERS_DEDICADOS:
        dominio = scraper_cls.dominio
        leiloeiro_id, nome, uf = _resolver_dono(dominio)
        lotes = asyncio.run(_coletar(scraper_cls))
        sp = [lo for lo in lotes if lo.uf == "SP" and lo.cidade]
        with get_session() as session:
            stats = upsert_lotes(session, sp, leiloeiro_id, uf)
        total_ins += stats.inseridos
        total_atu += stats.atualizados
        linhas.extend(_linha(lo, nome, uf) for lo in sp)
        log.info(
            "site_dedicado",
            dominio=dominio,
            leiloeiro=nome,
            uf=uf,
            imoveis_sp=len(sp),
            inseridos=stats.inseridos,
            atualizados=stats.atualizados,
            sem_dono_no_cadastro=(leiloeiro_id is None),
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    destino = DATA_DIR / "imoveis_sp_sites_proprios.csv"
    with destino.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUNAS)
        writer.writeheader()
        writer.writerows(linhas)

    print(f"\nImóveis SP (sites próprios dedicados): {len(linhas)}")
    print(f"Upsert no banco: inseridos={total_ins} atualizados={total_atu}")
    print(f"CSV: {destino}")


if __name__ == "__main__":
    main()
