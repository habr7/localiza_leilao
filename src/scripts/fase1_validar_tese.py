"""Script de validação da tese (Fase 1).

Lê `data/fase1_input.csv` com leilões já realizados, classifica cada um pela UF
do leiloeiro (SP vs. não-SP), calcula o ágio e a taxa de lotes desertos por grupo,
roda um teste de Mann-Whitney U comparando os ágios e emite um veredito automático
em `data/fase1_output.md`.

O veredito segue o critério de avanço do PROJECT.md (Fase 1): a tese é considerada
validada se a mediana de ágio do grupo não-SP for ao menos 3 pontos percentuais
*menor* que a do grupo SP, OU se a taxa de lotes desertos do grupo não-SP for ao
menos 10 pontos percentuais *maior*.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from zoneinfo import ZoneInfo

import pandas as pd
import structlog
from scipy.stats import mannwhitneyu

from src.core.config import settings

log = structlog.get_logger()

# Caminhos de entrada/saída.
DATA_DIR = Path("data")
INPUT_CSV = DATA_DIR / "fase1_input.csv"
OUTPUT_MD = DATA_DIR / "fase1_output.md"

# Limiares do critério de avanço (PROJECT.md, Fase 1).
LIMIAR_AGIO_PP = 0.03  # 3 pontos percentuais de diferença na mediana de ágio
LIMIAR_DESERTO_PP = 0.10  # 10 pontos percentuais de diferença na taxa de deserto
N_MINIMO_GRUPO = 30  # abaixo disso em qualquer grupo, o veredito é INSUFICIENTE

# UFs brasileiras (siglas de 2 letras).
_UFS = {
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
}

# Mapa de siglas de Juntas Comerciais -> UF. Inclui variações comuns.
JUNTA_TO_UF: dict[str, str] = {
    "JUCEAC": "AC",
    "JUCEAL": "AL",
    "JUCAP": "AP",
    "JUCEAP": "AP",
    "JUCEA": "AM",
    "JUCEAM": "AM",
    "JUCEB": "BA",
    "JUCEBA": "BA",
    "JUCEC": "CE",
    "JUCECE": "CE",
    "JUCISDF": "DF",
    "JUCIDF": "DF",
    "JUCEDF": "DF",
    "JUCEES": "ES",
    "JUCEG": "GO",
    "JUCEGO": "GO",
    "JUCEMA": "MA",
    "JUCEMAT": "MT",
    "JUCEMT": "MT",
    "JUCEMS": "MS",
    "JUCEMG": "MG",
    "JUCEPA": "PA",
    "JUCEP": "PB",
    "JUCEPB": "PB",
    "JUCEPAR": "PR",
    "JUCEPE": "PE",
    "JUCEPI": "PI",
    "JUCERJA": "RJ",
    "JUCERJ": "RJ",
    "JUCERN": "RN",
    "JUCERGS": "RS",
    "JUCERS": "RS",
    "JUCER": "RO",
    "JUCERO": "RO",
    "JUCERR": "RR",
    "JUCESC": "SC",
    "JUCESP": "SP",
    "JUCESE": "SE",
    "JUCETINS": "TO",
    "JUCETO": "TO",
}
# Aceita também a UF informada diretamente como prefixo (ex.: "SP 123").
JUNTA_TO_UF.update({uf: uf for uf in _UFS})


def parse_uf_matricula(matricula: str | None) -> str | None:
    """Extrai a UF do leiloeiro a partir do prefixo da matrícula.

    Aceita variações com espaço, hífen e maiúsculas/minúsculas, por exemplo:
    "JUCERJA 123", "jucerja-123", "JUCERJA123", "  Jucesp 456  ". Retorna a sigla
    da UF (ex.: "RJ") ou None se o prefixo não for reconhecido.
    """
    if not matricula:
        return None
    token = re.match(r"[A-Za-z]+", matricula.strip())
    if token is None:
        return None
    return JUNTA_TO_UF.get(token.group(0).upper())


def calcular_agio(preco_arremate: float | None, lance_minimo_2: float | None) -> float | None:
    """Calcula o ágio = preco_arremate / lance_minimo_2 - 1.

    Retorna None quando não há preço de arremate ou o lance mínimo é inválido
    (None ou <= 0), evitando divisão por zero.
    """
    if preco_arremate is None or lance_minimo_2 is None:
        return None
    if lance_minimo_2 <= 0:
        return None
    return preco_arremate / lance_minimo_2 - 1


def classificar_status(preco_arremate: float | None) -> str:
    """Classifica o lote como 'arrematado' (houve preço) ou 'deserto'."""
    if preco_arremate is None or preco_arremate <= 0:
        return "deserto"
    return "arrematado"


def determinar_veredito(
    n_sp: int,
    n_nao_sp: int,
    mediana_agio_sp: float | None,
    mediana_agio_nao_sp: float | None,
    taxa_deserto_sp: float,
    taxa_deserto_nao_sp: float,
) -> str:
    """Aplica o critério de avanço da Fase 1 e retorna o veredito.

    Retorna 'INSUFICIENTE' se algum grupo tiver menos de N_MINIMO_GRUPO leilões;
    'TESE VALIDADA' se o ágio do não-SP for >= 3pp menor OU a taxa de deserto do
    não-SP for >= 10pp maior; caso contrário 'TESE REFUTADA'.
    """
    if n_sp < N_MINIMO_GRUPO or n_nao_sp < N_MINIMO_GRUPO:
        return "INSUFICIENTE"

    agio_valida = (
        mediana_agio_sp is not None
        and mediana_agio_nao_sp is not None
        and (mediana_agio_sp - mediana_agio_nao_sp) >= LIMIAR_AGIO_PP
    )
    deserto_valida = (taxa_deserto_nao_sp - taxa_deserto_sp) >= LIMIAR_DESERTO_PP

    if agio_valida or deserto_valida:
        return "TESE VALIDADA"
    return "TESE REFUTADA"


@dataclass
class GrupoStats:
    """Estatísticas agregadas de um grupo de leilões (SP ou não-SP)."""

    nome: str
    total: int = 0
    desertos: int = 0
    arrematados: int = 0
    agios: list[float] = field(default_factory=list)

    @property
    def taxa_deserto(self) -> float:
        return self.desertos / self.total if self.total else 0.0

    @property
    def mediana_agio(self) -> float | None:
        return median(self.agios) if self.agios else None

    @property
    def media_agio(self) -> float | None:
        return mean(self.agios) if self.agios else None


@dataclass
class Analise:
    """Resultado completo da análise da Fase 1."""

    sp: GrupoStats
    nao_sp: GrupoStats
    indefinidos: int
    mann_whitney: tuple[float, float] | None  # (estatística U, p-valor)
    veredito: str


def _num(valor: object) -> float | None:
    """Converte um valor potencialmente ausente (NaN) em float ou None."""
    if valor is None or pd.isna(valor):
        return None
    # O CSV é lido como str; valores numéricos chegam como texto.
    return float(str(valor))


def carregar_dados(path: Path = INPUT_CSV) -> pd.DataFrame:
    """Lê o CSV de entrada da Fase 1."""
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo de entrada não encontrado: {path}. "
            "Preencha data/fase1_input.csv antes de rodar a validação."
        )
    df = pd.read_csv(path, dtype=str)
    log.info("dados_carregados", arquivo=str(path), linhas=len(df))
    return df


def teste_mann_whitney(
    agios_sp: list[float], agios_nao_sp: list[float]
) -> tuple[float, float] | None:
    """Roda Mann-Whitney U (bilateral) entre os ágios dos dois grupos.

    Retorna (estatística, p-valor) ou None quando não há amostra suficiente ou
    os valores são todos idênticos (caso em que o teste não é aplicável).
    """
    if not agios_sp or not agios_nao_sp:
        return None
    try:
        resultado = mannwhitneyu(agios_sp, agios_nao_sp, alternative="two-sided")
    except ValueError as exc:
        log.warning("mann_whitney_inaplicavel", motivo=str(exc))
        return None
    return float(resultado.statistic), float(resultado.pvalue)


def analisar(df: pd.DataFrame) -> Analise:
    """Classifica os leilões em SP/não-SP e calcula as estatísticas do veredito."""
    sp = GrupoStats("SP")
    nao_sp = GrupoStats("não-SP")
    indefinidos = 0

    for row in df.itertuples(index=False):
        matricula = getattr(row, "leiloeiro_matricula", None)
        uf = parse_uf_matricula(matricula)
        if uf is None:
            indefinidos += 1
            log.warning("uf_indefinida", matricula=matricula)
            continue

        grupo = sp if uf == "SP" else nao_sp
        preco = _num(getattr(row, "preco_arremate", None))
        lance2 = _num(getattr(row, "lance_minimo_2praca", None))

        grupo.total += 1
        if classificar_status(preco) == "deserto":
            grupo.desertos += 1
        else:
            grupo.arrematados += 1
            agio = calcular_agio(preco, lance2)
            if agio is not None:
                grupo.agios.append(agio)

    log.info(
        "grupos_analisados",
        sp_total=sp.total,
        nao_sp_total=nao_sp.total,
        indefinidos=indefinidos,
    )

    mw = teste_mann_whitney(sp.agios, nao_sp.agios)
    veredito = determinar_veredito(
        sp.total,
        nao_sp.total,
        sp.mediana_agio,
        nao_sp.mediana_agio,
        sp.taxa_deserto,
        nao_sp.taxa_deserto,
    )
    log.info("veredito_calculado", veredito=veredito)
    return Analise(
        sp=sp,
        nao_sp=nao_sp,
        indefinidos=indefinidos,
        mann_whitney=mw,
        veredito=veredito,
    )


def _fmt_pct(valor: float | None) -> str:
    """Formata uma fração como porcentagem (ex.: 0.3 -> '30,0%')."""
    if valor is None:
        return "—"
    return f"{valor * 100:.1f}%".replace(".", ",")


def gerar_markdown(analise: Analise) -> str:
    """Monta o relatório em Markdown da Fase 1."""
    agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S %Z")
    sp, ns = analise.sp, analise.nao_sp

    if analise.mann_whitney is None:
        mw_linha = "Não aplicável (amostra de ágios insuficiente em algum grupo)."
    else:
        u, p = analise.mann_whitney
        mw_linha = f"U = {u:.2f}, p-valor = {p:.4f}"

    diff_agio = (
        None
        if sp.mediana_agio is None or ns.mediana_agio is None
        else sp.mediana_agio - ns.mediana_agio
    )
    diff_deserto = ns.taxa_deserto - sp.taxa_deserto

    return f"""# Validação da Tese — Fase 1

