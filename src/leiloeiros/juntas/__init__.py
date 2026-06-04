"""Registro dos coletores de Junta Comercial disponíveis.

JUCESP serve à lista de exclusão (PDF do D.O.E.); as demais são alvos da tese
(leiloeiros não-SP). Cobertura atual: SP + 16 UFs com parser ao vivo.
"""

from src.leiloeiros.juntas.base import JuntaScraper
from src.leiloeiros.juntas.jucea import JuceaScraper  # AM
from src.leiloeiros.juntas.juceac import JuceacScraper  # AC
from src.leiloeiros.juntas.juceb import JucebScraper  # BA
from src.leiloeiros.juntas.jucec import JucecScraper  # CE
from src.leiloeiros.juntas.jucedf import JucedfScraper  # DF
from src.leiloeiros.juntas.jucees import JuceesScraper  # ES
from src.leiloeiros.juntas.juceg import JucegScraper  # GO
from src.leiloeiros.juntas.jucemat import JucematScraper  # MT
from src.leiloeiros.juntas.jucemg import JucemgScraper  # MG
from src.leiloeiros.juntas.jucems import JucemsScraper  # MS
from src.leiloeiros.juntas.jucepa import JucepaScraper  # PA
from src.leiloeiros.juntas.jucepar import JuceparScraper  # PR
from src.leiloeiros.juntas.jucepb import JucepbScraper  # PB
from src.leiloeiros.juntas.jucepi import JucepiScraper  # PI
from src.leiloeiros.juntas.jucer import JucerScraper  # RO
from src.leiloeiros.juntas.jucerja import JucerjaScraper  # RJ
from src.leiloeiros.juntas.jucesc import JucescScraper  # SC
from src.leiloeiros.juntas.jucese import JuceseScraper  # SE
from src.leiloeiros.juntas.jucesp import JucespScraper  # SP (exclusão)
from src.leiloeiros.juntas.jucisrs import JucisrsScraper  # RS

# Ordem: SP (exclusão) + não-SP por UF.
_SCRAPERS: list[type[JuntaScraper]] = [
    JucespScraper,  # SP
    JuceparScraper,  # PR
    JucegScraper,  # GO
    JucematScraper,  # MT
    JucepbScraper,  # PB
    JucepiScraper,  # PI
    JucerjaScraper,  # RJ
    JucemgScraper,  # MG
    JucisrsScraper,  # RS
    JucescScraper,  # SC
    JucedfScraper,  # DF
    JuceaScraper,  # AM
    JucebScraper,  # BA
    JucecScraper,  # CE
    JucerScraper,  # RO
    JuceseScraper,  # SE
    JuceacScraper,  # AC
    JuceesScraper,  # ES
    JucemsScraper,  # MS
    JucepaScraper,  # PA
]

JUNTAS_DISPONIVEIS: dict[str, type[JuntaScraper]] = {s.junta: s for s in _SCRAPERS}

__all__ = [
    "JuntaScraper",
    "JUNTAS_DISPONIVEIS",
    "JucespScraper",
    "JuceparScraper",
    "JucegScraper",
    "JucematScraper",
    "JucepbScraper",
    "JucepiScraper",
    "JucerjaScraper",
    "JucemgScraper",
    "JucisrsScraper",
    "JucescScraper",
    "JucedfScraper",
    "JuceaScraper",
    "JucebScraper",
    "JucecScraper",
    "JucerScraper",
    "JuceseScraper",
    "JuceacScraper",
    "JuceesScraper",
    "JucemsScraper",
    "JucepaScraper",
]
