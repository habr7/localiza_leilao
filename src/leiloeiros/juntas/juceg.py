"""Coletor da JUCEG (Goiás) — leiloeiros não-SP (alvo da tese).

A JUCEG publica os leiloeiros numa página (WordPress) com tabelas aninhadas.
Cada leiloeiro é uma célula-folha com um cabeçalho
``<h6>NOME (Matrícula: 007/90 de ...) – Situação: REGULAR</h6>`` e um bloco
``<pre>`` com e-mail, site e endereço.
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser, Node

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import JuntaScraper

_NOME_MATRICULA = re.compile(r"([A-ZÀ-Ý][^()]+?)\s*\(Matr[ií]cula:?\s*(\d+/\d+)", re.UNICODE)


class JucegScraper(JuntaScraper):
    junta = "JUCEG"
    uf = "GO"
    url_lista = "https://goias.gov.br/juceg/leiloeiros/"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        registros: list[LeiloeiroRaw] = []
        vistos: set[str] = set()
        for td in tree.css("td"):
            if td.css("table"):  # ignora células que contêm tabelas aninhadas
                continue
            cabecalho = td.css_first("h6") or td
            m = _NOME_MATRICULA.search(cabecalho.text())
            if not m:
                continue
            numero = m.group(2)
            if numero in vistos:
                continue
            vistos.add(numero)
            nome = re.sub(r"[\s–\-]+$", "", m.group(1)).strip()
            registros.append(self._novo_raw(nome, numero, _site(td)))
        return registros


def _site(td: Node) -> str | None:
    """Extrai o site do leiloeiro: link http (não-mailto) ou campo 'Site:' do texto."""
    for a in td.css("a"):
        href = a.attributes.get("href") or ""
        if href.startswith("http") and "mailto" not in href:
            return href
    m = re.search(r"Site:\s*([^\s<]+)", td.text())
    return m.group(1) if m else None
