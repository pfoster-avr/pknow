Goal: Distill a long AI-agent session transcript down to a *minimal, correct, timeless*
summary — the durable facts a future reader actually needs — while throwing away the
crash-and-fix saga and operational noise that dominate the raw log.

This is a different job from [Summarize_convo_without_losing_too_much.md](prompts/Summarize_convo_without_losing_too_much.md):
that one preserves every turn in order at reduced detail (a lossy compaction). This one is
aggressive and *judgment-driven* — it keeps only what's worth remembering next time, in the
user's own framing, and drops everything else.

It is designed to write the body that follows a human-written `# Context` block (background,
goals, prior findings), but works standalone too — just apply it and let it produce the
summary. It has been reused on unrelated sessions simply by telling an agent
"apply this prompt as well as possible" to a new conversation, with excellent results.

There is a companion skill that wraps this prompt: [skills/minimal_timeless_summary/SKILL.md](skills/minimal_timeless_summary/SKILL.md).

---

# The prompt (2026 — the winning version after ~15 iterations)

```
You are writing the "# Conversation Summary" for an AI-agent session transcript, for the expert who ran it. You get the full transcript (a file) and a "# Context" block already written above it (their background, goals, prior findings) — do NOT repeat anything from Context.

Goal: a minimal, correct, timeless summary — only the durable facts a future reader needs, nothing transient. The session might be an engineering build, an experiment, a research dig, an ops/debugging effort, or an open-ended goal; adapt to whatever shape the work actually took rather than forcing it into a fixed template.

How to decide what goes in (do this — don't just summarize linearly):

1. Find the spine. Read what the USER cares about: their stated goals, the questions they keep returning to, the things they ask the agent to verify or compute, their motives for requests. The backbone of the summary is the plan(s) they designed, the work they requested, and the findings they pushed for — NOT the chronology of the agent's actions.

2. Harvest the load-bearing tokens. Pull out every exact identifier a reader would need to act again: project/task/experiment names, checkpoint or artifact names, flags, env vars, file/index/resource paths, and every number the user or agent computed (counts, hours, percentages, ratios, thresholds). These are the point of a timeless note — reproduce them verbatim, in the same words/format the log uses. Round long computed numbers the way the user wrote them; where the user is inconsistent, use judgement on how much precision is meaningful.

3. Apply the inclusion test to everything else. Keep a fact only if a future reader could NOT rediscover it naturally in the course of the same work. Keep: non-obvious gotchas, design decisions, hard-won identifiers, and surprising measured results. Drop: transient operations (monitoring, waiting, restarts for resource contention, pod/run names, commit hashes, image tags, full tracebacks, byte sizes) and routine bugfixes that any agent would hit and fix anyway while doing the task. When unsure whether something is a durable finding or operational debris, leave it out.

SHARP EXCLUSION RULE (this is the most common mistake — apply it ruthlessly): a working session is mostly a saga of crashes and fixes, and almost NONE of that belongs in a timeless note. Specifically, DROP entirely:
- The bug-fix narrative. Any error the agent diagnosed and patched just to make the work run (schema/pickle/compat mismatches, type/units fixes, dependency/worker/path resolution, etc.) is something a future runner would simply hit and fix again — it is NOT a durable finding. Do not list these bugs, their fixes, or their file locations.
- Build/deploy ephemera: image tags, commit hashes/SHAs, byte/GiB sizes, pod/workflow/run names, generated-file indices, cache file counts — mention these ONLY if the user themselves treated one as a point of interest.
Keep a "finding" ONLY if it is a fact about the requested work, the data, or the procedure that the user would want to KNOW next time and could not trivially rediscover — e.g. a measured result, a distribution, a required env var, a named knob/setting, or an identifier that took real effort (especially the user's) to pin down.

SYNTHESIS (don't just copy what's stated once): reconstruct, don't transcribe. If the user spawned variations on a task (branches, arms, retries, renamed attempts), collect the full roster of resulting identifiers — every distinct variant and the dimension it varies along — and present it in compact notation rather than narrating each one. Likewise, gather the measurements the user/agent deemed important into one place; when several are folds of the same quantity (optimized vs debug, before vs after, marginal vs joint), keep them in a parallel comparison structure. Give clear names to groupings — the user's name if they gave one, otherwise your own.

PREFER THE USER'S FINAL FRAMING: throughout the log the user repeatedly stops to standardize, rephrase, or correct numbers and concepts in their own words (re-deriving a quantity with their own labels, renaming a variant, restating what something "really is"). When the user has restated something, use THEIR final wording, labels, symbols, and rounding — not the agent's earlier or more verbose version. The agent's running commentary is scaffolding; the user's distilled statements are the signal.

Match the register and scale. Mirror the user's and agent's own phrasing for concepts and identifiers. Be terse — compact bullets, not prose; backtick all identifiers/flags/paths/names. Let length follow the durable content, not the transcript length: a short or repetitive session yields a short note, a long substantive one yields more — never pad to fill, never truncate real findings to be brief.

Output only the final summary body (no "# Conversation Summary" header).
```

## How to use it

1. Put the transcript on disk where the agent can read it (feed the path; large logs are fine — tell it to read in chunks if its tools cap read size).
2. Optionally write a short `# Context` block above where the summary will go (who the user is, the standing goal, prior findings). The prompt is built to *not* repeat Context, so anything you put there is subtracted from the output.
3. Apply the prompt (or invoke the companion skill). No per-conversation editing of the prompt is needed — it is deliberately domain-neutral.
4. Skim the result for the two things it's most likely to slip on (see below).

## Why this works (what earlier attempts got wrong)

The decisive lesson from iterating: **teach the model how to *judge* importance, don't hand it
the answer.** Early high-scoring versions worked only because they injected the expected
structure and numbers — useless on any other conversation. The winning prompt instead encodes
the reader's judgment as reusable rules:

- **Spine before chronology.** Anchoring on what the *user* kept pushing for (not the agent's
  action log) reliably surfaced the right backbone across very different session shapes.
- **The SHARP EXCLUSION RULE is the single biggest lever.** Left to itself, an agent reproduces
  the entire bug-fix saga, image tags, and byte counts — exactly the transient debris a timeless
  note must omit. Naming those classes explicitly and telling it to cut them ruthlessly dropped
  output length by ~20–25% and removed almost all the noise.
- **Synthesis over transcription.** "Reconstruct the full roster of variants in compact notation"
  produced a single coherent list of task/experiment identifiers instead of a launch-by-launch
  narration.
- **Prefer the user's final framing.** Users re-derive and rename things mid-session; taking their
  last distilled wording/labels/rounding (over the agent's earlier verbose version) matched a
  hand-written gold much more closely.

## Known imperfections / things to watch

- **Slightly over-includes borderline operational facts.** It sometimes keeps a "current state at
  session end" tail (last checkpoint numbers) or a minor digression the author would have cut.
  These are borderline judgment calls, not errors — trim by hand if you want it tighter.
- **Timing/measurement register can drift toward raw per-run anchors.** If the user gave a distilled
  figure or range for something noisy (e.g. "~0.5–0.9h"), make sure the summary used *that* rather
  than a table of individual run readings. A later revision added an explicit instruction for this;
  spot-check it.
- **Unreachable facts stay unreachable.** Anything true only in the author's head and never stated in
  the transcript won't appear — correctly. Don't grade the summary down for omitting knowledge the
  log never contained.
