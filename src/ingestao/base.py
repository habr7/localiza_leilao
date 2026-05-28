"""Infraestrutura de scraping da Fase 3 (ingestão de lotes).

Define o `LoteRaw` (registro cru de um lote de imóvel extraído de uma fonte) e o
`BaseScraper` (cliente httpx assíncrono com rate limiting por domínio, respeito a
robots.txt, User-Agent identificável e retries com backoff), conforme a seção 7
do PROJECT.md e o §4.1 do plano de desenvolvimento.

Cada fonte (agregador, site próprio, etc.) é uma subclasse que implementa
`listar_lotes_sp()`.
"""

from __future__ import annotations

import abc
import asyncio
import time
import urllib.robotparser
from typing import Self
from dataclasses import dataclass, field
from urllib.parse import urlsplit

import httpx
import structlog

log = structlog.get_logger()

# User-Agent identificável (seção 7 do PROJECT.md).
USER_AGENT = "leiloes-assimetria-bot/0.1 (+contato: humbertojunior7@hotmail.com)"
# Throttling mínimo por domínio: >= 1 req/s.
DELAY_PADRAO_S = 1.0


@dataclass
class LoteRaw:
    """Registro cru de um lote de imóvel, antes da normalização do pipeline.

    Campos que importam para o produto (leilões ABERTOS): imóvel em SP, leiloeiro
    (nome + matrículas), lance mínimo, datas de praça, tipo de leilão. As
    matrículas vêm como lista porque um leiloeiro pode exibir mais de uma
    (ex.: JUCESP + JUCEMG) — a UF efetiva é resolvida com a regra "SP vence".
    """

    fonte_origem: str  # ex.: "megaleiloes"
    fonte_tipo: str  # 'agregador' | 'site_proprio' | 'jucesp_comunicacao' | 'doe'
    fonte_url: str  # URL do lote/detalhe na fonte
    titulo: str | None = None
    numero_lote: str | None = None
    tipo_imovel: str | None = None
    cidade: str | None = None
    uf: str | None = None  # UF do IMÓVEL (filtro duro: SP)
    bairro: str | None = None
    endereco_completo: str | None = None
    cep: str | None = None
    area_m2: float | None = None
    avaliacao: float | None = None
    lance_minimo_1: float | None = None
    lance_minimo_2: float | None = None
    ocupado: bool | None = None
    fotos: list[str] = field(default_factory=list)
    descricao: str | None = None
    # Leilão
    tipo_leilao: str | None = None  # 'judicial' | 'extrajudicial'
    comitente: str | None = None
    data_1praca: str | None = None
    data_2praca: str | None = None
    edital_url: str | None = None
    # Leiloeiro (cru, como exibido na fonte)
    leiloeiro_nome: str | None = None
    leiloeiro_matriculas: list[str] = field(default_factory=list)
    dados_extras: dict | None = None


class _RateLimiter:
    """Garante um intervalo mínimo entre requisições por domínio."""

    def __init__(self, delay_s: float = DELAY_PADRAO_S) -> None:
        self._delay = delay_s
        self._ultimo: dict[str, float] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def aguardar(self, dominio: str) -> None:
        lock = self._locks.setdefault(dominio, asyncio.Lock())
        async with lock:
            agora = time.monotonic()
            decorrido = agora - self._ultimo.get(dominio, 0.0)
            if decorrido < self._delay:
                await asyncio.sleep(self._delay - decorrido)
            self._ultimo[dominio] = time.monotonic()


class BaseScraper(abc.ABC):
    """Base de scraping: cliente compartilhado, throttling, robots e retries."""

    fonte_origem: str
    fonte_tipo: str

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        delay_s: float = DELAY_PADRAO_S,
        respeitar_robots: bool = True,
    ) -> None:
        self._client = client
        self._client_proprio = client is None
        self._rate = _RateLimiter(delay_s)
        self._respeitar_robots = respeitar_robots
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    async def __aenter__(self) -> Self:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": USER_AGENT}, timeout=30, follow_redirects=True
            )
            self._client_proprio = True
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._client_proprio and self._client is not None:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": USER_AGENT}, timeout=30, follow_redirects=True
            )
            self._client_proprio = True
        return self._client

    async def _robots_permite(self, url: str) -> bool:
        if not self._respeitar_robots:
            return True
        partes = urlsplit(url)
        base = f"{partes.scheme}://{partes.netloc}"
        if base not in self._robots:
            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(f"{base}/robots.txt")
            guardado: urllib.robotparser.RobotFileParser | None = parser
            try:
                resp = await self._get_client().get(f"{base}/robots.txt")
                if resp.status_code == 200:
                    parser.parse(resp.text.splitlines())
                else:
                    guardado = None  # sem robots acessível -> não bloqueia
            except httpx.HTTPError:
                guardado = None
            self._robots[base] = guardado
        rp = self._robots[base]
        return True if rp is None else rp.can_fetch(USER_AGENT, url)

    async def fetch(self, url: str, tentativas: int = 3) -> str | None:
        """Baixa uma página respeitando robots, throttling e retries com backoff.

        Retorna None se o robots proibir ou se todas as tentativas falharem
        (ex.: 403 anti-bot) — a fonte simplesmente não contribui, sem derrubar
        a coleta inteira.
        """
        if not await self._robots_permite(url):
            log.warning("robots_bloqueou", fonte=self.fonte_origem, url=url)
            return None
        dominio = urlsplit(url).netloc
        for tentativa in range(1, tentativas + 1):
            await self._rate.aguardar(dominio)
            try:
                resp = await self._get_client().get(url)
                resp.raise_for_status()
                return resp.text
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                # 4xx (exceto 429) não melhora com retry.
                if status != 429 and 400 <= status < 500:
                    log.warning("fetch_4xx", fonte=self.fonte_origem, url=url, status=status)
                    return None
                espera = 2.0**tentativa
                log.warning(
                    "fetch_retry",
                    fonte=self.fonte_origem,
                    url=url,
                    status=status,
                    tentativa=tentativa,
                    espera=espera,
                )
                await asyncio.sleep(espera)
            except httpx.HTTPError as exc:
                espera = 2.0**tentativa
                log.warning(
                    "fetch_erro",
                    fonte=self.fonte_origem,
                    url=url,
                    erro=type(exc).__name__,
                    tentativa=tentativa,
                    espera=espera,
                )
                await asyncio.sleep(espera)
        log.error("fetch_falhou", fonte=self.fonte_origem, url=url)
        return None
