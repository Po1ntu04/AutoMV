# Phase 3 Character Bank Plan

## Decision

The next stage should lock the character bank before shot generation. This
prevents later image and video generations from drifting into different people,
especially for the ex-girlfriend.

The female lead is one person with several memory, fantasy, and emotional
states. She is not a set of separate appearances.

## Character Labels

- `Male_Hiker`: protagonist, mid-20s Hong Kong / East Asian male, dark graphite
  hiking shell, black base layer, dark hiking backpack, tired restrained eyes.
- `Ex_Emergency_Contact`: ex-girlfriend and imagined emergency contact,
  mid-20s Hong Kong / East Asian female, natural black hair, calm oval face,
  pale neutral clothing, mostly seen indirectly.

Machine-readable cards are stored in:

```text
emergency_contact_mv/character_bank/label.json
```

## 100-Second Female Variant Policy

Primary variants:

- `phone_contact_trace`: she exists in the phone and contact residue.
- `snow_rescue_fantasy`: she exists in snow, rescue light, and impossible arrival.
- `silent_judgement`: she exists as reflection, distance, and moral boundary.

Minimal variant:

- `memory_first_love`: only 1-2 fragments to prove the relationship was real.

Avoid or optional:

- `real_world_demystified`: not needed unless the ending explicitly releases the
  fantasy by showing that she has her own ordinary life.

## 100-Second Narrative Boundaries

- The French phone call should be a mental mechanism, not a confirmed real
  call to her.
- The Mont Blanc accident should be shown as traces, rescue light, rope, ice,
  and absence, not as a visible fall or disaster sequence.
- Old intimacy should appear only as residue: glass reflection, MTR exit,
  photo back, or unopened photograph.
- Her possible trip to him should be only a possibility fragment: airport
  glass, luggage wheel, gate light, or jet bridge.

## Generation Tasks

Codex / ChatGPT tasks:

- Keep `label.json` as the canonical character identity source.
- Generate reference prompts from the label cards.
- Build the 100-second shot plan using only the selected female variants.
- Add consistency checks for face shape, hair, clothing palette, and scene role.

User tasks:

- Pick final reference images for `Male_Hiker` and `Ex_Emergency_Contact`.
- Reject female candidates that look like a different person across variants.
- Confirm whether the 100-second cut should include any `memory_first_love`
  fragment, or keep her almost entirely as phone trace / snow fantasy /
  reflection.
