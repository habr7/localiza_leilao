"""Coletor da JUCESC (Santa Catarina) — leiloeiros não-SP (alvo da tese)."""

from __future__ import annotations

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import JuntaScraper


class JucescScraper(JuntaScraper):
    junta = "JUCESC"
    uf = "SC"
    # TODO(rede): preencher com a URL da relação pública de leiloeiros da JUCESC
    # (homepage: https://www.jucesc.sc.gov.br).
    url_lista = None

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        raise NotImplementedError(
            "JUCESC: implementar selectors contra o HTML real (sessão com rede)."
        )
