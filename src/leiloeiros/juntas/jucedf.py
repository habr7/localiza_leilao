"""Coletor da JUCEDF / JUCIS-DF (Distrito Federal) — leiloeiros não-SP.

Lista pública em blocos <p> rotulados (NOME em <strong>, depois Matrícula:,
Endereço:, Site:, E-mail:, Situação Funcional:). Traz site do leiloeiro.
"""

from __future__ import annotations

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas._util import parse_blocos_rotulados
from src.leiloeiros.juntas.base import JuntaScraper


class JucedfScraper(JuntaScraper):
    junta = "JUCEDF"
    uf = "DF"
    url_lista = "https://www.jucis.df.gov.br/leiloeiros/"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        return parse_blocos_rotulados(html, self.uf, self.junta, self.fonte_cadastro, "p")
