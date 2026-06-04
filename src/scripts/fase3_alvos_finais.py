"""Fase 3 — classificação final dos indícios cruzando os dois sinais de JUCESP.

Combina, sobre o CSV de indícios já coletado (`sites_proprios_sp.csv`):
1. **cross-check por nome** contra a relação oficial da JUCESP (D.O.E.); e
2. a coluna `jucesp` da leitura do site (`sites_proprios_sp_verificado.csv`).

Gera `data/imoveis_sp_alvos_final.csv` com `tem_jucesp` (sim/nao/desconhecido) —
``sim`` se qualquer sinal acusou JUCESP. Os alvos puros da tese são ``nao``.

Uso:
    uv run python -m src.scripts.fase3_alvos_finais
"""

from __future__ import annotations

import csv
from pathlib import Path

import structlog

from src.core.db import get_session
from src.leiloeiros.jucesp_exclusao import carregar_nomes_jucesp
from src.leiloeiros.resolver import normalizar_nome

log = structlog.get_logger()

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
VERIFICADO = DATA_DIR / "sites_proprios_sp_verificado.csv"
INDICIOS = DATA_DIR / "sites_proprios_sp.csv"
SAIDA = DATA_DIR / "imoveis_sp_alvos_final.csv"


def main() -> None:
    fonte = VERIFICADO if VERIFICADO.exists() else INDICIOS
    linhas = list(csv.DictReader(fonte.open(encoding="utf-8")))

    with get_session() as session:
        nomes_jucesp = carregar_nomes_jucesp(session)

    campos = [*linhas[0].keys()]
    for col in ("jucesp_nome", "tem_jucesp"):
        if col not in campos:
            campos.append(col)

    clean_sites: set[str] = set()
    dirty_sites: set[str] = set()
    for ln in linhas:
        por_nome = normalizar_nome(ln.get("leiloeiro", "")) in nomes_jucesp
        ln["jucesp_nome"] = "sim" if por_nome else "nao"
        por_site = (ln.get("jucesp") or "") == "sim"
        if por_nome or por_site:
            ln["tem_jucesp"] = "sim"
            dirty_sites.add(ln["site"])
        else:
            ln["tem_jucesp"] = ln.get("jucesp") or "desconhecido"  # nao | desconhecido
            if ln["tem_jucesp"] == "nao":
                clean_sites.add(ln["site"])

    with SAIDA.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas)

    alvos = [ln for ln in linhas if ln["tem_jucesp"] == "nao"]
    print(f"\nIndícios totais: {len(linhas)}")
    print(
        f"  COM JUCESP (excluídos, por nome ou site): {sum(1 for x in linhas if x['tem_jucesp'] == 'sim')}"
    )
    print(
        f"  ALVOS PUROS (sem JUCESP): {len(alvos)} indícios em {len(clean_sites - dirty_sites)} sites"
    )
    print(f"CSV: {SAIDA}")


if __name__ == "__main__":
    main()
