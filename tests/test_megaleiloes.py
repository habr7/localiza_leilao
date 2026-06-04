"""Testes de parsing do agregador Mega Leilões (fixtures HTML reais recortadas)."""

from pathlib import Path

from src.ingestao.agregadores.megaleiloes import (
    _parse_dinheiro,
    parse_detalhe,
    parse_listagem,
)
from src.leiloeiros.resolver import uf_efetiva_de_matriculas

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_dinheiro():
    assert _parse_dinheiro("R$ 108.900,00") == 108900.0
    assert _parse_dinheiro("Lance R$ 1.234.567,89") == 1234567.89
    assert _parse_dinheiro("sob consulta") is None
    assert _parse_dinheiro(None) is None


def test_parse_listagem_extrai_cards():
    html = (FIXTURES / "megaleiloes_listagem_sp.html").read_text(encoding="utf-8")
    lotes = parse_listagem(html)
    assert lotes, "deveria extrair ao menos um lote"
    for lote in lotes:
        assert lote.fonte_origem == "megaleiloes"
        assert lote.fonte_tipo == "agregador"
        assert "/imoveis/" in lote.fonte_url  # só imóveis, não veículos
        assert lote.titulo
    # Pelo menos um lote com cidade/UF resolvidas a partir do link de localidade.
    assert any(lote.uf for lote in lotes)


def test_parse_detalhe_leiloeiro_e_tipo():
    html = (FIXTURES / "megaleiloes_detalhe.html").read_text(encoding="utf-8")
    det = parse_detalhe(html)
    assert det["tipo_leilao"] in {"judicial", "extrajudicial"}
    assert det["leiloeiro_nome"]
    # O leiloeiro da fixture exibe duas matrículas (JUCESP + JUCEMG).
    assert len(det["leiloeiro_matriculas"]) >= 2
    assert any("JUCESP" in m for m in det["leiloeiro_matriculas"])


def test_uf_efetiva_jucesp_vence():
    """Leiloeiro com JUCESP é tratado como SP mesmo exibindo matrícula de fora."""
    matriculas = [
        "JUCESP Nº 844 - Leiloeiro Oficial no Estado de São Paulo",
        "JUCEMG Nº 1192 - Leiloeiro Oficial no Estado de Minas Gerais",
    ]
    assert uf_efetiva_de_matriculas(matriculas) == "SP"


def test_uf_efetiva_somente_fora():
    assert uf_efetiva_de_matriculas(["JUCEMG Nº 1192"]) == "MG"
    assert uf_efetiva_de_matriculas(["JUCERJA 321", "JUCEMG 9"]) in {"RJ", "MG"}


def test_uf_efetiva_nada_reconhecido():
    assert uf_efetiva_de_matriculas([None, "texto sem matrícula"]) is None


def test_detalhe_fixture_resolve_para_sp():
    """Integração: a fixture real (JUCESP+JUCEMG) deve resolver para SP (excluído)."""
    html = (FIXTURES / "megaleiloes_detalhe.html").read_text(encoding="utf-8")
    det = parse_detalhe(html)
    assert uf_efetiva_de_matriculas(det["leiloeiro_matriculas"]) == "SP"


def test_franquia_ms_reusa_plataforma():
    """A franquia Mega Leilões MS reusa a plataforma com base_url própria."""
    from src.ingestao.agregadores.megaleiloes import MegaLeiloesMsScraper

    assert MegaLeiloesMsScraper.fonte_origem == "megaleiloesms"
    assert MegaLeiloesMsScraper.fonte_tipo == "site_proprio"
    assert "megaleiloesms" in MegaLeiloesMsScraper.base_url


def test_parse_listagem_fonte_parametrizada():
    from pathlib import Path

    from src.ingestao.agregadores.megaleiloes import parse_listagem

    html = (Path(__file__).parent / "fixtures" / "megaleiloes_listagem_sp.html").read_text(
        encoding="utf-8"
    )
    lotes = parse_listagem(html, "megaleiloesms", "site_proprio")
    assert lotes and all(lo.fonte_origem == "megaleiloesms" for lo in lotes)
