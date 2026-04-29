#!/usr/bin/env python3
"""Write a compact phase report from local probe artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


def load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", type=Path)
    parser.add_argument("--out", default=None, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.out or Path(f"emergency_contact_mv/docs/progress/phase1_{date.today().isoformat()}.md")

    audio_probe = load_json(root / "emergency_contact_mv/work/00_audio_probe/audio_probe.json")
    validation = load_json(root / "emergency_contact_mv/work/00_audio_probe/phase1_validation.json")
    timeline = load_json(root / "emergency_contact_mv/work/03_lyrics_timeline/lyrics_timeline_template.json")
    timeline_count = len(timeline) if isinstance(timeline, list) else 0

    lines = [
        "# Phase 1 Report: Engineering Scaffold",
        "",
        "## Completed",
        "- Added project scaffold for the Emergency Contact MV workflow.",
        "- Imported runtime source files into ignored input/work directories on the remote host.",
        "- Probed the source audio with ffprobe.",
        "- Created a rough lyric timeline template for manual alignment.",
        "- Added dry-run validation; no paid image or video generation was triggered.",
        "",
        "## Evidence",
        f"- Audio probe: `{json.dumps(audio_probe, ensure_ascii=False) if audio_probe else 'missing'}`",
        f"- Timeline template rows: {timeline_count}",
        f"- Validation: `{json.dumps(validation, ensure_ascii=False) if validation else 'missing'}`",
        "",
        "## Risks",
        "- The lyric timeline is a rough template and must be manually aligned before shot generation.",
        "- Existing repository history already tracks large media under `result/1`; phase 1 prevents new media commits but does not rewrite history.",
        "- A hard-coded Volcano AK/SK was present in the original lip-sync helper; this phase removes it from the working tree, but the credential should still be rotated.",
        "",
        "## User Tasks",
        "- Fill `emergency_contact_mv/.env` on b101 when live API tests are needed.",
        "- Manually review `work/03_lyrics_timeline/lyrics_timeline_template.json` before ASR alignment is treated as authoritative.",
        "- Rotate any exposed Volcano credentials that were previously committed.",
        "",
        "## ChatGPT/Web Tasks",
        "- Later phases can use web ChatGPT or image tools for character reference exploration.",
        "- No image-generation task is required for phase 1.",
        "",
        "## Next Phase",
        "- Build ASR/lyrics alignment and manually reviewed `lyrics_timeline.json`.",
        "- Produce the first complete `shots.json` from the locked timeline and style bible.",
    ]
    target = root / out
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
