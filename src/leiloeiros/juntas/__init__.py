"""Registro dos coletores de Junta Comercial disponíveis.

Acrescente novas Juntas aqui à medida que forem implementadas. JUCESP serve à
lista de exclusão; as demais são alvos da tese (leiloeiros não-SP).

Prioridade de UFs (de onde mais saem leiloeiros que atuam em SP, conforme
docs/leiloeiros.md): RJ, MG, PR, RS, SC, DF, GO primeiro; demais depois.
"""

from src.leiloeiros.juntas.base import JuntaScraper
from src.leiloeiros.juntas.jucedf import JucedfScraper
from src.leiloeiros.juntas.juceg import JucegScraper
from src.leiloeiros.juntas.jucemat import JucematScraper
from src.leiloeiros.juntas.jucemg import JucemgScraper
from src.leiloeiros.juntas.jucepar import JuceparScraper
from src.leiloeiros.juntas.jucepb import JucepbScraper
from src.leiloeiros.juntas.jucepi import JucepiScraper
from src.leiloeiros.juntas.jucergs import JucergsScraper
from src.leiloeiros.juntas.jucerja import JucerjaScraper
from src.leiloeiros.juntas.jucesc import JucescScraper
from src.leiloeiros.juntas.jucesp import JucespScraper

JUNTAS_DISPONIVEIS: dict[str, type[JuntaScraper]] = {
    # SP: lista de exclusão (quem é da JUCESP NÃO é oportunidade da tese).
    JucespScraper.junta: JucespScraper,
    # Não-SP: alvos da tese. Com parser ao vivo (trazem site_oficial):
    JuceparScraper.junta: JuceparScraper,  # PR
    JucegScraper.junta: JucegScraper,  # GO
    JucematScraper.junta: JucematScraper,  # MT
    JucepbScraper.junta: JucepbScraper,  # PB
    JucepiScraper.junta: JucepiScraper,  # PI
    # Não-SP: interface pronta, parser ao vivo pendente (lista em JS/PDF):
    JucerjaScraper.junta: JucerjaScraper,
    JucemgScraper.junta: JucemgScraper,
    JucergsScraper.junta: JucergsScraper,
    JucescScraper.junta: JucescScraper,
    JucedfScraper.junta: JucedfScraper,
}

__all__ = [
    "JuntaScraper",
    "JucespScraper",
    "JucerjaScraper",
    "JucemgScraper",
    "JuceparScraper",
    "JucergsScraper",
    "JucescScraper",
    "JucedfScraper",
    "JucegScraper",
    "JucematScraper",
    "JucepbScraper",
    "JucepiScraper",
    "JUNTAS_DISPONIVEIS",
]
