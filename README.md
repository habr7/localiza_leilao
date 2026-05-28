# Garimpo de Leilões com Assimetria de Atenção

Sistema para identificar leilões de imóveis localizados em **São Paulo** conduzidos por
**leiloeiros matriculados em outras Juntas Comerciais (não-JUCESP)**, com foco em leilões
**extrajudiciais**. A tese: quando um leiloeiro de fora de SP conduz o leilão, a divulgação
tende a se concentrar no estado de origem, o público-alvo paulista pode não tomar conhecimento,
e a menor concorrência abre espaço para arremate com menor ágio (maior desconto).

A fonte da verdade do escopo é o [`PROJECT.md`](./PROJECT.md); o roadmap de implementação
está em [`docs/plano_desenvolvimento.md`](./docs/plano_desenvolvimento.md). Leia-os antes
de desenvolver.

## Como rodar

Pré-requisitos: Python 3.11+ e [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env   # ajuste DATABASE_URL se necessário
```

### Banco local (desenvolvimento)

As fases 2+ usam PostgreSQL. Em sessões do Claude Code on the web, o hook
`.claude/hooks/session_start.sh` sobe o Postgres, cria o banco `leiloes` e aplica as
migrations automaticamente. Para fazer isso à mão localmente:

```bash
service postgresql start
su postgres -c "psql -c \"CREATE ROLE \\\"user\\\" LOGIN PASSWORD 'pass' SUPERUSER;\""
su postgres -c "psql -c 'CREATE DATABASE leiloes OWNER \"user\";'"
uv run alembic upgrade head
```

### Qualidade

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest -q
```

(os testes que dependem de banco fazem *skip* automático se o Postgres não estiver de pé.)

## Fase 1 (validação da tese) — opcional / backtest

A Fase 1 foi pulada (tese assumida como válida), mas o script segue disponível como
ferramenta de backtest: preencha `data/fase1_input.csv` e rode
`uv run python -m src.scripts.fase1_validar_tese` (veredito em `data/fase1_output.md`).

## Identificar imóveis-alvo (Fase 3)

Coleta imóveis em SP num agregador, resolve a UF do leiloeiro e separa os alvos
(leiloeiro **não-JUCESP**):

```bash
uv run python -m src.scripts.fase3_identificar_imoveis --max-paginas 20
# gera data/imoveis_sp.csv (tudo) e data/imoveis_alvo.csv (só não-SP)
```

Por que tão poucos alvos saem dos agregadores grandes (e por que um CSV "só de um
site" não é o retrato do mercado): ver [`docs/cobertura_diagnostico.md`](./docs/cobertura_diagnostico.md).

## Sites próprios de leiloeiros não-SP (maior assimetria)

Onde de fato moram os imóveis-alvo: o site do próprio leiloeiro de fora. Primeiro
popule o cadastro a partir das Juntas (traz o `site_oficial`), depois varra:

```bash
uv run python -m src.scripts.fase2_cadastrar_leiloeiros   # 5 Juntas -> ~530 leiloeiros, ~240 sites
uv run python -m src.scripts.fase3_sites_proprios          # varredura heurística (descoberta)
uv run python -m src.scripts.fase3_sites_dedicados         # parsers dedicados -> banco + CSV estruturado
```

- **Descoberta** (`fase3_sites_proprios`): heurística sobre TODOS os sites do
  cadastro → `data/sites_proprios_sp.csv` (indícios de imóvel em SP).
- **Estruturado** (`fase3_sites_dedicados`): parsers dedicados por site
  (`webleiloes`, `leiloariasmart`) que extraem o lote (tipo, cidade, lance, praça),
  resolvem o leiloeiro dono e fazem upsert idempotente em `leiloes`/`lotes`/
  `lote_fontes` → `data/imoveis_sp_sites_proprios.csv`.

## Status

- **Fase 1** — pulada (tese assumida válida); script mantido como backtest.
- **Fase 2** (cadastro de leiloeiros) — modelo de dados, resolvedor de UF
  (`src/leiloeiros/resolver.py`), cadastro com upsert idempotente e import CSV, e
  scrapers para **8 Juntas**. Parsers ao vivo prontos para **JUCEPAR** e **JUCEG**
  (com `site_oficial`); demais Juntas pendentes (lista em JS/PDF — ver
  [`docs/leiloeiros.md`](./docs/leiloeiros.md)).
- **Fase 3** (ingestão) — `BaseScraper` (`src/ingestao/base.py`); agregador
  **Mega Leilões** (`agregadores/megaleiloes.py`) + script de imóveis-alvo; e a
  varredura de **sites próprios** (`sites_proprios/scanner.py` +
  `fase3_sites_proprios`). **A fazer:** mais agregadores, parsers dedicados por site
  próprio com indício SP, e comunicações JUCESP.
- **Fases 4–5** — planejadas (ver `docs/plano_desenvolvimento.md`).
