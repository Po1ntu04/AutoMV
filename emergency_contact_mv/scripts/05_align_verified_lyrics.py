#!/usr/bin/env python3
"""Align verified lyric lines to ASR sentence and word timestamps."""

from __future__ import annotations

import argparse
import difflib
import json
import re
from dataclasses import dataclass
from pathlib import Path


PUNCT_RE = re.compile(r"[\s，。！？、；：,.!?;:'\"“”‘’（）()《》【】\[\]\-—_]+")

CHAR_MAP = str.maketrans(
    {
        "傳": "传",
        "來": "来",
        "語": "语",
        "屬": "属",
        "巔": "巅",
        "墜": "坠",
        "堕": "坠",
        "為": "为",
        "號": "号",
        "碼": "码",
        "刪": "删",
        "該": "该",
        "種": "种",
        "氓": "亡",
        "愛": "爱",
        "聯": "联",
        "繫": "系",
        "還": "还",
        "沒": "没",
        "絲": "丝",
        "傷": "伤",
        "異": "异",
        "斷": "断",
        "氣": "气",
        "問": "问",
        "趕": "赶",
        "機": "机",
        "歡": "欢",
        "無": "无",
        "後": "后",
        "煩": "烦",
        "覺": "觉",
        "長": "长",
        "責": "责",
        "駕": "驾",
        "馭": "驭",
        "離": "离",
        "騷": "骚",
        "擾": "扰",
        "兒": "儿",
        "誰": "谁",
        "絡": "络",
        "難": "难",
        "陣": "阵",
        "時": "时",
        "關": "关",
        "掛": "挂",
        "總": "总",
        "講": "讲",
        "帶": "带",
        "淚": "泪",
        "設": "设",
        "簡": "简",
        "單": "单",
        "僥": "侥",
        "倖": "幸",
        "禍": "祸",
        "須": "须",
        "記": "记",
        "棄": "弃",
        "現": "现",
        "實": "实",
        "夠": "够",
        "運": "运",
        "話": "话",
        "邊": "边",
        "變": "变",
        "應": "应",
        "於": "于",
        "別": "别",
        "惡": "恶",
        "劇": "剧",
        "頑": "顽",
        "給": "给",
        "喪": "丧",
        "牽": "牵",
        "伴": "绊",
        "他": "它",
    }
)

PHRASE_MAP = {
    "联系还是已在": "联系还是依在",
    "苦痛": "负痛",
    "关挂日子": "鳏寡日子",
    "长者责任驾驭": "将这责任加诸",
    "将这责任嫁祸": "将这责任加诸",
    "侥幸绊你": "牵绊你",
    "再深亦被嫌弃": "在生亦被嫌弃",
    "借位现实可想你": "借遗言说好想你",
    "常有幻想": "尚有幻想",
    "这我再剧真的": "这恶作剧真的",
    "再告别式": "在告别式",
}


@dataclass
class SentenceSpan:
    text: str
    norm: str
    tokens: list[dict]
    begin_time: int
    end_time: int


def normalize(text: str) -> str:
    value = PUNCT_RE.sub("", text.translate(CHAR_MAP)).lower()
    for source, target in PHRASE_MAP.items():
        value = value.replace(source, target)
    return value


def read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _fallback_char_tokens(sentence: dict, norm: str) -> list[dict]:
    begin = int(sentence.get("begin_time", 0))
    end = int(sentence.get("end_time", begin))
    span = max(end - begin, len(norm))
    return [
        {
            "text": char,
            "norm": char,
            "begin_time": begin + int(span * idx / len(norm)),
            "end_time": begin + int(span * (idx + 1) / len(norm)),
        }
        for idx, char in enumerate(norm)
    ]


