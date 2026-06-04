"""Coletor da JUCEMS (Mato Grosso do Sul) — leiloeiros não-SP (alvo da tese).

Lista pública (WordPress) em texto rotulado: o NOME (em <u><strong>) vem logo
acima de "Matrícula:", seguido de Endereço/Fone/E-mail/Site/Situação. Traz site.
"""

from __future__ import annotations

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas._util import parse_lista_rotulada
from src.leiloeiros.juntas.base import JuntaScraper


class JucemsScraper(JuntaScraper):
    junta = "JUCEMS"
    uf = "MS"
    url_lista = (
        "https://www.jucems.ms.gov.br/empresas/controles-especiais/agentes-auxiliares/leiloeiros/"
    )

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        body = tree.body.text(separator="\n") if tree.body else ""
        return parse_lista_rotulada(body, self.uf, self.junta, self.fonte_cadastro)
