"""Offline and service commands."""

import argparse
import json
import sys
from pathlib import Path

from .corpus import ROOT, entries_of, load_corpus


def main():
    parser = argparse.ArgumentParser(prog="tuus", description="Telechronistic micro-utterance synthesis.")
    parser.add_argument("--root", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "build", "coverage"):
        commands.add_parser(name)
    evaluation = commands.add_parser("evaluate")
    evaluation.add_argument("--generate-only", action="store_true")
    evaluation.add_argument("--reviewed", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            corpora = load_corpus(args.root)
            print(f"Validated {len(entries_of(corpora))} entries in {len(corpora)} kairolexica; zero errors.")
        elif args.command == "build":
            from .offline import build
            print(f"Prepared {build(args.root)} semantic embeddings.")
        elif args.command == "coverage":
            from .offline import coverage
            report = coverage(args.root)
            print(json.dumps({"entries": report["entry_count"], "gaps": report["gaps"],
                              "thin_years": report["thin_years"]}))
        elif args.command == "evaluate":
            from .evaluation import evaluate
            evaluate(args.root, generate_only=args.generate_only, reviewed=args.reviewed)
    except (ValueError, FileNotFoundError) as error:
        print(f"Validation failure: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
