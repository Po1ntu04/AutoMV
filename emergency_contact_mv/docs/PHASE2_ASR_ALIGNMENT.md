# Phase 2 ASR And Lyric Alignment

Phase 2 uses DashScope Qwen-ASR file transcription for the full source song and
then aligns locally verified lyric lines to ASR timestamps.

The ASR API call is intentionally separated from the alignment script:

```bash
python emergency_contact_mv/scripts/06_refresh_oss_source_url.py --root .
python emergency_contact_mv/scripts/04_dashscope_asr_filetrans.py --root .
python emergency_contact_mv/scripts/05_align_verified_lyrics.py \
  --asr emergency_contact_mv/work/02_asr/dashscope_asr_result.json \
  --lines emergency_contact_mv/work/03_lyrics_timeline/lyrics_lines_manual.txt \
  --out emergency_contact_mv/work/03_lyrics_timeline/lyrics_timeline_full.json \
  --target-out emergency_contact_mv/work/03_lyrics_timeline/lyrics_timeline_100s.json
```

`06_refresh_oss_source_url.py` signs the configured OSS source object and writes
the signed URL only to ignored `.env` files. It does not print the URL. Set
`SOURCE_AUDIO_OBJECT_KEY` when the OSS object name differs from the local input
filename.

The aligner uses monotonic dynamic programming to map ASR sentences to
consecutive verified lyric lines, then splits each sentence into line-level
timestamps with exact, fuzzy, or proportional matching. The result remains a
draft until manually reviewed. The aligner records `match_method`,
`match_confidence`, `sentence_confidence`, and `review_status` for each line.
