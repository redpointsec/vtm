#!/usr/bin/env bash
# vtm container entrypoint.
#
# Idempotent: applies migrations on every start, but only loads the seed
# fixtures the first time (when vtmdb.sqlite3 does not yet exist). Restarting
# the container therefore preserves any state created during a session.
#
# OPENAI_API_KEY is consumed by the chatbot. The app starts fine without it
# (chatbot endpoints just fail at request time). OPENROUTER_API_KEY is
# accepted as an alias so callers using OpenRouter naming work too.
set -euo pipefail

cd /app

if [ -z "${OPENAI_API_KEY:-}" ] && [ -n "${OPENROUTER_API_KEY:-}" ]; then
  export OPENAI_API_KEY="${OPENROUTER_API_KEY}"
fi

# Start the bundled redis-server in the background. taskManager.settings imports
# redis and hard-codes REDIS_HOST=localhost; login uses it for failed-attempt
# tracking. Running it in-container keeps the deployment a single service.
echo "[entrypoint] starting redis-server..."
redis-server --daemonize yes --bind 127.0.0.1 --port 6379 --save "" --appendonly no
for _ in 1 2 3 4 5 6 7 8 9 10; do
  if redis-cli ping 2>/dev/null | grep -q PONG; then
    break
  fi
  sleep 0.2
done

DB_FILE="${DB_FILE:-/app/vtmdb.sqlite3}"
FRESH_DB=0
if [ ! -f "${DB_FILE}" ]; then
  FRESH_DB=1
fi

echo "[entrypoint] applying migrations..."
python manage.py migrate --noinput

if [ "${FRESH_DB}" = "1" ]; then
  echo "[entrypoint] fresh database detected, loading seed fixtures..."
  python manage.py loaddata taskManager/fixtures/*
else
  echo "[entrypoint] existing database detected, skipping fixture load"
fi

echo "[entrypoint] starting: $*"
exec "$@"
