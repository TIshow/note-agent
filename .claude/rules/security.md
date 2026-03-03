# Security rules

## Secrets
- API keys and credentials are loaded exclusively from environment variables via `python-dotenv`.
- Never hard-code secrets, even as placeholders (e.g., `sk-ant-xxx`).
- Never log secret values. Log key names only (e.g., `ANTHROPIC_API_KEY is set`).
- `.env` is in `.gitignore`. `.env.example` contains only key names and safe placeholder values.

## Session files
- `session/auth.json` contains browser cookies and local storage — treat it as a credential.
- It is gitignored. Never echo or print its contents in logs.
- If you need to inspect it, do so in a local terminal, not in code.

## LLM inputs
- Do not include raw user-provided filenames or paths in LLM prompts without sanitisation.
- Truncate inputs that exceed a reasonable token budget before sending to the API.

## File handling
- All file paths must be resolved against a known base directory (`INBOX_DIR`, `ARTICLES_DIR`).
- Reject any path that resolves outside the project root (path traversal guard).

## Dependencies
- New Python dependencies require explicit justification in the PR description.
- Do not add dependencies that are unmaintained or have known CVEs.
- Run `uv lock` after adding dependencies and commit the lockfile.