def extract_sentences(asr: dict) -> list[SentenceSpan]:
    transcripts = asr.get("transcripts", [])
    if not transcripts:
        raise RuntimeError("ASR result has no transcripts")
    spans: list[SentenceSpan] = []
    for transcript in transcripts:
        for sentence in transcript.get("sentences", []):
            text = sentence.get("text", "")
            norm = normalize(text)
            if len(norm) < 2:
                continue
            tokens: list[dict] = []
            for word in sentence.get("words") or []:
                token_norm = normalize(word.get("text", ""))
                if not token_norm:
                    continue
                begin = int(word.get("begin_time", sentence.get("begin_time", 0)))
                end = int(word.get("end_time", begin))
                tokens.append(
                    {
                        "text": word.get("text", ""),
                        "norm": token_norm,
                        "begin_time": begin,
                        "end_time": end,
                    }
                )
            if not tokens:
                tokens = _fallback_char_tokens(sentence, norm)
            spans.append(
                SentenceSpan(
                    text=text,
                    norm=norm,
                    tokens=tokens,
                    begin_time=int(sentence.get("begin_time", tokens[0]["begin_time"])),
                    end_time=int(sentence.get("end_time", tokens[-1]["end_time"])),
                )
            )
    if not spans:
        raise RuntimeError("ASR result yielded no timestamped sentences")
    return spans


def build_char_stream(tokens: list[dict]) -> tuple[str, list[int]]:
    chars: list[str] = []
    char_to_token: list[int] = []
    for token_idx, token in enumerate(tokens):
        for char in token["norm"]:
            chars.append(char)
            char_to_token.append(token_idx)
    return "".join(chars), char_to_token


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    len_ratio = min(len(a), len(b)) / max(len(a), len(b))
    return ratio * 0.85 + len_ratio * 0.15


def best_fuzzy_span(target: str, source: str, cursor: int) -> tuple[int, int, float]:
    target_len = max(1, len(target))
    best = (cursor, min(len(source), cursor + target_len), 0.0)
    min_len = max(1, int(target_len * 0.55))
    max_len = max(min_len, int(target_len * 1.75))
    for start in range(cursor, len(source)):
        for length in range(min_len, max_len + 1):
            end = min(len(source), start + length)
            if end <= start:
                continue
            score = similarity(target, source[start:end])
            if score > best[2]:
                best = (start, end, score)
        if best[2] >= 0.96 and start > cursor + target_len:
            break
    return best


def sentence_group_plan(lines: list[str], sentences: list[SentenceSpan], max_group: int = 6) -> list[tuple[int, int, int, float]]:
    line_norms = [normalize(line) for line in lines]
    sentence_count = len(sentences)
    line_count = len(lines)
    neg = -10**9
    dp = [[neg] * (line_count + 1) for _ in range(sentence_count + 1)]
    back: list[list[tuple[int, int, int, float] | None]] = [[None] * (line_count + 1) for _ in range(sentence_count + 1)]
    dp[0][0] = 0.0
    for i, sentence in enumerate(sentences):
        for j in range(line_count + 1):
            if dp[i][j] <= neg / 2:
                continue
            if dp[i][j] > dp[i + 1][j]:
                dp[i + 1][j] = dp[i][j]
                back[i + 1][j] = (j, j, -1, 0.0)
            for group_size in range(1, min(max_group, line_count - j) + 1):
                group_text = "".join(line_norms[j : j + group_size])
                score = similarity(group_text, sentence.norm)
                # Mildly prefer natural lyric groups while allowing long ASR sentences.
                value = dp[i][j] + score * 100.0 - abs(len(group_text) - len(sentence.norm)) * 0.35 - max(0, group_size - 4) * 3.0
                if value > dp[i + 1][j + group_size]:
                    dp[i + 1][j + group_size] = value
                    back[i + 1][j + group_size] = (j, j + group_size, i, score)
    if back[sentence_count][line_count] is None:
        raise RuntimeError("Could not align all lyric lines to ASR sentences")
    plan: list[tuple[int, int, int, float]] = []
    i = sentence_count
    j = line_count
    while i > 0:
        prev = back[i][j]
        if prev is None:
            raise RuntimeError("Broken alignment backtrace")
        start_line, end_line, sentence_idx, score = prev
        if sentence_idx >= 0:
            plan.append((start_line, end_line, sentence_idx, score))
        j = start_line
        i -= 1
    return list(reversed(plan))


