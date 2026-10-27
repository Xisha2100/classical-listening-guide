# Repository Guidelines

## Project Structure & Content Organization

This repository is currently a lightweight workspace for music-appreciation notes. Keep primary articles as Markdown files. As the collection grows, organize material by topic rather than by authoring date, for example:

- `作品/` for notes on individual works or albums
- `作曲家/` for composer and artist profiles
- `流派/` for genre and historical context
- `assets/` for referenced images, scores, and short media samples

Place an asset beside its note only when it is used exclusively there; otherwise use `assets/`. Use relative Markdown links so documents remain portable.

## Development and Validation Commands

There is no build system or automated test suite configured. Before submitting changes, use these lightweight checks from the repository root:

```sh
rg --files                    # Review tracked content and organization
rg '\]\([^)]*\)' --glob '*.md' # Inspect Markdown links
git diff --check             # Detect whitespace and conflict-marker issues
```

Open edited Markdown files in a previewer to confirm headings, tables, footnotes, images, and Chinese typography render correctly. If a Markdown linter is added later, document its exact invocation here.

## Writing Style & Naming Conventions

Use UTF-8 and Markdown with a single `#` title per document. Keep headings descriptive and hierarchical; do not skip heading levels. Prefer concise paragraphs, Chinese full-width punctuation in Chinese prose, and fenced code blocks with a language tag when applicable.

Use clear, stable filenames such as `贝多芬-第五交响曲.md`; avoid generic names like `notes-final.md`. Name assets descriptively, for example `贝多芬第五交响曲-主题谱例.png`. Preserve established spellings for work titles, catalog numbers, composers, and performers throughout a document.

## Review Guidelines

Treat factual and navigational checks as testing. Verify dates, catalog numbers, translations, quotations, and source attributions. Confirm every new relative link and embedded asset resolves on a case-sensitive filesystem. Large media files should be compressed and included only when licensing permits.

## Commit & Pull Request Guidelines

No Git history is available in this directory, so no existing commit convention can be inferred. Use short, imperative subjects such as `Add analysis of Debussy's La Mer`. Keep each commit focused on one topic.

Pull requests should summarize the content changed, identify important sources, and note renamed or moved files. Include screenshots only when rendered layout, notation, or image placement materially changes. Link related issues when available.
