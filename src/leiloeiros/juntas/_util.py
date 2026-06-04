"""Utilitários compartilhados pelos parsers de Junta Comercial.

Reúne o que mais se repete entre as listas públicas: normalização de URL de site
e um parser de listas "rotuladas" em texto (``NOME ... Matrícula: X ... <url>``),
usado por Juntas que publicam o cadastro como texto com rótulos (JUCEPB, JUCEPI).
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser

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


# Rótulo de site e um domínio "pelado" (sem www/http), ex.: "dearaujoleiloes.com.br".
_RE_SITE_LABEL = re.compile(r"(?:Site|S[íi]tio\s+Eletr[ôo]nico)\s*:?\s*([^\s<,;]+)", re.IGNORECASE)
_RE_DOMINIO = re.compile(r"\b[\w.\-]+\.(?:com|net|org)(?:\.br)?\b", re.IGNORECASE)


def extrair_site(texto: str) -> str | None:
    """Acha o site num bloco: 1º pelo rótulo "Site:/Sítio Eletrônico:", senão URL.

    Captura também domínios "pelados" (sem www/http), comuns em algumas Juntas.
    """
    m = _RE_SITE_LABEL.search(texto)
    if m:
        cand = m.group(1).strip()
        if "@" not in cand and _RE_DOMINIO.search(cand):
            return normalizar_site(cand)
    url = _RE_URL.search(texto)
    return normalizar_site(url.group(0)) if url else None


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
        registros.append(
            LeiloeiroRaw(
                nome=nome,
                matricula=matricula,
                uf_matricula=uf,
                junta_comercial=junta,
                site_oficial=extrair_site(bloco),
                fonte_cadastro=fonte_cadastro,
            )
        )
    return registros


# Prefixo de ordem de antiguidade: "1 - Nome", "12 – Nome".
_RE_ORDEM = re.compile(r"^\s*\d+\s*[-–]\s*")


def parse_tabela(
    html: str,
    uf: str,
    junta: str,
    fonte_cadastro: str,
    idx_nome: int,
    idx_matricula: int,
    idx_site: int | None = None,
    matricula_so_numero: bool = False,
    pular_cabecalho: bool = True,
) -> list[LeiloeiroRaw]:
    """Extrai leiloeiros de uma tabela HTML (nome e matrícula em colunas dadas).

    Trata o prefixo de ordem de antiguidade no nome ("1 - Fulano" -> "Fulano").
    ``idx_site`` (opcional) indica a coluna onde está o site (extrai a 1ª URL).
    ``matricula_so_numero`` extrai apenas o número da célula de matrícula (ex.:
    "Matrícula - 01 22/08/1984" -> "01"). Linhas sem matrícula são ignoradas.
    """
    registros: list[LeiloeiroRaw] = []
    tree = HTMLParser(html)
    cols_max = max(i for i in (idx_nome, idx_matricula, idx_site) if i is not None)
    for i, tr in enumerate(tree.css("tr")):
        if pular_cabecalho and i == 0 and tr.css("th"):
            continue
        celulas = tr.css("td")
        if len(celulas) <= cols_max:
            continue
        textos = [re.sub(r"\s+", " ", c.text()).strip() for c in celulas]
        nome = _RE_ORDEM.sub("", textos[idx_nome]).strip()
        matricula = textos[idx_matricula].strip()
        if matricula_so_numero:
            num = re.search(r"\d[\d/\-]*", matricula)
            matricula = num.group(0) if num else ""
        if not nome or not re.search(r"\d", matricula):
            continue
        site = None
        if idx_site is not None:
            site = extrair_site(celulas[idx_site].text())
        registros.append(
            LeiloeiroRaw(
                nome=nome,
                matricula=matricula,
                uf_matricula=uf,
                junta_comercial=junta,
                site_oficial=site,
                fonte_cadastro=fonte_cadastro,
            )
        )
    return registros


def parse_blocos_rotulados(
    html: str, uf: str, junta: str, fonte_cadastro: str, sep_css: str = "p"
) -> list[LeiloeiroRaw]:
    """Extrai leiloeiros de blocos HTML (um por elemento ``sep_css``) rotulados.

    Cada bloco tem o nome (1ª linha, normalmente em <strong>) e rótulos
    ``Matrícula:`` e ``Site:``. Usado quando a Junta publica um <p> por leiloeiro.
    """
    registros: list[LeiloeiroRaw] = []
    tree = HTMLParser(html)
    for bloco in tree.css(sep_css):
        texto = bloco.text(separator="\n")
        m = re.search(r"Matr[íi]cula:\s*([\w/\-.]+)", texto, re.I)
        if not m:
            continue
        # Nome: primeira linha não vazia que não seja rótulo.
        nome = None
        for linha in texto.split("\n"):
            linha = linha.strip()
            if linha and not _NAO_NOME.search(linha) and len(linha.split()) >= 2:
                nome = linha
                break
        if not nome:
            continue
        registros.append(
            LeiloeiroRaw(
                nome=nome,
                matricula=m.group(1).strip(),
                uf_matricula=uf,
                junta_comercial=junta,
                site_oficial=extrair_site(texto),
                fonte_cadastro=fonte_cadastro,
            )
        )
    return registros
