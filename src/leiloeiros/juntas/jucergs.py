"""Coletor da JUCERGS (Rio Grande do Sul) — leiloeiros não-SP (alvo da tese)."""

from __future__ import annotations

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import JuntaScraper


class JucergsScraper(JuntaScraper):
    junta = "JUCERGS"
    uf = "RS"
    # TODO(rede): preencher com a URL da relação pública de leiloeiros da JUCERGS
    # (homepage: https://jucisrs.rs.gov.br).
    url_lista = None

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        raise NotImplementedError(
            "JUCERGS: implementar selectors contra o HTML real (sessão com rede)."
        )
