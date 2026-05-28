"""Fase 3 — identifica imóveis-alvo: imóvel em SP + leiloeiro NÃO-SP.

Roda o(s) scraper(s) de agregador, resolve a UF efetiva do leiloeiro a partir das
matrículas exibidas (regra "JUCESP vence" — ver `uf_efetiva_de_matriculas`) e
exporta um CSV em ``data/``. Os imóveis-alvo da tese são os com ``uf_imovel=SP``
e ``uf_leiloeiro != SP``.

Uso:
    uv run python -m src.scripts.fase3_identificar_imoveis [--max-paginas N]

O CSV completo (todos os imóveis SP coletados, com a flag ``fora_sp``) fica em
``data/imoveis_sp.csv``; o recorte só com os alvos, em ``data/imoveis_alvo.csv``.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
from collections import Counter
from pathlib import Path

import structlog

from src.ingestao.agregadores.megaleiloes import MegaLeiloesScraper
from src.ingestao.base import LoteRaw
from src.leiloeiros.resolver import uf_efetiva_de_matriculas

log = structlog.get_logger()

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

COLUNAS = [
    "fonte",
    "codigo",
    "titulo",
    "tipo_imovel",
    "cidade",
    "uf_imovel",
    "lance_minimo",
    "tipo_leilao",
    "comitente",
    "leiloeiro",
    "uf_leiloeiro",
    "fora_sp",
    "matriculas",
    "url",
]


def _linha(lote: LoteRaw) -> dict[str, object]:
    uf_leiloeiro = uf_efetiva_de_matriculas(list(lote.leiloeiro_matriculas))
    fora_sp = (uf_leiloeiro is not None) and (uf_leiloeiro != "SP")
    return {
        "fonte": lote.fonte_origem,
        "codigo": lote.numero_lote or "",
        "titulo": lote.titulo or "",
        "tipo_imovel": lote.tipo_imovel or "",
        "cidade": lote.cidade or "",
        "uf_imovel": lote.uf or "",
        "lance_minimo": lote.lance_minimo_1 or "",
        "tipo_leilao": lote.tipo_leilao or "",
        "comitente": lote.comitente or "",
        "leiloeiro": lote.leiloeiro_nome or "",
        "uf_leiloeiro": uf_leiloeiro or "",
        "fora_sp": "sim" if fora_sp else "nao",
        "matriculas": " | ".join(lote.leiloeiro_matriculas),
        "url": lote.fonte_url,
    }


def _escrever_csv(path: Path, linhas: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUNAS)
        writer.writeheader()
        writer.writerows(linhas)


async def coletar(max_paginas: int | None) -> list[LoteRaw]:
    async with MegaLeiloesScraper() as scraper:
        return await scraper.listar_lotes_sp(max_paginas=max_paginas)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-paginas",
        type=int,
        default=3,
        help="Máximo de páginas de listagem a varrer (default: 3; ~48 lotes/página).",
    )
    args = parser.parse_args()

    lotes = asyncio.run(coletar(args.max_paginas))
    linhas = [_linha(lo) for lo in lotes]
    alvos = [ln for ln in linhas if ln["fora_sp"] == "sim"]

    _escrever_csv(DATA_DIR / "imoveis_sp.csv", linhas)
    _escrever_csv(DATA_DIR / "imoveis_alvo.csv", alvos)

    por_uf = Counter(ln["uf_leiloeiro"] or "?" for ln in linhas)
    sem_matricula = sum(1 for ln in linhas if not ln["matriculas"])
    log.info(
        "fase3_resumo",
        imoveis_sp=len(linhas),
        imoveis_alvo_fora_sp=len(alvos),
        sem_matricula_resolvida=sem_matricula,
        por_uf_leiloeiro=dict(por_uf),
    )
    print(f"\nImóveis SP coletados: {len(linhas)}")
    print(f"Imóveis-alvo (leiloeiro não-SP): {len(alvos)}")
    print(f"Distribuição por UF do leiloeiro: {dict(por_uf)}")
    print(f"CSVs: {DATA_DIR / 'imoveis_sp.csv'} e {DATA_DIR / 'imoveis_alvo.csv'}")


if __name__ == "__main__":
    main()
