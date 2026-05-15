Goal: Find a prompt that will get an AI to cut down conversations without summarizing out useful commands, losing ordering, or losing intent. The prompt below worked reasonably well, but did lose a fair bit of info.

Oldest prompt that worked:
    Please read the conversation at /workspaces/av/junk/pfoster/ai_scripter/ai_conversations/manual/Recalculation-August-2025.txt and summarize the messages IN THE ORDER THEY HAPPENED, and write it to a new file.
    You have a 1M token context, and the file easily fits, but your tools restrict you from reading the whole file at once, so read in sections. I recommend reading the whole file first, and then walking through message by message.

    Because you are summarizing in order, the number of messages shouldn't change much, just repetitive check messages and such get eliminated

    HARD RULE: Do not lose any command output lines referenced in a message further down the file. Eg: if a message says:
    ```
    Check main date
    $ cd /workspaces/av && git --no-pager log --oneline -1 --format='%ci' main
    ╭────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
    │ 2026-04-03 17:09:17 +0000
    │ <exited with exit code 0>
    ╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

    ● Right, main is from Apr 3. Let me pull to get up to date, then create the plan.
    ```
    You must keep the output line
    `  │ 2026-04-03 17:09:17 +0000`
    because it is referenced later (in this case right after)


---

# Newer prompt that worked very well (2026-05-15)

Used on copilot-CLI session dumps produced by `export_copilot_sessions.py`. Tested on
Claude Opus 4.7 (1M context) as the main agent and as a `general-purpose` subagent —
both produced ~38KB summaries (from a ~234KB input) that preserved every turn header
and every user message exactly, with reproducible per-turn summaries.

Substitute the actual file path. The `## 🤖 Assistant turn 2 \`19:07\`` example header
is the exact format the copilot dump uses; change it to match whatever header format
the conversation file uses.

```
Look at <PATH TO CONVERSATION FILE>
write a second .stripped.md version of the file with each of the agent's turns replaced with a summary.
You must keep the lines like
## 🤖 Assistant turn 2 `19:07`
exactly intact, so that I can see them as a match on a `diff` between input and output.

You have a 1M token context window, so the whole convo should fit, but your tool usage limits you to only reading a certain number of chars at a time (IDK how many), so you will need to read in chunks

User text must be preserved exactly, but everything else in the user turns can be omitted.

This task is meant to use your skill at summmarizing, not to produce or use a script, but to also force you to not delete or reorder turns. When you are done, I will hand check that.

User text is already sufficiently information dense. If you wonder what level of summarization I want, look at the user text as an example. This is why replacing user text is prohibited.

Do not use a script except:
- you may use it to remove things in html tags except <details>
- to clean up the comma-space sequences in `**apply_patch** (` blocks

If you use a script, you may only use it as preprocessing, and you must keep the intermediate file produced by the script, so I can see that you followed the rules
```

## Why this works (observations from two independent runs)

- **Header-line invariant as anti-cheat.** The "must match on `diff`" requirement on the
  `## 🤖 Assistant turn N \`HH:MM\`` header lines forces the model to produce a summary
  for *every* turn in order, including no-op/empty turns. Out of >100 prompt variants
  tried previously, this is one of only two that did not delete or reorder turns.
- **Anchor LoD by example.** Telling the model "use the user text as an example of the
  level-of-detail I want" without ever defining LoD numerically reliably produced
  ~1–4 sentence summaries per turn at the right density. Two independent runs both
  produced ~5000-line / ~38KB outputs from the same input.
- **"Don't use a script" + narrow exceptions.** Forbidding scripts pushes the model to
  actually read and summarize, but the two explicit exceptions (strip non-`<details>`
  tags; decode the comma-space char runs that copilot-dump emits inside
  `**apply_patch** (` blocks) let it preprocess away the structural noise that would
  otherwise dominate its context window. Both runs used a Python preprocess script
  and then summarized from an intermediate file. The "keep the intermediate file"
  clause gave the user a way to verify the script obeyed the scope.
- **User-text-must-be-exact.** This anchors verification: a single user message that
  doesn't `diff`-match means something was paraphrased. Both runs preserved user
  text byte-for-byte.

## Known imperfections / things to watch

- **Timestamps are reconstructed from memory and sometimes drift.** Both runs had to
  go back and fix HH:MM mismatches on the assistant headers after a final `diff`
  check. Neither cheated by re-dumping the header lines verbatim; they fixed them
  one at a time. Other "magic strings" (commit SHAs, image tags, file paths) are
  probably similarly at risk but harder to spot-check. Mitigation idea for future
  versions: explicitly enumerate the kinds of strings that must round-trip.
- **Preprocessing scope is ambiguous.** "Remove things in html tags except `<details>`"
  was interpreted two different ways: one run stripped the tag *and its contents*
  (preferred), the other only stripped the tags and left the contents. Both are
  defensible readings. Future revision should say e.g. "remove the tags AND the text
  between them" if the stripping interpretation is the intended one.
- **Quirky source structure leaks through but doesn't break things.** In the test
  conversation, a User message appears *inside* the body of Assistant turn 2 (an
  IDE-log artifact). One run preserved this as a User-Agent-User-Agent sequence
  with an empty turn 2, the other silently folded the orphan content into the next
  turn. Both readings were judged fine.
- **Small cross-turn info leakage.** Details learned in one turn sometimes show up
  in a neighboring turn's summary. At this LoD it actually improves readability
  rather than misleading, but at smaller LoD this would likely be harmful.
- **"No scripts" still permits shell utilities.** Both runs used `diff`, `grep`,
  `wc`, `sed` from the terminal for verification/preview without writing heredocs
  or scripts. This was a deliberate non-issue and worth keeping — the constraint
  was on *summarization logic* being in a script, not on shell hygiene.

## How to use it

1. Make sure the conversation file is on disk and the agent can read it.
2. Paste the prompt above, replacing `<PATH TO CONVERSATION FILE>` and adjusting
   the example header line if needed.
3. After the agent reports done, run a `diff` over only the protected header lines
   (e.g. `diff <(grep -E "^## 🤖|^## 👤" input.md) <(grep -E "^## 🤖|^## 👤" output.md)`).
   Empty output means every turn survived. If timestamps differ, the agent will
   usually fix them when asked.
4. Spot-check a few random turns against the source for content fidelity; pay extra
   attention to magic strings (SHAs, image tags, exact file paths).
