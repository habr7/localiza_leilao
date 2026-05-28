"""Consulta dos lotes-alvo (Fase C — usabilidade simples).

Lista e exporta os lotes que satisfazem a tese: imóvel localizado em SP, leilão
ABERTO, conduzido por leiloeiro NÃO-SP. Junta `lotes` + `leiloes` + `leiloeiros`,
imprime um resumo no console e grava `data/lotes_alvo.csv` para consulta fácil.

Uso:
    uv run python -m src.scripts.consultar_lotes_alvo
    uv run python -m src.scripts.consultar_lotes_alvo --tipo extrajudicial
    uv run python -m src.scripts.consultar_lotes_alvo --fonte site_proprio
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import aliased

from src.core.db import get_session
from src.core.models import Leilao, Leiloeiro, Lote

SAIDA_CSV = Path("data/lotes_alvo.csv")
COLUNAS = [
    "cidade",
    "uf",
    "tipo_imovel",
    "lance_minimo_1",
    "leiloeiro",
    "uf_leiloeiro",
    "tipo",
    "fonte_tipo",
    "fonte_origem",
    "data_1praca",
    "fonte_url",
]


def consultar(tipo: str | None, fonte_tipo: str | None) -> list[dict[str, object]]:
    """Retorna os lotes-alvo (imóvel SP + leiloeiro não-SP + leilão aberto)."""
    leiloeiro = aliased(Leiloeiro)
    query = (
        select(Lote, Leilao, leiloeiro)
        .join(Leilao, Lote.leilao_id == Leilao.id)
        .join(leiloeiro, Leilao.leiloeiro_id == leiloeiro.id, isouter=True)
        .where(
            Lote.uf == "SP",
            Leilao.uf_leiloeiro.isnot(None),
            Leilao.uf_leiloeiro != "SP",
            Leilao.status == "aberto",
        )
    )
    if tipo:
        query = query.where(Leilao.tipo == tipo)
    if fonte_tipo:
        query = query.where(Leilao.fonte_tipo == fonte_tipo)
    query = query.order_by(Leilao.uf_leiloeiro, Lote.cidade)

    linhas: list[dict[str, object]] = []
    with get_session() as session:
        for lote, leilao, leilo in session.execute(query).all():
            linhas.append(
                {
                    "cidade": lote.cidade,
                    "uf": lote.uf,
                    "tipo_imovel": lote.tipo_imovel,
                    "lance_minimo_1": lote.lance_minimo_1,
                    "leiloeiro": leilo.nome if leilo else None,
                    "uf_leiloeiro": leilao.uf_leiloeiro,
                    "tipo": leilao.tipo,
                    "fonte_tipo": leilao.fonte_tipo,
                    "fonte_origem": leilao.fonte_origem,
                    "data_1praca": leilao.data_1praca,
                    "fonte_url": leilao.fonte_url,
                }
            )
    return linhas


def exportar_csv(linhas: list[dict[str, object]], destino: Path = SAIDA_CSV) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as fh:
        escritor = csv.DictWriter(fh, fieldnames=COLUNAS)
        escritor.writeheader()
        escritor.writerows(linhas)


def main() -> None:
    """Consulta os lotes-alvo, imprime um resumo e exporta o CSV."""
    parser = argparse.ArgumentParser(description="Consulta dos lotes-alvo da tese.")
    parser.add_argument("--tipo", choices=["judicial", "extrajudicial"], default=None)
    parser.add_argument(
        "--fonte", dest="fonte_tipo", default=None, help="ex.: site_proprio, agregador"
    )
    args = parser.parse_args()

    linhas = consultar(args.tipo, args.fonte_tipo)
    exportar_csv(linhas)

    print(f"Lotes-alvo (imóvel SP + leiloeiro não-SP + aberto): {len(linhas)}")
    por_uf: dict[str, int] = {}
    por_fonte: dict[str, int] = {}
    for ln in linhas:
        por_uf[str(ln["uf_leiloeiro"])] = por_uf.get(str(ln["uf_leiloeiro"]), 0) + 1
        por_fonte[str(ln["fonte_tipo"])] = por_fonte.get(str(ln["fonte_tipo"]), 0) + 1
    print(f"  por UF do leiloeiro: {por_uf}")
    print(f"  por tipo de fonte:   {por_fonte}")
    print(f"\nExportado para {SAIDA_CSV}")
    for ln in linhas[:10]:
        print(
            f"  [{ln['uf_leiloeiro']}/{ln['tipo']:13}] {str(ln['cidade'])[:18]:18} "
            f"R$ {ln['lance_minimo_1']}  {ln['leiloeiro']}"
        )


if __name__ == "__main__":
    main()
