"""Command-line entry point."""
from __future__ import annotations

import argparse
import logging
import sys

from .agent import Agent
from .config import get_settings
from .models import WritingStyle


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="note-agent",
        description="Generate note.com drafts from text files in data/inbox/",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate articles but do not move inbox files or upload to note.com",
    )
    parser.add_argument(
        "--save-to-note",
        action="store_true",
        help="Upload generated drafts to note.com (requires session/auth.json)",
    )
    parser.add_argument(
        "--style",
        default="general",
        choices=[s.value for s in WritingStyle],
        help=(
            "Writing style / perspective: "
            "'general' = general audience, "
            "'quantamental' = investor + quant-fundamental analyst"
        ),
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )

    args = parser.parse_args(argv)

    settings = get_settings()
    _setup_logging(args.log_level or settings.log_level)

    agent = Agent(settings)
    drafts = agent.run(
        dry_run=args.dry_run,
        save_to_note=args.save_to_note,
        style=WritingStyle(args.style),
    )

    print(f"Done. {len(drafts)} draft(s) generated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
