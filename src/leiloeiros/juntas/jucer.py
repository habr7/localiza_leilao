"""Coletor da JUCER (Rondônia) — leiloeiros não-SP (alvo da tese).

Lista pública em definition-list: ``<dt><strong>NOME</strong></dt>`` seguido de
vários ``<dd><em>Rótulo: valor</em></dd>`` (Matrícula, Site, Situação...). Site
presente em parte das entradas.
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas._util import _RE_URL, normalizar_site
from src.leiloeiros.juntas.base import JuntaScraper


class JucerScraper(JuntaScraper):
    junta = "JUCER"
    uf = "RO"
    url_lista = "https://rondonia.ro.gov.br/jucer/lista-de-leiloeiros-oficiais/"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        registros: list[LeiloeiroRaw] = []
        for dt in tree.css("dt"):
            nome = re.sub(r"\s+", " ", dt.text()).strip()
            if len(nome.split()) < 2:
                continue
            # Junta o texto dos <dd> seguintes até o próximo <dt>.
            bloco = ""
            node = dt.next
            while node is not None and node.tag != "dt":
                if node.tag == "dd":
                    bloco += " " + node.text()
                node = node.next
            m = re.search(r"Matr[íi]cula:\s*([\w/\-.]+)", bloco, re.I)
            if not m:
                continue
            site_m = _RE_URL.search(bloco)
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
