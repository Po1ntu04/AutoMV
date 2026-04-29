# Operations Review - 2026-04-30

This note records reusable approval policy and execution lessons from the
Emergency Contact MV setup, ASR, timeline calibration, and character bank stages.

## Self-Approval Policy

The user granted broad approval for SSH operations on b101. For future project
work, the assistant should self-approve the following without asking again,
provided the action is scoped to:

```text
/data1/yuzhixiang/work/music2mv/AutoMV
```

Approved by pattern:

- SSH read-only inspection: `git status`, `git log`, `git diff`, `find`,
  `sed`, `python` readers, `ffprobe`, `ls`, `du`, `grep`/`rg`.
- SSH project writes that create or update tracked source/config/docs/scripts in
  the AutoMV repository.
- Writes to ignored project work areas such as `.env`, `emergency_contact_mv/.env`,
  `emergency_contact_mv/work/`, `emergency_contact_mv/input/`, and generated
  local review clips.
- `scp` of project scripts, docs, configs, prompts, and reports from the local
  Codex workspace into the b101 AutoMV project.
- Running project-local validation, ASR, timeline alignment, manual timeline
  override scripts, JSON validation, `py_compile`, `ffmpeg` clip extraction, and
  one-byte OSS access probes.
- Git staging, committing, fetching, and pushing intended AutoMV phase commits.
- One-shot GitHub authenticated push when ordinary `origin` push cannot prompt
  for credentials, followed by verification that `origin` remains the normal
  repository URL.
- DashScope ASR calls and OSS signed URL refreshes using already configured
  environment variables.

Still ask or stop for review when:

- The action is destructive outside project-generated temporary files, for
  example recursive deletion, reset, checkout overwrite, or force push.
- The action would commit `.env`, media files, signed URLs, API keys, raw PATs,
  ASR provider URLs, or other secrets.
- The action would enable paid bulk image/video generation beyond the current
  phase settings.
- The action changes repository history already pushed to GitHub.
- The action publishes generated media externally or changes licensing/privacy
  exposure.
- The command writes outside the AutoMV project tree and is not clearly limited
  to a temporary transfer path.

## Error Ledger

### SSH Key Access From Local Sandbox

Symptom:

- Local non-escalated SSH timed out and reported that the private key path was
  not accessible.

Cause:

- The local sandbox could not read the Windows SSH key path.

Updated method:

- Use escalated `ssh`/`scp` for b101 operations that require the local private
  key. Keep commands project-scoped and state the purpose briefly.

### User Signed OSS URL Returned 403

Symptom:

- DashScope ASR failed with `FILE_403_FORBIDDEN`.
- Direct remote probe of the supplied signed URL also returned 403.

Cause:

- The supplied signed URL was not currently usable by b101/DashScope.

Updated method:

- Generate a fresh short-lived OSS signed URL from configured OSS credentials.
- Write the result only to ignored `.env` files.
- Do not print the signed URL in logs or reports.

### OSS Object Name Was Not The Local Filename

Symptom:

- The refresh script inferred `song.mp3`, but the actual OSS object was the
  original Chinese filename. The refreshed URL still failed.

Cause:

- The b101 local input filename and OSS object key differed.

Updated method:

- Prefer explicit `SOURCE_AUDIO_OBJECT_KEY`.
- Keep the object key in ignored `.env` files when local and OSS names differ.
- Treat `SOURCE_AUDIO_PATH` as a local path, not as an OSS object name.

### OSS Bucket Env Alias Mismatch

Symptom:

- The refresh script expected `ALIYUN_OSS_BUCKET`; the environment used
  `ALIYUN_OSS_BUCKET_NAME`.

Cause:

- Different naming conventions across project code and user-provided env.

Updated method:

- Support aliases such as `ALIYUN_OSS_BUCKET_NAME`, `OSS_BUCKET`, and
  `OSS_BUCKET_NAME`.
- For env validation, report presence/absence only, never values.

### HEAD Probe Failed For A GET-Signed URL

Symptom:

- A signed URL generated for `GET` returned 403 when verified with `HEAD`.

Cause:

- OSS signatures include the HTTP method, so `HEAD` does not validate a URL
  signed for `GET`.

Updated method:

- Verify GET-signed URLs with a one-byte ranged `GET` request.
- Report only status, byte count, and content-range presence.

### PowerShell And Remote Here-Doc Quoting

Symptom:

- A nested PowerShell/SSH/Python here-doc failed with quoting and syntax errors.

Cause:

- Mixed Windows PowerShell quoting, remote shell quoting, Chinese text, and
  embedded Python string delimiters were brittle.

Updated method:

- Prefer local `apply_patch` plus `scp` for substantial file edits.
- For remote one-off Python, keep strings simple and avoid nested f-string quote
  conflicts.
- Validate transferred scripts with `python3 -m py_compile`.

### Naive ASR Character Matching Produced Poor Timeline

Symptom:

- Initial alignment had many `needs_manual_review` rows and the target 100s
  window was effectively shifted to the end.

Cause:

- Full-song greedy character matching was too fragile for Cantonese ASR text,
  simplified verified lyrics, paraphrase-like ASR substitutions, and long ASR
  sentence spans.

Updated method:

- Align ASR sentences to consecutive verified lyric groups with monotonic
  dynamic programming.
- Split sentence groups into line-level timing by exact, fuzzy, or proportional
  methods.
- Preserve `match_method`, `match_confidence`, `sentence_confidence`, and
  `review_status` for audit.
- Use a manual override file for confirmed listening corrections.

### ASR Still Needs Human Listening For Musically Ambiguous Lines

Symptom:

- L05 and L42 were audibly offset even after the improved alignment.

Cause:

- ASR word timing can be coarse around held notes, compressed syllables, or
  phrase splits that differ from the verified lyric line breaks.

Updated method:

- Keep human listening as the final authority for low-confidence or musically
  ambiguous lines.
- Store corrections in `configs/timeline_manual_overrides.json`.
- Reapply with `scripts/07_apply_timeline_overrides.py` after any ASR rerun.

### Ordinary HTTPS Git Push Could Not Prompt

Symptom:

- `git push origin main` failed because it could not read a GitHub username in
  the non-interactive SSH session.

Cause:

- b101 had no persistent interactive GitHub credential available.

Updated method:

- Use a one-shot authenticated push only for the current command.
- Immediately verify:
  - `git remote get-url origin` is still the normal GitHub URL.
  - `git fetch origin main` updates `origin/main`.
  - local `HEAD`, `origin/main`, and GitHub `main` match.

### Tracking Branch Looked Stale After Successful Push

Symptom:

- After a direct push, local `origin/main` still pointed at the previous commit.

Cause:

- The direct push updated GitHub, but the local remote-tracking ref was not
  fetched.

Updated method:

- Run `git fetch origin main` after push before final status reporting.

## Standard Phase Closeout Checklist

Before reporting a phase complete:

- Run syntax/format validators relevant to changed files.
- Run `git diff --check`.
- Inspect `git status --short`.
- Review `git diff --stat` and staged names before commit.
- Scan tracked files for PATs, signed URLs, API keys, and env values.
- Verify ignored work products exist when they are part of the phase output.
- Commit with a phase-specific message.
- Push, fetch, and confirm `HEAD`, `origin/main`, and GitHub `main` align.
- Summarize what the user must review separately from what the assistant can do
  next.
