"""Coletor da JUCERJA (Rio de Janeiro) — leiloeiros não-SP (alvo da tese)."""

from __future__ import annotations

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import JuntaScraper


class JucerjaScraper(JuntaScraper):
    junta = "JUCERJA"
    uf = "RJ"
    # TODO(rede): preencher com a URL da relação pública de leiloeiros da JUCERJA
    # (homepage: https://www.jucerja.rj.gov.br).
    url_lista = None

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        raise NotImplementedError(
            "JUCERJA: implementar selectors contra o HTML real (sessão com rede)."
        )
