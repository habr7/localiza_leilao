"""Fase 3 — varre os sites próprios dos leiloeiros não-SP atrás de imóveis em SP.

Carrega do cadastro os leiloeiros com `site_oficial` (populado pela Fase 2 a
partir das Juntas), varre cada site (heurística de descoberta — ver
`src/ingestao/sites_proprios/scanner.py`) e exporta os indícios de imóvel em SP
em ``data/sites_proprios_sp.csv``.

É aqui que mora a maior assimetria da tese: imóvel paulista anunciado no site de
um leiloeiro de fora, fora do radar dos agregadores nacionais.

Uso:
    uv run python -m src.scripts.fase3_sites_proprios [--limite N] [--max-paginas M]
"""

from __future__ import annotations

import argparse
import asyncio
import csv
from pathlib import Path

import structlog
from sqlalchemy import select

from src.core.db import get_session
from src.core.models import Leiloeiro
from src.ingestao.sites_proprios.scanner import AchadoSP, SiteProprioScanner
from src.leiloeiros.jucesp_exclusao import carregar_nomes_jucesp
from src.leiloeiros.resolver import normalizar_nome

log = structlog.get_logger()

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
COLUNAS = ["leiloeiro", "uf_leiloeiro", "junta", "site", "cidade_sp", "pagina_url", "contexto"]


def _carregar_sites(excluir_jucesp: bool = True) -> list[tuple[str, str, str, str]]:
    """(nome, uf, junta, site) dos leiloeiros não-SP com site, um por domínio.

    Com ``excluir_jucesp`` (padrão), remove quem também tem matrícula JUCESP
    (cross-check por nome) — restando só os alvos puros da tese. Deduplica por
    site para não varrer o mesmo domínio duas vezes.
    """
    with get_session() as session:
        nomes_jucesp = carregar_nomes_jucesp(session) if excluir_jucesp else set()
        q = (
            select(Leiloeiro)
            .where(Leiloeiro.site_oficial.isnot(None))
            .where(Leiloeiro.uf_matricula != "SP")
            .where(Leiloeiro.ativo.is_(True))
        )
        por_site: dict[str, tuple[str, str, str, str]] = {}
        for lo in session.scalars(q):
            if not lo.site_oficial:
                continue
            if excluir_jucesp and normalizar_nome(lo.nome) in nomes_jucesp:
                continue
            por_site.setdefault(
                lo.site_oficial,
                (lo.nome, lo.uf_matricula, lo.junta_comercial, lo.site_oficial),
            )
        return list(por_site.values())


async def _varrer_todos(
    sites: list[tuple[str, str, str, str]], max_paginas: int
) -> list[dict[str, str]]:
    linhas: list[dict[str, str]] = []
    async with SiteProprioScanner(delay_s=1.0) as scanner:
        for idx, (nome, uf, junta, site) in enumerate(sites, 1):
            try:
                achados: list[AchadoSP] = await scanner.varrer_site(site, max_paginas=max_paginas)
            except Exception as exc:  # noqa: BLE001 — um site quebrado não para a varredura
                log.warning("site_erro", site=site, erro=type(exc).__name__)
                achados = []
            for a in achados:
                linhas.append(
                    {
                        "leiloeiro": nome,
                        "uf_leiloeiro": uf,
                        "junta": junta,
                        "site": site,
                        "cidade_sp": a.cidade or "",
                        "pagina_url": a.pagina_url,
                        "contexto": a.contexto,
                    }
                )
            log.info("site_varrido", i=idx, total=len(sites), site=site, achados=len(achados))
    return linhas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limite", type=int, default=None, help="nº máx. de sites a varrer")
    parser.add_argument("--max-paginas", type=int, default=8, help="páginas por site")
    args = parser.parse_args()

    sites = _carregar_sites()
    if args.limite:
        sites = sites[: args.limite]
    log.info("sites_carregados", total=len(sites))

    linhas = asyncio.run(_varrer_todos(sites, args.max_paginas))

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    destino = DATA_DIR / "sites_proprios_sp.csv"
    with destino.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUNAS)
        writer.writeheader()
        writer.writerows(linhas)

    sites_com_achado = len({ln["site"] for ln in linhas})
    print(f"\nSites varridos: {len(sites)}")
    print(f"Indícios de imóvel em SP: {len(linhas)} (em {sites_com_achado} sites)")
    print(f"CSV: {destino}")


if __name__ == "__main__":
    main()
