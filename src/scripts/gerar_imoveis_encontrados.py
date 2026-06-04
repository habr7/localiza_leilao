"""Consolida TODOS os imóveis encontrados num único CSV para análise.

Junta as três fontes desta investigação num arquivo com colunas uniformes
(cidade, link, descrição, valor), marcando a origem e o status JUCESP:

1. ``imoveis_sp.csv``               — agregador Mega Leilões (estruturado; JUCESP).
2. ``imoveis_sp_sites_proprios.csv``— sites próprios dedicados (estruturado; limpo).
3. ``imoveis_sp_nacional.csv``      — varredura nacional dos sites limpos
   (heurístico; valor extraído do contexto quando presente).

Saída: ``data/imoveis_encontrados.csv``.

Uso:
    uv run python -m src.scripts.gerar_imoveis_encontrados
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SAIDA = DATA_DIR / "imoveis_encontrados.csv"

COLUNAS = [
    "fonte",
    "leiloeiro",
    "uf_leiloeiro",
    "jucesp",
    "cidade",
    "tipo_imovel",
    "descricao",
    "valor",
    "link",
]

_RE_MONEY = re.compile(r"R\$\s*([\d.]+,\d{2})")


def _valor(texto: str) -> str:
    """Extrai o 1º valor em R$ de um texto (ou vazio)."""
    m = _RE_MONEY.search(texto or "")
    return m.group(1) if m else ""


def _ler(nome: str) -> list[dict[str, str]]:
    caminho = DATA_DIR / nome
    if not caminho.exists():
        return []
    with caminho.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _do_mega() -> list[dict[str, str]]:
    linhas = []
    for r in _ler("imoveis_sp.csv"):
        linhas.append(
            {
                "fonte": "megaleiloes (agregador)",
                "leiloeiro": r.get("leiloeiro", ""),
                "uf_leiloeiro": r.get("uf_leiloeiro", ""),
                # No Mega, todos resolveram para SP (têm JUCESP).
                "jucesp": "sim" if r.get("fora_sp") == "nao" else "?",
                "cidade": r.get("cidade", ""),
                "tipo_imovel": r.get("tipo_imovel", ""),
                "descricao": r.get("titulo", ""),
                "valor": str(r.get("lance_minimo", "") or ""),
                "link": r.get("url", ""),
            }
        )
    return linhas


def _do_sites_dedicados() -> list[dict[str, str]]:
    linhas = []
    for r in _ler("imoveis_sp_sites_proprios.csv"):
        desc = " ".join(x for x in (r.get("tipo_imovel"), r.get("bairro"), r.get("praca")) if x)
        linhas.append(
            {
                "fonte": f"site_proprio: {r.get('fonte', '')}",
                "leiloeiro": r.get("leiloeiro", ""),
                "uf_leiloeiro": r.get("uf_leiloeiro", ""),
                "jucesp": "nao",  # site verificado sem JUCESP
                "cidade": r.get("cidade", ""),
                "tipo_imovel": r.get("tipo_imovel", ""),
                "descricao": desc,
                "valor": str(r.get("lance_minimo", "") or ""),
                "link": r.get("url", ""),
            }
        )
    return linhas


def _do_nacional() -> list[dict[str, str]]:
    linhas = []
    for r in _ler("imoveis_sp_nacional.csv"):
        dominio = re.sub(r"https?://(www\.)?", "", r.get("site", "")).rstrip("/")
        linhas.append(
            {
                "fonte": f"site_proprio: {dominio}",
                "leiloeiro": r.get("leiloeiro", ""),
                "uf_leiloeiro": r.get("uf_leiloeiro", ""),
                "jucesp": "nao",  # já filtrado por nome (alvos puros)
                "cidade": r.get("cidade_sp", ""),
                "tipo_imovel": "",
                "descricao": (r.get("contexto", "") or "")[:200],
                "valor": _valor(r.get("contexto", "")),
                "link": r.get("pagina_url", ""),
            }
        )
    return linhas


def main() -> None:
    linhas = _do_sites_dedicados() + _do_nacional() + _do_mega()
    # Deduplica por (link, cidade, descricao).
    vistos: set[tuple[str, str, str]] = set()
    unicas = []
    for ln in linhas:
        chave = (ln["link"], ln["cidade"], ln["descricao"][:60])
        if chave in vistos:
            continue
        vistos.add(chave)
        unicas.append(ln)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUNAS)
        writer.writeheader()
        writer.writerows(unicas)

    limpos = sum(1 for x in unicas if x["jucesp"] == "nao")
    com_valor = sum(1 for x in unicas if x["valor"])
    print(f"\nImóveis encontrados (total): {len(unicas)}")
    print(f"  sem JUCESP (alvos da tese): {limpos}")
    print(f"  com JUCESP (referência): {len(unicas) - limpos}")
    print(f"  com valor preenchido: {com_valor}")
    print(f"CSV: {SAIDA}")


if __name__ == "__main__":
    main()
