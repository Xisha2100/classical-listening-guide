# Repository Guidelines

## Project Purpose and Responsibilities

This is a Codex music-appreciation workspace with a local score reader. Codex researches, analyzes, imports scores, and writes records. The browser only reads local notes, displays notation, and plays excerpts. Do not reintroduce online search, model API clients/configuration, or note-authoring controls into the web app.

Before music-analysis work, read [Agent.md](Agent.md) for analysis methods and delivery standards, and follow [分析工作规范](分析工作规范.md) for data and authoring rules. Preserve sources, original excerpts, model provenance, score edition identity, and independent location/content/listening review states. Never claim human listening review based on automated playback tests.

## Project Structure & Content Organization

Keep primary articles as Markdown, organized by topic rather than authoring date:

- `作品/<work_id>/*.md`: active analysis cards with YAML metadata and prose.
- `作品/<work_id>/研究记录/`: evidence, reasoning, and model-run records; not indexed as cards.
- `作品/<work_id>/archive/`: previous versions, retained outside the active reader.
- `作曲家/`, `流派/`: composer profiles and historical context as the collection grows.
- `assets/`: source scores, generated MEI/SVG/event indexes, guides, segment exports, sources and local audio.
- `app/`: FastAPI reader, React frontend, local authoring commands, and regression tests.

Use relative Markdown links. Keep exclusive assets beside their note when appropriate; shared assets belong in `assets/`. Markdown card metadata is authoritative; `assets/segments/` is its JSON export, while SQLite is a rebuildable index.

## Development and Validation Commands

From the repository root:

```sh
./start.sh
app/.venv/bin/python app/scripts/project.py check
app/.venv/bin/python -m pytest app/tests -q
npm --prefix app/frontend test
npm --prefix app/frontend run build
bash app/scripts/browser_tests.sh
rg --files
rg '\]\([^)]*\)' --glob '*.md'
git diff --check
```

Run tests appropriate to the change. Browser tests require a running local server; set `MUSIC_TEST_URL` to select its URL. Inspect screenshots in `output/playwright/` and preview edited documentation. For authoring commands, see [README](README.md). Use `project.py save-analysis` / `save-guide` to validate and persist records, and `import-score` to create a new score edition. Never run old corpus preparation scripts as routine startup or validation; they may install or migrate example content.

Preserve existing content and unsaved browser drafts during refactors. Runtime reading may rebuild caches, but must not overwrite notes, score editions, or their event files. Do not inspect or expose ignored legacy `.env` or `app/.local/` credentials; the reader does not use them.

## Writing Style & Naming Conventions

Use UTF-8 and one `#` title per Markdown document. Keep descriptive, hierarchical headings without skipping levels. Use concise Chinese prose, full-width Chinese punctuation, and language-tagged code fences. Use stable filenames such as `贝多芬-第五交响曲.md` and descriptive asset names. Preserve established work titles, catalogue numbers, composer names, and performer spellings.

## Review Guidelines

Verify factual claims, catalogue numbers, translations, quotations, and attributions. Ensure local relative links resolve on a case-sensitive filesystem. Keep original quotations separate from summaries. Preserve score hashes and versions; never silently transfer anchors to a different edition. Retain old analyses when replacing them, and identify hypotheses and unresolved boundaries. Large media must have appropriate licensing and compression.

## Commit & Pull Request Guidelines

Use focused commits with short imperative subjects. PRs should describe the concrete behavior or content change, sources, validation, and material limitations. Identify renamed or moved files. Include screenshots when the rendered layout or notation materially changes. Follow the user's authorization for GitHub publication; local development alone does not require a push.
