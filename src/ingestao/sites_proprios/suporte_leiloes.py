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
        # A plataforma tem dois layouts de card: `article.lote-main` (tema novo) e
        # `.lote-item` (tema antigo, ex.: e-confianca). Extraímos via texto do card
        # para cobrir ambos.
        for art in tree.css("article.lote-main, .lote-item"):
            link = art.css_first("a.link-img") or art.css_first('a[href*="/lote/"]')
            href = link.attributes.get("href") if link else None
            if not href:
                continue
            texto = re.sub(r"\s+", " ", art.text())
            cidade, uf = _cidade_uf(texto)
            if uf != "SP" or not cidade:  # filtro duro do projeto
                continue
            lotes.append(
                LoteRaw(
                    fonte_origem=f"site_proprio:{dominio}",
                    fonte_tipo=self.fonte_tipo,
                    fonte_url=canonical_url(urljoin(origem, href)),
                    tipo=_tipo_leilao(href),
                    cidade=cidade,
                    uf=uf,
                    titulo=_titulo(art),
                    numero_lote=_numero_lote(texto),
                    tipo_imovel=_tipo_imovel(texto),
                    lance_minimo_1=_dinheiro(texto),
                    descricao=_titulo(art),
                    dados_extras={
                        "status": "aberto" if "aberto para lances" in texto.lower() else None,
                        "desconto": _desconto(texto),
                    },
                )
            )
        return lotes


def _origem(url: str) -> str:
    partes = urlsplit(url if url.startswith("http") else f"https://{url}")
    return f"{partes.scheme}://{partes.netloc}"


def _numero_lote(texto: str) -> str | None:
    m = re.search(r"Lote\s*[-ºo°]?\s*(\d+)", texto, re.IGNORECASE)
    return m.group(1) if m else None


def _desconto(texto: str) -> str | None:
    m = re.search(r"(\d+)%\s*desconto", texto, re.IGNORECASE)
    return f"{m.group(1)}%" if m else None


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
