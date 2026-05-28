"""Coletores de sites próprios de leiloeiros não-SP (Fase 3).

`scanner.py` é a varredura heurística de descoberta (qualquer site). Os módulos
por site (ex.: `webleiloes`, `leiloariasmart`) são **parsers dedicados** que
extraem o lote estruturado. `SCRAPERS_DEDICADOS` lista os que já existem.
"""

from src.ingestao.sites_proprios.leiloariasmart import LeiloariaSmartScraper
from src.ingestao.sites_proprios.webleiloes import WebLeiloesScraper

# Scrapers dedicados disponíveis (cada um com `.dominio` para casar no cadastro).
SCRAPERS_DEDICADOS = [WebLeiloesScraper, LeiloariaSmartScraper]

__all__ = ["WebLeiloesScraper", "LeiloariaSmartScraper", "SCRAPERS_DEDICADOS"]
