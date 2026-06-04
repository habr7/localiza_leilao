"""Coletor da JUCEMG (Minas Gerais) — leiloeiros não-SP (alvo da tese).

Lista pública em tabela HTML (página "Leiloeiros - Antiguidade"): coluna 1 traz
"ordem - nome", coluna 2 a matrícula. Sem site do leiloeiro.
"""

from __future__ import annotations

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas._util import parse_tabela
from src.leiloeiros.juntas.base import JuntaScraper


class JucemgScraper(JuntaScraper):
    junta = "JUCEMG"
    uf = "MG"
    url_lista = "https://jucemg.mg.gov.br/pagina/141/Leiloeiros+Antiguidade"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        return parse_tabela(html, self.uf, self.junta, self.fonte_cadastro, 0, 1)