def time_from_chars(sentence: SentenceSpan, start_char: int, end_char: int) -> tuple[int, int, str]:
    source, char_to_token = build_char_stream(sentence.tokens)
    if not source:
        return sentence.begin_time, sentence.end_time, ""
    start_token = char_to_token[min(start_char, len(char_to_token) - 1)]
    end_token = char_to_token[max(min(end_char - 1, len(char_to_token) - 1), 0)]
    start_ms = sentence.tokens[start_token]["begin_time"]
    end_ms = sentence.tokens[end_token]["end_time"]
    if end_ms <= start_ms:
        end_ms = min(sentence.end_time, start_ms + 220)
    return start_ms, end_ms, source[start_char:end_char]


def split_sentence_group(lines: list[str], sentence: SentenceSpan, group_score: float, line_offset: int) -> list[dict]:
    source, _ = build_char_stream(sentence.tokens)
    line_norms = [normalize(line) for line in lines]
    total_weight = sum(max(1, len(norm)) for norm in line_norms)
    cursor = 0
    rows: list[dict] = []
    elapsed_weight = 0
    for local_idx, (line, target) in enumerate(zip(lines, line_norms), start=1):
        found = source.find(target, cursor) if target else -1
        if found >= 0:
            start_char = found
            end_char = found + len(target)
            confidence = 1.0
            method = "sentence_exact"
            start_ms, end_ms, matched = time_from_chars(sentence, start_char, end_char)
            cursor = max(cursor, end_char)
        else:
            start_char, end_char, confidence = best_fuzzy_span(target, source, cursor)
            if confidence >= 0.72:
                method = "sentence_fuzzy"
                start_ms, end_ms, matched = time_from_chars(sentence, start_char, end_char)
                cursor = max(cursor, end_char)
            else:
                method = "sentence_proportional"
                confidence = min(group_score, confidence)
                line_weight = max(1, len(target))
                group_duration = max(1, sentence.end_time - sentence.begin_time)
                start_ms = sentence.begin_time + int(group_duration * elapsed_weight / total_weight)
                end_ms = sentence.begin_time + int(group_duration * (elapsed_weight + line_weight) / total_weight)
                matched = sentence.norm
        elapsed_weight += max(1, len(target))
        rows.append(
            {
                "id": f"L{line_offset + local_idx:02d}",
                "start": round(start_ms / 1000.0, 2),
                "end": round(max(end_ms, start_ms + 180) / 1000.0, 2),
                "text_verified": line,
                "asr_match_text": matched,
                "match_method": method,
                "match_confidence": round(confidence, 3),
                "sentence_confidence": round(group_score, 3),
                "function": "manual_review_required",
                "emotion": "manual_review_required",
                "review_status": "needs_manual_review" if min(confidence, group_score) < 0.68 else "asr_aligned_needs_spot_check",
            }
        )
    return rows


def enforce_monotonic(rows: list[dict]) -> list[dict]:
    previous_end = 0.0
    for row in rows:
        start = max(float(row["start"]), previous_end)
        end = max(float(row["end"]), start + 0.18)
        row["start"] = round(start, 2)
        row["end"] = round(end, 2)
        previous_end = row["end"]
    return rows


def align(lines: list[str], sentences: list[SentenceSpan]) -> list[dict]:
    rows: list[dict] = []
    for start_line, end_line, sentence_idx, score in sentence_group_plan(lines, sentences):
        rows.extend(split_sentence_group(lines[start_line:end_line], sentences[sentence_idx], score, start_line))
    return enforce_monotonic(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asr", required=True, type=Path)
    parser.add_argument("--lines", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--target-start", type=float, default=122.7)
    parser.add_argument("--target-end", type=float, default=222.7)
    parser.add_argument("--target-out", type=Path, default=None)
    args = parser.parse_args()

    asr = json.loads(args.asr.read_text(encoding="utf-8"))
    lines = read_lines(args.lines)
    rows = align(lines, extract_sentences(asr))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.target_out:
        target_rows = [row for row in rows if row["end"] >= args.target_start and row["start"] <= args.target_end]
        args.target_out.parent.mkdir(parents=True, exist_ok=True)
        args.target_out.write_text(json.dumps(target_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"aligned_rows={len(rows)}")


if __name__ == "__main__":
    main()
