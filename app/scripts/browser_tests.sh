#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
cli="$PWD/app/frontend/node_modules/.bin/playwright-cli"
if [[ ! -x "$cli" ]]; then echo '请先运行 ./start.sh 安装依赖。' >&2; exit 1; fi
mkdir -p output/playwright
trap '"$cli" -s=music-regression close >/dev/null 2>&1 || true' EXIT
"$cli" -s=music-regression open "${MUSIC_TEST_URL:-http://127.0.0.1:8765}"
"$cli" -s=music-regression resize 1440 1000
for test in browser-smoke browser-corpus browser-reader browser-tcha-phrases; do
  log="output/playwright/${test}.log"
  if ! "$cli" -s=music-regression run-code "$(cat "app/tests/${test}.js")" > "$log" 2>&1; then
    cat "$log"
    exit 1
  fi
  app/.venv/bin/python - "$log" <<'PYREPORT'
import json, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text()
try:
    if '### Error' in text: raise ValueError('Browser command failed')
    result = json.loads(text.split('### Result\n', 1)[1].split('\n', 1)[0])
    if result.get('result') != 'passed': raise ValueError('Browser assertion failed')
    if 'tested' in result: result['tested'] = len(result['tested'])
    print(Path(sys.argv[1]).stem + ': ' + json.dumps(result, ensure_ascii=False))
except (ValueError, IndexError):
    print(text)
    sys.exit(1)
PYREPORT
done
