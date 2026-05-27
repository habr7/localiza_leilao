# Garimpo de Leilões com Assimetria de Atenção

Sistema para identificar leilões de imóveis localizados em **São Paulo** conduzidos por
**leiloeiros matriculados em outras Juntas Comerciais (não-JUCESP)**, com foco em leilões
**extrajudiciais**. A tese: quando um leiloeiro de fora de SP conduz o leilão, a divulgação
tende a se concentrar no estado de origem, o público-alvo paulista pode não tomar conhecimento,
e a menor concorrência abre espaço para arremate com menor ágio (maior desconto).

A fonte da verdade do escopo é o [`PROJECT.md`](./PROJECT.md). Leia-o antes de qualquer
desenvolvimento.

## Como rodar

Pré-requisitos: Python 3.11+ e [uv](https://docs.astral.sh/uv/).

```bash
# instalar dependências
uv sync

# copiar o exemplo de variáveis de ambiente e ajustar
cp .env.example .env
```

O PostgreSQL **não** é necessário para a Fase 1 (validação da tese). Ele só entra quando
formos aplicar as migrations (`alembic upgrade head`) em fases posteriores.

## Como rodar a Fase 1 (validação da tese)

1. Preencha `data/fase1_input.csv` com pelo menos 50 leilões já realizados (o cabeçalho
   já está no arquivo).
2. Rode o script de validação:
   ```bash
   uv run python -m src.scripts.fase1_validar_tese
   ```
3. Leia o veredito em `data/fase1_output.md`.

## Status

Fase 1 — validação da tese (em andamento). Sem scraping e sem API até a tese ser validada.
