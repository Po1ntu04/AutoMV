# Emergency Contact MV Workflow

This directory contains the project-specific scaffold for the 100-second
director version of `Emergency Contact`.

The workflow intentionally treats AutoMV as a reusable reference architecture,
not as a one-click pipeline. Lip-sync, singer performance, generated subtitles,
and generated phone UI are disabled by default.

## Phase 1 Scope

- Create a reproducible project structure.
- Import source song and verified lyrics into ignored runtime directories.
- Probe audio with `ffprobe`.
- Create a rough lyric timeline template for manual alignment.
- Add configuration, style bible, character bank, backend policy, verifier rubric,
  and dry-run validation.
- Do not call paid image or video generation APIs.

## Directory Contract

```text
emergency_contact_mv/
  input/       ignored; source mp3, verified lyrics, planning notes
  configs/     committed; project configuration and schema
  scripts/     committed; reproducible phase scripts
  work/        ignored; generated probes, timelines, ASR, candidates
  outputs/     ignored; review sheets, rough cuts, final exports
  docs/        committed; phase reports and operator notes
```


## Environment

Real credentials live in ignored files:

- `.env` for the original AutoMV `config.py` loader.
- `emergency_contact_mv/.env` for this project scaffold.

The committed `.env.example` must remain a placeholder-only template. With the
currently available keys, phase 2 should prefer DashScope for planning, ASR,
image/video, Qwen-VL verification, and use Huoshan/Seedance only as an optional
video fallback. OpenAI and Doubao stay disabled until their keys are available.

## Run Phase 1

```bash
python emergency_contact_mv/scripts/run_phase1.py --root .
```

Phase 1 is successful when the script writes:

- `emergency_contact_mv/work/00_audio_probe/audio_probe.json`
- `emergency_contact_mv/work/03_lyrics_timeline/lyrics_timeline_template.json`
- `emergency_contact_mv/work/00_audio_probe/phase1_validation.json`
- `emergency_contact_mv/docs/progress/phase1_YYYY-MM-DD.md`
