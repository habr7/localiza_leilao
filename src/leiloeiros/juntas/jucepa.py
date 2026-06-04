"""Coletor da JUCEPA (Pará) — leiloeiros não-SP (alvo da tese).

Lista pública (Drupal) em blocos <p>: NOME em <strong> acima de "Matrícula:",
com "Sítio Eletrônico:" trazendo o site (parte das entradas).
"""

from __future__ import annotations

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas._util import parse_lista_rotulada
from src.leiloeiros.juntas.base import JuntaScraper


class JucepaScraper(JuntaScraper):
    junta = "JUCEPA"
    uf = "PA"
    url_lista = "https://www.jucepa.pa.gov.br/node/171"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        body = tree.body.text(separator="\n") if tree.body else ""
        return parse_lista_rotulada(body, self.uf, self.junta, self.fonte_cadastro)
