# Python rules

## Style
- Line length: 100. Enforced by ruff.
- Imports: stdlib → third-party → local, separated by blank lines (ruff-isort handles this).
- Use `from __future__ import annotations` in all new modules.
- Prefer `pathlib.Path` over `os.path`.
- No `print()` in library code — use `logging`.

## Types
- All public functions must have type annotations.
- Use `pydantic.BaseModel` for structured data objects (articles, configs).
- Avoid `Any` unless wrapping an untyped external API.

## Error handling
- Raise specific exceptions, not bare `Exception`.
- Use `Result`-style returns (return value + error) only at module boundaries, not internally.
- Log errors with context before re-raising.

## Async
- Use `asyncio` for I/O-bound work (LLM calls, browser automation).
- Do not mix sync and async in the same call stack without an explicit bridge.

## Modules
- `src/models.py`          — Pydantic data models only, no I/O
- `src/config.py`          — Settings loaded from env, no side effects at import time
- `src/article_generator.py` — LLM call logic
- `src/note_client.py`     — Playwright automation, draft creation only
- `src/agent.py`           — Orchestration loop
- `src/cli.py`             — Entry point, argument parsing
