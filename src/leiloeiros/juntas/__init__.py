"""Registro dos coletores de Junta Comercial disponíveis.

Acrescente novas Juntas aqui à medida que forem implementadas. JUCESP serve à
lista de exclusão; as demais são alvos da tese (leiloeiros não-SP).
"""

from src.leiloeiros.juntas.base import JuntaScraper
from src.leiloeiros.juntas.juceb import JucebScraper
from src.leiloeiros.juntas.jucec import JucecScraper
from src.leiloeiros.juntas.jucees import JuceesScraper
from src.leiloeiros.juntas.juceg import JucegScraper
from src.leiloeiros.juntas.jucemg import JucemgScraper
from src.leiloeiros.juntas.jucems import JucemsScraper
from src.leiloeiros.juntas.jucepar import JuceparScraper
from src.leiloeiros.juntas.jucerja import JucerjaScraper
from src.leiloeiros.juntas.jucesc import JucescScraper
from src.leiloeiros.juntas.jucesp import JucespScraper

JUNTAS_DISPONIVEIS: dict[str, type[JuntaScraper]] = {
    JucespScraper.junta: JucespScraper,
    JucerjaScraper.junta: JucerjaScraper,
    JucemgScraper.junta: JucemgScraper,
    JucegScraper.junta: JucegScraper,
    JucebScraper.junta: JucebScraper,
    JuceparScraper.junta: JuceparScraper,
    JucescScraper.junta: JucescScraper,
    JucecScraper.junta: JucecScraper,
    JucemsScraper.junta: JucemsScraper,
    JuceesScraper.junta: JuceesScraper,
}

__all__ = [
    "JuntaScraper",
    "JucespScraper",
    "JucerjaScraper",
    "JucemgScraper",
    "JucegScraper",
    "JucebScraper",
    "JuceparScraper",
    "JucescScraper",
    "JucecScraper",
    "JucemsScraper",
    "JuceesScraper",
    "JUNTAS_DISPONIVEIS",
]
