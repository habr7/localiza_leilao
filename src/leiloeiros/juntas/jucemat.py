"""Coletor da JUCEMAT (Mato Grosso) — leiloeiros não-SP (alvo da tese).

A JUCEMAT publica a relação como cartões (`.featured-box`): cada cartão traz o
nome em ``<h2>``, o número da matrícula em ``span.label`` e, numa lista de ícones
(``ul.list-icons``), o endereço, telefone, e-mail e **site** do leiloeiro.
"""

from __future__ import annotations

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas._util import _RE_URL, normalizar_site
from src.leiloeiros.juntas.base import JuntaScraper


class JucematScraper(JuntaScraper):
    junta = "JUCEMAT"
    uf = "MT"
    url_lista = "https://www.jucemat.mt.gov.br/leiloeiros"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        registros: list[LeiloeiroRaw] = []
        for box in tree.css(".featured-box"):
            h2 = box.css_first("h2")
            if h2 is None:
                continue
            nome = h2.text(strip=True)
            if not nome:
                continue
            label = box.css_first("span.label")
            matricula = label.text(strip=True) if label else ""
            if not matricula:
                continue
            site = None
            for li in box.css("li"):
                m = _RE_URL.search(li.text())
                if m:
                    site = m.group(0)
                    break
            registros.append(
                LeiloeiroRaw(
                    nome=nome,
                    matricula=matricula,
                    # Matrícula da JUCEMAT é só o número (ex.: "4"); fixamos UF/Junta.
                    uf_matricula=self.uf,
                    junta_comercial=self.junta,
                    site_oficial=normalizar_site(site),
                    fonte_cadastro=self.fonte_cadastro,
                )
            )
        return registros
