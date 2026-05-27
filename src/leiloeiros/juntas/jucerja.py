"""Coletor da JUCERJA (Rio de Janeiro) — leiloeiros não-SP (alvo da tese).

A JUCERJA renderiza a lista de leiloeiros numa ``section.ats-listaLeiloeiros``,
onde cada leiloeiro é um ``li.ats-listaLnks-item`` com pares de rótulo/valor
(``<h5>Rótulo:</h5><h6>Valor</h6>``).

Limitação conhecida: o servidor entrega apenas a 1ª página (5 leiloeiros); as
demais são carregadas via AJAX/JS (paginação ``data-value``). A coleta completa
exigiria executar o JS (Playwright) ou o endpoint de paginação, ainda não
mapeado. Enquanto isso, ``coletar`` traz a 1ª página e o complemento vem por LAI.
"""

from __future__ import annotations

from selectolax.parser import HTMLParser

from src.leiloeiros.cadastro import LeiloeiroRaw
from src.leiloeiros.juntas.base import JuntaScraper


class JucerjaScraper(JuntaScraper):
    junta = "JUCERJA"
    uf = "RJ"
    url_lista = "https://www.jucerja.rj.gov.br/AuxiliaresComercio/Leiloeiros"

    def _parse(self, html: str) -> list[LeiloeiroRaw]:
        tree = HTMLParser(html)
        secao = tree.css_first("section.ats-listaLeiloeiros") or tree.body
        if secao is None:
            return []
        registros: list[LeiloeiroRaw] = []
        for item in secao.css("li.ats-listaLnks-item"):
            campos = _campos_do_item(item)
            nome = campos.get("Leiloeiro")
            numero = _matricula(campos)
            if not (nome and numero):
                continue
            registros.append(self._novo_raw(nome, numero, _site(campos)))
        return registros


def _campos_do_item(item: object) -> dict[str, str]:
    """Lê os pares <h5>rótulo</h5>/<h6>valor</h6> de um item da lista."""
    rotulos = item.css("h5")  # type: ignore[attr-defined]
    valores = item.css("h6")  # type: ignore[attr-defined]
    campos: dict[str, str] = {}
    for h5, h6 in zip(rotulos, valores, strict=False):
        chave = h5.text(strip=True).rstrip(":").strip()
        campos[chave] = h6.text(strip=True)
    return campos


def _matricula(campos: dict[str, str]) -> str | None:
    """Extrai o número da matrícula (rótulo "Nº Matrícula"), evitando "Data Matrícula"."""
    for chave, valor in campos.items():
        chave_l = chave.lower()
        if "matr" in chave_l and "data" not in chave_l:
            return valor or None
    return None


def _site(campos: dict[str, str]) -> str | None:
    """Extrai o site, tratando o placeholder "Não cadastrado" como ausência."""
    for chave, valor in campos.items():
        if "site" in chave.lower():
            if valor and "não cadastrado" not in valor.lower():
                return valor
    return None
