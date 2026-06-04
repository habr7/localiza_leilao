"""Coletor da JUCESP (São Paulo) — **lista de exclusão** da tese.

Quem é matriculado na JUCESP é de SP e NÃO entra como oportunidade. A JUCESP
publica a relação oficial dos leiloeiros num **PDF** (D.O.E.), não em HTML. Aqui
baixamos esse PDF e extraímos ``matrícula``, ``nome`` e ``situação`` — uma linha
por leiloeiro no formato ``{nº} {NOME} {dd/mm/aaaa} {situação}``.

A principal utilidade é o **cross-check por nome**: um leiloeiro de fora (PR/MT/…)
pode ter **também** matrícula JUCESP; se o nome dele bate com um nome desta lista,
ele não é alvo da tese (ver `src/leiloeiros/jucesp_exclusao.py`).
"""

from __future__ import annotations

import re

import httpx
import structlog
from pypdf import PdfReader

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import USER_AGENT, JuntaScraper

log = structlog.get_logger()

URL_PDF = "https://www.institucional.jucesp.sp.gov.br/downloads/Relacao_de_Leiloeiros.pdf"

# Linha do PDF: "960 PHILLIPE SANTOS INIGUEZ OMELLA 03/11/2015 Atuante".
_RE_LINHA = re.compile(
    r"(?P<mat>\d{1,5})\s+"
    r"(?P<nome>[A-ZÀ-Ý][A-ZÀ-Ýa-zà-ÿ.\s]+?)\s+"
    r"\d{2}/\d{2}/\d{4}\s+"
    r"(?P<sit>Atuante|Suspens[oa]|Cancelad[oa]|Licenciad[oa]|Inativ[oa])",
)


def parse_pdf_text(texto: str) -> list[LeiloeiroRaw]:
    """Extrai os leiloeiros JUCESP do texto do PDF (uma linha por leiloeiro)."""
    registros: list[LeiloeiroRaw] = []
    for m in _RE_LINHA.finditer(texto):
        nome = re.sub(r"\s+", " ", m.group("nome")).strip()
        if len(nome) < 4:
            continue
        registros.append(
            LeiloeiroRaw(
                nome=nome,
                matricula=m.group("mat"),
                uf_matricula="SP",
                junta_comercial="JUCESP",
                fonte_cadastro="jucesp:pdf_doe",
            )
        )
    return registros


class JucespScraper(JuntaScraper):
    junta = "JUCESP"
    uf = "SP"
    url_lista = URL_PDF  # PDF (D.O.E.), não HTML

    async def coletar(self) -> list[LeiloeiroRaw]:
        """Baixa o PDF oficial da JUCESP e extrai a relação de leiloeiros."""
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=60, follow_redirects=True
        ) as client:
            resp = await client.get(URL_PDF)
            resp.raise_for_status()
        import io

        reader = PdfReader(io.BytesIO(resp.content))
        texto = "\n".join(page.extract_text() or "" for page in reader.pages)
        registros = parse_pdf_text(texto)
        log.info("jucesp_pdf", leiloeiros=len(registros))
        return registros

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        # A JUCESP vem de PDF (ver coletar); _parse trata texto já extraído.
        return parse_pdf_text(html)
