"""Parser dedicado do site próprio WebLeilões (webleiloes.com.br).

Leiloeiro de fora de SP (Tiago Tessler Blecher — JUCEMAT/MT) com muitos imóveis em
SP. Diferente do `scanner` heurístico, aqui extraímos o **lote estruturado**:
a listagem `/busca?tipo=Imóveis&pagina=N` traz `<article>` por lote, com o link
(`/oferta/leilao/imoveis/{tipo}/{n}/id-{id}/{slug}-{uf}`), o título/cidade no
``alt`` da imagem, o lance em ``.r1 strong`` e a praça em ``.r1 span``.

Filtro duro: só lotes com UF = SP.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

import structlog
from selectolax.parser import HTMLParser

from src.ingestao.base import BaseScraper, LoteRaw

log = structlog.get_logger()

BASE = "https://www.webleiloes.com.br"
URL_BUSCA = f"{BASE}/busca?tipo=Imóveis"

# /oferta/leilao/imoveis/{tipo}/{n}/id-{id}/{slug-cidade}-{uf}
_RE_HREF = re.compile(
    r"/oferta/leilao/imoveis/(?P<tipo>[\w-]+)/\d+/id-(?P<id>\d+)/(?P<slug>.+?)-(?P<uf>[a-z]{2})$"
)
_RE_MONEY = re.compile(r"R\$\s*([\d.]+,\d{2})")
# alt: "Apartamento - Parque dos Pinus, Ribeirão Preto/SP" ou "Fazenda ... - Cosmópolis/SP"
_RE_ALT_CIDADE = re.compile(r"[-,]\s*(?P<cidade>[^,\-/]+?)\s*/[A-Z]{2}\s*$")

_TIPO_SLUG = {
    "apartamentos": "apartamento",
    "casas": "casa",
    "terrenos": "terreno",
    "rural": "rural",
    "comercial": "comercial",
    "lote": "terreno",
    "galpoes": "galpao",
}


def _money(texto: str | None) -> float | None:
    if not texto:
        return None
    m = _RE_MONEY.search(texto)
    return float(m.group(1).replace(".", "").replace(",", ".")) if m else None


def parse_lotes(html: str) -> list[LoteRaw]:
    """Extrai os lotes de imóveis de uma página de busca (filtra SP no chamador)."""
    tree = HTMLParser(html)
    lotes: list[LoteRaw] = []
    vistos: set[str] = set()
    for art in tree.css("article"):
        a = art.css_first('a[href*="/oferta/leilao/imoveis/"]')
        if a is None:
            continue
        href = (a.attributes.get("href") or "").split("?")[0]
        m = _RE_HREF.match(href)
        if not m or href in vistos:
            continue
        vistos.add(href)
        img = art.css_first("img")
        alt = (img.attributes.get("alt") if img else "") or ""
        cidade = bairro = None
        titulo = alt.strip() or None
        alt_m = _RE_ALT_CIDADE.search(alt.strip())
        if alt_m:
            cidade = alt_m.group("cidade").strip()
            # bairro: o trecho entre " - " e ", {cidade}/UF" (só quando há vírgula
            # separando bairro e cidade; senão não há bairro).
            if " - " in alt and "," in alt:
                cand = alt.split(" - ", 1)[1].rsplit(",", 1)[0].strip()
                if cand and "/" not in cand and cand != cidade:
                    bairro = cand
        r1 = art.css_first(".r1")
        praca = None
        if r1 is not None:
            span = r1.css_first("span")
            praca = span.text(strip=True) if span else None
        lance = _money(r1.text() if r1 else None)
        status = art.css_first(".s-status")
        lotes.append(
            LoteRaw(
                fonte_origem="webleiloes",
                fonte_tipo="site_proprio",
                fonte_url=urljoin(BASE, href),
                titulo=titulo,
                numero_lote=m.group("id"),
                tipo_imovel=_TIPO_SLUG.get(m.group("tipo"), m.group("tipo")),
                cidade=cidade,
                uf=m.group("uf").upper(),
                bairro=bairro,
                lance_minimo_1=lance,
                descricao=praca,
                dados_extras={"status": status.text(strip=True) if status else None},
            )
        )
    return lotes


class WebLeiloesScraper(BaseScraper):
    """Coletor do site próprio WebLeilões (imóveis em SP)."""

    fonte_origem = "webleiloes"
    fonte_tipo = "site_proprio"
    dominio = "webleiloes.com.br"  # casa com o site_oficial do cadastro

    async def listar_lotes_sp(self, max_paginas: int = 15) -> list[LoteRaw]:
        por_url: dict[str, LoteRaw] = {}
        for pagina in range(1, max_paginas + 1):
            url = URL_BUSCA if pagina == 1 else f"{URL_BUSCA}&pagina={pagina}"
            html = await self.fetch(url, tentativas=2)
            if not html:
                break
            da_pagina = parse_lotes(html)
            if not da_pagina:
                break
            antes = len(por_url)
            for lo in da_pagina:
                if lo.uf == "SP":
                    por_url[lo.fonte_url] = lo
            log.info(
                "webleiloes_pagina", pagina=pagina, lotes=len(da_pagina), sp_total=len(por_url)
            )
            # Páginas além do fim repetem o conteúdo: se nada novo entrou, para.
            if len(por_url) == antes:
                break
        return list(por_url.values())
