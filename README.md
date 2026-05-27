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

## Status

- **Fase 1** — pulada (tese assumida válida); script mantido como backtest.
- **Fase 2** (cadastro de leiloeiros) — núcleo pronto: modelo de dados, resolvedor de
  UF (`src/leiloeiros/resolver.py`), cadastro com upsert idempotente e import CSV, e a
  interface dos scrapers de Junta. **Pendente:** parsers ao vivo das Juntas (precisam de
  rede liberada — ver [`docs/fontes.md`](./docs/fontes.md)).
- **Fases 3–5** — planejadas (ver `docs/plano_desenvolvimento.md`).
