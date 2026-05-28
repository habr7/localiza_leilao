"""Coletor da JUCEPI (Piauí) — leiloeiros não-SP (alvo da tese).

Lista em texto rotulado: ``NOME / Matrícula: n.º 11/2006, em ... / ... / Site: <url>``.
Usa o parser compartilhado `parse_lista_rotulada`.
"""

from __future__ import annotations

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas._util import parse_lista_rotulada
from src.leiloeiros.juntas.base import JuntaScraper


class JucepiScraper(JuntaScraper):
    junta = "JUCEPI"
    uf = "PI"
    url_lista = "https://portal.pi.gov.br/jucepi/leiloeiro-oficial/"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        body = tree.body.text(separator="\n") if tree.body else ""
        return parse_lista_rotulada(body, self.uf, self.junta, self.fonte_cadastro)
