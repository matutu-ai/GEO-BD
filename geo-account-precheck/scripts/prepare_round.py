#!/usr/bin/env python3
"""Prepare the next-round input from a previous diagnostic report.

Only static company facts are copied.  AI observations, competitors, Evidence
and metrics are cleared so the next run never inherits old detection numbers.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMPANY_KEYS = [
    "name",
    "aliases",
    "brands",
    "business",
    "industry",
    "products",
    "services",
    "customers",
    "cases",
    "locations",
    "founders",
    "experts",
    "certificates",
    "patents",
    "media",
    "website",
    "contacts",
    "address",
    "phone",
    "social_accounts",
    "reviews",
    "third_party_profiles",
    "competitors",
    "negative_information",
]


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("JSON must be an object")
    return data


def extract_company(report: dict[str, Any]) -> dict[str, Any]:
    company = report.get("company") or {}
    raw = company.get("raw")
    if isinstance(raw, dict) and raw:
        return {key: copy.deepcopy(raw[key]) for key in COMPANY_KEYS if key in raw}

    entity = report.get("entity") or {}
    fields = entity.get("fields") or {}
    result: dict[str, Any] = {}
    for key in COMPANY_KEYS:
        if company.get(key) not in (None, "", []):
            result[key] = copy.deepcopy(company[key])
            continue
        values = [
            item.get("value")
            for item in fields.get(key, [])
            if item.get("status") != "UNKNOWN" and item.get("value")
        ]
        if values:
            result[key] = values
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from",
        dest="source",
        required=True,
        type=Path,
        help="Path to a previous reports/diagnostic.json.",
    )
    parser.add_argument("--out", required=True, type=Path, help="Path to write the next-round input JSON.")
    args = parser.parse_args(argv)

    report = load_json(args.source)
    template = load_json(ROOT / "inputs" / "diagnostic-template.json")
    company = extract_company(report)
    entity = report.get("entity") or {}
    issues = (report.get("company") or {}).get("issues") or []

    template["company"] = company
    template["materials"] = copy.deepcopy(entity.get("raw_materials") or [])
    template["issues"] = copy.deepcopy(issues if isinstance(issues, list) else [])
    template["ai_observations"] = []
    template["competitors"] = []
    template["evidence"] = []
    template["current_metrics"] = {}
    template["validation"] = {}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    name = company.get("name") or "UNKNOWN"
    print(f"PREPARED_ROUND: company={name}, observations/competitors/evidence cleared -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
