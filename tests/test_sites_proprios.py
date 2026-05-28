"""Testes do scraper da plataforma Suporte Leilões (sites próprios, Fase 3.2)."""

from decimal import Decimal
from pathlib import Path

from src.ingestao.sites_proprios.suporte_leiloes import (
    SuporteLeiloesScraper,
    _cidade_uf,
    _tipo_imovel,
    _tipo_leilao,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_cards_extrai_lotes_sp():
    html = (FIXTURES / "suporte_leiloes_busca_sp.html").read_text(encoding="utf-8")
    lotes = SuporteLeiloesScraper()._parse_cards(html, "https://www.liderleiloes.com.br")
    assert len(lotes) == 12
    # Todos os lotes são imóveis em SP (filtro duro).
    assert all(lote.uf == "SP" for lote in lotes)
    assert all(lote.fonte_tipo == "site_proprio" for lote in lotes)
    assert all(lote.fonte_origem == "site_proprio:www.liderleiloes.com.br" for lote in lotes)
    primeiro = lotes[0]
    assert primeiro.cidade == "São Paulo"
    assert primeiro.numero_lote == "1"
    assert primeiro.lance_minimo_1 == Decimal("1050000.00")
    assert "/lote/" in primeiro.fonte_url and "utm_" not in primeiro.fonte_url
    # Título limpo (sem o rodapé de preço/status concatenado).
    assert primeiro.titulo and "Lance Inicial" not in primeiro.titulo


def test_parse_cards_layout_antigo_lote_item():
    # e-confianca usa o tema antigo (.lote-item) da mesma plataforma.
    html = (FIXTURES / "suporte_leiloes_econf_sp.html").read_text(encoding="utf-8")
    lotes = SuporteLeiloesScraper()._parse_cards(html, "https://www.e-confianca.com.br")
    assert len(lotes) == 12
    assert all(lote.uf == "SP" for lote in lotes)
    assert all(lote.fonte_origem == "site_proprio:www.e-confianca.com.br" for lote in lotes)
    primeiro = lotes[0]
    assert primeiro.cidade == "Ribeirão Preto"
    assert primeiro.numero_lote == "1"
    assert primeiro.lance_minimo_1 == Decimal("314557.90")


def test_cidade_uf_pega_ultima_ocorrencia():
    assert _cidade_uf("Imóvel em Vila Zelina, São Paulo/SP São Paulo - SP") == ("São Paulo", "SP")
    assert _cidade_uf("sem localidade") == (None, None)


def test_tipo_imovel_especifico_antes_de_terreno():
    # "em terreno de" não deve classificar um prédio como terreno.
    assert _tipo_imovel("Prédio industrial em terreno de 300 m²") == "predio"
    assert _tipo_imovel("Apartamento 45 m²") == "apartamento"
    assert _tipo_imovel("Lote de terreno 200 m²") == "terreno"


def test_tipo_leilao_pelo_slug():
    assert _tipo_leilao("/eventos/leilao/123-leilao-judicial-x/lote/1/y") == "judicial"
    assert _tipo_leilao("/eventos/leilao/123-leilao-extrajudicial/lote/1/y") == "extrajudicial"
