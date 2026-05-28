"""Coletor da JUCEDF (Distrito Federal) — leiloeiros não-SP (alvo da tese)."""

from __future__ import annotations

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import JuntaScraper


class JucedfScraper(JuntaScraper):
    junta = "JUCEDF"
    uf = "DF"
    # TODO(rede): preencher com a URL da relação pública de leiloeiros da JUCEDF
    # (homepage: https://www.jucis.df.gov.br).
    url_lista = None

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        raise NotImplementedError(
            "JUCEDF: implementar selectors contra o HTML real (sessão com rede)."
        )
