"""Coletor da JUCISRS (Rio Grande do Sul) — leiloeiros não-SP (alvo da tese).

A lista vem de um endpoint POST no subdomínio ``sistemas.jucisrs.rs.gov.br``
(o domínio principal fica 503). O corpo HTML traz blocos separados por <hr>:
``<font>NUM</font> - NOME (situação) CIDADE-UF ... <a href=site>``. Traz site.
"""

from __future__ import annotations

import re

import httpx

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas._util import normalizar_site
from src.leiloeiros.juntas.base import USER_AGENT, JuntaScraper

URL_POST = "https://sistemas.jucisrs.rs.gov.br/leiloeiros/busca/listar"

_RE_CAB = re.compile(r"(?P<mat>\d{1,5})\s*</font>\s*-\s*(?P<nome>[^<(]+)", re.IGNORECASE)
_RE_SITE = re.compile(
    r'href=["\'](?P<site>https?://(?!www\.diariooficial|[^"\']*gov\.br)[^"\']+)', re.IGNORECASE
)


def parse_listagem_rs(html: str) -> list[LeiloeiroRaw]:
    registros: list[LeiloeiroRaw] = []
    for bloco in re.split(r"<hr", html):
        cab = _RE_CAB.search(bloco)
        if not cab:
            continue
        nome = re.sub(r"\s+", " ", cab.group("nome")).strip()
        if len(nome) < 4:
            continue
        site_m = _RE_SITE.search(bloco)
        registros.append(
            LeiloeiroRaw(
                nome=nome,
                matricula=cab.group("mat").strip(),
                uf_matricula="RS",
                junta_comercial="JUCISRS",
                site_oficial=normalizar_site(site_m.group("site") if site_m else None),
                fonte_cadastro="junta:jucisrs",
            )
        )
    return registros


class JucisrsScraper(JuntaScraper):
    junta = "JUCISRS"
    uf = "RS"
    url_lista = URL_POST
    verificar_ssl = False

    async def coletar(self) -> list[LeiloeiroRaw]:
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=40, follow_redirects=True, verify=False
        ) as client:
            resp = await client.post(URL_POST, data={"Nome": "a", "CodMunicipio": "0"})
            resp.raise_for_status()
        return parse_listagem_rs(resp.text)

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        return parse_listagem_rs(html)
