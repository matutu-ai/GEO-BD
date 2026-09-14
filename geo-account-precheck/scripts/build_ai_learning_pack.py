#!/usr/bin/env python3
"""Build a compact AI learning pack from an existing diagnostic.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.learning_pack import build_ai_learning_pack, render_ai_learning_pack  # noqa: E402


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("diagnostic JSON must be an object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Existing diagnostic.json.")
    parser.add_argument("--output", type=Path, help="Write compact Markdown for AI copy/paste.")
    parser.add_argument("--json", dest="json_output", type=Path, help="Write structured learning-pack JSON.")
    args = parser.parse_args(argv)

    pack = build_ai_learning_pack(_load(args.input))
    markdown = render_ai_learning_pack(pack)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown + "\n", encoding="utf-8")
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not args.output and not args.json_output:
        print(markdown)
    else:
        company = (pack.get("company_status") or {}).get("company_name") or "UNKNOWN"
        print(f"GEO_BD_SKILL_EXPORT: schema={pack.get('schema_version', 'UNKNOWN')} company={company}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
