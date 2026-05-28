"""Varredura de sites próprios de leiloeiros não-SP em busca de imóveis em SP.

Esta é a fonte de **maior assimetria** da tese: o leiloeiro de fora de SP anuncia
o imóvel paulista no seu próprio site, longe dos agregadores nacionais. Como cada
site tem estrutura própria (não há padrão), a varredura é **heurística e de
descoberta**, não um extrator estruturado por site:

1. baixa a home do site;
2. acha links candidatos no mesmo domínio (imóveis/leilões/lotes/bens);
3. baixa essas páginas (com teto) e procura sinais de imóvel localizado em SP
   (token de localidade terminando em ``/SP`` ou "São Paulo" perto de palavras de
   imóvel), guardando o trecho de contexto para revisão humana.

O objetivo é responder: *este leiloeiro de fora tem imóvel em SP no site dele?*
Os achados alimentam a revisão e, depois, um parser dedicado por site se valer a pena.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import structlog
from selectolax.parser import HTMLParser

from src.ingestao.base import BaseScraper

log = structlog.get_logger()

# Palavras que indicam imóvel (para distinguir de leilões de veículos/diversos).
_PALAVRAS_IMOVEL = (
    "imóvel",
    "imovel",
    "imóveis",
    "imoveis",
    "apartamento",
    "casa",
    "terreno",
    "lote",
    "sala",
    "galpão",
    "galpao",
    "sobrado",
    "chácara",
    "chacara",
    "loja",
    "edifício",
    "edificio",
    "gleba",
    "fazenda",
    "sítio",
    "sitio",
    "prédio",
    "predio",
    "cobertura",
    "comercial",
    "rural",
    "kitnet",
)
# Texto de link que sugere uma página de listagem de imóveis/leilões.
_LINK_CANDIDATO = re.compile(
    r"im[oó]ve|leil|lote|bem|bens|aberto|andamento|cat[aá]logo|venda", re.IGNORECASE
)
# Localidade terminando em SP: "Cidade/SP", "Cidade - SP", "São Paulo/SP".
_RE_LOCAL_SP = re.compile(r"([A-ZÀ-Ý][A-Za-zÀ-ÿ.'’]+(?:\s+[A-Za-zÀ-ÿ.'’]+){0,3})\s*[/\-–]\s*SP\b")
_RE_SAO_PAULO = re.compile(r"\bS[ãa]o\s+Paulo\b", re.IGNORECASE)


@dataclass
class AchadoSP:
    """Um indício de imóvel em SP encontrado no site de um leiloeiro de fora."""

    site: str  # site do leiloeiro
    pagina_url: str  # página onde o indício apareceu
    cidade: str | None  # cidade detectada (quando "Cidade/SP")
    contexto: str  # trecho de texto ao redor do indício


def _tem_palavra_imovel(texto: str) -> bool:
    baixo = texto.lower()
    return any(p in baixo for p in _PALAVRAS_IMOVEL)


def encontrar_links_candidatos(html: str, base_url: str, limite: int = 10) -> list[str]:
    """Links do mesmo domínio que parecem páginas de listagem (imóveis/leilões)."""
    dominio = urlsplit(base_url).netloc
    vistos: dict[str, None] = {}
    tree = HTMLParser(html)
    for a in tree.css("a"):
        href = (a.attributes.get("href") or "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        texto = a.text() or ""
        if not (_LINK_CANDIDATO.search(href) or _LINK_CANDIDATO.search(texto)):
            continue
        url = urljoin(base_url, href).split("#")[0]
        if urlsplit(url).netloc != dominio or url == base_url:
            continue
        vistos.setdefault(url, None)
        if len(vistos) >= limite:
            break
    return list(vistos)


def detectar_imoveis_sp(html: str, site: str, pagina_url: str) -> list[AchadoSP]:
    """Acha indícios de imóvel em SP numa página (texto + palavras de imóvel)."""
    tree = HTMLParser(html)
    texto = tree.body.text(separator=" ") if tree.body else ""
    texto = re.sub(r"\s+", " ", texto)
    if not _tem_palavra_imovel(texto):
        return []
    achados: list[AchadoSP] = []
    vistos: set[str] = set()

    for m in _RE_LOCAL_SP.finditer(texto):
        cidade = m.group(1).strip()
        # Evita capturar siglas/ruído (ex.: "Lote 12/SP" não é cidade).
        if cidade.lower() in {"lote", "matrícula", "matricula", "r", "rua"}:
            continue
        ini, fim = max(0, m.start() - 60), min(len(texto), m.end() + 60)
        contexto = texto[ini:fim].strip()
        chave = cidade.lower()
        if chave in vistos:
            continue
        vistos.add(chave)
        achados.append(AchadoSP(site=site, pagina_url=pagina_url, cidade=cidade, contexto=contexto))

    # "São Paulo" sem o "/SP" (ex.: "Estado de São Paulo"), se ainda não houver achados.
    if not achados:
        for m in _RE_SAO_PAULO.finditer(texto):
            ini, fim = max(0, m.start() - 60), min(len(texto), m.end() + 60)
            achados.append(
                AchadoSP(
                    site=site,
                    pagina_url=pagina_url,
                    cidade="São Paulo",
                    contexto=texto[ini:fim].strip(),
                )
            )
            break
    return achados


class SiteProprioScanner(BaseScraper):
    """Varre o site de um leiloeiro à procura de imóveis em SP (heurística)."""

    fonte_origem = "site_proprio"
    fonte_tipo = "site_proprio"

    async def varrer_site(self, site: str, max_paginas: int = 8) -> list[AchadoSP]:
        """Home + páginas de listagem candidatas; agrega indícios de imóvel SP."""
        # tentativas=1: numa varredura ampla, site fora do ar / anti-bot é pulado
        # rápido (sem gastar o backoff de retries em centenas de domínios).
        home = await self.fetch(site, tentativas=1)
        if not home:
            return []
        achados: list[AchadoSP] = list(detectar_imoveis_sp(home, site, site))
        candidatos = encontrar_links_candidatos(home, site, limite=max_paginas)
        for url in candidatos:
            html = await self.fetch(url, tentativas=1)
            if not html:
                continue
            achados.extend(detectar_imoveis_sp(html, site, url))
        return achados