Gerado em: {agora}

## Veredito: **{analise.veredito}**

Critério de avanço: tese validada se a mediana de ágio do grupo não-SP for ao menos
{LIMIAR_AGIO_PP * 100:.0f}pp menor que a do grupo SP, OU se a taxa de lotes desertos do
não-SP for ao menos {LIMIAR_DESERTO_PP * 100:.0f}pp maior. Mínimo de {N_MINIMO_GRUPO}
leilões por grupo (abaixo disso: INSUFICIENTE).

## Resumo por grupo

| Métrica | SP (JUCESP) | Não-SP |
|---|---|---|
| Total de leilões | {sp.total} | {ns.total} |
| Lotes arrematados | {sp.arrematados} | {ns.arrematados} |
| Lotes desertos | {sp.desertos} | {ns.desertos} |
| Taxa de deserto | {_fmt_pct(sp.taxa_deserto)} | {_fmt_pct(ns.taxa_deserto)} |
| Mediana de ágio | {_fmt_pct(sp.mediana_agio)} | {_fmt_pct(ns.mediana_agio)} |
| Média de ágio | {_fmt_pct(sp.media_agio)} | {_fmt_pct(ns.media_agio)} |

Leilões com UF indefinida (excluídos da análise): {analise.indefinidos}

## Diferenças observadas

- Diferença de mediana de ágio (SP − não-SP): {_fmt_pct(diff_agio)}
  (limiar para validar: {LIMIAR_AGIO_PP * 100:.0f}pp)
- Diferença de taxa de deserto (não-SP − SP): {_fmt_pct(diff_deserto)}
  (limiar para validar: {LIMIAR_DESERTO_PP * 100:.0f}pp)

## Teste estatístico

Mann-Whitney U (bilateral) sobre os ágios dos dois grupos: {mw_linha}

---

> Ágio = preço de arremate / lance mínimo da 2ª praça − 1. Lotes desertos são
> excluídos do cálculo de ágio, mas contam na taxa de deserto.
"""


def main() -> None:
    """Orquestra a validação da Fase 1: lê, analisa e grava o relatório."""
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            __import__("logging").getLevelName(settings.log_level)
        )
    )
    log.info("fase1_iniciada")
    df = carregar_dados()
    analise = analisar(df)
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_MD.write_text(gerar_markdown(analise), encoding="utf-8")
    log.info("relatorio_gravado", arquivo=str(OUTPUT_MD), veredito=analise.veredito)


if __name__ == "__main__":
    main()
