#!/bin/bash

set -euo pipefail

cd /app

for env_file in .env.local .env; do
  if [ -f "$env_file" ]; then
    set -a
    # shellcheck disable=SC1090
    source "$env_file"
    set +a
  fi
done

BIND_HOST=${HOST:-0.0.0.0}
BIND_PORT=${PORT:-8000}

echo "🚀 启动 TravelAgentSystem..."
echo "   应用入口: app.main:app"
echo "   绑定地址: ${BIND_HOST}:${BIND_PORT}"

exec uvicorn app.main:app \
  --host "${BIND_HOST}" \
  --port "${BIND_PORT}"
