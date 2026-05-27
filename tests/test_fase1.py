"""Testes unitários do script de validação da tese (Fase 1)."""

import pytest

from src.scripts.fase1_validar_tese import (
    calcular_agio,
    determinar_veredito,
    parse_uf_matricula,
)


def test_calcular_agio():
    """Ágio = preco_arremate / lance_minimo_2 - 1."""
    assert calcular_agio(130000, 100000) == pytest.approx(0.30)
    assert calcular_agio(100000, 100000) == pytest.approx(0.0)
    # Sem arremate (deserto) ou lance mínimo inválido -> None.
    assert calcular_agio(None, 100000) is None
    assert calcular_agio(130000, 0) is None
    assert calcular_agio(130000, None) is None


@pytest.mark.parametrize(
    "matricula,uf_esperada",
    [
        ("JUCERJA 123", "RJ"),
        ("jucerja-123", "RJ"),
        ("JUCERJA123", "RJ"),
        ("  Jucesp 456  ", "SP"),
        ("JUCEMG-77", "MG"),
        ("jucepar 9", "PR"),
        ("SP 456", "SP"),  # UF informada diretamente
        ("XPTO 1", None),  # prefixo desconhecido
        ("", None),
        (None, None),
    ],
)
def test_parse_uf_matricula(matricula, uf_esperada):
    """A UF deve sair correta mesmo com espaço, hífen e caixa variada."""
    assert parse_uf_matricula(matricula) == uf_esperada


def test_veredito_insuficiente():
    """Com menos de 30 leilões em algum grupo, o veredito é INSUFICIENTE."""
    veredito = determinar_veredito(
        n_sp=10,
        n_nao_sp=50,
        mediana_agio_sp=0.30,
        mediana_agio_nao_sp=0.10,
        taxa_deserto_sp=0.05,
        taxa_deserto_nao_sp=0.40,
    )
    assert veredito == "INSUFICIENTE"


def test_veredito_validada_por_agio():
    """Com n suficiente e ágio do não-SP >= 3pp menor, a tese é validada."""
    veredito = determinar_veredito(
        n_sp=40,
        n_nao_sp=40,
        mediana_agio_sp=0.20,
        mediana_agio_nao_sp=0.15,  # 5pp menor
        taxa_deserto_sp=0.10,
        taxa_deserto_nao_sp=0.12,  # só 2pp, não basta sozinho
    )
    assert veredito == "TESE VALIDADA"


def test_veredito_refutada():
    """Com n suficiente mas sem diferença relevante, a tese é refutada."""
    veredito = determinar_veredito(
        n_sp=40,
        n_nao_sp=40,
        mediana_agio_sp=0.20,
        mediana_agio_nao_sp=0.19,  # só 1pp
        taxa_deserto_sp=0.10,
        taxa_deserto_nao_sp=0.13,  # só 3pp
    )
    assert veredito == "TESE REFUTADA"
