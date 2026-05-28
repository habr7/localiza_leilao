"""Testes da interface dos scrapers de Junta Comercial."""

import pytest

from src.leiloeiros.juntas import JUNTAS_DISPONIVEIS, JucerjaScraper, JucespScraper
from src.leiloeiros.matricula import JUNTA_TO_UF


def test_registro_de_juntas():
    assert JUNTAS_DISPONIVEIS["JUCESP"].uf == "SP"
    assert JUNTAS_DISPONIVEIS["JUCERJA"].uf == "RJ"
    assert JUNTAS_DISPONIVEIS["JUCEMG"].uf == "MG"


def test_juntas_nao_sp_cadastradas():
    """As 7 Juntas não-SP de maior prioridade estão registradas com a UF correta."""
    esperado = {
        "JUCERJA": "RJ",
        "JUCEMG": "MG",
        "JUCEPAR": "PR",
        "JUCERGS": "RS",
        "JUCESC": "SC",
        "JUCEDF": "DF",
        "JUCEG": "GO",
    }
    for junta, uf in esperado.items():
        assert junta in JUNTAS_DISPONIVEIS, f"{junta} não registrada"
        assert JUNTAS_DISPONIVEIS[junta].uf == uf
        # A sigla precisa ser reconhecida pelo resolvedor (mapa Junta -> UF).
        assert JUNTA_TO_UF.get(junta) == uf


def test_juntas_sp_apenas_jucesp():
    """Só a JUCESP é de SP; todas as demais são alvos não-SP da tese."""
    de_sp = [j for j, s in JUNTAS_DISPONIVEIS.items() if s.uf == "SP"]
    assert de_sp == ["JUCESP"]


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
