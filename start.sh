#!/bin/bash

cd /app

# Load backend/.env if present
if [ -f backend/.env ]; then
  set -a
  source backend/.env
  set +a
fi

BIND_HOST=${HOST:-0.0.0.0}
BIND_PORT=${PORT:-7860}

echo "🚀 启动 TravelAgentSystem..."
echo "   绑定的地址: ${BIND_HOST}:${BIND_PORT}"

exec gunicorn backend.app.api.main:app \
  --bind ${BIND_HOST}:${BIND_PORT} \
  --workers 1 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 600 \
  --access-logfile - \
  --error-logfile -
