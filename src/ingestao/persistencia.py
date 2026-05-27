"""Persistência idempotente de lotes coletados (Fase 3).

Recebe um `LoteRaw` já resolvido (com a UF do leiloeiro) e faz upsert em
`leiloes`, `lotes` e `lote_fontes`. Todas as escritas usam `ON CONFLICT DO
UPDATE` por chave natural, então rodar a ingestão duas vezes não duplica.

Modelagem do agregador: cada "batch" do portal é um leilão (chave natural:
`fonte_url`) com um lote. A deduplicação física entre fontes é da Fase 4.
"""

from __future__ import annotations

from dataclasses import dataclass

import structlog
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.core.models import Leilao, Lote, LoteFonte
from src.ingestao.base import LoteRaw
from src.leiloeiros.resolver import Resolucao

log = structlog.get_logger()


@dataclass
class IngestaoStats:
    """Contagem do resultado de uma ingestão."""

    processados: int = 0
    fora_sp: int = 0
    sp: int = 0
    uf_indefinida: int = 0


def persistir_lote(session: Session, lote: LoteRaw, resolucao: Resolucao) -> None:
    """Faz upsert idempotente de leilão + lote + fonte para um lote resolvido."""
    leilao_id = _upsert_leilao(session, lote, resolucao)
    lote_id = _upsert_lote(session, lote, leilao_id)
    _upsert_lote_fonte(session, lote, lote_id, resolucao)


def _upsert_leilao(session: Session, lote: LoteRaw, resolucao: Resolucao) -> object:
    leiloeiro_id = resolucao.leiloeiro.id if resolucao.leiloeiro else None
    valores = {
        "fonte_url": lote.fonte_url,
        "fonte_origem": lote.fonte_origem,
        "fonte_tipo": lote.fonte_tipo,
        "tipo": lote.tipo,
        "uf_leiloeiro": resolucao.uf,
        "leiloeiro_id": leiloeiro_id,
        "modalidade": lote.modalidade,
        "comitente": lote.comitente,
        "data_1praca": lote.data_1praca,
        "data_2praca": lote.data_2praca,
        "edital_url": lote.edital_url,
        "status": "aberto",
    }
    base = insert(Leilao).values(**valores)
    stmt = base.on_conflict_do_update(
        constraint="uq_leiloes_fonte_url",
        set_={
            "fonte_tipo": base.excluded.fonte_tipo,
            "tipo": base.excluded.tipo,
            "uf_leiloeiro": base.excluded.uf_leiloeiro,
            "leiloeiro_id": base.excluded.leiloeiro_id,
            "modalidade": base.excluded.modalidade,
            "comitente": base.excluded.comitente,
            "data_1praca": base.excluded.data_1praca,
            "data_2praca": base.excluded.data_2praca,
            "edital_url": base.excluded.edital_url,
        },
    ).returning(Leilao.id)
    return session.execute(stmt).scalar_one()


def _upsert_lote(session: Session, lote: LoteRaw, leilao_id: object) -> object:
    # Chave de dedup estável por lote do portal (código do lote; URL como fallback).
    hash_dedup = lote.numero_lote or lote.fonte_url
    valores = {
        "leilao_id": leilao_id,
        "hash_dedup": hash_dedup,
        "numero_lote": lote.numero_lote,
        "tipo_imovel": lote.tipo_imovel,
        "endereco_completo": lote.endereco_completo,
        "cidade": lote.cidade,
        "uf": lote.uf,
        "bairro": lote.bairro,
        "cep": lote.cep,
        "matricula_imovel": lote.matricula_imovel,
        "avaliacao": lote.avaliacao,
        "lance_minimo_1": lote.lance_minimo_1,
        "lance_minimo_2": lote.lance_minimo_2,
        "descricao": lote.descricao or lote.titulo,
    }
    base = insert(Lote).values(**valores)
    stmt = base.on_conflict_do_update(
        constraint="uq_lotes_dedup_leilao",
        set_={
            "numero_lote": base.excluded.numero_lote,
            "tipo_imovel": base.excluded.tipo_imovel,
            "endereco_completo": base.excluded.endereco_completo,
            "cidade": base.excluded.cidade,
            "bairro": base.excluded.bairro,
            "cep": base.excluded.cep,
            "matricula_imovel": base.excluded.matricula_imovel,
            "avaliacao": base.excluded.avaliacao,
            "lance_minimo_1": base.excluded.lance_minimo_1,
            "lance_minimo_2": base.excluded.lance_minimo_2,
            "descricao": base.excluded.descricao,
        },
    ).returning(Lote.id)
    return session.execute(stmt).scalar_one()


def _upsert_lote_fonte(
    session: Session, lote: LoteRaw, lote_id: object, resolucao: Resolucao
) -> None:
    extras = {
        "leiloeiro_nome": lote.leiloeiro_nome,
        "leiloeiro_matriculas": lote.leiloeiro_matriculas,
        "uf_leiloeiro": resolucao.uf,
        "confianca_uf": resolucao.confianca,
        "titulo": lote.titulo,
    }
    valores = {
        "lote_id": lote_id,
        "fonte_origem": lote.fonte_origem,
        "fonte_tipo": lote.fonte_tipo,
        "fonte_url": lote.fonte_url,
        "dados_extras": extras,
    }
    base = insert(LoteFonte).values(**valores)
    stmt = base.on_conflict_do_update(
        constraint="uq_lote_fontes_url",
        set_={
            "fonte_origem": base.excluded.fonte_origem,
            "fonte_tipo": base.excluded.fonte_tipo,
            "dados_extras": base.excluded.dados_extras,
        },
    )
    session.execute(stmt)
