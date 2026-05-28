"""Testes da interface dos scrapers de Junta Comercial."""

from pathlib import Path

import pytest

from src.leiloeiros.juntas import (
    JUNTAS_DISPONIVEIS,
    JucebScraper,
    JucegScraper,
    JucemgScraper,
    JucerjaScraper,
    JucespScraper,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_registro_de_juntas():
    assert JUNTAS_DISPONIVEIS["JUCESP"].uf == "SP"
    assert JUNTAS_DISPONIVEIS["JUCERJA"].uf == "RJ"
    assert JUNTAS_DISPONIVEIS["JUCEMG"].uf == "MG"
    assert JUNTAS_DISPONIVEIS["JUCEG"].uf == "GO"
    assert JUNTAS_DISPONIVEIS["JUCEB"].uf == "BA"


def test_fonte_cadastro_derivada():
    assert JucerjaScraper().fonte_cadastro == "junta:jucerja"


def test_coletar_csv_aplica_defaults_da_junta(tmp_path):
    csv_path = tmp_path / "lai_jucerja.csv"
    csv_path.write_text("nome,matricula\nAna Souza,123\n", encoding="utf-8")
    registros = JucerjaScraper().coletar_csv(str(csv_path))
    assert registros[0].uf_matricula == "RJ"
    assert registros[0].junta_comercial == "JUCERJA"
    assert registros[0].fonte_cadastro == "lai:jucerja"


async def test_coletar_sem_url_lista_avisa_pendencia():
    """Sem URL de lista pública configurada, coletar sinaliza a pendência."""
    with pytest.raises(NotImplementedError):
        await JucespScraper().coletar()


def test_parse_jucemg_extrai_leiloeiros():
    html = (FIXTURES / "jucemg_leiloeiros.html").read_text(encoding="utf-8")
    registros = JucemgScraper()._parse(html)
    # A relação alfabética da JUCEMG tem mais de 200 leiloeiros.
    assert len(registros) > 200
    por_nome = {r.nome: r for r in registros}
    adriana = por_nome["Adriana Pires Amancio"]
    assert adriana.matricula == "JUCEMG 1062"
    assert adriana.uf_matricula == "MG"
    assert adriana.junta_comercial == "JUCEMG"
    assert adriana.site_oficial == "http://www.apaleiloes.com.br"
    assert adriana.fonte_cadastro == "junta:jucemg"
    # Anotação "(MATRÍCULA SUPLEMENTAR)" é removida do nome.
    assert "Alex Willian Hoppe" in por_nome
    assert all("SUPLEMENTAR" not in r.nome.upper() for r in registros)


def test_parse_jucerja_extrai_leiloeiros_da_pagina():
    html = (FIXTURES / "jucerja_leiloeiros.html").read_text(encoding="utf-8")
    registros = JucerjaScraper()._parse(html)
    # O servidor entrega a 1ª página (5 leiloeiros); o resto vem por AJAX/LAI.
    assert len(registros) == 5
    por_nome = {r.nome: r for r in registros}
    murilo = por_nome["MURILO CARDOZO CHAVES"]
    assert murilo.matricula == "JUCERJA 8"
    assert murilo.uf_matricula == "RJ"
    assert murilo.site_oficial is None  # "Não cadastrado" vira ausência
    luiz = por_nome["LUIZ TENÓRIO DE PAULA"]
    assert luiz.matricula == "JUCERJA 19"
    assert luiz.site_oficial == "www.depaulaonline.com.br"


def test_parse_juceg_extrai_leiloeiros():
    html = (FIXTURES / "juceg_leiloeiros.html").read_text(encoding="utf-8")
    registros = JucegScraper()._parse(html)
    assert len(registros) > 50
    por_nome = {r.nome: r for r in registros}
    joao = por_nome["JOÃO ALVES BARROS"]
    assert joao.matricula == "JUCEG 007/90"
    assert joao.uf_matricula == "GO"
    assert joao.junta_comercial == "JUCEG"
    # Muitos leiloeiros de GO têm site próprio (alvo do scraper da Fase 3.2).
    assert sum(1 for r in registros if r.site_oficial) > 20


def test_parse_juceb_extrai_leiloeiros():
    html = (FIXTURES / "juceb_leiloeiros.html").read_text(encoding="utf-8")
    registros = JucebScraper()._parse(html)
    assert len(registros) > 50
    por_nome = {r.nome: r for r in registros}
    paulo = por_nome["Paulo Cézar Rocha Teixeira"]
    assert paulo.matricula == "JUCEB 004627/00"
    assert paulo.uf_matricula == "BA"
    assert paulo.site_oficial == "http://www.leiloesjudiciaisbahia.com.br"
    assert sum(1 for r in registros if r.site_oficial) > 20
