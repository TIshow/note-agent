"""LLM-based article generator. Calls Anthropic API, returns ArticleDraft."""

from __future__ import annotations

import logging
from pathlib import Path

import anthropic

from .models import ArticleDraft, DraftStatus, InputDocument, WritingStyle

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

_STYLE_PROMPT_FILES: dict[WritingStyle, str] = {
    WritingStyle.general: "style_general.txt",
    WritingStyle.quantamental: "style_quantamental.txt",
}


def _load_system_prompt(style: WritingStyle) -> str:
    prompt_file = _PROMPTS_DIR / _STYLE_PROMPT_FILES[style]
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_file}")
    return prompt_file.read_text(encoding="utf-8").strip()


def _parse_response(text: str, source_path: Path, style: WritingStyle) -> ArticleDraft:
    """Parse LLM output into an ArticleDraft. Raises ValueError on bad format."""
    lines = text.strip().splitlines()
    title_line = next((line for line in lines if line.startswith("TITLE:")), None)
    if not title_line:
        raise ValueError("LLM response missing TITLE: line")

    title = title_line.removeprefix("TITLE:").strip()
    sep_idx = next((i for i, line in enumerate(lines) if line.strip() == "---"), None)
    body = "\n".join(lines[sep_idx + 1 :]).strip() if sep_idx is not None else ""

    return ArticleDraft(title=title, body=body, source_path=source_path, style=style)


class ArticleGenerator:
    def __init__(self, client: anthropic.Anthropic, model: str = "claude-opus-4-6") -> None:
        self._client = client
        self._model = model

    def generate(self, doc: InputDocument) -> ArticleDraft:
        """Generate a draft from an InputDocument using the document's writing style.

        Raises on API error or missing prompt template.
        """
        logger.info("Generating draft for %s (style=%s)", doc.path.name, doc.style.value)
        system_prompt = _load_system_prompt(doc.style)
        try:
            message = self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": doc.content}],
            )
            raw = message.content[0].text  # type: ignore[union-attr]
            draft = _parse_response(raw, doc.path, doc.style)
            draft.status = DraftStatus.generated
            return draft
        except anthropic.APIError as e:
            logger.error("Anthropic API error for %s: %s", doc.path.name, e)
            raise
