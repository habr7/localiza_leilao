"""Resolvedor de leiloeiro: de (nome, matrícula) crus para UF e cadastro.

Coração do matching da tese. Dado o que um portal exibe sobre o leiloeiro
(um nome e/ou uma string de matrícula), descobre a UF e, quando possível, o
registro correspondente no cadastro da Fase 2.

Princípio de segurança: a UF vem **sempre** da matrícula resolvida ou do
cadastro — nunca da "marca" do site. É assim que evitamos a armadilha de
leiloeiros associados a outro estado mas matriculados na JUCESP (ex.: Zukerman).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from src.leiloeiros.matricula import parse_matricula

# Limiar de similaridade para casar nomes (0..1).
LIMIAR_NOME = 0.87


def uf_efetiva_de_matriculas(matriculas: list[str | None]) -> str | None:
    """Resolve a UF efetiva de um leiloeiro que exibe VÁRIAS matrículas.

    Muitos portais (ex.: Mega Leilões) listam o mesmo leiloeiro com mais de uma
    matrícula — tipicamente uma JUCESP e outra de fora (ex.: "JUCESP Nº 844" +
    "JUCEMG Nº 1192"). Para a tese isso importa: se o leiloeiro tem matrícula
    **JUCESP**, ele pode atuar livremente em SP e NÃO há assimetria — tratamos
    como SP (excluído). Só é alvo quem é exclusivamente de fora.

    Regra: SP "vence" se aparecer em qualquer matrícula; senão, retorna a
    primeira UF não-SP reconhecida; se nada for reconhecido, None.
    """
    ufs = [parse_matricula(m).uf for m in matriculas]
    ufs_validas = [uf for uf in ufs if uf]
    if not ufs_validas:
        return None
    if "SP" in ufs_validas:
        return "SP"
    return ufs_validas[0]


# Termos que poluem o nome do leiloeiro nos portais.
_RUIDO_NOME = re.compile(
    r"\b(leiloeir[oa]\s+oficial|leiloeir[oa]|oficial|sr[a]?\.?|dr[a]?\.?)\b",
    re.IGNORECASE,
)


def normalizar_nome(nome: str | None) -> str:
    """Normaliza um nome para comparação: sem acento, minúsculo, sem ruído."""
    if not nome:
        return ""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", nome) if not unicodedata.combining(c)
    )
    sem_ruido = _RUIDO_NOME.sub(" ", sem_acento)
    return re.sub(r"\s+", " ", sem_ruido).strip().lower()


@dataclass(frozen=True)
class LeiloeiroRef:
    """Entrada de cadastro usada na resolução (subconjunto de `leiloeiros`)."""

    nome: str
    matricula: str
    uf_matricula: str
    junta_comercial: str | None = None
    id: object | None = None
    aliases: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Resolucao:
    """Resultado da resolução de um leiloeiro."""

    uf: str | None
    fora_sp: bool | None  # None quando a UF é desconhecida
    confianca: str  # 'alta' | 'media' | 'baixa'
    leiloeiro: LeiloeiroRef | None
    motivo: str


class LeiloeiroResolver:
    """Resolve (nome, matrícula) contra um cadastro de leiloeiros em memória."""

    def __init__(self, cadastro: list[LeiloeiroRef] | None = None) -> None:
        self._cadastro = cadastro or []
        # Índice por (junta, número) e por nome/alias normalizados.
        self._por_matricula: dict[tuple[str, str], LeiloeiroRef] = {}
        self._por_nome: dict[str, LeiloeiroRef] = {}
        for ref in self._cadastro:
            m = parse_matricula(ref.matricula)
            if m.junta and m.numero:
                self._por_matricula[(m.junta, m.numero)] = ref
            for nome in [ref.nome, *ref.aliases]:
                chave = normalizar_nome(nome)
                if chave:
                    self._por_nome.setdefault(chave, ref)

    def _match_nome(self, nome: str | None) -> LeiloeiroRef | None:
        alvo = normalizar_nome(nome)
        if not alvo:
            return None
        if alvo in self._por_nome:
            return self._por_nome[alvo]
        melhor: LeiloeiroRef | None = None
        melhor_score = 0.0
        for chave, ref in self._por_nome.items():
            score = SequenceMatcher(None, alvo, chave).ratio()
            if score > melhor_score:
                melhor_score, melhor = score, ref
        return melhor if melhor_score >= LIMIAR_NOME else None

    def resolver(self, nome: str | None = None, matricula: str | None = None) -> Resolucao:
        """Resolve a UF e (quando possível) o leiloeiro do cadastro.

        Confiança:
        - 'alta'  : UF veio da matrícula E há leiloeiro casado por matrícula;
        - 'media' : UF veio da matrícula (sem casar cadastro) OU veio de um
                    match forte de nome no cadastro;
        - 'baixa' : nada reconhecido (UF desconhecida).
        """
        m = parse_matricula(matricula)

        # 1) Matrícula com UF reconhecida.
        if m.uf:
            ref = None
            if m.junta and m.numero:
                ref = self._por_matricula.get((m.junta, m.numero))
            if ref is None:
                ref = self._match_nome(nome)
            confianca = "alta" if (m.junta and m.numero and ref) else "media"
            return Resolucao(
                uf=m.uf,
                fora_sp=m.uf != "SP",
                confianca=confianca,
                leiloeiro=ref,
                motivo="uf_da_matricula",
            )

        # 2) Sem UF na matrícula: tentar pelo nome no cadastro.
        ref = self._match_nome(nome)
        if ref is not None:
            uf = ref.uf_matricula
            return Resolucao(
                uf=uf,
                fora_sp=uf != "SP",
                confianca="media",
                leiloeiro=ref,
                motivo="uf_do_cadastro_por_nome",
            )

        # 3) Nada reconhecido.
        return Resolucao(
            uf=None,
            fora_sp=None,
            confianca="baixa",
            leiloeiro=None,
            motivo="nao_resolvido",
        )
