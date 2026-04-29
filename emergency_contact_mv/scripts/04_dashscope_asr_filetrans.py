#!/usr/bin/env python3
"""Run DashScope Qwen-ASR file transcription for the source song."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def request_json(url: str, headers: dict[str, str], payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="GET" if data is None else "POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body}") from exc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", type=Path)
    parser.add_argument("--audio-url", default=None)
    parser.add_argument("--out-dir", default="emergency_contact_mv/work/02_asr", type=Path)
    parser.add_argument("--model", default=None)
    parser.add_argument("--language", default="yue")
    parser.add_argument("--poll-seconds", type=float, default=5.0)
    parser.add_argument("--timeout-seconds", type=float, default=900.0)
    parser.add_argument("--no-submit", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    load_env_file(root / ".env")
    load_env_file(root / "emergency_contact_mv/.env")

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not set")
    audio_url = args.audio_url or os.getenv("SOURCE_AUDIO_URL")
    if not audio_url:
        raise RuntimeError("SOURCE_AUDIO_URL is not set")
    model = args.model or os.getenv("ASR_FILETRANS_MODEL") or "qwen3-asr-flash-filetrans"

    out_dir = root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    submit_path = out_dir / "dashscope_asr_submit.json"
    poll_path = out_dir / "dashscope_asr_task.json"
    result_path = out_dir / "dashscope_asr_result.json"

    if args.no_submit:
        print("no_submit=true")
        return

    base_url = os.getenv("DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/api/v1")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    payload = {
        "model": model,
        "input": {"file_url": audio_url},
        "parameters": {
            "channel_id": [0],
            "language": args.language,
            "enable_itn": False,
            "enable_words": True,
        },
    }
    submit = request_json(f"{base_url}/services/audio/asr/transcription", headers, payload)
    submit_path.write_text(json.dumps(submit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    task_id = submit.get("output", {}).get("task_id")
    if not task_id:
        raise RuntimeError(f"No task_id in submit response: {submit}")

    deadline = time.time() + args.timeout_seconds
    last = submit
    while time.time() < deadline:
        task = request_json(f"{base_url}/tasks/{task_id}", headers)
        poll_path.write_text(json.dumps(task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        status = task.get("output", {}).get("task_status")
        print(f"task_id={task_id} status={status}")
        last = task
        if status == "SUCCEEDED":
            transcription_url = task.get("output", {}).get("result", {}).get("transcription_url")
            if not transcription_url:
                raise RuntimeError(f"No transcription_url in task response: {task}")
            result = request_json(transcription_url, {})
            result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(result_path)
            return
        if status in {"FAILED", "UNKNOWN"}:
            raise RuntimeError(json.dumps(task, ensure_ascii=False, indent=2))
        time.sleep(args.poll_seconds)

    raise TimeoutError(json.dumps(last, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
