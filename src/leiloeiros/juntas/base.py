"""Interface comum dos scrapers de Junta Comercial (Fase 2).

Cada Junta vira uma subclasse que sabe (a) onde está a lista pública de
leiloeiros e (b) como parsear o HTML. O parsing real depende de inspecionar o
HTML ao vivo (rede), então `_parse` fica como ponto de extensão a ser
implementado na sessão com acesso de rede liberado.

Juntas sem lista pública navegável usam `coletar_csv` (carga da resposta de um
pedido LAI/e-SIC em CSV) — caminho que já funciona offline.
"""

from __future__ import annotations

import abc
import asyncio

import httpx
import structlog

from src.leiloeiros.cadastro import LeiloeiroRaw, importar_csv

log = structlog.get_logger()

# User-Agent identificável e throttling, conforme a seção 7 do PROJECT.md.
USER_AGENT = "leiloes-assimetria-bot/0.1 (+contato: humbertojunior7@hotmail.com)"
DELAY_PADRAO_S = 1.0  # >= 1 req/s por domínio


class JuntaScraper(abc.ABC):
    """Base para um coletor de leiloeiros de uma Junta Comercial."""

    junta: str  # ex.: "JUCERJA"
    uf: str  # ex.: "RJ"
    url_lista: str | None = None  # URL da relação pública de leiloeiros

    @property
    def fonte_cadastro(self) -> str:
        return f"junta:{self.junta.lower()}"

    def _novo_raw(
        self,
        nome: str,
        numero: str,
        site_oficial: str | None = None,
        aliases: list[str] | None = None,
    ) -> LeiloeiroRaw:
        """Monta um LeiloeiroRaw com os defaults da Junta (matrícula canônica).

        A matrícula é gravada como ``"<JUNTA> <numero>"`` (ex.: "JUCEMG 1062")
        para que o resolvedor derive UF/Junta pelo prefixo e case por
        (junta, número) com alta confiança.
        """
        return LeiloeiroRaw(
            nome=nome,
            matricula=f"{self.junta} {numero}",
            uf_matricula=self.uf,
            junta_comercial=self.junta,
            site_oficial=site_oficial,
            aliases=aliases,
            fonte_cadastro=self.fonte_cadastro,
        )

    async def _fetch(self, url: str, client: httpx.AsyncClient | None = None) -> str:
        """Baixa uma página respeitando UA identificável e throttling."""
        proprio = client is None
        client = client or httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=30, follow_redirects=True
        )
        try:
            resposta = await client.get(url)
            resposta.raise_for_status()
            await asyncio.sleep(DELAY_PADRAO_S)
            return resposta.text
        finally:
            if proprio:
                await client.aclose()

    async def coletar(self) -> list[LeiloeiroRaw]:
        """Baixa a lista pública e a converte em registros crus de leiloeiro."""
        if not self.url_lista:
            raise NotImplementedError(
                f"{self.junta}: sem URL de lista pública configurada. "
                "Descubra a URL na sessão com rede ou use coletar_csv (LAI)."
            )
        html = await self._fetch(self.url_lista)
        return self._parse(html)

    @abc.abstractmethod
    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        """Extrai leiloeiros do HTML da lista. Implementar contra o HTML real."""

    def coletar_csv(self, path: str) -> list[LeiloeiroRaw]:
        """Carrega leiloeiros de um CSV (resposta de LAI), aplicando defaults da Junta."""
        registros = importar_csv(path)
        for r in registros:
            r.uf_matricula = r.uf_matricula or self.uf
            r.junta_comercial = r.junta_comercial or self.junta
            r.fonte_cadastro = r.fonte_cadastro or f"lai:{self.junta.lower()}"
        return registros
