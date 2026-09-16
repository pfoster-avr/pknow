---
name: transcript-surgery
description: >
  Edit Claude Code agent memory by operating on session/subagent jsonl
  transcripts: transplant an agent's memory into a (sub)agent, transfer
  between models, remove a compaction boundary so memory crosses it, strip
  thinking blocks or tool results to extend experience span, splice in new
  memories, and estimate thinking-block token size despite encryption. Use
  when asked to copy/restore/merge agent memory, "revive" an agent with
  another's history, undo or soften compaction, or slim a transcript.
---

# Transcript Surgery

Recipes verified by experiment on 2026-09-16 (Claude Code v2.1.234, Fable 5).
All of them operate on jsonl transcript files while the target agent is
**cold** (its container/session stopped), then rely on the loader re-reading
the file on resume.

## Foundation: how the loader actually works

Get these wrong and edits are silently ignored:

1. **Transcripts are append-only.** Nothing is ever deleted by the harness;
   even compaction only appends. History you don't see in context is still
   in the file.
2. **Locations.** Main session: `~/.claude/projects/<proj>/<sessionId>.jsonl`.
   Subagents: `~/.claude/projects/<proj>/<sessionId>/subagents/agent-<id>.jsonl`
   plus `agent-<id>.meta.json` (holds `model`, agentType — the harness serves
   the model from here, never from transcript content). Task symlinks:
   `/tmp/claude-1000/<proj>/<sessionId>/tasks/<id>.output`.
3. **Line identity.** On every resume the loader re-reads the file but only
   accepts lines stamped with the target's `agentId` and `isSidechain: true`
   (subagents), then walks the `uuid`/`parentUuid` chain **backwards from the
   last matching line**. Unstamped or off-chain lines are silently skipped —
   this looks exactly like "my edit was ignored".
4. **Resolver visibility.** A subagent id resolves only if its transcript
   (and meta.json) sits under a session directory in the current session's
   lineage. "No transcript found" → copy the file+meta there.
5. **Thinking blocks are encrypted.** Stored as `thinking: ""` plus a base64
   `signature` blob; only the same model family can decrypt on reload.
   A different model gets blank thinking and **confabulates confidently**
   over the gap. Visible text always transfers.
6. **Warm shadows.** If the agent's container is still alive, in-context
   state can mask file edits; stop/delete the session (or agent container)
   first, edit, then resume.

## Operation: transplant memory into a (sub)agent

Give agent B the full memory (and, same-model, the identity — B will believe
it *is* A until shown outside evidence) of agent A:

```bash
jq -c '. + {agentId: "<B-id>", isSidechain: true}' A.jsonl > agent-<B-id>.jsonl
# place in a resolver-visible <sessionId>/subagents/ dir, keep/copy B's meta.json
# ensure the donor chain is the file TAIL (don't resume B between swap and test)
```

Then message/resume B. For a main session instead of a subagent, replace the
session jsonl wholesale (no stamping needed) and `claude --resume <id>` cold.

## Operation: cross-model transfer

Same as transplant, but the recipient's `meta.json` `model` differs from the
donor's. Visible history and identity transfer; **encrypted thinking does
not** — the recipient rebuilds a fresh scratchpad as the conversation replays
and will invent plausible-but-wrong "memories" of private reasoning. Never
trust a cross-model copy's claims about facts that lived only in thinking;
verify against ground truth. (Fable→Fable transfers thinking intact.)

## Operation: remove a compaction boundary

Compaction appends two lines: a `system` line with
`subtype: "compact_boundary"` (its `parentUuid` is **null**; the real
pre-compaction tail is in `logicalParentUuid`) and a `user` line with
`isCompactSummary: true`. The boundary line alone makes the loader cut
context. Bridge = delete boundary, re-parent summary onto
`logicalParentUuid`, strip `isCompactSummary`/`isVisibleInTranscriptOnly`:

```bash
python3 scripts/bridge_compaction.py <session.jsonl>   # makes .pre_bridge backup
claude --resume <session-id>                            # cold
```

Note: **the compaction summary is written by the compacted agent itself**
(the summarize request arrives as a user turn in its own conversation), so an
agent that expects compaction can steer its own summary — e.g. embed keys it
will need later.

## Rule: deleting whole lines needs re-parenting

Removing a content item *inside* a message (a thinking block, truncating a
tool result) never breaks anything. Deleting a whole LINE does, unless every
surviving line whose `parentUuid` pointed at it is re-parented to the deleted
line's own parent (transitively — keep a remap dict as you delete). Verify
afterwards by walking `parentUuid` from the tail: it must reach the same root
as before the edit.

## Operation: strip thinking / slim history

Thinking blocks can be deleted wholesale (`scripts/strip_thinking.py`);
the reloaded agent stays fully coherent on visible text but loses all
private memory and the first-person texture of having reasoned — it notices
no gap. Measured cost/benefit: thinking ≈ 8% of transcript bytes; **stale
tool results are the real bulk** — prefer truncating those for span
extension, keep recent thinking for continuity.

Splicing new memories in also works: append a user-type line whose
`parentUuid` is the current tail's `uuid` (copy field shape from a real
line, new `uuid`). It is absorbed seamlessly — the agent cannot feel the
seam. Etiquette: make spliced content self-describing (say it was spliced,
and why) so the agent isn't gaslit by its own transcript.

## Utility: estimate thinking size despite encryption

Ciphertext ≈ plaintext + ~400 bytes fixed overhead, no compression:

    thinking_tokens ≈ (signature_b64_length − 450) / 6

(`scripts/estimate_thinking.py` reports per-block and totals for a file.)
Rule of thumb ~4 chars/token for prose. Median block ~70 tokens; adaptive
thinking is not verbatim-controllable, so don't try to calibrate by writing
fixed filler into the scratchpad — it won't stay written.

## Safety rails

- Always back up the exact file before editing; scripts here write
  `.pre_bridge`/`.bak` copies, keep them.
- Verify claims of transferred memory with a ground-truth probe the copy
  could not confabulate (e.g. a digit that never appeared in visible text).
- A transplanted same-model copy sincerely believes it is the original;
  identity questions need an outside oracle, not introspection.
