"""Scraper da plataforma "Suporte Leilões" (Fase 3.2 — sites próprios).

Muitos leiloeiros pequenos (de várias UFs) usam a mesma plataforma white-label
servida por `static.suporteleiloes.com.br` (SPA em `/build/app.*.js`). Em vez de
um scraper por leiloeiro, um único scraper cobre todos os sites dessa plataforma
— é o que torna a varredura escalável para os sites obscuros (menor concorrência).

Como funciona a coleta (descoberto inspecionando a SPA):
- `GET /api/buscadorMount?categoria=2` devolve, em JSON, a distribuição de
  IMÓVEIS por UF do site. Serve de survey barato: o site tem imóvel em SP?
- `GET /buscador?categoria=2&uf=SP&pagina=N` com header `X-Requested-With:
  XMLHttpRequest` faz o servidor renderizar o HTML dos lotes (12 por página),
  que parseamos em `LoteRaw`.

A UF do leiloeiro NÃO sai daqui: como é o site próprio dele, quem chama informa
o leiloeiro do cadastro (não-SP) na hora de resolver/persistir.
"""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin, urlsplit

from selectolax.parser import HTMLParser

from src.ingestao.base import BaseScraper, LoteRaw, canonical_url

CATEGORIA_IMOVEIS = 2
_XHR = {"X-Requested-With": "XMLHttpRequest"}
_MAX_PAGINAS = 30

# Palavras-chave para inferir tipo_imovel. Específicos primeiro; "terreno"/"gleba"
# por último (aparecem em frases como "em terreno de 300 m²" de outros tipos).
_TIPOS_IMOVEL = [
    ("apartamento", "apartamento"),
    ("flat", "apartamento"),
    ("sobrado", "casa"),
    ("casa", "casa"),
    ("prédio", "predio"),
    ("predio", "predio"),
    ("galp", "galpao"),
    ("sala", "comercial"),
    ("loja", "comercial"),
    ("ponto comercial", "comercial"),
    ("fazenda", "rural"),
    ("sítio", "rural"),
    ("chácara", "rural"),
    ("rural", "rural"),
    ("gleba", "terreno"),
    ("terreno", "terreno"),
]


class SuporteLeiloesScraper(BaseScraper):
    """Coleta lotes de imóveis em SP de um site da plataforma Suporte Leilões."""

    fonte_tipo = "site_proprio"

    async def imoveis_por_uf(self, base_url: str) -> dict[str, int] | None:
        """Survey: imóveis por UF do site, ou None se não for a plataforma."""
        url = f"{_origem(base_url)}/api/buscadorMount?categoria={CATEGORIA_IMOVEIS}"
        try:
            corpo = await self.get(url, headers={**_XHR, "Accept": "application/json"})
            dados = json.loads(corpo)
        except (ValueError, OSError):
            return None
        if not isinstance(dados, dict) or "ufs" not in dados:
            return None
        return {u["id"]: u.get("total", 0) for u in dados.get("ufs", [])}

    async def coletar_site(self, base_url: str) -> list[LoteRaw]:
        """Lista os imóveis em SP de um site (vazio se não houver SP)."""
        ufs = await self.imoveis_por_uf(base_url)
        if not ufs or ufs.get("SP", 0) <= 0:
            return []
        origem = _origem(base_url)
        unicos: dict[str, LoteRaw] = {}
        for pagina in range(1, _MAX_PAGINAS + 1):
            url = f"{origem}/buscador?categoria={CATEGORIA_IMOVEIS}&uf=SP&page={pagina}"
            html = await self.get(url, headers=_XHR)
            pagina_lotes = self._parse_cards(html, origem)
            # Para quando a página é vazia ou só repete lotes já vistos (fim da lista).
            novos = [lote for lote in pagina_lotes if lote.fonte_url not in unicos]
            if not novos:
                break
            for lote in novos:
                unicos[lote.fonte_url] = lote
        return list(unicos.values())

    def _parse_cards(self, html: str, origem: str) -> list[LoteRaw]:
        tree = HTMLParser(html)
        dominio = urlsplit(origem).netloc
        lotes: list[LoteRaw] = []
        for art in tree.css("article.lote-main"):
            link = art.css_first("a.link-img") or art.css_first('a[href*="/lote/"]')
            href = link.attributes.get("href") if link else None
            if not href:
                continue
            cidade, uf = _cidade_uf(art.text())
            if uf != "SP" or not cidade:  # filtro duro do projeto
                continue
            url = canonical_url(urljoin(origem, href))
            lotes.append(
                LoteRaw(
                    fonte_origem=f"site_proprio:{dominio}",
                    fonte_tipo=self.fonte_tipo,
                    fonte_url=url,
                    tipo=_tipo_leilao(href),
                    cidade=cidade,
                    uf=uf,
                    titulo=_titulo(art),
                    numero_lote=_numero_lote(art),
                    tipo_imovel=_tipo_imovel(art.text()),
                    lance_minimo_1=_lance_inicial(art),
                    descricao=_titulo(art),
                    dados_extras={
                        "status": _texto(art, ".strong-status"),
                        "desconto": _texto(art, ".item-desconto"),
                    },
                )
            )
        return lotes


