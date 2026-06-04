"""Cross-check de JUCESP por nome — completa o filtro da tese.

Um leiloeiro de fora (PR/MT/GO/…) pode ter **também** matrícula na JUCESP. Quando
isso acontece, ele pode atuar livremente em SP e **não** é alvo da tese. A relação
oficial da JUCESP (carregada por `jucesp.py`) dá os nomes; aqui comparamos os
nomes normalizados dos leiloeiros não-SP contra os da JUCESP.

É um sinal complementar à leitura do site (`verificacao.py`): pega quem o site não
declara, mas que consta na lista oficial da JUCESP.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.models import Leiloeiro
from src.leiloeiros.resolver import normalizar_nome


def carregar_nomes_jucesp(session: Session) -> set[str]:
    """Nomes normalizados dos leiloeiros matriculados na JUCESP."""
    nomes = session.scalars(select(Leiloeiro.nome).where(Leiloeiro.junta_comercial == "JUCESP"))
    return {normalizar_nome(n) for n in nomes if n}


@dataclass(frozen=True)
class CruzamentoJucesp:
    """Um leiloeiro não-SP que também consta na JUCESP (logo, não é alvo)."""

    nome: str
    uf_matricula: str
    junta_comercial: str
    site_oficial: str | None


def leiloeiros_nao_sp_com_jucesp(session: Session) -> list[CruzamentoJucesp]:
    """Leiloeiros não-SP cujo nome também aparece na lista da JUCESP.

    Estes têm matrícula JUCESP (mesma pessoa) → devem ser excluídos da tese,
    mesmo que estejam numa Junta de fora.
    """
    nomes_sp = carregar_nomes_jucesp(session)
    resultado: list[CruzamentoJucesp] = []
    nao_sp = session.scalars(
        select(Leiloeiro).where(Leiloeiro.uf_matricula != "SP", Leiloeiro.ativo.is_(True))
    )
    for leil in nao_sp:
        if normalizar_nome(leil.nome) in nomes_sp:
            resultado.append(
                CruzamentoJucesp(
                    nome=leil.nome,
                    uf_matricula=leil.uf_matricula,
                    junta_comercial=leil.junta_comercial,
                    site_oficial=leil.site_oficial,
                )
            )
    return resultado
