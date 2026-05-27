"""Coletor do agregador Mega Leilões (Fase 3).

Lista imóveis em SP (`/imoveis/sp`) e, para cada card, abre a página de detalhe
para extrair o leilão (tipo, datas de praça, edital), o lote (endereço, cidade,
avaliação, lances mínimos) e o **leiloeiro (nome + matrículas)** — este último é
o insumo do `LeiloeiroResolver` para decidir a UF (gatilho da tese).

Os agregadores são baseline de cobertura e, sobretudo, descobridores de quais
leiloeiros não-SP atuam em imóveis paulistas.
"""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from selectolax.parser import HTMLParser

from src.ingestao.base import BaseScraper, LoteRaw, canonical_url

BASE = "https://www.megaleiloes.com.br"
URL_IMOVEIS_SP = f"{BASE}/imoveis/sp"

# Singularização leve de categorias do breadcrumb para `tipo_imovel`.
_TIPO_IMOVEL = {
    "apartamentos": "apartamento",
    "casas": "casa",
    "terrenos": "terreno",
    "comerciais": "comercial",
    "rurais": "rural",
    "galpoes": "galpao",
    "garagens": "garagem",
    "predios": "predio",
    "lojas": "loja",
    "salas": "sala",
}


class MegaLeiloesScraper(BaseScraper):
    fonte_origem = "megaleiloes"
    fonte_tipo = "agregador"

    async def listar_lotes_sp(self, limite: int | None = None) -> list[LoteRaw]:
        html = await self.get(URL_IMOVEIS_SP)
        urls = self._extrair_urls_detalhe(html)
        if limite is not None:
            urls = urls[:limite]
        lotes: list[LoteRaw] = []
        for url in urls:
            detalhe = await self.get(url)
            lote = self._parse_detalhe(detalhe, url)
            if lote is not None:
                lotes.append(lote)
        return lotes

    def _extrair_urls_detalhe(self, html: str) -> list[str]:
        """Extrai as URLs (canônicas, sem utm) dos cards de imóvel da listagem."""
        tree = HTMLParser(html)
        urls: list[str] = []
        vistos: set[str] = set()
        for card in tree.css("div.card.open"):
            link = card.css_first("a.card-title")
            href = link.attributes.get("href") if link else None
            if not href:
                continue
            url = canonical_url(href)
            if url not in vistos:
                vistos.add(url)
                urls.append(url)
        return urls

    def _parse_detalhe(self, html: str, url: str) -> LoteRaw | None:
        tree = HTMLParser(html)
        itens = _itens(tree)
        tipo_imovel, uf, cidade = _breadcrumb(tree)
        if uf != "SP" or not cidade:  # filtro duro do projeto (cidade é obrigatória)
            return None
        nome, matriculas = _leiloeiro(tree)
        praca1, valor1 = _praca(tree, "first")
        praca2, valor2 = _praca(tree, "second")
        return LoteRaw(
            fonte_origem=self.fonte_origem,
            fonte_tipo=self.fonte_tipo,
            fonte_url=url,
            tipo=_tipo_leilao(tree),
            cidade=cidade,
            uf=uf,
            titulo=_titulo(tree),
            numero_lote=_codigo(url),
            tipo_imovel=tipo_imovel,
            endereco_completo=itens.get("Localização"),
            avaliacao=_dinheiro(itens.get("Valor de Avaliação")),
            lance_minimo_1=valor1,
            lance_minimo_2=valor2,
            data_1praca=praca1,
            data_2praca=praca2,
            edital_url=_edital(tree),
            matricula_imovel=_matricula_imovel(html),
            leiloeiro_nome=nome,
            leiloeiro_matriculas=matriculas,
        )


def _itens(tree: HTMLParser) -> dict[str, str]:
    """Lê os blocos `.item` (header/value) da página de detalhe."""
    campos: dict[str, str] = {}
    for item in tree.css(".item"):
        h = item.css_first(".header")
        v = item.css_first(".value")
        if h and v:
            campos[h.text(strip=True)] = re.sub(r"\s+", " ", v.text(strip=True)).strip()
    return campos


def _breadcrumb(tree: HTMLParser) -> tuple[str | None, str | None, str | None]:
    """Extrai (tipo_imovel, uf, cidade) do breadcrumb.

    Estrutura: Mega Leilões > Imóveis > <Categoria> > <Estado> > <Cidade>.
    """
    partes = [a.text(strip=True) for a in tree.css(".breadcrumb a") if a.text(strip=True)]
    # Remove o nó "Imóveis" e o nó-raiz para isolar categoria/estado/cidade.
    relevantes = [p for p in partes if p.lower() not in ("mega leilões", "imóveis", "início")]
    tipo_imovel = uf = cidade = None
    if relevantes:
        cat = relevantes[0].lower()
        tipo_imovel = _TIPO_IMOVEL.get(cat, cat)
    if len(relevantes) >= 2:
        uf = _UF_POR_NOME.get(relevantes[1].lower())
    if len(relevantes) >= 3:
        cidade = relevantes[2]
    return tipo_imovel, uf, cidade


