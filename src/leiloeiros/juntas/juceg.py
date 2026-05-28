"""Coletor da JUCEG (Goiás) — leiloeiros não-SP (alvo da tese).

A JUCEG publica a relação em texto corrido: cada leiloeiro começa por
``NOME (Matrícula: 084/20 de 22/10/2020) – Situação: REGULAR`` e, nas linhas
seguintes do bloco, traz ``e-mail:`` e ``site:``. Dividimos o texto por esses
cabeçalhos e extraímos o site dentro de cada bloco.
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import JuntaScraper

# Cabeçalho de um leiloeiro: "NOME (Matrícula: 084/20 de 22/10/2020)".
_RE_HEADER = re.compile(r"(?P<nome>[^\n(]{4,70}?)\s*\(Matr[íi]cula:\s*(?P<matricula>[^)]+?)\)")
_RE_SITE = re.compile(r"site:\s*(?P<site>\S+)", re.IGNORECASE)
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


class JucegScraper(JuntaScraper):
    junta = "JUCEG"
    uf = "GO"
    url_lista = "https://goias.gov.br/juceg/leiloeiros/"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        body = tree.body.text(separator="\n") if tree.body else ""
        cabecalhos = list(_RE_HEADER.finditer(body))
        registros: list[LeiloeiroRaw] = []
        for i, m in enumerate(cabecalhos):
            nome = m.group("nome").strip().split("\n")[-1].strip()
            # Matrícula vem como "084/20 de 22/10/2020"; guardamos só "084/20".
            matricula = re.split(r"\s+de\s+", m.group("matricula").strip())[0].strip()
            if not nome or not matricula:
                continue
            inicio = m.end()
            fim = cabecalhos[i + 1].start() if i + 1 < len(cabecalhos) else inicio + 400
            site_m = _RE_SITE.search(body[inicio:fim])
            registros.append(
                LeiloeiroRaw(
                    nome=nome,
                    matricula=matricula,
                    # A matrícula da JUCEG ("084/20") não carrega prefixo de Junta.
                    uf_matricula=self.uf,
                    junta_comercial=self.junta,
                    site_oficial=_normalizar_site(site_m.group("site") if site_m else None),
                    fonte_cadastro=self.fonte_cadastro,
                )
            )
        return registros
