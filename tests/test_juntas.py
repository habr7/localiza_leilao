"""Testes da interface dos scrapers de Junta Comercial."""

import pytest

from src.leiloeiros.juntas import JUNTAS_DISPONIVEIS, JucerjaScraper, JucespScraper


def test_registro_de_juntas():
    assert JUNTAS_DISPONIVEIS["JUCESP"].uf == "SP"
    assert JUNTAS_DISPONIVEIS["JUCERJA"].uf == "RJ"
    assert JUNTAS_DISPONIVEIS["JUCEMG"].uf == "MG"


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
