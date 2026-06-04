"""Coletor da JUCEC (Ceará) — leiloeiros não-SP (alvo da tese).

Lista pública em tabela HTML: Matrícula(+data) | Nome | Contato(site) |
Endereço. A matrícula vem colada à data na coluna 0; o site na coluna Contato.
"""

from __future__ import annotations

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas._util import parse_tabela
from src.leiloeiros.juntas.base import JuntaScraper


class JucecScraper(JuntaScraper):
    junta = "JUCEC"
    uf = "CE"
    url_lista = "https://www.jucec.ce.gov.br/leiloeiros/"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        return parse_tabela(
            html,
            self.uf,
            self.junta,
            self.fonte_cadastro,
            idx_nome=1,
            idx_matricula=0,
            idx_site=2,
            matricula_so_numero=True,
        )