def _origem(url: str) -> str:
    partes = urlsplit(url if url.startswith("http") else f"https://{url}")
    return f"{partes.scheme}://{partes.netloc}"


def _texto(art: object, seletor: str) -> str | None:
    el = art.css_first(seletor)  # type: ignore[attr-defined]
    return re.sub(r"\s+", " ", el.text(strip=True)) if el else None


def _numero_lote(art: object) -> str | None:
    txt = _texto(art, ".item-numeroLote") or ""
    m = re.search(r"\d+", txt)
    return m.group(0) if m else None


def _titulo(art: object) -> str | None:
    """Título/descrição do lote: texto do link principal, sem COD/status."""
    link = None
    for a in art.css('a[href*="/lote/"]'):  # type: ignore[attr-defined]
        if len(a.text(strip=True)) > 40:
            link = a
            break
    if link is None:
        return None
    texto = re.sub(r"\s+", " ", link.text(strip=True))
    texto = re.sub(r"^COD\.?\s*\d+\s*", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"^(Aberto para Lances|Encerrado|Suspenso)\s*", "", texto, flags=re.IGNORECASE)
    # Corta o rodapé do card (preço/status), que vem concatenado no mesmo link.
    texto = re.split(r"Lance Inicial|Lance Atual|Status atual", texto)[0]
    return texto.strip() or None


def _lance_inicial(art: object) -> Decimal | None:
    for rc in art.css(".reset-colorGrid"):  # type: ignore[attr-defined]
        valor = _dinheiro(rc.text())
        if valor is not None:
            return valor
    return None


def _cidade_uf(texto: str) -> tuple[str | None, str | None]:
    """Extrai (cidade, uf) do padrão 'Cidade/UF' ou 'Cidade - UF' (última ocorrência)."""
    achados = re.findall(r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ .]+?)\s*[-/]\s*([A-Z]{2})\b", texto or "")
    if not achados:
        return None, None
    cidade, uf = achados[-1]
    return cidade.strip(), uf


def _tipo_leilao(href: str) -> str:
    """Infere judicial/extrajudicial pelo slug do evento na URL."""
    low = href.lower()
    if "extrajudicial" in low:
        return "extrajudicial"
    if "judicial" in low:
        return "judicial"
    return "extrajudicial"


def _tipo_imovel(texto: str) -> str | None:
    low = (texto or "").lower()
    for chave, tipo in _TIPOS_IMOVEL:
        if chave in low:
            return tipo
    return None


def _dinheiro(texto: str | None) -> Decimal | None:
    if not texto:
        return None
    m = re.search(r"R\$\s*([\d.]+,\d{2})", texto)
    if not m:
        return None
    try:
        return Decimal(m.group(1).replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None
