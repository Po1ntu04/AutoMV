#!/usr/bin/env python3
"""Run the phase-1 scaffold checks end to end."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> None:
    print("+ " + " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    py = sys.executable

    run(
        [
            py,
            "emergency_contact_mv/scripts/00_probe_audio.py",
            "--audio",
            "emergency_contact_mv/input/song.mp3",
            "--out",
            "emergency_contact_mv/work/00_audio_probe/audio_probe.json",
        ],
        root,
    )
    run(
        [
            py,
            "emergency_contact_mv/scripts/01_prepare_timeline_template.py",
            "--lyrics",
            "emergency_contact_mv/input/lyrics_verified.txt",
            "--out",
            "emergency_contact_mv/work/03_lyrics_timeline/lyrics_timeline_template.json",
        ],
        root,
    )
    run([py, "emergency_contact_mv/scripts/02_validate_project.py", "--root", "."], root)
    run([py, "emergency_contact_mv/scripts/03_write_phase_report.py", "--root", "."], root)


if __name__ == "__main__":
    main()
