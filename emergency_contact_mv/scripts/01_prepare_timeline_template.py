#!/usr/bin/env python3
"""Create a manually editable lyric timeline template from verified lyrics."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


KNOWN_PHRASES = [
    "传来法语",
    "问你 是我的家属吧",
    "原来我已 自那 白朗之巅堕下",
    "明明分开 为何打这号码",
    "你可会很不解 我怎不删了它",
    "我知不该 但是不改",
    "像某种流亡的爱",
    "千里之外 联系 还是 依在",
    "有没有一丝 半秒 伤悲",
    "要是我今晚 异地 断气",
    "问你可肯即夜 赶搭通宵客机",
    "有没有一丝 半秒 欢喜",
    "再无人以后 来烦住你",
    "若觉得 将这责任加诸 很离奇",
    "是我自私 今世最后 骚扰的人儿",
    "只想 是你",
    "必须 是你",
    "很想被念记 即使 淡淡 微微",
    "就算在生 亦被嫌弃",
    "都想借 遗言说 好想你",
    "可惜 最尾 未够 运气 一起",
    "话到嘴边打住 早变陌路人",
    "尚有幻想是大忌",
    "这号码应该 长眠于手机",
    "就算死 亦别 再骚扰你",
    "在告别式 给我带泪 奔丧的情人",
]


def split_lyrics(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text.strip())
    phrases = [phrase for phrase in KNOWN_PHRASES if phrase in normalized]
    if phrases:
        return phrases
    tokens = normalized.split()
    return [" ".join(tokens[i : i + 8]) for i in range(0, len(tokens), 8)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lyrics", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--start", type=float, default=122.7)
    parser.add_argument("--end", type=float, default=222.7)
    args = parser.parse_args()

    text = args.lyrics.read_text(encoding="utf-8")
    phrases = split_lyrics(text)
    if not phrases:
        raise RuntimeError("No lyric phrases found")
    span = args.end - args.start
    step = span / len(phrases)
    rows = []
    for idx, phrase in enumerate(phrases, start=1):
        start = args.start + (idx - 1) * step
        end = args.start + idx * step
        rows.append(
            {
                "id": f"L{idx:02d}",
                "start": round(start, 2),
                "end": round(end, 2),
                "text_verified": phrase,
                "function": "manual_review_required",
                "emotion": "manual_review_required",
                "review_status": "rough_template_not_aligned",
            }
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} rough lyric timeline rows to {args.out}")


if __name__ == "__main__":
    main()
