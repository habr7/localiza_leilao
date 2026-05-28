"""Ingestão dos sites próprios de leiloeiros não-SP (Fase 3.2).

Varre os `site_oficial` do cadastro (leiloeiros NÃO-SP), detecta os que rodam na
plataforma Suporte Leilões e coleta os imóveis localizados em SP com leilão
aberto — o coração da tese (sites pequenos/obscuros, menor concorrência). Cada
lote é persistido com `fonte_tipo='site_proprio'` e a UF do leiloeiro vinda do
cadastro (é o site dele, então sabemos quem é).

Uso:
    uv run python -m src.scripts.fase3_sites_proprios
"""

from __future__ import annotations

import asyncio
import logging
from urllib.parse import urlsplit

import structlog
from sqlalchemy import select

from src.core.config import settings
from src.core.db import get_session
from src.core.models import Leiloeiro
from src.ingestao.base import LoteRaw
from src.ingestao.persistencia import IngestaoStats, persistir_lote
from src.ingestao.sites_proprios.suporte_leiloes import SuporteLeiloesScraper
from src.leiloeiros.resolver import LeiloeiroRef, Resolucao

log = structlog.get_logger()


def _dominio(site: str) -> str | None:
    """Normaliza o site_oficial para um domínio; descarta e-mails mal gravados."""
    valor = site.strip()
    if not valor or "@" in valor:
        return None
    if not valor.startswith("http"):
        valor = f"https://{valor}"
    netloc = urlsplit(valor).netloc.lower()
    return netloc or None


def carregar_sites_nao_sp() -> dict[str, LeiloeiroRef]:
    """Mapeia domínio -> leiloeiro não-SP do cadastro que tem site_oficial."""
    sites: dict[str, LeiloeiroRef] = {}
    with get_session() as session:
        query = select(Leiloeiro).where(
            Leiloeiro.uf_matricula != "SP",
            Leiloeiro.site_oficial.isnot(None),
            Leiloeiro.ativo.is_(True),
        )
        for leiloeiro in session.scalars(query):
            dominio = _dominio(leiloeiro.site_oficial or "")
            if dominio and dominio not in sites:
                sites[dominio] = LeiloeiroRef(
                    id=leiloeiro.id,
                    nome=leiloeiro.nome,
                    matricula=leiloeiro.matricula,
                    uf_matricula=leiloeiro.uf_matricula,
                    junta_comercial=leiloeiro.junta_comercial,
                )
    return sites


async def coletar_todos(dominios: list[str]) -> dict[str, list[LoteRaw]]:
    """Coleta lotes SP de todos os domínios em paralelo (domínios distintos)."""
    sem = asyncio.Semaphore(12)
    # Varredura ampla: muitos domínios estão fora do ar. Falhar rápido
    # (1 tentativa, timeout curto) em vez de gastar minutos em retries.
    async with SuporteLeiloesScraper(tentativas=1, timeout_s=8.0) as scraper:

        async def um(dominio: str) -> tuple[str, list[LoteRaw]]:
            async with sem:
                try:
                    return dominio, await scraper.coletar_site(f"https://{dominio}")
                except Exception as exc:  # noqa: BLE001
                    log.warning("site_falhou", dominio=dominio, erro=str(exc))
                    return dominio, []

        resultados = await asyncio.gather(*[um(d) for d in dominios])
    return {d: lotes for d, lotes in resultados if lotes}


def persistir(
    por_dominio: dict[str, list[LoteRaw]], sites: dict[str, LeiloeiroRef]
) -> IngestaoStats:
    """Persiste os lotes, atribuindo a cada um o leiloeiro (não-SP) dono do site."""
    stats = IngestaoStats()
    with get_session() as session:
        for dominio, lotes in por_dominio.items():
            ref = sites[dominio]
            resol = Resolucao(
                uf=ref.uf_matricula,
                fora_sp=ref.uf_matricula != "SP",
                confianca="alta",
                leiloeiro=ref,
                motivo="site_proprio",
            )
            for lote in lotes:
                persistir_lote(session, lote, resol)
                stats.processados += 1
                if resol.fora_sp:
                    stats.fora_sp += 1
                else:
                    stats.sp += 1
            log.info(
                "site_coletado",
                dominio=dominio,
                leiloeiro=ref.nome,
                uf=ref.uf_matricula,
                lotes=len(lotes),
            )
    return stats


def main() -> None:
    """Orquestra a varredura dos sites próprios não-SP (plataforma Suporte Leilões)."""
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        )
    )
    sites = carregar_sites_nao_sp()
    log.info("fase3_sites_proprios_iniciada", dominios=len(sites))

    por_dominio = asyncio.run(coletar_todos(list(sites)))
    stats = persistir(por_dominio, sites)

    print(f"\nSites com imóveis SP (plataforma Suporte Leilões): {len(por_dominio)}")
    for dominio, lotes in sorted(por_dominio.items(), key=lambda x: -len(x[1])):
        ref = sites[dominio]
        print(f"  {len(lotes):4} lotes SP  {dominio:34} ({ref.nome[:30]}, {ref.uf_matricula})")
    print(
        f"\nTotal: {stats.processados} lotes-alvo persistidos "
        f"(leiloeiro não-SP + imóvel SP), fonte_tipo=site_proprio."
    )


if __name__ == "__main__":
    main()
