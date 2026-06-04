"""Coletor da JUCER (Rondônia) — leiloeiros não-SP (alvo da tese).

Lista pública em definition-lists ``<dl>`` aninhados (nome em ``<dt><strong>``,
campos em ``<dd><em>Rótulo: valor</em></dd>``). Como o aninhamento quebra a
travessia por irmãos, lemos o texto linear e aplicamos o parser rotulado
(``NOME`` acima de ``Matrícula:``, com ``Site:`` no bloco). Traz site em parte.
"""

from __future__ import annotations

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas._util import parse_lista_rotulada
from src.leiloeiros.juntas.base import JuntaScraper


class JucerScraper(JuntaScraper):
    junta = "JUCER"
    uf = "RO"
    url_lista = "https://rondonia.ro.gov.br/jucer/lista-de-leiloeiros-oficiais/"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        body = tree.body.text(separator="\n") if tree.body else ""
        return parse_lista_rotulada(body, self.uf, self.junta, self.fonte_cadastro)
