# note.com adapter rules

## Absolute constraints
- **Never call any publish endpoint or click any publish button.**
- Drafts are saved via note.com's draft API or "Save as draft" UI action only.
- If a publish button is detected during automation, log a warning and abort the run.

## Browser session
- Auth state lives in `session/auth.json` (Playwright storageState format).
- Populate `session/auth.json` manually via `playwright codegen note.com` or a login script.
- Never automate the login flow with credentials in code. Load the session file instead.

## Selectors
- Prefer role-based selectors (`getByRole`, `getByLabel`) over CSS selectors.
- When CSS selectors are unavoidable, document why next to the selector.
- note.com updates its UI occasionally — isolate selectors in `NoteClient` so changes are local.

## Draft lifecycle
1. Navigate to the note.com editor.
2. Fill title and body from the generated markdown.
3. Click "下書き保存" (save draft). Do not proceed further.
4. Return the draft URL for logging.

## Rate limiting
- Add a minimum 2-second delay between browser actions.
- If a request fails with 429 or a CAPTCHA is detected, abort and log — do not retry in a loop.

## Markdown handling
- note.com accepts a subset of Markdown. Strip unsupported syntax before pasting.
- Keep a list of known-unsupported elements in `NoteClient` as a class constant.
