# Prompt para a próxima sessão (rede liberada)

> Cole o conteúdo abaixo numa **nova** sessão do Claude Code on the web, neste repo,
> com o ambiente configurado em **Network access = Full**. (A nova sessão é necessária
> porque a mudança de rede só vale em sessão nova.)

---

```
Leia, nesta ordem, antes de qualquer ação: PROJECT.md (fonte da verdade do escopo),
docs/plano_desenvolvimento.md (roadmap das fases 2-5), docs/fontes.md e
docs/leiloeiros.md. Confirme em 2 frases qual é a tese central e qual é a virada
conceitual (o produto opera sobre leilões ABERTOS, não depende de preço de arremate
nem de número de lances).

Contexto do que já existe (feito em sessões anteriores):
- Schema completo (leiloeiros, leiloes c/ uf_leiloeiro e fonte_tipo, lotes, resultados,
  lote_fontes) com migrations Alembic aplicadas pelo hook .claude/hooks/session_start.sh.
- Fase 2 núcleo PRONTA e testada: src/leiloeiros/matricula.py (parse de matrícula),
  src/leiloeiros/resolver.py (resolve nome/matrícula -> UF com confiança; a UF vem
  SEMPRE da matrícula/cadastro, nunca da marca do site), src/leiloeiros/cadastro.py
  (upsert idempotente + import CSV), e src/leiloeiros/juntas/ (interface JuntaScraper +
  JUCESP/JUCERJA/JUCEMG com parsing ao vivo PENDENTE).

Regra central reafirmada pelo Humberto: o alvo são leiloeiros/sites PEQUENOS que NÃO
são da JUCESP, mas cujo imóvel está em SP. Não usar allowlist fixa de domínios —
descobrir os sites a partir do cadastro das Juntas e dos agregadores.

Antes de codar, valide o ambiente:
1. Rede: faça um GET de teste (httpx) em https://www.megaleiloes.com.br/robots.txt e
   confirme status 200 (não 403 "Host not in allowlist"). Se ainda der 403, PARE e me
   avise — a sessão não está com Full.
2. Banco: rode `uv run alembic current` e confirme que está no head. Se não, rode o
   bootstrap: `bash .claude/hooks/session_start.sh`.
3. Qualidade base: `uv run ruff check . && uv run mypy src && uv run pytest -q` (tudo verde).

Execute NA ORDEM. Commit pequeno e descritivo (pt-BR) ao fim de cada bloco. Não pule,
não adicione features fora do pedido, pergunte se houver ambiguidade. Código em inglês,
docstrings/comentários em pt-BR. Respeite robots.txt, throttling >= 1 req/s por domínio
e User-Agent identificável (seção 7 do PROJECT.md). Cada scraper deve ter ao menos uma
fixture HTML salva em tests/fixtures/ e um teste de parsing. Upserts idempotentes.

==========================================
BLOCO 1 — FECHAR FASE 2 (scrapers de Junta ao vivo)
==========================================
1.1. Para JUCESP, JUCERJA e JUCEMG: inspecione o site real, descubra a URL da relação
     pública de leiloeiros, preencha `url_lista` e implemente `_parse(html)` em cada
     classe de src/leiloeiros/juntas/. Salve uma fixture HTML real (recortada) por Junta.
1.2. Se alguma Junta não tiver lista pública navegável, NÃO invente: documente em
     docs/leiloeiros.md e deixe o caminho coletar_csv (LAI) pronto.
1.3. Escreva um script src/scripts/fase2_cadastrar_leiloeiros.py que roda os scrapers
     disponíveis e faz upsert via cadastro.upsert_leiloeiros. Logue fonte, encontrados,
     inseridos, atualizados (structlog).
1.4. Rode o script de verdade e popule o banco. Mostre quantos leiloeiros não-SP entraram.
1.5. Teste o resolvedor contra alguns nomes reais coletados (sanity check).
1.6. COMMIT: "feat: scrapers das Juntas (JUCESP/JUCERJA/JUCEMG) e carga do cadastro".

==========================================
BLOCO 2 — INICIAR FASE 3 (ingestão)
==========================================
2.1. Implemente src/ingestao/base.py: BaseScraper (httpx async, RateLimiter por domínio,
     leitura de robots.txt, UA identificável, retries/backoff) e os dataclasses LoteRaw.
2.2. Implemente 1 agregador (comece pelo Mega Leilões) em src/ingestao/agregadores/:
     listar imóveis uf=SP, extrair leilão + lote + leiloeiro(nome+matrícula). Fixture +
     teste de parsing.
2.3. Pipeline de ingestão: para cada lote, use LeiloeiroResolver (carregue o cadastro via
     cadastro.carregar_cadastro) para preencher leiloes.uf_leiloeiro e fonte_tipo; faça
     upsert idempotente de leilao/lote/lote_fontes.
2.4. Rode contra o site real e mostre quantos lotes em SP com leiloeiro não-SP foram
     encontrados (o sinal da tese).
2.5. COMMIT: "feat: BaseScraper + ingestao Mega Leiloes com matching de leiloeiro".

==========================================
FECHAMENTO
==========================================
- `uv run ruff check . && uv run ruff format . && uv run mypy src && uv run pytest -q`
  (tudo verde). Commit de lint se preciso.
- Faça push para a branch de trabalho.
- Resumo: o que foi feito, nº de leiloeiros não-SP cadastrados, nº de lotes-alvo
  encontrados, e o que entra na próxima sessão (mais agregadores + sites próprios não-SP +
  comunicações JUCESP; depois Fase 4 pipeline/score).
```
