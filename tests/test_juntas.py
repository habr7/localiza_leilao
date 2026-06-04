"""Testes da interface dos scrapers de Junta Comercial."""

import pytest

from src.leiloeiros.juntas import JUNTAS_DISPONIVEIS, JucerjaScraper
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
        "JUCISRS": "RS",
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
    from src.leiloeiros.cadastro import LeiloeiroRaw
    from src.leiloeiros.juntas.base import JuntaScraper

    class _SemLista(JuntaScraper):
        junta = "XX"
        uf = "XX"
        url_lista = None

        def _parse(self, html: str) -> list[LeiloeiroRaw]:
            return []

    with pytest.raises(NotImplementedError):
        await _SemLista().coletar()


def test_jucepar_parse_extrai_nome_matricula_site():
    """JUCEPAR: acordeão com nome, matrícula e site oficial."""
    from pathlib import Path

    from src.leiloeiros.juntas import JuceparScraper

    html = (Path(__file__).parent / "fixtures" / "jucepar_lista.html").read_text(encoding="utf-8")
    registros = JuceparScraper()._parse(html)
    assert registros, "deveria extrair leiloeiros"
    for r in registros:
        assert r.nome and r.matricula
        assert r.uf_matricula == "PR"
        assert r.junta_comercial == "JUCEPAR"
    # Ao menos um com site oficial detectado (o elo da Fase 3).
    assert any(r.site_oficial and r.site_oficial.startswith("http") for r in registros)


def test_juceg_parse_extrai_nome_matricula_site():
    """JUCEG: texto corrido com cabeçalho de matrícula e site no bloco."""
    from pathlib import Path

    from src.leiloeiros.juntas import JucegScraper

    html = (Path(__file__).parent / "fixtures" / "juceg_lista.html").read_text(encoding="utf-8")
    registros = JucegScraper()._parse(html)
    assert registros, "deveria extrair leiloeiros"
    primeiro = registros[0]
    assert primeiro.uf_matricula == "GO"
    assert "/" in primeiro.matricula  # ex.: "008/95" (sem o " de DATA")
    assert " de " not in primeiro.matricula
    assert any(r.site_oficial for r in registros)


def _fix(nome):
    from pathlib import Path

    return (Path(__file__).parent / "fixtures" / nome).read_text(encoding="utf-8")


def test_jucemat_parse_cards():
    """JUCEMAT: cartões .featured-box com nome (h2), matrícula (label) e site."""
    from src.leiloeiros.juntas import JucematScraper

    registros = JucematScraper()._parse(_fix("jucemat_lista.html"))
    assert registros
    for r in registros:
        assert r.uf_matricula == "MT" and r.junta_comercial == "JUCEMAT"
        assert r.nome and r.matricula
    assert any(r.site_oficial and r.site_oficial.startswith("http") for r in registros)


def test_jucepb_parse_rotulada():
    """JUCEPB: lista rotulada (Matrícula:/Site:)."""
    from src.leiloeiros.juntas import JucepbScraper

    registros = JucepbScraper()._parse(_fix("jucepb_lista.html"))
    assert registros
    assert registros[0].uf_matricula == "PB"
    assert any(r.site_oficial for r in registros)


def test_jucepi_parse_rotulada():
    """JUCEPI: lista rotulada com matrícula 'n.º 11/2006, em ...' normalizada."""
    from src.leiloeiros.juntas import JucepiScraper

    registros = JucepiScraper()._parse(_fix("jucepi_lista.html"))
    assert registros
    r = registros[0]
    assert r.uf_matricula == "PI"
    assert "n.º" not in r.matricula and "," not in r.matricula
    assert any(x.site_oficial for x in registros)


def test_parse_tabela_com_site_e_matricula_numero():
    from src.leiloeiros.juntas._util import parse_tabela

    html = """<table>
      <tr><th>Mat</th><th>Nome</th><th>Contato</th></tr>
      <tr><td>Matrícula - 01 22/08/1984</td><td>Fernando Castelo</td>
          <td>Site: www.montenegroleiloes.com.br E-MAIL: x@y.com</td></tr>
    </table>"""
    regs = parse_tabela(
        html, "CE", "JUCEC", "junta:jucec", 1, 0, idx_site=2, matricula_so_numero=True
    )
    assert len(regs) == 1
    assert regs[0].nome == "Fernando Castelo"
    assert regs[0].matricula == "01"
    assert regs[0].site_oficial == "https://www.montenegroleiloes.com.br"


def test_parse_tabela_ordem_antiguidade():
    from src.leiloeiros.juntas._util import parse_tabela

    html = "<table><tr><td>1 - Ângela Bechara</td><td>77</td></tr></table>"
    regs = parse_tabela(html, "MG", "JUCEMG", "junta:jucemg", 0, 1)
    assert regs[0].nome == "Ângela Bechara" and regs[0].matricula == "77"


def test_parse_blocos_rotulados_df():
    from src.leiloeiros.juntas._util import parse_blocos_rotulados

    html = (
        "<p><strong>DENISE ARAÚJO DOS SANTOS</strong><br>Matrícula: 117<br>"
        "Site: dearaujoleiloes.com.br<br>Situação Funcional: Regular</p>"
    )
    regs = parse_blocos_rotulados(html, "DF", "JUCEDF", "junta:jucedf", "p")
    assert regs[0].nome == "DENISE ARAÚJO DOS SANTOS"
    assert regs[0].matricula == "117"
    assert regs[0].site_oficial == "https://dearaujoleiloes.com.br"


def test_cobertura_minima_de_juntas():
    """O registro cobre SP (exclusão) + >=16 UFs não-SP com parser ao vivo."""
    ufs_nao_sp = {s.uf for s in JUNTAS_DISPONIVEIS.values() if s.uf != "SP"}
    assert "SP" in {s.uf for s in JUNTAS_DISPONIVEIS.values()}
    assert len(ufs_nao_sp) >= 16
