"""Coletor da JUCEP/JUCEPB (Paraíba) — leiloeiros não-SP (alvo da tese).

Lista em texto rotulado: ``NOME / Matrícula: 10/2014 / ... / Site: <url>``.
Usa o parser compartilhado `parse_lista_rotulada`.
"""

from __future__ import annotations

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas._util import parse_lista_rotulada
from src.leiloeiros.juntas.base import JuntaScraper


class JucepbScraper(JuntaScraper):
    junta = "JUCEPB"
    uf = "PB"
    url_lista = "https://jucep.pb.gov.br/contatos/leiloeiros"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        body = tree.body.text(separator="\n") if tree.body else ""
        return parse_lista_rotulada(body, self.uf, self.junta, self.fonte_cadastro)
