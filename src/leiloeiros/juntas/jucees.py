"""Coletor da JUCEES (Espírito Santo) — leiloeiros não-SP (alvo da tese).

Lista pública em cards ``.leiloeiro-card`` com campos rotulados explícitos:
``matricula:``, ``Nome:``, ``Site:``. Traz site do leiloeiro.
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas._util import _RE_URL, normalizar_site
from src.leiloeiros.juntas.base import JuntaScraper


class JuceesScraper(JuntaScraper):
    junta = "JUCEES"
    uf = "ES"
    url_lista = "https://leiloeiros.jucees.es.gov.br/leiloeiros"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        registros: list[LeiloeiroRaw] = []
        for card in tree.css(".leiloeiro-card"):
            texto = card.text(separator="\n")
            nome_m = re.search(r"Nome:\s*(.+)", texto)
            mat_m = re.search(r"matr[íi]cula:\s*([\w/\-.]+)", texto, re.I)
            if not nome_m or not mat_m:
                continue
            nome = nome_m.group(1).strip()
            if len(nome.split()) < 2:
                continue
            site_m = _RE_URL.search(texto)
            registros.append(
                LeiloeiroRaw(
                    nome=nome,
                    matricula=mat_m.group(1).strip(),
                    uf_matricula=self.uf,
                    junta_comercial=self.junta,
                    site_oficial=normalizar_site(site_m.group(0) if site_m else None),
                    fonte_cadastro=self.fonte_cadastro,
                )
            )
        return registros
