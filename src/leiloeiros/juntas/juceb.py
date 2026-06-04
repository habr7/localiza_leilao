"""Coletor da JUCEB (Bahia) — leiloeiros não-SP (alvo da tese).

Lista pública em tabela HTML: Nome | Contatos(site) | Endereço | Nomeação |
Matrícula | Portaria | Situação. O site fica na coluna "Contatos". A cadeia
SSL do servidor falha, então desativamos a verificação de certificado.
"""

from __future__ import annotations

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas._util import parse_tabela
from src.leiloeiros.juntas.base import JuntaScraper


class JucebScraper(JuntaScraper):
    junta = "JUCEB"
    uf = "BA"
    url_lista = "https://www.ba.gov.br/juceb/home/matriculas-e-carteira-profissional/leiloeiros"
    verificar_ssl = False

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        return parse_tabela(
            html,
            self.uf,
            self.junta,
            self.fonte_cadastro,
            idx_nome=0,
            idx_matricula=4,
            idx_site=1,
        )
