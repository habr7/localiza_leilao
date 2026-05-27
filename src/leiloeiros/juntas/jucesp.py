"""Coletor da JUCESP (São Paulo).

Usado para a **lista de exclusão**: quem é matriculado na JUCESP é de SP e
NÃO entra como oportunidade da tese. Coletamos para saber quem excluir.

Estado da investigação (sessão com rede liberada): o domínio
``www.jucesp.sp.gov.br`` (e o portal ``jucesponline.sp.gov.br``) respondeu
**503** de forma consistente a clientes automatizados — provável bloqueio
anti-bot/WAF para IP de datacenter. Não há, portanto, lista pública navegável
acessível por aqui. Mantemos ``url_lista=None`` e o caminho de carga via
``coletar_csv`` (resposta de pedido LAI/e-SIC) já está pronto. Reavaliar em
produção com IP residencial/proxy ou navegador (Playwright).
"""

from __future__ import annotations

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import JuntaScraper


class JucespScraper(JuntaScraper):
    junta = "JUCESP"
    uf = "SP"
    # Domínio retorna 503 a clientes automatizados (ver docstring). Sem lista
    # pública acessível: usar coletar_csv (LAI) até haver IP/navegador adequado.
    url_lista = None

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        raise NotImplementedError(
            "JUCESP: site retorna 503 a clientes automatizados; usar coletar_csv (LAI)."
        )
