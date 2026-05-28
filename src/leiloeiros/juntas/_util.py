"""Utilitários compartilhados pelos parsers de Junta Comercial.

Reúne o que mais se repete entre as listas públicas: normalização de URL de site
e um parser de listas "rotuladas" em texto (``NOME ... Matrícula: X ... <url>``),
usado por Juntas que publicam o cadastro como texto com rótulos (JUCEPB, JUCEPI).
"""

from __future__ import annotations

import re

from src.leiloeiros.cadastro import LeiloeiroRaw

_SITE_VAZIO = {"-", "--", "n/a", "na", "não", "nao", "x", "site"}
# Reconhece uma URL de site (http(s) ou começando por www), evitando e-mails.
_RE_URL = re.compile(r"(?:https?://|www\.)[\w.\-]+\.(?:com|net|br)[\w./\-]*", re.IGNORECASE)
# Linhas que NÃO são nome de leiloeiro (rótulos e valores de situação).
_NAO_NOME = re.compile(
    r":\s*$|^(situa|regular|irregular|ativo|inativo|matr[íi]cula|endere|telefone"
    r"|fone|site|e-?mail|data)\b",
    re.IGNORECASE,
)


def normalizar_site(site: str | None) -> str | None:
    """Limpa e completa a URL do site (ou None se não houver site real)."""
    if not site:
        return None
    site = site.strip().rstrip(".,;").strip()
    if not site or site.lower() in _SITE_VAZIO or "@" in site:
        return None
    if not site.startswith(("http://", "https://")):
        site = "https://" + site.lstrip("/")
    return site


def _limpar_matricula(valor: str) -> str:
    """Normaliza a matrícula textual (ex.: "n.º 11/2006, em 18/12/2006" -> "11/2006")."""
    valor = re.sub(r"n\.?[ºo°]\s*", "", valor, flags=re.IGNORECASE)
    valor = re.split(r",|\bem\b", valor)[0]
    return valor.strip()


def parse_lista_rotulada(body: str, uf: str, junta: str, fonte_cadastro: str) -> list[LeiloeiroRaw]:
    """Extrai leiloeiros de uma lista em texto com o rótulo ``Matrícula:``.

    Para cada ``Matrícula:`` no texto: o **nome** é a linha não-rótulo logo acima;
    a **matrícula** é o valor após o rótulo (ou a linha seguinte); o **site** é a
    primeira URL dentro do bloco do leiloeiro (até o próximo ``Matrícula:``).
    """
    # Remove linhas vazias para que o nome fique sempre imediatamente acima do
    # rótulo "Matrícula:" (alguns layouts intercalam <br>/linhas em branco).
    linhas = [ln.strip() for ln in body.split("\n") if ln.strip()]
    indices = [i for i, ln in enumerate(linhas) if re.match(r"Matr[íi]cula:", ln, re.I)]
    registros: list[LeiloeiroRaw] = []
    for pos, i in enumerate(indices):
        nome = None
        for j in range(i - 1, max(-1, i - 6), -1):
            cand = linhas[j]
            if cand and not _NAO_NOME.search(cand) and len(cand.split()) >= 2:
                nome = cand
                break
        if not nome:
            continue
        # Matrícula: valor após o rótulo na mesma linha, ou a próxima linha.
        resto = re.sub(r"Matr[íi]cula:\s*", "", linhas[i], flags=re.I).strip()
        if not resto and i + 1 < len(linhas):
            resto = linhas[i + 1]
        matricula = _limpar_matricula(resto)
        if not matricula:
            continue
        fim = indices[pos + 1] if pos + 1 < len(indices) else min(len(linhas), i + 14)
        bloco = "\n".join(linhas[i:fim])
        site_m = _RE_URL.search(bloco)
        registros.append(
            LeiloeiroRaw(
                nome=nome,
                matricula=matricula,
                uf_matricula=uf,
                junta_comercial=junta,
                site_oficial=normalizar_site(site_m.group(0) if site_m else None),
                fonte_cadastro=fonte_cadastro,
            )
        )
    return registros
