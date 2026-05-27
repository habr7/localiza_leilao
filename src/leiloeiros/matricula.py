"""Parsing de matrícula de leiloeiro e mapeamento Junta Comercial -> UF.

Módulo canônico reutilizado pelo resolvedor (Fase 2) e pelo script da Fase 1.
A UF do leiloeiro é o gatilho central da tese (não-SP), então a derivação a
partir da matrícula vive em um único lugar, testável isoladamente.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# UFs brasileiras (siglas de 2 letras).
UFS = {
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
_PREFIXO_TO_UF: dict[str, str] = {**JUNTA_TO_UF, **{uf: uf for uf in UFS}}


@dataclass(frozen=True)
class Matricula:
    """Matrícula de leiloeiro decomposta."""

    raw: str
    junta: str | None  # sigla detectada, ex.: "JUCERJA" (None se desconhecida)
    uf: str | None  # UF derivada, ex.: "RJ" (None se não reconhecida)
    numero: str | None  # número da matrícula, ex.: "123"


def parse_matricula(matricula: str | None) -> Matricula:
    """Decompõe uma matrícula em (junta, uf, número).

    Aceita variações com espaço, hífen e maiúsculas/minúsculas, por exemplo:
    "JUCERJA 123", "jucerja-123", "JUCERJA123", "  Jucesp 456  ", "SP 99".
    """
    raw = matricula or ""
    texto = raw.strip()
    if not texto:
        return Matricula(raw=raw, junta=None, uf=None, numero=None)

    prefixo_match = re.match(r"[A-Za-z]+", texto)
    prefixo = prefixo_match.group(0).upper() if prefixo_match else None
    numero_match = re.search(r"\d+", texto)
    numero = numero_match.group(0) if numero_match else None

    uf = _PREFIXO_TO_UF.get(prefixo) if prefixo else None
    # Só consideramos "junta" quando o prefixo é de fato uma sigla de Junta
    # (e não apenas a UF informada solta).
    junta = prefixo if prefixo in JUNTA_TO_UF else None
    return Matricula(raw=raw, junta=junta, uf=uf, numero=numero)


def parse_uf_matricula(matricula: str | None) -> str | None:
    """Atalho: retorna apenas a UF derivada da matrícula (ou None)."""
    return parse_matricula(matricula).uf
