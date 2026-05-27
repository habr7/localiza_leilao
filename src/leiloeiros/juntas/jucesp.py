"""Coletor da JUCESP (São Paulo).

Usado para a **lista de exclusão**: quem é matriculado na JUCESP é de SP e
NÃO entra como oportunidade da tese. Coletamos para saber quem excluir.
"""

from __future__ import annotations

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import JuntaScraper


class JucespScraper(JuntaScraper):
    junta = "JUCESP"
    uf = "SP"
    # TODO(rede): localizar a URL da relação pública de leiloeiros da JUCESP
    # (homepage: https://www.jucesp.sp.gov.br) e preencher url_lista.
    url_lista = None

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        raise NotImplementedError(
            "JUCESP: implementar selectors contra o HTML real (sessão com rede)."
        )
