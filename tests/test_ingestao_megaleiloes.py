"""Testes do scraper do Mega Leilões e da resolução multi-matrícula."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from src.ingestao.agregadores.megaleiloes import MegaLeiloesScraper
from src.ingestao.base import canonical_url
from src.leiloeiros.resolver import LeiloeiroRef, LeiloeiroResolver

FIXTURES = Path(__file__).parent / "fixtures"


def test_extrair_urls_detalhe_da_listagem():
    html = (FIXTURES / "mega_imoveis_sp.html").read_text(encoding="utf-8")
    urls = MegaLeiloesScraper()._extrair_urls_detalhe(html)
    assert len(urls) == 48
    # URLs canônicas (sem utm) e apontando para imóveis.
    assert all("utm_" not in u for u in urls)
    assert all("/imoveis/" in u for u in urls)


def test_parse_detalhe_extrai_lote_e_leiloeiro():
    detalhe = (FIXTURES / "mega_detalhe_lote.html").read_text(encoding="utf-8")
    url = "https://www.megaleiloes.com.br/imoveis/apartamentos/sp/sao-vicente/x-j123913"
    lote = MegaLeiloesScraper()._parse_detalhe(detalhe, url)
    assert lote is not None
    assert lote.uf == "SP"
    assert lote.cidade == "São Vicente"
    assert lote.tipo == "judicial"
    assert lote.tipo_imovel == "apartamento"
    assert lote.numero_lote == "J123913"
    assert lote.avaliacao == Decimal("168781.97")
    assert lote.lance_minimo_1 == Decimal("168781.97")
    assert lote.lance_minimo_2 == Decimal("118147.37")
    assert lote.data_1praca == datetime(2026, 5, 28, 11, 0)
    assert lote.data_2praca == datetime(2026, 6, 17, 11, 0)
    assert lote.edital_url and lote.edital_url.endswith(".pdf")
    assert lote.leiloeiro_nome == "Fernando José Cerello G. Pereira"
    # O leiloeiro tem matrícula em SP e em MG — ambas capturadas.
    assert lote.leiloeiro_matriculas == ["JUCESP 844", "JUCEMG 1192"]


def test_canonical_url_remove_query_e_fragmento():
    assert canonical_url("https://x.com/a/b?utm_x=1#frag") == "https://x.com/a/b"


def test_resolver_multiplas_sp_prevalece():
    """Leiloeiro com matrícula SP + MG opera como SP (não é alvo da tese)."""
    r = LeiloeiroResolver().resolver_multiplas(
        nome="Fernando José Cerello G. Pereira",
        matriculas=["JUCESP 844", "JUCEMG 1192"],
    )
    assert r.uf == "SP"
    assert r.fora_sp is False


def test_resolver_multiplas_so_nao_sp():
    """Sem nenhuma matrícula SP, resolve para a UF não-SP."""
    r = LeiloeiroResolver().resolver_multiplas(nome="Fulano", matriculas=["JUCEMG 1192"])
    assert r.uf == "MG"
    assert r.fora_sp is True


def test_resolver_multiplas_prefere_alta_confianca():
    """Com cadastro, casar por matrícula eleva a confiança para 'alta'."""
    cadastro = [LeiloeiroRef(nome="Ana", matricula="JUCEMG 1192", uf_matricula="MG")]
    r = LeiloeiroResolver(cadastro).resolver_multiplas(
        nome="Ana", matriculas=["JUCEMG 1192", "JUCEPAR 5"]
    )
    assert r.uf == "MG"
    assert r.confianca == "alta"
