"""Testes dos parsers dedicados de sites próprios (fixtures HTML reais)."""

from pathlib import Path

from src.ingestao.sites_proprios.leiloariasmart import parse_lotes as parse_smart
from src.ingestao.sites_proprios.webleiloes import parse_lotes as parse_web

FIX = Path(__file__).parent / "fixtures"


def test_webleiloes_extrai_lotes_estruturados():
    lotes = parse_web((FIX / "webleiloes_busca.html").read_text(encoding="utf-8"))
    assert lotes
    for lo in lotes:
        assert lo.fonte_origem == "webleiloes"
        assert lo.fonte_tipo == "site_proprio"
        assert lo.fonte_url.startswith("https://www.webleiloes.com.br/oferta/")
        assert lo.uf  # UF extraída do slug
        assert lo.tipo_imovel
    # Pelo menos um em SP com cidade e lance.
    sp = [lo for lo in lotes if lo.uf == "SP"]
    assert sp
    assert any(lo.cidade and lo.lance_minimo_1 for lo in sp)
    # bairro nunca deve conter a barra de UF (guard de limpeza).
    assert all("/" not in (lo.bairro or "") for lo in lotes)


def test_leiloariasmart_extrai_lotes_e_cidade_limpa():
    lotes = parse_smart((FIX / "leiloariasmart_home.html").read_text(encoding="utf-8"))
    assert lotes
    for lo in lotes:
        assert lo.fonte_origem == "leiloariasmart"
        assert lo.fonte_url.startswith("https://www.leiloariasmart.com.br/imovel/")
        assert lo.uf and lo.cidade
        # Cidade começa em maiúscula e não traz unidades de medida (m², ha).
        assert lo.cidade[0].isupper()
        assert "m²" not in lo.cidade and " ha" not in lo.cidade
