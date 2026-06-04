"""Testes do scraper da JUCESP (PDF) e do cross-check por nome."""

from src.leiloeiros.juntas.jucesp import parse_pdf_text
from src.leiloeiros.resolver import normalizar_nome


def test_parse_pdf_text_extrai_linhas():
    texto = (
        "terça-feira, 28 de março de 2023 Diário Oficial\n"
        "960 PHILLIPE SANTOS INIGUEZ OMELLA 03/11/2015 Atuante\n"
        "986 MARCELO BRIDI 24/11/2015 Atuante\n"
        "1361 BRUNO HENRIQUE LOPES 10/01/2020 Atuante\n"
    )
    regs = parse_pdf_text(texto)
    assert len(regs) == 3
    for r in regs:
        assert r.uf_matricula == "SP"
        assert r.junta_comercial == "JUCESP"
        assert r.matricula.isdigit()
    assert any("BRUNO HENRIQUE LOPES" in r.nome for r in regs)


def test_cross_check_nome_normalizado_casa():
    # O mesmo leiloeiro, grafias diferentes, deve casar após normalização.
    jucesp = {normalizar_nome("BRUNO HENRIQUE LOPES")}
    assert normalizar_nome("Bruno Henrique Lopes") in jucesp
    assert normalizar_nome("CAROLINE DE SOUSA RIBAS") not in jucesp
