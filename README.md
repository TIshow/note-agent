# note-agent

Automatically generate **note.com article drafts** from text files or transcripts.

> **Draft only.** This tool never publishes. All output goes to `data/articles/` and
> optionally to note.com as a saved draft.

---

## What it does (MVP)

1. Reads `.txt` files from `data/inbox/`
2. Sends each file to Claude (Anthropic API) to generate a Japanese article draft
3. Saves the draft as Markdown to `data/articles/`
4. Optionally uploads to note.com as a saved draft via Playwright
5. Moves processed inputs to `data/processed/`

### Writing styles

| Style          | Description                                                                                 |
| -------------- | ------------------------------------------------------------------------------------------- |
| `general`      | General-audience note.com article (default)                                                 |
| `quantamental` | Investor + quantamental analyst perspective — combines quant data with fundamental judgment |

---

## Local setup

### Prerequisites

- [asdf](https://asdf-vm.com/) with `python` and `nodejs` plugins
- [uv](https://docs.astral.sh/uv/)
- [pnpm](https://pnpm.io/)

### 1. Install runtimes

```bash
asdf install
```

### 2. Install Python dependencies

```bash
uv sync
```

### 3. Install Node dependencies and Playwright browsers

```bash
pnpm install
pnpm run install-browsers
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in ANTHROPIC_API_KEY and NOTE_USER_ID
```

---

## Running

```bash
# Generate drafts — general style (dry run, inbox files not moved)
uv run note-agent --dry-run

# Generate drafts — investor/quantamental perspective
uv run note-agent --style quantamental --dry-run

# Generate drafts and move processed files
uv run note-agent

# Generate and upload to note.com as drafts (requires session/auth.json)
uv run note-agent --save-to-note --style quantamental --no-headless
```

### Setting up note.com session

```bash
# Record your login session manually
pnpm exec playwright codegen https://note.com
# Save the storageState to session/auth.json when prompted
```

---

## Tests & lint

```bash
pytest -q          # run all tests
ruff check .       # lint
ruff format .      # format
```

---

## Project structure

```
src/                  Python source
tests/                pytest tests
data/inbox/           Drop input .txt files here
data/articles/        Generated markdown drafts
data/processed/       Inputs after successful processing
data/logs/            Run logs and Playwright traces
session/              Browser auth state (gitignored)
prompts/              Prompt templates
.claude/rules/        Repo-specific rules for Claude Code
```

---

## Current scope

- [x] Project scaffold and toolchain
- [x] Pydantic models
- [x] LLM-based article generator (Claude API)
- [x] note.com Playwright client (draft save only)
- [x] CLI with `--dry-run` and `--save-to-note` flags
- [ ] Prompt templates in `prompts/`
- [ ] Nightly scheduling (cron / GitHub Actions)
- [ ] Retry logic and error reporting
