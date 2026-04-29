#!/usr/bin/env python3
"""Probe the source audio without making generation API calls."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def run_ffprobe(audio: Path) -> dict:
    if not shutil.which("ffprobe"):
        raise RuntimeError("ffprobe is not available on PATH")
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(audio),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
    return {
        "source": str(audio),
        "duration": float(data.get("format", {}).get("duration", 0.0)),
        "format_name": data.get("format", {}).get("format_name"),
        "bit_rate": data.get("format", {}).get("bit_rate"),
        "codec_name": audio_stream.get("codec_name"),
        "sample_rate": int(audio_stream.get("sample_rate", 0) or 0),
        "channels": audio_stream.get("channels"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    if not args.audio.exists():
        raise FileNotFoundError(args.audio)
    probe = run_ffprobe(args.audio)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(probe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(probe, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
