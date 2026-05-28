"""Coletor da JUCEPAR (Paraná) — leiloeiros não-SP (alvo da tese).

A JUCEPAR publica a relação de leiloeiros habilitados em HTML, num acordeão de
itens (`.collapsible-item`): cada item traz, no título, o nome e a matrícula
(``NOME | Matrícula: 21/329-L | Data: ...``) e, no corpo, endereço, telefones,
**Site** e e-mail. O site oficial é o elo que destrava a Fase 3 (sites próprios):
é nele que o leiloeiro de fora anuncia imóveis em SP.
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import JuntaScraper

# Título do item: "NOME | Matrícula: 21/329-L | Data: 02/08/2021".
_RE_TITULO = re.compile(
    r"(?P<nome>.+?)\s*\|\s*Matr[íi]cula:\s*(?P<matricula>[^|]+?)\s*(?:\|\s*Data:.*)?$"
)
_RE_SITE = re.compile(r"Site:\s*(?P<site>\S+)")
# Valores que significam "sem site".
_SITE_VAZIO = {"-", "--", "n/a", "na", "não", "nao", "x"}


def _normalizar_site(site: str | None) -> str | None:
    """Limpa e completa a URL do site (ou None se não houver site real)."""
    if not site:
        return None
    site = site.strip().rstrip(".,;").strip()
    if not site or site.lower() in _SITE_VAZIO or "@" in site:
        return None
    if not site.startswith(("http://", "https://")):
        site = "https://" + site.lstrip("/")
    return site


class JuceparScraper(JuntaScraper):
    junta = "JUCEPAR"
    uf = "PR"
    url_lista = "https://www.juntacomercial.pr.gov.br/Pagina/LEILOEIROS-OFICIAIS-HABILITADOS"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        registros: list[LeiloeiroRaw] = []
        for item in tree.css(".collapsible-item"):
            titulo = item.css_first("a.collapsible-item-title-link")
            if titulo is None:
                continue
            m = _RE_TITULO.match(re.sub(r"\s+", " ", titulo.text()).strip())
            if not m:
                continue
            corpo = re.sub(r"\s+", " ", item.text())
            site_m = _RE_SITE.search(corpo)
            registros.append(
                LeiloeiroRaw(
                    nome=m.group("nome").strip(),
                    matricula=m.group("matricula").strip(),
                    # A matrícula da JUCEPAR (ex.: "21/329-L") não carrega prefixo
                    # de Junta, então fixamos a UF/Junta aqui.
                    uf_matricula=self.uf,
                    junta_comercial=self.junta,
                    site_oficial=_normalizar_site(site_m.group("site") if site_m else None),
                    fonte_cadastro=self.fonte_cadastro,
                )
            )
        return registros
