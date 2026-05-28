"""Coletor da JUCEES (Espírito Santo) — leiloeiros não-SP (alvo da tese).

A JUCEES expõe os leiloeiros em cards (`.leiloeiro-card`): o cabeçalho traz
``matricula: 002/1976`` e o corpo traz ``Nome:``, ``Endereço:``, ``E-mail:`` e,
quando há, o site. A rota `/leiloeiros` do subdomínio devolve o HTML renderizado.
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import BROWSER_UA, JuntaScraper, extrair_site

_MATRICULA = re.compile(r"matr[ií]cula:?\s*([\w/.\-]+)", re.IGNORECASE)
_NOME = re.compile(r"Nome:\s*(.+?)\s*(?:Endere[çc]o|E-?mail|Telefone|Site|$)", re.IGNORECASE)


class JuceesScraper(JuntaScraper):
    junta = "JUCEES"
    uf = "ES"
    url_lista = "https://leiloeiros.jucees.es.gov.br/leiloeiros"
    user_agent = BROWSER_UA

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        registros: list[LeiloeiroRaw] = []
        vistos: set[str] = set()
        for card in tree.css(".leiloeiro-card"):
            texto = re.sub(r"\s+", " ", card.text())
            m_mat = _MATRICULA.search(texto)
            m_nome = _NOME.search(texto)
            if not (m_mat and m_nome):
                continue
            numero = m_mat.group(1)
            nome = m_nome.group(1).strip()
            if not nome or numero in vistos:
                continue
            vistos.add(numero)
            registros.append(self._novo_raw(nome, numero, extrair_site(card)))
        return registros
