"""Coletor da JUCEPAR (Paraná) — leiloeiros não-SP (alvo da tese)."""

from __future__ import annotations

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import JuntaScraper


class JuceparScraper(JuntaScraper):
    junta = "JUCEPAR"
    uf = "PR"
    # TODO(rede): preencher com a URL da relação pública de leiloeiros da JUCEPAR
    # (homepage: https://www.juntacomercial.pr.gov.br).
    url_lista = None

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        raise NotImplementedError(
            "JUCEPAR: implementar selectors contra o HTML real (sessão com rede)."
        )
