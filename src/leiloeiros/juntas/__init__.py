"""Registro dos coletores de Junta Comercial disponíveis.

Acrescente novas Juntas aqui à medida que forem implementadas. JUCESP serve à
lista de exclusão; as demais são alvos da tese (leiloeiros não-SP).
"""

from src.leiloeiros.juntas.base import JuntaScraper
from src.leiloeiros.juntas.juceb import JucebScraper
from src.leiloeiros.juntas.juceg import JucegScraper
from src.leiloeiros.juntas.jucemg import JucemgScraper
from src.leiloeiros.juntas.jucerja import JucerjaScraper
from src.leiloeiros.juntas.jucesp import JucespScraper

JUNTAS_DISPONIVEIS: dict[str, type[JuntaScraper]] = {
    JucespScraper.junta: JucespScraper,
    JucerjaScraper.junta: JucerjaScraper,
    JucemgScraper.junta: JucemgScraper,
    JucegScraper.junta: JucegScraper,
    JucebScraper.junta: JucebScraper,
}

__all__ = [
    "JuntaScraper",
    "JucespScraper",
    "JucerjaScraper",
    "JucemgScraper",
    "JucegScraper",
    "JucebScraper",
    "JUNTAS_DISPONIVEIS",
]
