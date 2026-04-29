#!/usr/bin/env python3
"""Validate phase-1 scaffold without paid generation."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


REQUIRED_CONFIGS = [
    "emergency_contact_mv/configs/emergency_contact_100s.yaml",
    "emergency_contact_mv/configs/style_bible.yaml",
    "emergency_contact_mv/configs/character_bank.yaml",
    "emergency_contact_mv/configs/backend_policy.yaml",
    "emergency_contact_mv/configs/verifier_rubric.yaml",
    "emergency_contact_mv/configs/shot_schema.schema.json",
]


def command_exists(name: str) -> bool:
    try:
        subprocess.run([name, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except OSError:
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", type=Path)
    parser.add_argument("--out", default="emergency_contact_mv/work/00_audio_probe/phase1_validation.json", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()

    checks = {
        "configs_present": all((root / p).exists() for p in REQUIRED_CONFIGS),
        "env_example_present": (root / "emergency_contact_mv/.env.example").exists(),
        "song_present": (root / "emergency_contact_mv/input/song.mp3").exists(),
        "lyrics_present": (root / "emergency_contact_mv/input/lyrics_verified.txt").exists(),
        "ffmpeg_present": command_exists("ffmpeg"),
        "ffprobe_present": command_exists("ffprobe"),
        "live_api_default": False,
        "api_env_present": {
            "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
            "DASHSCOPE_API_KEY": bool(os.getenv("DASHSCOPE_API_KEY")),
            "ALIYUN_OSS_ACCESS_KEY_ID": bool(os.getenv("ALIYUN_OSS_ACCESS_KEY_ID")),
            "ALIYUN_OSS_BUCKET_NAME": bool(os.getenv("ALIYUN_OSS_BUCKET_NAME")),
        },
    }
    checks["ok"] = all(
        [
            checks["configs_present"],
            checks["env_example_present"],
            checks["song_present"],
            checks["lyrics_present"],
            checks["ffmpeg_present"],
            checks["ffprobe_present"],
        ]
    )
    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    if not checks["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
