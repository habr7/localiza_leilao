"""Testes da varredura heurística de sites próprios (funções puras)."""

from src.ingestao.sites_proprios.scanner import (
    detectar_imoveis_sp,
    encontrar_links_candidatos,
)


def test_encontrar_links_candidatos_mesmo_dominio():
    html = """
    <a href="/imoveis">Imóveis</a>
    <a href="https://outro.com/imoveis">Externo</a>
    <a href="/leiloes-em-andamento">Leilões</a>
    <a href="/sobre">Sobre</a>
    <a href="mailto:x@y.com">email</a>
    """
    links = encontrar_links_candidatos(html, "https://leiloeirox.com.br")
    assert "https://leiloeirox.com.br/imoveis" in links
    assert "https://leiloeirox.com.br/leiloes-em-andamento" in links
    # Não inclui domínio externo, âncora institucional nem mailto.
    assert all("outro.com" not in u for u in links)
    assert all("/sobre" not in u for u in links)


def test_detectar_imovel_sp_com_localidade():
    html = """<html><body>
      Apartamento 60m² - Santos / SP - Lance inicial R$ 200.000,00
      Casa em Campinas/SP, 3 quartos.
    </body></html>"""
    achados = detectar_imoveis_sp(html, "https://x.com.br", "https://x.com.br/imoveis")
    cidades = " ".join(a.cidade or "" for a in achados)
    # A cidade extraída é aproximada (heurística); o que importa é flaggar SP.
    assert "Santos" in cidades
    assert "Campinas" in cidades
    assert all(a.site == "https://x.com.br" for a in achados)


def test_detectar_ignora_pagina_sem_imovel():
    html = "<html><body>Veículos em Curitiba/SP — leilão de carros</body></html>"
    # Sem palavra de imóvel, não deve flaggar (é leilão de veículo).
    assert detectar_imoveis_sp(html, "https://x.com.br", "https://x.com.br") == []


def test_detectar_sao_paulo_sem_barra():
    html = "<html><body>Imóvel localizado no Estado de São Paulo.</body></html>"
    achados = detectar_imoveis_sp(html, "https://x.com.br", "https://x.com.br")
    assert achados and achados[0].cidade == "São Paulo"
