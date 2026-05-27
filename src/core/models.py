"""Modelos de dados do núcleo (seção 5 do PROJECT.md).

Define os modelos ORM SQLAlchemy 2.0 (tabelas `leiloeiros`, `leiloes`, `lotes`,
`resultados`) e os modelos Pydantic correspondentes (sufixo `Schema`) usados para
entrada/saída de dados.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    CheckConstraint,
    Computed,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import UserDefinedType

from src.core.db import Base


class Point(UserDefinedType):
    """Tipo nativo `POINT` do PostgreSQL (usado para coordenadas após geocoding)."""

    cache_ok = True

    def get_col_spec(self, **kw: object) -> str:
        return "POINT"


# Valor padrão para colunas UUID: gerado no servidor pelo PostgreSQL.
_uuid_default = text("gen_random_uuid()")


class Leiloeiro(Base):
    """Leiloeiro matriculado em uma Junta Comercial (nunca SP nesta tese)."""

    __tablename__ = "leiloeiros"
    __table_args__ = (
        UniqueConstraint("matricula", "uf_matricula", name="uq_leiloeiros_matricula_uf"),
        Index("idx_leiloeiros_uf", "uf_matricula"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=_uuid_default
    )
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    matricula: Mapped[str] = mapped_column(Text, nullable=False)
    # UF da matrícula: 'RJ', 'MG', etc. NUNCA 'SP' na query principal da tese.
    uf_matricula: Mapped[str] = mapped_column(String(2), nullable=False)
    junta_comercial: Mapped[str] = mapped_column(Text, nullable=False)
    cpf: Mapped[str | None] = mapped_column(Text)
    site_oficial: Mapped[str | None] = mapped_column(Text)
    # Plataformas em que o leiloeiro aparece (ex.: ['megaleiloes.com.br']).
    plataformas: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    # Variações de nome encontradas em portais (ajuda o resolvedor a casar nomes).
    aliases: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    # De onde veio o cadastro: 'jucesp_site', 'lai_jucemg', 'agregador:mega', ...
    fonte_cadastro: Mapped[str | None] = mapped_column(Text)
    # Última vez que o leiloeiro apareceu numa coleta.
    visto_em: Mapped[datetime | None] = mapped_column()
    ativo: Mapped[bool] = mapped_column(server_default=text("true"))
    atualizado_em: Mapped[datetime] = mapped_column(server_default=func.now())

    leiloes: Mapped[list[Leilao]] = relationship(back_populates="leiloeiro")


class Leilao(Base):
    """Leilão (judicial ou extrajudicial) conduzido por um leiloeiro."""

    __tablename__ = "leiloes"
    __table_args__ = (
        CheckConstraint("tipo IN ('judicial', 'extrajudicial')", name="ck_leiloes_tipo"),
        Index("idx_leiloes_uf_leiloeiro", "uf_leiloeiro"),
        Index("idx_leiloes_fonte_tipo", "fonte_tipo"),
        Index("idx_leiloes_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=_uuid_default
    )
    leiloeiro_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("leiloeiros.id"))
    # UF da matrícula do leiloeiro, desnormalizada no momento da ingestão.
    # Permite filtrar "não-SP" sem JOIN e preserva o valor histórico. É o
    # gatilho central da tese: uf_leiloeiro != 'SP' com imóvel em SP.
    uf_leiloeiro: Mapped[str | None] = mapped_column(String(2))
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    # 'alienacao_fiduciaria', 'particular', 'falencia', ...
    modalidade: Mapped[str | None] = mapped_column(Text)
    # Banco / fundo / credor que promove o leilão.
    comitente: Mapped[str | None] = mapped_column(Text)
    data_1praca: Mapped[datetime | None] = mapped_column()
    data_2praca: Mapped[datetime | None] = mapped_column()
    edital_url: Mapped[str | None] = mapped_column(Text)
    # Fonte da coleta: 'megaleiloes', 'site_proprio:xyz', 'doe_mg', ...
    fonte_origem: Mapped[str] = mapped_column(Text, nullable=False)
    # Categoria da fonte: 'agregador' | 'site_proprio' | 'jucesp_comunicacao' |
    # 'doe'. Fontes pequenas/obscuras (site_proprio) sinalizam maior assimetria.
    fonte_tipo: Mapped[str | None] = mapped_column(Text)
    fonte_url: Mapped[str] = mapped_column(Text, nullable=False)
    coletado_em: Mapped[datetime] = mapped_column(server_default=func.now())
    # 'aberto', 'realizado', 'cancelado', 'suspenso'.
    status: Mapped[str] = mapped_column(Text, server_default=text("'aberto'"))

    leiloeiro: Mapped[Leiloeiro | None] = relationship(back_populates="leiloes")
    lotes: Mapped[list[Lote]] = relationship(back_populates="leilao")


class Lote(Base):
    """Lote individual de um leilão. Filtro duro: imóvel localizado em SP."""

    __tablename__ = "lotes"
    __table_args__ = (
        CheckConstraint("uf = 'SP'", name="ck_lotes_uf_sp"),
        UniqueConstraint("hash_dedup", "leilao_id", name="uq_lotes_dedup_leilao"),
        Index("idx_lotes_cidade", "cidade"),
        Index("idx_lotes_dedup", "hash_dedup"),
        Index("idx_lotes_score", "score_oportunidade"),
        Index("idx_lotes_tipo_imovel", "tipo_imovel"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=_uuid_default
    )
    leilao_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("leiloes.id"))
    numero_lote: Mapped[str | None] = mapped_column(Text)
    # 'apartamento', 'casa', 'terreno', 'comercial', 'rural'.
    tipo_imovel: Mapped[str | None] = mapped_column(Text)
    endereco_completo: Mapped[str | None] = mapped_column(Text)
    cep: Mapped[str | None] = mapped_column(Text)
    cidade: Mapped[str] = mapped_column(Text, nullable=False)
    uf: Mapped[str] = mapped_column(String(2), nullable=False)
    bairro: Mapped[str | None] = mapped_column(Text)
    # Matrícula do imóvel no Registro de Imóveis.
    matricula_imovel: Mapped[str | None] = mapped_column(Text)
    area_m2: Mapped[Decimal | None] = mapped_column(Numeric)
    avaliacao: Mapped[Decimal | None] = mapped_column(Numeric)
    lance_minimo_1: Mapped[Decimal | None] = mapped_column(Numeric)
    lance_minimo_2: Mapped[Decimal | None] = mapped_column(Numeric)
    ocupado: Mapped[bool | None] = mapped_column()
    divida_iptu: Mapped[Decimal | None] = mapped_column(Numeric)
    divida_condominio: Mapped[Decimal | None] = mapped_column(Numeric)
    # Array de URLs de fotos.
    fotos: Mapped[dict | list | None] = mapped_column(JSONB)
    descricao: Mapped[str | None] = mapped_column(Text)
    coordenadas: Mapped[object | None] = mapped_column(Point)
    # hash(matricula_imovel + endereco) para deduplicação entre fontes.
    hash_dedup: Mapped[str | None] = mapped_column(Text)
    score_oportunidade: Mapped[Decimal | None] = mapped_column(Numeric)
    # Campo flexível por fonte.
    dados_extras: Mapped[dict | list | None] = mapped_column(JSONB)

    leilao: Mapped[Leilao | None] = relationship(back_populates="lotes")
    resultados: Mapped[list[Resultado]] = relationship(back_populates="lote")
    fontes: Mapped[list[LoteFonte]] = relationship(back_populates="lote")


class Resultado(Base):
    """Resultado de arrematação de um lote (Fase 1 e backtest contínuo)."""

    __tablename__ = "resultados"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=_uuid_default
    )
    lote_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("lotes.id"))
    arrematado: Mapped[bool | None] = mapped_column()
    preco_arremate: Mapped[Decimal | None] = mapped_column(Numeric)
    num_lances: Mapped[int | None] = mapped_column(Integer)
    # Snapshot do lance mínimo da 2ª praça no momento do resultado. Fica em
    # `resultados` (e não só em `lotes`) por duas razões: o PostgreSQL exige que
    # uma coluna GERADA referencie apenas colunas da própria tabela; e é um
    # registro imutável do piso usado no arremate, mesmo que o lote mude depois.
    lance_minimo_2: Mapped[Decimal | None] = mapped_column(Numeric)
    # Ágio calculado pelo banco: (preco_arremate / lance_minimo_2 - 1).
    agio: Mapped[Decimal | None] = mapped_column(
        Numeric,
        Computed(
            "CASE WHEN preco_arremate IS NOT NULL AND lance_minimo_2 > 0 "
            "THEN (preco_arremate / lance_minimo_2 - 1) ELSE NULL END",
            persisted=True,
        ),
    )
    coletado_em: Mapped[datetime] = mapped_column(server_default=func.now())

    lote: Mapped[Lote | None] = relationship(back_populates="resultados")


class LoteFonte(Base):
    """Fonte onde um lote foi visto. Um lote físico pode aparecer em N portais.

    A deduplicação mantém um único `lote` e registra cada portal que o anunciou
    aqui (referência cruzada), preservando a URL e os dados crus de cada fonte.
    """

    __tablename__ = "lote_fontes"
    __table_args__ = (UniqueConstraint("lote_id", "fonte_url", name="uq_lote_fontes_url"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=_uuid_default
    )
    lote_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("lotes.id"))
    fonte_origem: Mapped[str] = mapped_column(Text, nullable=False)
    fonte_tipo: Mapped[str | None] = mapped_column(Text)
    fonte_url: Mapped[str] = mapped_column(Text, nullable=False)
    coletado_em: Mapped[datetime] = mapped_column(server_default=func.now())
    dados_extras: Mapped[dict | list | None] = mapped_column(JSONB)

    lote: Mapped[Lote | None] = relationship(back_populates="fontes")


# ---------------------------------------------------------------------------
# Modelos Pydantic (entrada/saída). Sufixo `Schema`.
# ---------------------------------------------------------------------------


class LeiloeiroSchema(BaseModel):
    """Representação de entrada/saída de um leiloeiro."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = None
    nome: str
    matricula: str
    uf_matricula: str
    junta_comercial: str
    cpf: str | None = None
    site_oficial: str | None = None
    plataformas: list[str] | None = None
    aliases: list[str] | None = None
    fonte_cadastro: str | None = None
    visto_em: datetime | None = None
    ativo: bool = True
    atualizado_em: datetime | None = None


