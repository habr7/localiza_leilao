"""Coletor da JUCEMS (Mato Grosso do Sul) — leiloeiros não-SP (alvo da tese).

A JUCEMS publica cada leiloeiro como um bloco de ``<div>``: nome em
``<strong>``, seguido de ``Matrícula: NNN`` e dados de contato (incluindo site).
Parseamos dividindo o HTML do conteúdo por ``<strong>`` (cada bloco = leiloeiro).
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import JuntaScraper


class JucemsScraper(JuntaScraper):
    junta = "JUCEMS"
    uf = "MS"
    url_lista = (
        "https://www.jucems.ms.gov.br/empresas/controles-especiais/agentes-auxiliares/leiloeiros/"
    )

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        corpo = tree.css_first("main") or tree.css_first("article") or tree.body
        inner = (corpo.html or "").replace("&nbsp;", " ") if corpo is not None else ""
        registros: list[LeiloeiroRaw] = []
        vistos: set[str] = set()
        for bloco in re.split(r"<strong>", inner)[1:]:
            m_nome = re.match(r"(.*?)</strong>", bloco, re.S)
            if not m_nome:
                continue
            nome = re.sub(r"<[^>]+>", "", m_nome.group(1)).strip()
            resto = bloco[m_nome.end() :]
            m_mat = re.search(r"Matr[ií]cula:?\s*(\d+)", resto)
            if not (nome and m_mat) or m_mat.group(1) in vistos:
                continue
            vistos.add(m_mat.group(1))
            sites = re.findall(r'href="(https?://(?!.*mailto)[^"]+)"', resto)
            site = sites[0] if sites else _site_texto(resto)
            registros.append(self._novo_raw(nome, m_mat.group(1), site))
        return registros


def _site_texto(html: str) -> str | None:
    texto = re.sub(r"<[^>]+>", " ", html)
    m = re.search(r"site:?\s*((?:https?://|www\.)\S+)", texto, re.IGNORECASE)
    return m.group(1).rstrip(".,;") if m else None
