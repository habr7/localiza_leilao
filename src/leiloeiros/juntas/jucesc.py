"""Coletor da JUCESC (Santa Catarina) — leiloeiros não-SP (alvo da tese).

Lista pública em tabela HTML (subportal de leiloeiros): colunas
AARC(matrícula) | Nome | Data | Situação. Sem site do leiloeiro.
"""

from __future__ import annotations

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas._util import parse_tabela
from src.leiloeiros.juntas.base import JuntaScraper


class JucescScraper(JuntaScraper):
    junta = "JUCESC"
    uf = "SC"
    url_lista = "https://leiloeiros.jucesc.sc.gov.br/site/index.php"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        return parse_tabela(html, self.uf, self.junta, self.fonte_cadastro, 1, 0)
