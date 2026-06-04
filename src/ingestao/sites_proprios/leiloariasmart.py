"""Parser dedicado do site próprio Leiloaria Smart (leiloariasmart.com.br).

Leiloeiro de fora de SP (Lucas Andreatta de Oliveira — JUCEMAT/MT) com muitos
imóveis em SP. Todos os lotes vêm na home, em cartões ``.caixa-imoveis`` (a
paginação é client-side, então o HTML já traz todos). Cada cartão tem o link
``/imovel/{id}``, e o texto traz tipo de leilão, comitente, tipo do imóvel, a
localidade ``Cidade/UF`` (logo antes de "PRAÇA"), a data de praça e o lance.

Filtro duro: só lotes com UF = SP.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

import structlog
from selectolax.parser import HTMLParser

from src.ingestao.base import BaseScraper, LoteRaw

log = structlog.get_logger()

BASE = "https://www.leiloariasmart.com.br"

_RE_MONEY = re.compile(r"R\$\s*([\d.]+,\d{2})")
# Localidade "Cidade/UF" imediatamente antes de "PRAÇA"/"PRACA". Sem IGNORECASE no
# nome da cidade (precisa começar em maiúscula, senão casa no meio de uma palavra).
_RE_LOCAL = re.compile(r"([A-ZÀ-Ý][a-zà-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+){0,4})/([A-Z]{2})\s+PRA(?:Ç|C)A")
_RE_PRACA = re.compile(r"(PRA[ÇC]A[^R]*?\d{2}/\d{2}/\d{4}[^R]*?\d{2}:\d{2})", re.IGNORECASE)


def _money(texto: str) -> float | None:
    achados = _RE_MONEY.findall(texto)
    if not achados:
        return None
    # O último R$ do cartão costuma ser o lance/preço atual.
    return float(achados[-1].replace(".", "").replace(",", "."))


def parse_lotes(html: str) -> list[LoteRaw]:
    """Extrai os lotes dos cartões da home (filtra SP no chamador)."""
    tree = HTMLParser(html)
    lotes: list[LoteRaw] = []
    vistos: set[str] = set()
    for card in tree.css(".caixa-imoveis"):
        a = card.css_first('a[href^="/imovel"]')
        if a is None:
            continue
        href = (a.attributes.get("href") or "").split("?")[0]
        if not href or href in vistos:
            continue
        vistos.add(href)
        texto = re.sub(r"\s+", " ", card.text())
        loc = _RE_LOCAL.search(texto)
        if not loc:
            continue  # sem localidade reconhecível, não dá para afirmar a UF
        cidade = loc.group(1).strip()
        uf = loc.group(2).upper()
        tipo_leilao = (
            "extrajudicial"
            if "extrajudicial" in texto.lower()
            else ("judicial" if "judicial" in texto.lower() else None)
        )
        praca_m = _RE_PRACA.search(texto)
        lotes.append(
            LoteRaw(
                fonte_origem="leiloariasmart",
                fonte_tipo="site_proprio",
                fonte_url=urljoin(BASE, href),
                numero_lote=href.rsplit("/", 1)[-1],
                cidade=cidade,
                uf=uf,
                lance_minimo_1=_money(texto),
                tipo_leilao=tipo_leilao,
                descricao=praca_m.group(1).strip() if praca_m else None,
            )
        )
    return lotes


class LeiloariaSmartScraper(BaseScraper):
    """Coletor do site próprio Leiloaria Smart (imóveis em SP)."""

    fonte_origem = "leiloariasmart"
    fonte_tipo = "site_proprio"
    dominio = "leiloariasmart.com.br"  # casa com o site_oficial do cadastro

    async def listar_lotes_sp(self, max_paginas: int = 1) -> list[LoteRaw]:
        # "/leiloes/proximos" traz o catálogo ativo completo (não só os destaques
        # da home). Agregamos por URL para não duplicar.
        por_url: dict[str, LoteRaw] = {}
        for caminho in ("", "/leiloes/proximos", "/leiloes/extrajudiciais"):
            html = await self.fetch(BASE + caminho, tentativas=2)
            if not html:
                continue
            for lo in parse_lotes(html):
                if lo.uf == "SP":
                    por_url[lo.fonte_url] = lo
        log.info("leiloariasmart", sp=len(por_url))
        return list(por_url.values())
