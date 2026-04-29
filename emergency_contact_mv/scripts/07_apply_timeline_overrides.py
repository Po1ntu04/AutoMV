#!/usr/bin/env python3
"""Apply manual listening overrides to lyric timeline JSON files."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def apply_overrides(rows: list[dict], override_doc: dict) -> tuple[list[dict], list[str]]:
    overrides = {item["id"]: item for item in override_doc.get("overrides", [])}
    applied: list[str] = []
    output = deepcopy(rows)
    for row in output:
        override = overrides.get(row.get("id"))
        if not override:
            continue
        row["manual_override"] = {
            "source": override_doc.get("source", "manual listening correction"),
            "start_original": row.get("start"),
            "end_original": row.get("end"),
            "reason": override.get("reason", ""),
        }
        row["asr_match_method"] = row.get("match_method")
        row["start"] = round(float(override["start"]), 2)
        row["end"] = round(float(override["end"]), 2)
        row["match_method"] = "manual_listening_override"
        row["match_confidence"] = 1.0
        row["review_status"] = override.get("review_status", "manual_corrected")
        applied.append(row["id"])
    previous_end = 0.0
    for row in output:
        start = float(row["start"])
        end = float(row["end"])
        if start < previous_end:
            row.setdefault("timeline_warnings", []).append(
                f"start {start:.2f}s is before previous end {previous_end:.2f}s"
            )
        if end <= start:
            row.setdefault("timeline_warnings", []).append("end is not after start")
        previous_end = max(previous_end, end)
    return output, applied


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overrides", type=Path, default=Path("emergency_contact_mv/configs/timeline_manual_overrides.json"))
    parser.add_argument("--full", type=Path, default=Path("emergency_contact_mv/work/03_lyrics_timeline/lyrics_timeline_full.json"))
    parser.add_argument("--target", type=Path, default=Path("emergency_contact_mv/work/03_lyrics_timeline/lyrics_timeline_100s.json"))
    args = parser.parse_args()

    override_doc = load_json(args.overrides)
    full_rows = load_json(args.full)
    full_rows, full_applied = apply_overrides(full_rows, override_doc)
    write_json(args.full, full_rows)

    target_rows = [row for row in full_rows if row["end"] >= 122.7 and row["start"] <= 222.7]
    write_json(args.target, target_rows)
    target_applied = [row["id"] for row in target_rows if row.get("manual_override")]

    print(json.dumps({"full_applied": full_applied, "target_applied": target_applied}, ensure_ascii=False))


if __name__ == "__main__":
    main()
