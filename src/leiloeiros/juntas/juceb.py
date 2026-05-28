"""Coletor da JUCEB (Bahia) — leiloeiros não-SP (alvo da tese).

A JUCEB publica os leiloeiros numa tabela única com colunas fixas:
Nome | Contatos | Endereço | Nomeação | Matrícula | Nº Portaria | Situação.
O site, quando há, é um link http na coluna de contatos.
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser, Node

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import JuntaScraper

# Índices das colunas na tabela da JUCEB.
_COL_NOME = 0
_COL_CONTATOS = 1
_COL_MATRICULA = 4


class JucebScraper(JuntaScraper):
    junta = "JUCEB"
    uf = "BA"
    url_lista = "https://www.ba.gov.br/juceb/home/matriculas-e-carteira-profissional/leiloeiros"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        tabela = tree.css_first("table")
        if tabela is None:
            return []
        registros: list[LeiloeiroRaw] = []
        vistos: set[str] = set()
        for linha in tabela.css("tr"):
            celulas = linha.css("td")
            if len(celulas) <= _COL_MATRICULA:
                continue  # cabeçalho ou linha incompleta
            matricula = celulas[_COL_MATRICULA].text(strip=True)
            if not matricula or matricula in vistos:
                continue
            # O nome às vezes vem com o rótulo "Preposto" concatenado; corta nele.
            nome = re.sub(r"\s*Preposto.*$", "", celulas[_COL_NOME].text(strip=True)).strip()
            if not nome:
                continue
            vistos.add(matricula)
            registros.append(self._novo_raw(nome, matricula, _site(celulas[_COL_CONTATOS])))
        return registros


def _site(celula: Node) -> str | None:
    """Extrai o site (primeiro link http não-mailto) da coluna de contatos."""
    for a in celula.css("a"):
        href = a.attributes.get("href") or ""
        if href.startswith("http") and "mailto" not in href:
            return href
    return None
