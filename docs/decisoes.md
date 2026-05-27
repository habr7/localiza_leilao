# Decisões Arquiteturais

Registro enxuto de decisões relevantes. Atualizar a cada nova decisão.

## ORM e migrations: SQLAlchemy 2.0 + Alembic

Escolhemos SQLAlchemy 2.0 (estilo declarativo com `Mapped[]` / `mapped_column`) e Alembic
para versionar o schema. Por quê: SQLAlchemy é o ORM Python mais maduro e o estilo 2.0 dá
tipagem estática melhor; Alembic é o padrão de migrations do ecossistema e integra direto
com o `metadata` dos modelos.

## Banco: PostgreSQL

PostgreSQL (Supabase em produção) como banco principal. Por quê: já em uso pelo Humberto e
tem suporte nativo a JSONB, ARRAY e colunas geradas — recursos usados no modelo de lotes e
resultados para dados semi-estruturados das fontes.

## `agio` em `resultados`: snapshot de `lance_minimo_2` + coluna gerada STORED

O PROJECT.md (seção 5.4) define `agio` como coluna `GENERATED ALWAYS AS ... STORED` usando
`lance_minimo_2`. Porém `lance_minimo_2` pertence à tabela `lotes`, e o PostgreSQL só permite
que uma coluna gerada referencie colunas da própria tabela. A spec, como escrita, não compila.

Decisão (validada com o Humberto): adicionar `lance_minimo_2` também em `resultados`, como
snapshot do piso da 2ª praça no momento do resultado. Mantém o `agio` como coluna gerada
STORED, fiel à intenção do PROJECT.md, e ainda registra de forma imutável o lance mínimo
efetivamente usado no arremate (mesmo que o lote seja corrigido depois).
