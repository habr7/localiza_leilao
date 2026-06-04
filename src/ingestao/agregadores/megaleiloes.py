"""Agregador Mega Leilões (megaleiloes.com.br) — Fase 3.

É o agregador de maior volume e o primeiro da ordem do plano (§4.2). Serve de
**baseline de cobertura** e de **descobridor de leiloeiros** (nome + matrículas).

Estrutura do site (inspecionada ao vivo):
- Listagem de imóveis em SP: ``/sp?pagina=N`` (cards ``.card`` paginados).
  Cada card traz preço, título, código, e a localidade (cidade + UF) no link
  ``.card-locality`` (href ``/uf/cidade``).
- Página de detalhe do lote: ``.batch-type`` (Judicial/Extrajudicial) e blocos
  ``.author.item`` com ``.header`` ("Comitente"/"Leiloeiro") e ``.value``. O
  valor do leiloeiro traz o nome na 1ª linha e as matrículas nas seguintes
  (separadas por ``<br>``), ex.: "JUCESP Nº 844 - ...", "JUCEMG Nº 1192 - ...".

O parsing é separado da rede (`parse_listagem`/`parse_detalhe`) para ser testável
com fixtures HTML salvas.
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit

import structlog
from selectolax.parser import HTMLParser

from src.ingestao.base import BaseScraper, LoteRaw

log = structlog.get_logger()

BASE = "https://www.megaleiloes.com.br"
# Listagem de imóveis filtrada pelo estado de SP.
URL_SP = f"{BASE}/sp"


def _parse_dinheiro(texto: str | None) -> float | None:
    """Converte "R$ 108.900,00" em 108900.0 (ou None)."""
    if not texto:
        return None
    m = re.search(r"([\d.]+,\d{2})", texto)
    if not m:
        return None
    return float(m.group(1).replace(".", "").replace(",", "."))


def _tipo_imovel_da_url(url: str) -> str | None:
    """Extrai o tipo do imóvel do caminho ``/imoveis/{tipo}/{uf}/...``."""
    partes = [p for p in urlsplit(url).path.split("/") if p]
    if len(partes) >= 2 and partes[0] == "imoveis":
        return partes[1].rstrip("s") if partes[1].endswith("s") else partes[1]
    return None


def contar_cards(html: str) -> int:
    """Quantos cards (de qualquer categoria) a página de listagem tem.

    Serve para detectar o fim da paginação: ``/sp`` intercala imóveis com
    veículos/outros, então uma página pode não ter imóvel algum (``0`` em
    `parse_listagem`) e ainda assim existirem mais páginas adiante.
    """
    return len(HTMLParser(html).css(".card"))


def parse_listagem(
    html: str, fonte_origem: str = "megaleiloes", fonte_tipo: str = "agregador"
) -> list[LoteRaw]:
    """Extrai os lotes de uma página de listagem (cards). Sem dados do leiloeiro."""
    tree = HTMLParser(html)
    lotes: list[LoteRaw] = []
    for card in tree.css(".card"):
        titulo_node = card.css_first("a.card-title")
        if titulo_node is None:
            continue
        url = (titulo_node.attributes.get("href") or "").split("?")[0]
        if not url:
            continue
        # A listagem ``/sp`` mistura categorias; só queremos imóveis.
        if "/imoveis/" not in url:
            continue
        loc = card.css_first("a.card-locality")
        cidade = uf = None
        if loc is not None:
            href = loc.attributes.get("href") or ""
            segs = [s for s in urlsplit(href).path.split("/") if s]
            if len(segs) >= 2 and len(segs[0]) == 2:
                uf = segs[0].upper()
                cidade = segs[1].replace("-", " ").title()
        preco_node = card.css_first(".card-price")
        numero_node = card.css_first(".card-number")
        lotes.append(
            LoteRaw(
                fonte_origem=fonte_origem,
                fonte_tipo=fonte_tipo,
                fonte_url=url,
                titulo=titulo_node.text(strip=True) or None,
                numero_lote=(numero_node.text(strip=True) if numero_node else None),
                tipo_imovel=_tipo_imovel_da_url(url),
                cidade=cidade,
                uf=uf,
                lance_minimo_1=_parse_dinheiro(preco_node.text() if preco_node else None),
            )
        )
    return lotes


def parse_detalhe(html: str) -> dict:
    """Extrai do detalhe: tipo de leilão, comitente, leiloeiro (nome+matrículas)."""
    tree = HTMLParser(html)
    dados: dict = {
        "tipo_leilao": None,
        "comitente": None,
        "leiloeiro_nome": None,
        "leiloeiro_matriculas": [],
    }

    tipo_node = tree.css_first(".batch-type")
    if tipo_node is not None:
        texto = tipo_node.text(strip=True).lower()
        if "extra" in texto:
            dados["tipo_leilao"] = "extrajudicial"
        elif "judicial" in texto:
            dados["tipo_leilao"] = "judicial"

    for item in tree.css(".author.item"):
        header = item.css_first(".header")
        value = item.css_first(".value")
        if header is None or value is None:
            continue
        rotulo = header.text(strip=True).lower()
        # Linhas separadas por <br>: a 1ª é o nome, as demais são matrículas.
        linhas = [ln.strip() for ln in re.split(r"\n+", value.text(separator="\n")) if ln.strip()]
        if not linhas:
            continue
        if "comitente" in rotulo:
            dados["comitente"] = linhas[0]
        elif "leiloeiro" in rotulo:
            dados["leiloeiro_nome"] = linhas[0]
            matriculas = [ln for ln in linhas[1:] if re.search(r"\bJUCE", ln, re.I)]
            dados["leiloeiro_matriculas"] = matriculas
    return dados


class MegaLeiloesScraper(BaseScraper):
    """Coletor do agregador Mega Leilões (e franquias na mesma plataforma).

    A plataforma é reusada por franquias regionais (ex.: Mega Leilões MS) com a
    MESMA estrutura — basta trocar ``base_url`` e ``fonte_origem``. Os lotes SP de
    uma franquia podem ser conduzidos pelo mesmo leiloeiro JUCESP do Mega: por isso
    o detalhe traz as matrículas, resolvidas por-lote em `uf_efetiva_de_matriculas`.
    """

    fonte_origem = "megaleiloes"
    fonte_tipo = "agregador"
    base_url = BASE

    async def listar_lotes_sp(self, max_paginas: int | None = None) -> list[LoteRaw]:
        """Varre ``/sp?pagina=N`` e enriquece cada lote com dados do detalhe.

        ``max_paginas`` limita quantas páginas de listagem varrer (cada uma traz
        ~48 lotes). Sem limite, segue até uma página vazia.
        """
        url_sp = f"{self.base_url}/sp"
        lotes: list[LoteRaw] = []
        pagina = 1
        while True:
            if max_paginas is not None and pagina > max_paginas:
                break
            url = url_sp if pagina == 1 else f"{url_sp}?pagina={pagina}"
            html = await self.fetch(url)
            if not html:
                break
            # Fim da paginação = página sem nenhum card (não sem imóveis: a
            # listagem ``/sp`` intercala categorias).
            if contar_cards(html) == 0:
                break
            da_pagina = parse_listagem(html, self.fonte_origem, self.fonte_tipo)
            # Mantém só imóveis em SP (filtro duro da tese).
            da_pagina = [lo for lo in da_pagina if lo.uf == "SP"]
            lotes.extend(da_pagina)
            log.info(
                "mega_listagem",
                pagina=pagina,
                lotes_pagina=len(da_pagina),
                acumulado=len(lotes),
            )
            pagina += 1

        # Enriquecimento: detalhe de cada lote (leiloeiro + tipo de leilão).
        for lote in lotes:
            html = await self.fetch(lote.fonte_url)
            if not html:
                continue
            det = parse_detalhe(html)
            lote.tipo_leilao = det["tipo_leilao"]
            lote.comitente = det["comitente"]
            lote.leiloeiro_nome = det["leiloeiro_nome"]
            lote.leiloeiro_matriculas = det["leiloeiro_matriculas"]
        return lotes


class MegaLeiloesMsScraper(MegaLeiloesScraper):
    """Franquia Mega Leilões MS (megaleiloesms.com.br) — mesma plataforma.

    Site próprio de leiloeira não-SP (JUCEMAT), mas o inventário SP é o mesmo do
    Mega (leiloeiro com JUCESP). A resolução por-lote marca corretamente como SP.
    """

    fonte_origem = "megaleiloesms"
    fonte_tipo = "site_proprio"
    base_url = "https://www.megaleiloesms.com.br"
