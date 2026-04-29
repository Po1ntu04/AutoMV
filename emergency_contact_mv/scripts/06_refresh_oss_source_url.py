#!/usr/bin/env python3
"""Refresh SOURCE_AUDIO_URL with a short-lived OSS signed URL."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import time
from pathlib import Path
from urllib.parse import quote, urlencode


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def merge_env(root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for path in [root / ".env", root / "emergency_contact_mv" / ".env"]:
        values.update(load_env_file(path))
    return values


def first_env(env: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = env.get(key, "").strip()
        if value:
            return value
    return ""


def infer_object_key(root: Path, env: dict[str, str]) -> str:
    for key in ["SOURCE_AUDIO_OBJECT_KEY", "SOURCE_AUDIO_OSS_OBJECT_KEY", "OSS_SOURCE_AUDIO_OBJECT_KEY"]:
        value = env.get(key, "").strip()
        if value:
            return value
    candidates = sorted((root / "emergency_contact_mv" / "input").glob("*.mp3"))
    if len(candidates) == 1:
        return candidates[0].name
    source_path = env.get("SOURCE_AUDIO_PATH", "").strip()
    if source_path:
        return Path(source_path).name
    raise RuntimeError("Set SOURCE_AUDIO_OBJECT_KEY or keep exactly one mp3 in emergency_contact_mv/input/")


def signed_oss_url(env: dict[str, str], object_key: str, expires: int) -> str:
    bucket = first_env(env, "ALIYUN_OSS_BUCKET", "ALIYUN_OSS_BUCKET_NAME", "OSS_BUCKET", "OSS_BUCKET_NAME")
    endpoint = env.get("ALIYUN_OSS_ENDPOINT", "").strip()
    access_key_id = env.get("ALIYUN_OSS_ACCESS_KEY_ID", "").strip()
    access_key_secret = env.get("ALIYUN_OSS_ACCESS_KEY_SECRET", "").strip()
    missing = [
        name
        for name, value in [
            ("ALIYUN_OSS_BUCKET", bucket),
            ("ALIYUN_OSS_ENDPOINT", endpoint),
            ("ALIYUN_OSS_ACCESS_KEY_ID", access_key_id),
            ("ALIYUN_OSS_ACCESS_KEY_SECRET", access_key_secret),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError("Missing env keys: " + ", ".join(missing))
    endpoint = endpoint.replace("https://", "").replace("http://", "").rstrip("/")
    canonical_resource = f"/{bucket}/{object_key}"
    string_to_sign = f"GET\n\n\n{expires}\n{canonical_resource}"
    digest = hmac.new(access_key_secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha1).digest()
    signature = base64.b64encode(digest).decode("ascii")
    query = urlencode({"Expires": str(expires), "OSSAccessKeyId": access_key_id, "Signature": signature})
    return f"https://{bucket}.{endpoint}/{quote(object_key, safe='/')}?{query}"


def upsert_env_value(path: Path, key: str, value: str) -> bool:
    if not path.exists():
        return False
    lines = path.read_text(encoding="utf-8").splitlines()
    output: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith(f"{key}="):
            output.append(f"{key}={value}")
            replaced = True
        else:
            output.append(line)
    if not replaced:
        output.append(f"{key}={value}")
    path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--object-key", default="")
    parser.add_argument("--expires-hours", type=float, default=12.0)
    args = parser.parse_args()

    root = args.root.resolve()
    env = merge_env(root)
    object_key = args.object_key or infer_object_key(root, env)
    expires = int(time.time() + args.expires_hours * 3600)
    url = signed_oss_url(env, object_key, expires)
    updated = [
        str(path.relative_to(root))
        for path in [root / ".env", root / "emergency_contact_mv" / ".env"]
        if upsert_env_value(path, "SOURCE_AUDIO_URL", url)
    ]
    print(
        json.dumps(
            {
                "source_audio_url_refreshed": True,
                "updated_files": updated,
                "object_key": object_key,
                "expires_unix": expires,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
