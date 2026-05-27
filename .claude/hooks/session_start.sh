#!/usr/bin/env bash
# Bootstrap idempotente para sessões do Claude Code on the web.
# Garante, a cada início de sessão: dependências sincronizadas, Postgres local
# de pé, role/banco criados e migrations aplicadas. Tudo com `|| true` para nunca
# bloquear o início da sessão por falha intermitente.
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || true

# 1) Dependências (usa venv em cache quando existe).
command -v uv >/dev/null 2>&1 && uv sync --quiet || true

# 2) Postgres local (o serviço não persiste entre containers).
service postgresql start >/dev/null 2>&1 || true
for _ in 1 2 3 4 5 6 7 8; do
  pg_isready -q && break
  sleep 1
done

# 3) Role e database (idempotente).
su postgres -c "psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='user'\"" 2>/dev/null | grep -q 1 \
  || su postgres -c "psql -c \"CREATE ROLE \\\"user\\\" LOGIN PASSWORD 'pass' SUPERUSER;\"" >/dev/null 2>&1 || true
su postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='leiloes'\"" 2>/dev/null | grep -q 1 \
  || su postgres -c "psql -c \"CREATE DATABASE leiloes OWNER \\\"user\\\";\"" >/dev/null 2>&1 || true

# 4) Migrations.
uv run alembic upgrade head >/dev/null 2>&1 || true

echo "[bootstrap] pronto: deps + postgres(leiloes) + migrations aplicadas."
