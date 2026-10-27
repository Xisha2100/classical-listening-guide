#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
cli="$PWD/app/frontend/node_modules/.bin/playwright-cli"
if [[ ! -x "$cli" ]]; then echo '请先运行 ./start.sh 安装依赖。' >&2; exit 1; fi
mkdir -p output/playwright
trap '"$cli" -s=music-regression close >/dev/null 2>&1 || true' EXIT
"$cli" -s=music-regression open http://127.0.0.1:8765
"$cli" -s=music-regression resize 1440 1000
"$cli" -s=music-regression run-code "$(cat app/tests/browser-smoke.js)"
"$cli" -s=music-regression run-code "$(cat app/tests/browser-corpus.js)"
