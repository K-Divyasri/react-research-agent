"""Run the research agent from the terminal.

    python -m research_agent "What causes coral bleaching?"
    python -m research_agent "..." --steps          # show the full reason/act trace
    python -m research_agent "..." --json            # machine-readable Report
    python -m research_agent "..." --max-reads 1     # watch reflection add a source
    python -m research_agent "..." --real            # use a real model + web search (needs keys)

Thin on purpose: parse args, call research(), print. All the real behaviour lives
in the library, which is what makes it testable without the command line.
"""

from __future__ import annotations

import argparse
import sys

from .agent import research


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="research_agent",
        description="A ReAct agent that answers a question with cited sources.",
    )
    p.add_argument("question", help="The research question, in quotes.")
    p.add_argument("--steps", action="store_true", help="Print the full reason/act/observe trace.")
    p.add_argument("--json", action="store_true", help="Print the Report as JSON.")
    p.add_argument("--max-reads", type=int, default=3, help="Sources to read before finishing (offline).")
    p.add_argument("--max-steps", type=int, default=8, help="Hard cap on loop turns.")
    p.add_argument("--no-reflect", action="store_true", help="Skip the self-critique pass.")
    p.add_argument("--real", action="store_true", help="Use a real LLM + web search (needs API keys).")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        report = research(
            args.question,
            real=args.real,
            max_steps=args.max_steps,
            max_reads=args.max_reads,
            reflect=not args.no_reflect,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(report.model_dump_json(indent=2))
        return 0

    if args.steps:
        print("Reasoning trace")
        print("-" * 60)
        for s in report.steps:
            arrow = f"{s.action}" + (f" {s.action_input}" if s.action_input else "")
            print(f"{s.n}. thought: {s.thought}")
            print(f"   action:  {arrow}")
            print(f"   observe: {s.observation}")
        print("-" * 60)
        print()

    print(report.format())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
