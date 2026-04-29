# Phase 2 Run Report - 2026-04-29

## Scope

- Ran full-song DashScope ASR for `Gareth.T - 紧急联络人.mp3`.
- Aligned 54 verified lyric lines to ASR timestamps.
- Exported a 100-second target timeline window for the current MV cut.

## Execution Notes

- The user-provided signed OSS URL returned HTTP 403 and DashScope reported
  `FILE_403_FORBIDDEN`.
- A fresh OSS signed URL was generated from configured OSS credentials and
  written only to ignored `.env` files.
- `SOURCE_AUDIO_OBJECT_KEY` was added to ignored `.env` files because the
  remote local filename differs from the OSS object filename.
- The refreshed URL was validated with a one-byte signed `GET` request.
- DashScope ASR task completed with `SUCCEEDED`.
- Alignment outputs are stored under ignored `emergency_contact_mv/work/`.

## Alignment Metrics

- Full timeline rows: 54.
- Full timeline range: 15.28s to 214.32s.
- Target window rows: 26.
- Target window range: 121.16s to 214.32s.
- Target window line ids: L29 to L54.
- Match methods: 35 `sentence_exact`, 15 `sentence_fuzzy`, 4 `sentence_proportional`.
- Manual review rows after improved alignment: 2.

## Review Items

- L05 uses proportional timing because ASR omits part of the verified lyric.
- L42 uses proportional timing because ASR differs semantically from the
  verified lyric while the surrounding sentence group is aligned.

## Next Stage Inputs

- Use `lyrics_timeline_100s.json` as the working timeline for shot planning.
- Treat rows with `review_status=needs_manual_review` as required manual checks
  before final video rendering.
- Keep API keys, signed URLs, source media, ASR JSON, and timeline JSON out of
  git unless an explicit artifact publication decision is made.
