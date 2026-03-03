# note-agent — CLAUDE.md

## Project goal

Automatically generate **note.com article drafts** from text files or transcripts.
Runs are intended to be nightly / batch. Output goes to `data/articles/`.

Two writing styles are supported:
- `general` — general-audience note.com article (default)
- `quantamental` — investor + quantamental analyst perspective
  (combines quantitative data analysis with fundamental/qualitative judgment)

## Hard rules

- **Draft only. Never auto-publish.** Any code path that calls a publish API or clicks a
  publish button is forbidden unless the user explicitly unlocks it with a named flag.
- **Keep changes small and reversible.** Prefer adding new functions over modifying existing ones.
  Delete dead code rather than commenting it out.
- **Run tests and lint after every code change.** Commands: `pytest -q` and `ruff check .`.
- **Do not touch `session/` or `.env` files unless explicitly asked.** These contain auth state.
- **Save generated articles to `data/articles/`.** Processed inputs move to `data/processed/`.

## Commands

| Task               | Command                                  |
|--------------------|------------------------------------------|
| Test               | `pytest -q`                              |
| Lint               | `ruff check .`                           |
| Format             | `ruff format .`                          |
| Install            | `uv sync`                                |
| Node               | `pnpm install`                           |
| Run (general)      | `uv run note-agent --dry-run`            |
| Run (quantamental) | `uv run note-agent --style quantamental` |

## File layout

```
src/          Python source (models, config, generator, client, agent, cli)
tests/        pytest tests
data/inbox/   Input text files (drop files here)
data/articles/ Generated drafts (markdown)
data/processed/ Inputs after successful run
data/logs/    Run logs, Playwright traces
session/      Browser auth state — never commit
prompts/      Prompt templates
.claude/rules/ Repo-specific engineering rules
```

## Rules files

- `.claude/rules/python.md`      — Python style and conventions
- `.claude/rules/testing.md`     — Testing expectations
- `.claude/rules/note-adapter.md` — note.com browser automation rules
- `.claude/rules/security.md`    — Secrets and auth handling
