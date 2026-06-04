"""Coletor da JUCEA (Amazonas) — leiloeiros não-SP (alvo da tese).

Lista pública em texto rotulado: o NOME vem na linha logo acima de
"MATRÍCULA:", seguido de ENDEREÇO/TELEFONE/E-MAIL/SITE/SITUAÇÃO. Traz site.
"""

from __future__ import annotations

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas._util import parse_lista_rotulada
from src.leiloeiros.juntas.base import JuntaScraper


class JuceaScraper(JuntaScraper):
    junta = "JUCEA"
    uf = "AM"
    url_lista = "https://www.jucea.am.gov.br/leiloeiros/"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        body = tree.body.text(separator="\n") if tree.body else ""
        return parse_lista_rotulada(body, self.uf, self.junta, self.fonte_cadastro)