def _leiloeiro(tree: HTMLParser) -> tuple[str | None, list[str]]:
    """Extrai (nome, [matrículas]) do bloco do leiloeiro.

    O valor lista o nome na 1ª linha e cada matrícula numa linha "JUCExx Nº N".
    Devolvemos todas as matrículas (o leiloeiro pode ter matrícula em + de uma UF).
    """
    bloco = None
    for item in tree.css(".author.item, .item"):
        h = item.css_first(".header")
        if h and h.text(strip=True).lower() == "leiloeiro":
            bloco = item.css_first(".value")
            break
    if bloco is None:
        return None, []
    fragmentos = re.split(r"<br\s*/?>", bloco.html or "", flags=re.IGNORECASE)
    linhas = [re.sub(r"<[^>]+>", "", frag).replace("\xa0", " ").strip() for frag in fragmentos]
    linhas = [linha for linha in linhas if linha]
    nome = linhas[0] if linhas else None
    matriculas: list[str] = []
    for linha in linhas:
        m = re.match(r"([A-Za-zÀ-ÿ]{2,})\s*N[ºo°]\s*(\d+)", linha)
        if m:
            matriculas.append(f"{m.group(1).upper()} {m.group(2)}")
    return nome, matriculas


def _praca(tree: HTMLParser, qual: str) -> tuple[datetime | None, Decimal | None]:
    """Extrai (data, valor) da 1ª ('first') ou 2ª ('second') praça."""
    seletor = f"span.card-{qual}-instance-date"
    span = tree.css_first(seletor)
    if span is None:
        return None, None
    data = _data_hora(span.text(strip=True))
    # O valor fica no .card-instance-value do mesmo bloco .instance.
    instancia = span.parent
    valor = None
    if instancia is not None:
        v = instancia.css_first(".card-instance-value")
        if v:
            valor = _dinheiro(v.text(strip=True))
    return data, valor


def _tipo_leilao(tree: HTMLParser) -> str:
    """Mapeia o rótulo do site ('Judicial'/'Extrajudicial') para o domínio."""
    el = tree.css_first(".batch-type")
    texto = el.text(strip=True).lower() if el else ""
    return "judicial" if "judicial" in texto and "extra" not in texto else "extrajudicial"


def _titulo(tree: HTMLParser) -> str | None:
    el = tree.css_first("h1") or tree.css_first(".batch-title")
    return el.text(strip=True) if el else None


def _edital(tree: HTMLParser) -> str | None:
    for a in tree.css("a"):
        href = a.attributes.get("href") or ""
        if re.search(r"_edital_", href, re.IGNORECASE):
            return href
    return None


def _codigo(url: str) -> str | None:
    """Extrai o código do lote do final da URL (ex.: '...-j123913' -> 'J123913')."""
    m = re.search(r"-([a-zA-Z]\d+)/?$", url)
    return m.group(1).upper() if m else None


def _matricula_imovel(html: str) -> str | None:
    m = re.search(r"MATR[IÍ]CULA\s+N[ºo°]?\s*([\d.\-/]+)", html, re.IGNORECASE)
    return m.group(1) if m else None


def _data_hora(texto: str) -> datetime | None:
    """Converte 'Nª Praça: 28/05/2026 às 11:00' em datetime (hora opcional)."""
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})(?:\s+[àa]s\s+(\d{1,2}):(\d{2}))?", texto)
    if not m:
        return None
    dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
    hora = int(m.group(4)) if m.group(4) else 0
    minuto = int(m.group(5)) if m.group(5) else 0
    return datetime(ano, mes, dia, hora, minuto)


def _dinheiro(texto: str | None) -> Decimal | None:
    """Converte 'R$ 168.781,97' em Decimal('168781.97')."""
    if not texto:
        return None
    m = re.search(r"R\$\s*([\d.]+,\d{2})", texto)
    if not m:
        return None
    numero = m.group(1).replace(".", "").replace(",", ".")
    try:
        return Decimal(numero)
    except InvalidOperation:
        return None


# Nome do estado (como aparece no breadcrumb) -> UF.
_UF_POR_NOME = {
    "são paulo": "SP",
    "rio de janeiro": "RJ",
    "minas gerais": "MG",
    "paraná": "PR",
    "santa catarina": "SC",
    "rio grande do sul": "RS",
    "distrito federal": "DF",
    "goiás": "GO",
    "espírito santo": "ES",
    "bahia": "BA",
    "mato grosso": "MT",
    "mato grosso do sul": "MS",
    "pernambuco": "PE",
    "ceará": "CE",
}


__all__ = ["MegaLeiloesScraper"]
