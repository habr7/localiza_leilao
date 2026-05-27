"""Coletor da JUCEMG (Minas Gerais) — leiloeiros não-SP (alvo da tese)."""

from __future__ import annotations

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import JuntaScraper


class JucemgScraper(JuntaScraper):
    junta = "JUCEMG"
    uf = "MG"
    # TODO(rede): preencher com a URL da relação pública de leiloeiros da JUCEMG
    # (homepage: https://www.jucemg.mg.gov.br).
    url_lista = None

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        raise NotImplementedError(
            "JUCEMG: implementar selectors contra o HTML real (sessão com rede)."
        )