class LeilaoSchema(BaseModel):
    """Representação de entrada/saída de um leilão."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = None
    leiloeiro_id: uuid.UUID | None = None
    uf_leiloeiro: str | None = None
    tipo: str
    modalidade: str | None = None
    comitente: str | None = None
    data_1praca: datetime | None = None
    data_2praca: datetime | None = None
    edital_url: str | None = None
    fonte_origem: str
    fonte_tipo: str | None = None
    fonte_url: str
    coletado_em: datetime | None = None
    status: str = "aberto"


class LoteSchema(BaseModel):
    """Representação de entrada/saída de um lote."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = None
    leilao_id: uuid.UUID | None = None
    numero_lote: str | None = None
    tipo_imovel: str | None = None
    endereco_completo: str | None = None
    cep: str | None = None
    cidade: str
    uf: str
    bairro: str | None = None
    matricula_imovel: str | None = None
    area_m2: Decimal | None = None
    avaliacao: Decimal | None = None
    lance_minimo_1: Decimal | None = None
    lance_minimo_2: Decimal | None = None
    ocupado: bool | None = None
    divida_iptu: Decimal | None = None
    divida_condominio: Decimal | None = None
    fotos: list | dict | None = None
    descricao: str | None = None
    hash_dedup: str | None = None
    score_oportunidade: Decimal | None = None
    dados_extras: list | dict | None = None


class ResultadoSchema(BaseModel):
    """Representação de entrada/saída de um resultado de arrematação."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = None
    lote_id: uuid.UUID | None = None
    arrematado: bool | None = None
    preco_arremate: Decimal | None = None
    num_lances: int | None = None
    lance_minimo_2: Decimal | None = None
    agio: Decimal | None = None
    coletado_em: datetime | None = None


class LoteFonteSchema(BaseModel):
    """Representação de entrada/saída de uma fonte de lote."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = None
    lote_id: uuid.UUID | None = None
    fonte_origem: str
    fonte_tipo: str | None = None
    fonte_url: str
    coletado_em: datetime | None = None
    dados_extras: list | dict | None = None
