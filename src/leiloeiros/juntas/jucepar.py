"""Coletor da JUCEPAR (Paraná) — leiloeiros não-SP (alvo da tese).

A JUCEPAR publica os leiloeiros em itens "collapsible": o título traz
``NOME | Matrícula: 21/329-L | Data: ...`` e o corpo traz endereço, telefone e
``Site:``. Título e corpo estão pareados em document order.
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import BROWSER_UA, JuntaScraper, extrair_site

_TITULO = re.compile(r"(.+?)\s*\|\s*Matr[ií]cula:\s*([\w/.\-]+)", re.IGNORECASE)


class JuceparScraper(JuntaScraper):
    junta = "JUCEPAR"
    uf = "PR"
    url_lista = "https://www.juntacomercial.pr.gov.br/Pagina/LEILOEIROS-OFICIAIS-HABILITADOS"
    user_agent = BROWSER_UA

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        titulos = tree.css(".collapsible-item-title-link-text")
        corpos = tree.css(".collapsible-item-body")
        registros: list[LeiloeiroRaw] = []
        vistos: set[str] = set()
        for i, titulo in enumerate(titulos):
            m = _TITULO.match(titulo.text())
            if not m:
                continue
            numero = m.group(2)
            if numero in vistos:
                continue
            vistos.add(numero)
            corpo = corpos[i] if i < len(corpos) else None
            site = extrair_site(corpo) if corpo is not None else None
            registros.append(self._novo_raw(m.group(1).strip(), numero, site))
        return registros
