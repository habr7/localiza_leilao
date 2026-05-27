"""Testes do cadastro de leiloeiros (upsert idempotente e import CSV)."""

from src.leiloeiros.cadastro import (
    LeiloeiroRaw,
    carregar_cadastro,
    importar_csv,
    upsert_leiloeiros,
)


def test_importar_csv(tmp_path):
    csv_path = tmp_path / "leiloeiros.csv"
    csv_path.write_text(
        "nome,matricula,plataformas,aliases\n"
        "Ana Souza,JUCERJA 123,megaleiloes.com.br;leilaovip.com.br,Ana S.\n",
        encoding="utf-8",
    )
    registros = importar_csv(csv_path)
    assert len(registros) == 1
    assert registros[0].nome == "Ana Souza"
    assert registros[0].plataformas == ["megaleiloes.com.br", "leilaovip.com.br"]
    assert registros[0].aliases == ["Ana S."]


def test_upsert_idempotente(db_session):
    """Rodar o upsert duas vezes não duplica e conta atualizações."""
    registros = [
        LeiloeiroRaw(nome="Ana Souza", matricula="JUCERJA 123", fonte_cadastro="teste"),
        LeiloeiroRaw(nome="Bruno Lima", matricula="JUCEMG 50", fonte_cadastro="teste"),
    ]
    s1 = upsert_leiloeiros(db_session, registros)
    assert s1.inseridos == 2
    assert s1.atualizados == 0

    s2 = upsert_leiloeiros(db_session, registros)
    assert s2.inseridos == 0
    assert s2.atualizados == 2

    cadastro = carregar_cadastro(db_session)
    matriculas = {r.matricula for r in cadastro}
    assert "JUCERJA 123" in matriculas
    assert "JUCEMG 50" in matriculas


def test_upsert_deriva_uf_da_matricula(db_session):
    """A UF é derivada da matrícula quando não informada explicitamente."""
    upsert_leiloeiros(db_session, [LeiloeiroRaw(nome="Carla Dias", matricula="JUCEPAR 9")])
    cadastro = carregar_cadastro(db_session)
    carla = next(r for r in cadastro if r.matricula == "JUCEPAR 9")
    assert carla.uf_matricula == "PR"


def test_upsert_ignora_uf_indeterminavel(db_session):
    """Matrícula sem UF reconhecível é ignorada (não polui o cadastro)."""
    stats = upsert_leiloeiros(db_session, [LeiloeiroRaw(nome="Sem UF", matricula="XPTO 1")])
    assert stats.ignorados == 1
    assert stats.total == 0
