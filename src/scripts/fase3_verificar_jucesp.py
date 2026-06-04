"""Fase 3 — verifica JUCESP nos sites com indício de imóvel em SP.

Lê o CSV de descoberta (`data/sites_proprios_sp.csv`), pega os sites distintos com
indício e, para cada um, verifica se o leiloeiro tem matrícula **JUCESP** (ver
`verificacao.py`). Grava `data/sites_proprios_sp_verificado.csv` com uma coluna
``jucesp`` (sim/nao/desconhecido). Só os ``jucesp=nao`` são alvos puros da tese.

Uso:
    uv run python -m src.scripts.fase3_verificar_jucesp
"""

from __future__ import annotations

import asyncio
import csv
from pathlib import Path

import structlog

from src.ingestao.sites_proprios.verificacao import VerificadorJucesp

log = structlog.get_logger()

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
ENTRADA = DATA_DIR / "sites_proprios_sp.csv"
SAIDA = DATA_DIR / "sites_proprios_sp_verificado.csv"


async def _verificar_sites(sites: list[str]) -> dict[str, str]:
    resultado: dict[str, str] = {}
    async with VerificadorJucesp(delay_s=1.0) as v:
        for i, site in enumerate(sites, 1):
            try:
                tem = await v.tem_jucesp(site)
            except Exception as exc:  # noqa: BLE001
                log.warning("verif_erro", site=site, erro=type(exc).__name__)
                tem = None
            resultado[site] = "sim" if tem else ("desconhecido" if tem is None else "nao")
            log.info("verif_site", i=i, total=len(sites), site=site, jucesp=resultado[site])
    return resultado


def main() -> None:
    linhas = list(csv.DictReader(ENTRADA.open(encoding="utf-8")))
    sites = list(dict.fromkeys(ln["site"] for ln in linhas))
    log.info("verificar_jucesp", sites_distintos=len(sites))

    status = asyncio.run(_verificar_sites(sites))

    campos = [*linhas[0].keys(), "jucesp"] if linhas else ["site", "jucesp"]
    with SAIDA.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=campos)
        writer.writeheader()
        for ln in linhas:
            ln["jucesp"] = status.get(ln["site"], "desconhecido")
            writer.writerow(ln)

    limpos = sorted(s for s, st in status.items() if st == "nao")
    com_sp = sorted(s for s, st in status.items() if st == "sim")
    print(f"\nSites verificados: {len(sites)}")
    print(f"  limpos (sem JUCESP, ALVOS): {len(limpos)}")
    print(f"  com JUCESP (excluir): {len(com_sp)}")
    print(f"CSV: {SAIDA}")
    print("\nAlvos (sem JUCESP):")
    for s in limpos:
        print("  ", s)


if __name__ == "__main__":
    main()
