# AI Hallucination: Plausible Technical Reasoning

*Observed 2026-04-30 during investigation of interval/segment boundaries in AV codebase.*

## The pattern

When asked whether a technical behavior is possible, current AI models (Claude, GPT-4, etc.)
will often invent plausible-sounding technical justifications and present them as fact. These
fabrications are especially dangerous because they sound like expert reasoning.

## Examples observed in a single session

1. **"Localization is often less reliable during segment transitions"** — presented as a reason
   intervals wouldn't cross segment boundaries. No evidence for this claim; it was fabricated
   from general knowledge about sensor systems.

2. **"Boundaries are exclusive so things don't merge"** — claimed that `[A, X)` and `[X, B)`
   wouldn't merge due to exclusive endpoints. The actual code uses `start_ts <= current_end`,
   which *does* merge these. The AI didn't read the code before making this claim.

3. **Launch-scoped vs segment-scoped queries** — the AI initially guessed at which queries
   were launch-scoped vs segment-scoped without reading the SQL. The actual answer required
   reading the ClickHouse queries in `data_quality_intervals.py`.

## Why this is dangerous

- The fabricated reasoning was **internally consistent** — each claim supported the others
- The claims sounded like they came from domain expertise
- A user without deep codebase knowledge would have accepted them
- The correct answer required **empirical verification** (dumping actual data and comparing)

## Mitigation

- When an AI gives a technical reason for behavior, ask for the specific code path or data
  that demonstrates it
- "Can you show me where in the code that happens?" is the single most useful follow-up
- For data-dependent questions, prefer empirical verification (dump the data, write a
  comparison script) over code-reading speculation
- Treat AI technical reasoning as hypotheses to test, not conclusions to accept
