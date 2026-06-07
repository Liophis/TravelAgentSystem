#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

PYTHON_CMD=${BACKEND_PYTHON_CMD:-python}
PYTEST_CMD=${BACKEND_PYTEST_CMD:-pytest}

echo "[backend] checking project structure"
test -d backend

if [ -f backend/requirements.txt ]; then
  echo "[backend] installing/checking python dependencies is left to developer environment"
fi

if [ -f backend/pyproject.toml ]; then
  echo "[backend] pyproject detected"
fi

if [ -d backend/tests ] && find backend/tests -type f \( -name "test_*.py" -o -name "*_test.py" \) | grep -q .; then
  if command -v "${PYTEST_CMD%% *}" >/dev/null 2>&1; then
    echo "[backend] running pytest"
    PYTHONPATH=backend ${PYTEST_CMD} backend/tests
  else
    echo "[backend] pytest command not available; skipping tests"
  fi
elif [ -d backend/tests ]; then
  echo "[backend] no pytest files yet; scaffold pending"
fi

if [ -d backend/app ]; then
  echo "[backend] compiling python files"
  ${PYTHON_CMD} -m compileall backend/app >/dev/null
fi

echo "[backend] OK"
