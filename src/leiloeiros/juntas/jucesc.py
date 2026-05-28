"""Coletor da JUCESC (Santa Catarina) — leiloeiros não-SP (alvo da tese).

A JUCESC publica os leiloeiros numa tabela única (subdomínio
`leiloeiros.jucesc.sc.gov.br`) com colunas: nº matrícula | Nome | Data Matrícula
| Situação. A lista não traz site (enriquecer depois, se necessário).
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import BROWSER_UA, JuntaScraper


class JucescScraper(JuntaScraper):
    junta = "JUCESC"
    uf = "SC"
    url_lista = "https://leiloeiros.jucesc.sc.gov.br/site/"
    user_agent = BROWSER_UA

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        tabelas = tree.css("table")
        if not tabelas:
            return []
        tabela = max(tabelas, key=lambda t: len(t.css("tr")))
        registros: list[LeiloeiroRaw] = []
        vistos: set[str] = set()
        for linha in tabela.css("tr"):
            celulas = linha.css("td")
            if len(celulas) < 2:
                continue
            numero = celulas[0].text(strip=True)
            nome = celulas[1].text(strip=True)
            if not (re.fullmatch(r"\d+", numero) and nome) or numero in vistos:
                continue
            vistos.add(numero)
            registros.append(self._novo_raw(nome, numero))
        return registros
