"""Registro dos coletores de Junta Comercial disponíveis.

Acrescente novas Juntas aqui à medida que forem implementadas. JUCESP serve à
lista de exclusão; as demais são alvos da tese (leiloeiros não-SP).

Prioridade de UFs (de onde mais saem leiloeiros que atuam em SP, conforme
docs/leiloeiros.md): RJ, MG, PR, RS, SC, DF, GO primeiro; demais depois.
"""

from src.leiloeiros.juntas.base import JuntaScraper
from src.leiloeiros.juntas.jucedf import JucedfScraper
from src.leiloeiros.juntas.juceg import JucegScraper
from src.leiloeiros.juntas.jucemg import JucemgScraper
from src.leiloeiros.juntas.jucepar import JuceparScraper
from src.leiloeiros.juntas.jucergs import JucergsScraper
from src.leiloeiros.juntas.jucerja import JucerjaScraper
from src.leiloeiros.juntas.jucesc import JucescScraper
from src.leiloeiros.juntas.jucesp import JucespScraper

JUNTAS_DISPONIVEIS: dict[str, type[JuntaScraper]] = {
    # SP: lista de exclusão (quem é da JUCESP NÃO é oportunidade da tese).
    JucespScraper.junta: JucespScraper,
    # Não-SP: alvos da tese, na ordem de prioridade do projeto.
    JucerjaScraper.junta: JucerjaScraper,
    JucemgScraper.junta: JucemgScraper,
    JuceparScraper.junta: JuceparScraper,
    JucergsScraper.junta: JucergsScraper,
    JucescScraper.junta: JucescScraper,
    JucedfScraper.junta: JucedfScraper,
    JucegScraper.junta: JucegScraper,
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
    "JUNTAS_DISPONIVEIS",
]
