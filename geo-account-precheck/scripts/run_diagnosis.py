#!/usr/bin/env python3
"""Compatibility alias: run a GEO diagnostic with the same interface as run_diagnostic."""

from __future__ import annotations

import subprocess
import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    import run_diagnostic

    return run_diagnostic.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
