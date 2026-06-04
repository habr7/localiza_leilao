"""Coletor da JUCEAC (Acre) — leiloeiros não-SP (alvo da tese).

Lista pública em cards (Elementor "link-in-bio"): ``h2`` com o nome, e um ``p``
de descrição com Matrícula/Endereço/Site. Poucos trazem site.
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas._util import _RE_URL, normalizar_site
from src.leiloeiros.juntas.base import JuntaScraper


class JuceacScraper(JuntaScraper):
    junta = "JUCEAC"
    uf = "AC"
    url_lista = "https://juceac.ac.gov.br/leiloeiro/"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        registros: list[LeiloeiroRaw] = []
        for h2 in tree.css("h2.e-link-in-bio__heading, h2"):
            nome = re.sub(r"\s+", " ", h2.text()).strip()
            if len(nome.split()) < 2:
                continue
            # Texto do card: heading + irmãos até o próximo h2.
            bloco = ""
            node = h2.next
            while node is not None and node.tag != "h2":
                bloco += " " + node.text()
                node = node.next
            m = re.search(r"Matr[íi]cula\s*n?[ºo°]?\s*([\w/\-.]+)", bloco, re.I)
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
