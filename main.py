#!/usr/bin/env python3
"""Run GEO-BD V3 from the repository root."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
APP_ROOT = ROOT / "geo-account-precheck"
sys.path.insert(0, str(APP_ROOT))

from scripts.run_diagnostic import main as run_diagnostic  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=APP_ROOT / "tests" / "cases" / "case_001_tuoshi_ventilation" / "company.json",
        help="Client diagnostic JSON; defaults to the Golden Case.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "output",
        help="Output directory for the AI growth diagnosis artifacts.",
    )
    args = parser.parse_args(argv)
    return run_diagnostic(
        [
            "--input",
            str(args.input),
            "--offline",
            "--report-level",
            "all",
            "--output",
            str(args.output),
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
