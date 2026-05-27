"""Testes do resolvedor de leiloeiro (Fase 2)."""

from src.leiloeiros.matricula import parse_matricula
from src.leiloeiros.resolver import LeiloeiroRef, LeiloeiroResolver, normalizar_nome


def test_parse_matricula_decompoe():
    m = parse_matricula("JUCERJA 123")
    assert (m.junta, m.uf, m.numero) == ("JUCERJA", "RJ", "123")
    m2 = parse_matricula("jucesp-456")
    assert (m2.junta, m2.uf, m2.numero) == ("JUCESP", "SP", "456")
    # UF solta como prefixo: vira uf, mas não é "junta".
    m3 = parse_matricula("RS 9")
    assert (m3.junta, m3.uf, m3.numero) == (None, "RS", "9")


def test_normalizar_nome_remove_ruido_e_acento():
    assert normalizar_nome("Leiloeira Oficial Ana Lúcia") == "ana lucia"


def test_resolve_uf_pela_matricula_sem_cadastro():
    """Mesmo sem cadastro, a matrícula já entrega a UF (confiança média)."""
    r = LeiloeiroResolver().resolver(nome="Fulano", matricula="JUCEMG 77")
    assert r.uf == "MG"
    assert r.fora_sp is True
    assert r.confianca == "media"


def test_resolve_alta_confianca_com_cadastro():
    cadastro = [LeiloeiroRef(nome="Ana Lúcia Souza", matricula="JUCERJA 123", uf_matricula="RJ")]
    r = LeiloeiroResolver(cadastro).resolver(nome="Ana Lucia Souza", matricula="JUCERJA 123")
    assert r.uf == "RJ"
    assert r.fora_sp is True
    assert r.confianca == "alta"
    assert r.leiloeiro is not None


def test_armadilha_zukerman_nome_rj_mas_matricula_sp():
    """Nome 'associado ao RJ' mas matrícula JUCESP -> é de SP (não é alvo)."""
    cadastro = [LeiloeiroRef(nome="Fabio Zukerman", matricula="JUCESP 719", uf_matricula="SP")]
    r = LeiloeiroResolver(cadastro).resolver(nome="Zukerman", matricula="JUCESP 719")
    assert r.uf == "SP"
    assert r.fora_sp is False


def test_resolve_por_nome_quando_sem_matricula():
    cadastro = [LeiloeiroRef(nome="Carlos Eduardo Lima", matricula="JUCEPAR 50", uf_matricula="PR")]
    r = LeiloeiroResolver(cadastro).resolver(nome="Carlos Eduardo Lima", matricula=None)
    assert r.uf == "PR"
    assert r.fora_sp is True
    assert r.confianca == "media"
    assert r.motivo == "uf_do_cadastro_por_nome"


def test_nao_resolvido_fica_baixa_confianca():
    r = LeiloeiroResolver().resolver(nome="Desconhecido", matricula="XPTO 1")
    assert r.uf is None
    assert r.fora_sp is None
    assert r.confianca == "baixa"
