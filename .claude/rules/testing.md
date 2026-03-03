# Testing rules

## Expectations
- Every module in `src/` must have a corresponding test file in `tests/`.
- Tests run with `pytest -q`. All tests must pass before merging any change.
- Test file names: `tests/test_<module>.py`.

## Unit tests
- Test pure logic only — no network calls, no file I/O unless using tmp_path fixtures.
- Mock external dependencies (`anthropic`, `playwright`) at the boundary, not deep inside.
- Use `pytest.fixture` for shared setup. Keep fixtures in the same file or `tests/conftest.py`.

## What to test
- Happy path for each public function.
- Edge cases that actually occur (empty input, missing env var, malformed LLM response).
- Do not test implementation internals — test observable behaviour.

## What not to test
- Private helpers (`_prefixed` functions) unless they contain complex logic.
- Third-party library behaviour.
- The CLI argument parser in isolation — test the command outcome instead.

## Playwright (e2e)
- E2e tests live in `tests/e2e/` and are tagged `@pytest.mark.e2e`.
- They require `session/auth.json` to exist — skip gracefully if it does not.
- E2e tests must never publish. Assert that the draft URL contains `/drafts/`.
