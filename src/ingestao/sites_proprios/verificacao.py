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

_RE_JUCESP = re.compile(r"JUCESP", re.IGNORECASE)
# Links que provavelmente levam a uma página de lote (onde ficam as matrículas).
_RE_LOTE = re.compile(r"/imovel|/lote|/oferta|/bem[/-]|id-\d", re.IGNORECASE)


class VerificadorJucesp(BaseScraper):
    """Checa se o leiloeiro de um site tem matrícula JUCESP (home + 1 lote)."""

    fonte_origem = "verificacao"
    fonte_tipo = "verificacao"

    async def tem_jucesp(self, site: str) -> bool | None:
        """True se achou "JUCESP"; False se leu o site e não achou; None se não leu."""
        home = await self.fetch(site, tentativas=1)
        if not home:
            return None
        textos = [home]
        # Busca um link de lote para inspecionar (lá ficam as matrículas completas).
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
        return any(pagina_tem_jucesp(t) for t in textos)


def pagina_tem_jucesp(html: str) -> bool:
    """True se o texto da página menciona "JUCESP" (matrícula do leiloeiro)."""
    tree = HTMLParser(html)
    texto = tree.body.text(separator=" ") if tree.body else html
    return bool(_RE_JUCESP.search(texto))
