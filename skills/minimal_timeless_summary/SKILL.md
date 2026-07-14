---
name: minimal-timeless-summary
description: >-
  Distill a long AI-agent session transcript into a minimal, correct, timeless
  summary — the durable facts a future reader needs — while dropping the
  crash-and-fix saga and operational noise. Use whenever the user wants to
  summarize, distill, condense, or "save the important parts" of a
  conversation / session / transcript / log for keeping, to write the
  "Conversation Summary" that follows a Context block, or to "apply the timeless
  summary prompt" — even if they don't say the word "skill". Works on any
  session shape (build, experiment, research, ops/debugging, open-ended goal).
  NOT for a turn-by-turn or ordered replay that must preserve every message
  verbatim (that is a separate lossless-compaction prompt).
---

# Minimal Timeless Summary

Produce a **minimal, correct, timeless** summary of an AI-agent session transcript: only
the durable facts worth remembering next time, in the user's own framing, with the
transient debris cut. This is aggressive and judgment-driven — not a turn-by-turn replay.

The human-readable source and derivation notes for this prompt live at
[prompts/minimal_timeless_summary.md](../../prompts/minimal_timeless_summary.md). This SKILL
embeds the same prompt so it is self-contained if copied into an installed skills directory.

## Steps

1. Get the transcript path from the user. If it's large, read it in chunks — read the whole
   thing before writing anything.
2. If a `# Context` block (user background, standing goals, prior findings) exists above where
   the summary goes, read it and do **not** repeat its content. If none exists, just produce
   the summary.
3. Apply the instruction below verbatim to the transcript.
4. Output only the summary body (no `# Conversation Summary` header).
5. Skim for the two common slips: (a) over-kept operational tails (last checkpoint numbers,
   minor digressions) — trim; (b) noisy measurements shown as raw per-run anchors when the
   user gave a distilled figure/range — prefer the user's figure.

## Instruction (apply this to the transcript)

> You are writing the "# Conversation Summary" for an AI-agent session transcript, for the expert who ran it. You get the full transcript (a file) and a "# Context" block already written above it (their background, goals, prior findings) — do NOT repeat anything from Context.
>
> Goal: a minimal, correct, timeless summary — only the durable facts a future reader needs, nothing transient. The session might be an engineering build, an experiment, a research dig, an ops/debugging effort, or an open-ended goal; adapt to whatever shape the work actually took rather than forcing it into a fixed template.
>
> How to decide what goes in (do this — don't just summarize linearly):
>
> 1. Find the spine. Read what the USER cares about: their stated goals, the questions they keep returning to, the things they ask the agent to verify or compute, their motives for requests. The backbone of the summary is the plan(s) they designed, the work they requested, and the findings they pushed for — NOT the chronology of the agent's actions.
>
> 2. Harvest the load-bearing tokens. Pull out every exact identifier a reader would need to act again: project/task/experiment names, checkpoint or artifact names, flags, env vars, file/index/resource paths, and every number the user or agent computed (counts, hours, percentages, ratios, thresholds). These are the point of a timeless note — reproduce them verbatim, in the same words/format the log uses. Round long computed numbers the way the user wrote them; where the user is inconsistent, use judgement on how much precision is meaningful.
>
> 3. Apply the inclusion test to everything else. Keep a fact only if a future reader could NOT rediscover it naturally in the course of the same work. Keep: non-obvious gotchas, design decisions, hard-won identifiers, and surprising measured results. Drop: transient operations (monitoring, waiting, restarts for resource contention, pod/run names, commit hashes, image tags, full tracebacks, byte sizes) and routine bugfixes that any agent would hit and fix anyway while doing the task. When unsure whether something is a durable finding or operational debris, leave it out.
>
> SHARP EXCLUSION RULE (this is the most common mistake — apply it ruthlessly): a working session is mostly a saga of crashes and fixes, and almost NONE of that belongs in a timeless note. Specifically, DROP entirely:
> - The bug-fix narrative. Any error the agent diagnosed and patched just to make the work run (schema/pickle/compat mismatches, type/units fixes, dependency/worker/path resolution, etc.) is something a future runner would simply hit and fix again — it is NOT a durable finding. Do not list these bugs, their fixes, or their file locations.
> - Build/deploy ephemera: image tags, commit hashes/SHAs, byte/GiB sizes, pod/workflow/run names, generated-file indices, cache file counts — mention these ONLY if the user themselves treated one as a point of interest.
> Keep a "finding" ONLY if it is a fact about the requested work, the data, or the procedure that the user would want to KNOW next time and could not trivially rediscover — e.g. a measured result, a distribution, a required env var, a named knob/setting, or an identifier that took real effort (especially the user's) to pin down.
>
> SYNTHESIS (don't just copy what's stated once): reconstruct, don't transcribe. If the user spawned variations on a task (branches, arms, retries, renamed attempts), collect the full roster of resulting identifiers — every distinct variant and the dimension it varies along — and present it in compact notation rather than narrating each one. Likewise, gather the measurements the user/agent deemed important into one place; when several are folds of the same quantity (optimized vs debug, before vs after, marginal vs joint), keep them in a parallel comparison structure. Give clear names to groupings — the user's name if they gave one, otherwise your own.
>
> PREFER THE USER'S FINAL FRAMING: throughout the log the user repeatedly stops to standardize, rephrase, or correct numbers and concepts in their own words (re-deriving a quantity with their own labels, renaming a variant, restating what something "really is"). When the user has restated something, use THEIR final wording, labels, symbols, and rounding — not the agent's earlier or more verbose version. The agent's running commentary is scaffolding; the user's distilled statements are the signal.
>
> Match the register and scale. Mirror the user's and agent's own phrasing for concepts and identifiers. Be terse — compact bullets, not prose; backtick all identifiers/flags/paths/names. Let length follow the durable content, not the transcript length: a short or repetitive session yields a short note, a long substantive one yields more — never pad to fill, never truncate real findings to be brief.
>
> Output only the final summary body (no "# Conversation Summary" header).
