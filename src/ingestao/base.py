"""Infraestrutura de scraping da Fase 3 (ingestão multi-fonte).

`BaseScraper` concentra a disciplina de coleta exigida pelo PROJECT.md (seção 7)
e pelo plano (§4.1): cliente httpx assíncrono, rate limiting por domínio
(≥ 1 req/s), respeito a `robots.txt`, User-Agent identificável e retries com
backoff exponencial. Cada fonte concreta (agregador, site próprio, ...) herda
daqui e implementa `listar_lotes_sp`.

`LoteRaw` é o registro cru extraído de uma fonte, antes da resolução do
leiloeiro e do upsert no banco.
"""

from __future__ import annotations

import abc
import asyncio
import time
import urllib.robotparser
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from urllib.parse import urlparse, urlsplit, urlunsplit

import httpx
import structlog

log = structlog.get_logger()

# User-Agent identificável (PROJECT.md §7).
USER_AGENT = "leiloes-assimetria-bot/0.1 (+contato: humbertojunior7@hotmail.com)"
DELAY_PADRAO_S = 1.0  # >= 1 req/s por domínio
MAX_TENTATIVAS = 4
BACKOFF_BASE_S = 2.0


@dataclass
class LoteRaw:
    """Lote/imóvel cru extraído de uma fonte (antes de resolver o leiloeiro).

    Carrega dados do leilão, do lote e do leiloeiro como exibidos. A UF do
    leiloeiro NÃO é decidida aqui: guardamos as matrículas cruas e a resolução
    fica a cargo do `LeiloeiroResolver` (a UF vem da matrícula, nunca da marca).
    """

    fonte_origem: str
    fonte_tipo: str
    fonte_url: str
    tipo: str  # 'judicial' | 'extrajudicial'
    cidade: str
    uf: str
    titulo: str | None = None
    numero_lote: str | None = None
    tipo_imovel: str | None = None
    bairro: str | None = None
    endereco_completo: str | None = None
    cep: str | None = None
    avaliacao: Decimal | None = None
    lance_minimo_1: Decimal | None = None
    lance_minimo_2: Decimal | None = None
    data_1praca: datetime | None = None
    data_2praca: datetime | None = None
    edital_url: str | None = None
    comitente: str | None = None
    modalidade: str | None = None
    matricula_imovel: str | None = None
    leiloeiro_nome: str | None = None
    leiloeiro_matriculas: list[str] = field(default_factory=list)
    descricao: str | None = None
    dados_extras: dict | None = None


class RateLimiter:
    """Garante intervalo mínimo entre requisições ao mesmo domínio."""

    def __init__(self, intervalo_s: float = DELAY_PADRAO_S) -> None:
        self._intervalo = intervalo_s
        self._ultimo: dict[str, float] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def aguardar(self, dominio: str) -> None:
        lock = self._locks.setdefault(dominio, asyncio.Lock())
        async with lock:
            agora = time.monotonic()
            falta = self._intervalo - (agora - self._ultimo.get(dominio, 0.0))
            if falta > 0:
                await asyncio.sleep(falta)
            self._ultimo[dominio] = time.monotonic()


class BaseScraper(abc.ABC):
    """Base assíncrona para coletores de uma fonte de lotes."""

    fonte_origem: str  # ex.: "megaleiloes"
    fonte_tipo: str  # 'agregador' | 'site_proprio' | 'jucesp_comunicacao' | 'doe'

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        rate_limiter: RateLimiter | None = None,
        intervalo_s: float = DELAY_PADRAO_S,
    ) -> None:
        self._client = client
        self._client_proprio = client is None
        self._rate = rate_limiter or RateLimiter(intervalo_s)
        # Cache de robots.txt por domínio. None = liberar tudo (robots ausente).
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    async def __aenter__(self) -> BaseScraper:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": USER_AGENT}, timeout=40, follow_redirects=True
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
                headers={"User-Agent": USER_AGENT}, timeout=40, follow_redirects=True
            )
            self._client_proprio = True
        return self._client

    async def _robots_permite(self, url: str) -> bool:
        """Consulta o robots.txt do domínio (com cache) e diz se a URL é permitida."""
        partes = urlsplit(url)
        base = f"{partes.scheme}://{partes.netloc}"
        if base not in self._robots:
            rp: urllib.robotparser.RobotFileParser | None = None
            try:
                resp = await self._get_client().get(f"{base}/robots.txt")
                if resp.status_code == 200:
                    rp = urllib.robotparser.RobotFileParser()
                    rp.set_url(f"{base}/robots.txt")
                    rp.parse(resp.text.splitlines())
            except httpx.HTTPError:
                # Sem robots acessível: por cautela operacional, liberamos (rp=None).
                rp = None
            self._robots[base] = rp
        parser = self._robots[base]
        return True if parser is None else parser.can_fetch(USER_AGENT, url)

    async def get(self, url: str) -> str:
        """Baixa uma URL respeitando robots.txt, throttling e retries com backoff."""
        if not await self._robots_permite(url):
            raise PermissionError(f"robots.txt proíbe acesso a {url}")
        dominio = urlparse(url).netloc
        ultimo_erro: Exception | None = None
        for tentativa in range(1, MAX_TENTATIVAS + 1):
            await self._rate.aguardar(dominio)
            try:
                resp = await self._get_client().get(url)
                resp.raise_for_status()
                return resp.text
            except (httpx.HTTPError, httpx.HTTPStatusError) as exc:
                ultimo_erro = exc
                espera = BACKOFF_BASE_S * (2 ** (tentativa - 1))
                log.warning(
                    "get_falhou",
                    url=url,
                    tentativa=tentativa,
                    erro=str(exc),
                    proxima_espera_s=espera if tentativa < MAX_TENTATIVAS else 0,
                )
                if tentativa < MAX_TENTATIVAS:
                    await asyncio.sleep(espera)
        assert ultimo_erro is not None
        raise ultimo_erro

    @abc.abstractmethod
    async def listar_lotes_sp(self, limite: int | None = None) -> list[LoteRaw]:
        """Lista os lotes de imóveis em SP da fonte (cru, antes de resolver UF)."""


def canonical_url(url: str) -> str:
    """Remove query string e fragmento de uma URL (descarta utm_*, âncoras)."""
    partes = urlsplit(url)
    return urlunsplit((partes.scheme, partes.netloc, partes.path, "", ""))
