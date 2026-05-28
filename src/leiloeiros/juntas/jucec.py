"""Coletor da JUCEC (Ceará) — leiloeiros não-SP (alvo da tese).

A JUCEC publica os leiloeiros numa tabela: Matrícula | Nome | Contato | Endereço.
A coluna de contato costuma trazer o ``Site:`` do leiloeiro.
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import BROWSER_UA, JuntaScraper, extrair_site


class JucecScraper(JuntaScraper):
    junta = "JUCEC"
    uf = "CE"
    url_lista = "https://www.jucec.ce.gov.br/leiloeiros/"
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
            m = re.search(r"\d+", celulas[0].text())
            nome = celulas[1].text(strip=True)
            if not (m and nome) or m.group(0) in vistos:
                continue
            vistos.add(m.group(0))
            site = extrair_site(celulas[2]) if len(celulas) > 2 else None
            registros.append(self._novo_raw(nome, m.group(0), site))
        return registros
