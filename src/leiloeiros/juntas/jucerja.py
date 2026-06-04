"""Coletor da JUCERJA (Rio de Janeiro) — leiloeiros não-SP (alvo da tese).

A lista é carregada por AJAX: o endpoint ``PaginarLeiloeiros?pagina=N`` devolve
um fragmento HTML com itens rotulados (Leiloeiro / Situação / Nº Matrícula).
Paginação até a página vir vazia. Sem site do leiloeiro.
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import JuntaScraper

URL_PAGINA = "https://www.jucerja.rj.gov.br/AuxiliaresComercio/PaginarLeiloeiros?pagina={n}"

_RE_NOME = re.compile(r"Leiloeiro:\s*(?P<nome>.+?)\s+Situa", re.IGNORECASE)
_RE_MAT = re.compile(r"N[ºo°]\s*Matr[íi]cula:\s*(?P<mat>[\w/\-.]+)", re.IGNORECASE)


def parse_fragmento(html: str) -> list[LeiloeiroRaw]:
    tree = HTMLParser(html)
    registros: list[LeiloeiroRaw] = []
    itens = tree.css("li.ats-listaLnks-item") or tree.css("li")
    for li in itens:
        texto = re.sub(r"\s+", " ", li.text())
        n = _RE_NOME.search(texto)
        m = _RE_MAT.search(texto)
        if not n or not m:
            continue
        registros.append(
            LeiloeiroRaw(
                nome=n.group("nome").strip(),
                matricula=m.group("mat").strip(),
                uf_matricula="RJ",
                junta_comercial="JUCERJA",
                fonte_cadastro="junta:jucerja",
            )
        )
    return registros


class JucerjaScraper(JuntaScraper):
    junta = "JUCERJA"
    uf = "RJ"
    url_lista = URL_PAGINA.format(n=1)

    async def coletar(self) -> list[LeiloeiroRaw]:
        registros: list[LeiloeiroRaw] = []
        for pagina in range(1, 100):
            html = await self._fetch(URL_PAGINA.format(n=pagina))
            da_pagina = parse_fragmento(html)
            if not da_pagina:
                break
            registros.extend(da_pagina)
        return registros

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        return parse_fragmento(html)
