"""Coletor da JUCEG (Goiás) — leiloeiros não-SP (alvo da tese)."""

from __future__ import annotations

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import JuntaScraper


class JucegScraper(JuntaScraper):
    junta = "JUCEG"
    uf = "GO"
    # TODO(rede): preencher com a URL da relação pública de leiloeiros da JUCEG
    # (homepage: https://www.juceg.go.gov.br).
    url_lista = None

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        raise NotImplementedError(
            "JUCEG: implementar selectors contra o HTML real (sessão com rede)."
        )
