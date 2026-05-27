"""Coletor da JUCEMG (Minas Gerais) — leiloeiros não-SP (alvo da tese).

A JUCEMG publica a relação completa de leiloeiros em ordem alfabética numa
página HTML estática. Cada leiloeiro é um bloco iniciado por ``<strong>Nome</strong>``
seguido de ``Matrícula: <numero> de <data>`` e, quando há, e-mail e site.
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import JuntaScraper

# Remove anotações entre parênteses do tipo "(MATRÍCULA SUPLEMENTAR)" do nome,
# que poluem o matching mas não fazem parte do nome do leiloeiro.
_ANOTACAO_NOME = re.compile(r"\s*\((?:[^)]*?(?:MATR|SUPLE)[^)]*?)\)\s*", re.IGNORECASE)


class JucemgScraper(JuntaScraper):
    junta = "JUCEMG"
    uf = "MG"
    url_lista = "https://jucemg.mg.gov.br/pagina/140/Leiloeiros+Ordem+Alfab%C3%A9tica"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        container = tree.css_first("article") or tree.body
        if container is None:
            return []
        # `&nbsp;` aparece entre rótulo e valor; normaliza para casar a regex.
        inner = (container.html or "").replace("&nbsp;", " ")
        registros: list[LeiloeiroRaw] = []
        for bloco in re.split(r"<strong>", inner)[1:]:
            m_nome = re.match(r"(.*?)</strong>", bloco, re.S)
            if not m_nome:
                continue
            nome = _limpar_nome(re.sub(r"<[^>]+>", "", m_nome.group(1)))
            resto = bloco[m_nome.end() :]
            m_mat = re.search(r"Matr[ií]cula:\s*(\d+)", resto)
            if not (nome and m_mat):
                continue
            sites = re.findall(r'href="(https?://[^"]+)"', resto)
            registros.append(self._novo_raw(nome, m_mat.group(1), sites[0] if sites else None))
        return registros


def _limpar_nome(nome: str) -> str:
    """Normaliza o nome: remove anotações entre parênteses e espaços extras."""
    return re.sub(r"\s+", " ", _ANOTACAO_NOME.sub(" ", nome)).strip()
