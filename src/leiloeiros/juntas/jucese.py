"""Coletor da JUCESE (Sergipe) — leiloeiros não-SP (alvo da tese).

Lista pública em itens ``<li>``: ``<strong>Nº – Nome</strong>`` seguido de linhas
rotuladas (Matricula:, Site:, Situação:). Traz site do leiloeiro.
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas._util import _RE_URL, normalizar_site
from src.leiloeiros.juntas.base import JuntaScraper

_RE_ORDEM = re.compile(r"^\s*\d+\s*[ºo°]?\s*[-–]\s*")


class JuceseScraper(JuntaScraper):
    junta = "JUCESE"
    uf = "SE"
    url_lista = "https://jucese.se.gov.br/leiloeiros/"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        registros: list[LeiloeiroRaw] = []
        for li in tree.css("li"):
            texto = li.text(separator="\n")
            m = re.search(r"Matr[íi]cula:\s*([\w/\-.]+)", texto, re.I)
            if not m:
                continue
            strong = li.css_first("strong")
            nome = _RE_ORDEM.sub("", strong.text().strip()) if strong else ""
            if len(nome.split()) < 2:
                continue
            site_m = _RE_URL.search(texto)
            registros.append(
                LeiloeiroRaw(
                    nome=nome,
                    matricula=m.group(1).strip(),
                    uf_matricula=self.uf,
                    junta_comercial=self.junta,
                    site_oficial=normalizar_site(site_m.group(0) if site_m else None),
                    fonte_cadastro=self.fonte_cadastro,
                )
            )
        return registros
