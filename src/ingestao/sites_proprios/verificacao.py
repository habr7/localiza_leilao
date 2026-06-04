"""Verificação de matrícula JUCESP em sites de leiloeiros (filtro da tese).

A tese só vale para leiloeiros que **não** têm matrícula na JUCESP: quem tem
JUCESP pode atuar livremente em SP, sem assimetria. Um leiloeiro pode estar numa
Junta de fora (PR/MT/GO…) **e também** na JUCESP — e nesse caso não é alvo.

A forma mais confiável de descobrir todas as matrículas de um leiloeiro é o
próprio site dele: as páginas de lote/rodapé costumam listar "JUCESP nº ...,
JUCEMAT nº ...". Aqui baixamos a home e uma página de lote e procuramos "JUCESP".
"""

from __future__ import annotations

import re

import structlog
from selectolax.parser import HTMLParser

from src.ingestao.base import BaseScraper

log = structlog.get_logger()

# Matrícula JUCESP com número: "JUCESP n°1098", "JUCESP nº 844". Exigir o número
# evita falso positivo do seletor de estados (que lista "JUCESP" sem matrícula).
_RE_JUCESP_MAT = re.compile(r"JUCESP\D{0,10}\d", re.IGNORECASE)
# Qualquer matrícula de Junta com número (JUCERJA n°, JUCISRS n° 382, JUCEG nº 9…).
_RE_JUNTA_MAT = re.compile(r"\b(JUC[EI][A-Z]{1,5}|JUCIS[A-Z]{2})\D{0,10}\d", re.IGNORECASE)
# Links que provavelmente levam a uma página de lote (onde ficam as matrículas).
_RE_LOTE = re.compile(r"/imove|/imóve|/lote|/oferta|/bem[/-]|id-\d|/leilao/", re.IGNORECASE)

# Resultado da classificação.
TEM = "tem"  # achou matrícula JUCESP -> não é alvo
LIMPO = "limpo"  # leu matrícula de Junta não-SP e nenhuma JUCESP -> alvo puro
DESCONHECIDO = "desconhecido"  # não conseguiu ler matrícula (ex.: site em JS)


class VerificadorJucesp(BaseScraper):
    """Checa se o leiloeiro de um site tem matrícula JUCESP (home + 1 lote)."""

    fonte_origem = "verificacao"
    fonte_tipo = "verificacao"

    async def classificar(self, site: str) -> str:
        """Classifica o site em TEM | LIMPO | DESCONHECIDO lendo home + 1 lote."""
        home = await self.fetch(site, tentativas=1)
        if not home:
            return DESCONHECIDO
        textos = [home]
        tree = HTMLParser(home)
        lote_url = None
        for a in tree.css("a"):
            href = (a.attributes.get("href") or "").strip()
            if href and _RE_LOTE.search(href):
                lote_url = (
                    href if href.startswith("http") else site.rstrip("/") + "/" + href.lstrip("/")
                )
                break
        if lote_url:
            lote_html = await self.fetch(lote_url, tentativas=1)
            if lote_html:
                textos.append(lote_html)
        return classificar_jucesp(" ".join(textos))

    async def tem_jucesp(self, site: str) -> bool | None:
        """True se tem JUCESP; False se limpo (leu matrícula não-SP); None se incerto."""
        classe = await self.classificar(site)
        if classe == TEM:
            return True
        if classe == LIMPO:
            return False
        return None


def classificar_jucesp(html: str) -> str:
    """Classifica o texto em TEM | LIMPO | DESCONHECIDO.

    - TEM: há "JUCESP" seguido de número (matrícula JUCESP de fato).
    - LIMPO: há matrícula de outra Junta (com número) e nenhuma JUCESP.
    - DESCONHECIDO: nenhuma matrícula legível (não dá para afirmar nada).
    """
    tree = HTMLParser(html)
    texto = tree.body.text(separator=" ") if tree.body else html
    if _RE_JUCESP_MAT.search(texto):
        return TEM
    if any(m.group(0) for m in _RE_JUNTA_MAT.finditer(texto)):
        return LIMPO
    return DESCONHECIDO


def pagina_tem_jucesp(html: str) -> bool:
    """True se o texto menciona uma matrícula JUCESP (com número)."""
    return classificar_jucesp(html) == TEM
