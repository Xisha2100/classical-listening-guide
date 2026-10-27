#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -x app/.venv/bin/python ]]; then
  if command -v uv >/dev/null 2>&1; then
    uv venv app/.venv --python 3.12
  elif command -v python3.12 >/dev/null 2>&1; then
    python3.12 -m venv app/.venv
  else
    echo '请先安装 uv 或 Python 3.12，再运行 ./start.sh。' >&2
    exit 1
  fi
fi
if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo '请先安装 Node.js 22 或更新版本（含 npm）。' >&2; exit 1
fi
if [[ ! -f app/.venv/.requirements-installed ]] || ! cmp -s app/requirements.lock app/.venv/.requirements-installed; then
  if command -v uv >/dev/null 2>&1; then
    uv pip sync --python app/.venv/bin/python app/requirements.lock
  else
    app/.venv/bin/python -m pip install -r app/requirements.lock
  fi
  cp app/requirements.lock app/.venv/.requirements-installed
fi
if [[ ! -d app/frontend/node_modules ]] || [[ ! -f app/frontend/node_modules/.package-lock-installed ]] || ! cmp -s app/frontend/package-lock.json app/frontend/node_modules/.package-lock-installed; then
  (cd app/frontend && npm ci)
  cp app/frontend/package-lock.json app/frontend/node_modules/.package-lock-installed
fi
if [[ ! -f app/.env ]]; then cp app/.env.example app/.env; fi
app/.venv/bin/python app/scripts/prepare_corpus.py
(cd app/frontend && npm run build)
export PYTHONPATH="$PWD/app${PYTHONPATH:+:$PYTHONPATH}"
echo '导听助手已准备好。浏览器打开 http://127.0.0.1:8765；Ctrl+C 停止。'
exec app/.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
