---
name: iterative-pr-review
description: >-
  Bring one PR, or a stack of PRs, up to human-reviewer quality by alternating reviewer and fixer
  between two model families. A fresh reviewer each round checks against the owner's criteria; a
  naive reader must explain the PR from its description alone; the loop stops only when a fresh
  reviewer finds nothing substantive. Use when the user asks to "review and fix these PRs until
  they look good", "do mutual review", "polish this stack before reviewers see it", or to run
  /iterative-PR-review; also for any large AI-written change that must read as if a careful
  senior engineer wrote it. Not for a one-shot review comment pass.
---

# Iterative PR review

You run a review loop. Each round, a fresh agent reviews the current state of the PRs and another
agent fixes what it finds. The roles alternate between you and a subagent of a **different model
family**: if you are Opus, use Fable, and the reverse. Reviewers never see earlier findings. The
loop ends when a fresh reviewer finds nothing substantive (no MUST findings), not after a fixed
number of rounds.

The method comes from a run where it took 7 rounds; rounds 1–6 each found a real defect. These
included a build break, a stated safety property that was not implemented, a CI failure, and a
regression the fixer had introduced in the previous round. See
[reference/evidence.md](reference/evidence.md) for what each part of the method caught.

## Inputs to collect first

1. **The PRs.** Numbers, branches and base. If the branches form a stack, note the order and
   whether each is exactly one commit on the one below.
2. **The owner's criteria, verbatim.** Use the user's own words. If they gave none, propose the
   default set below and use it unless they object.
3. **An objective behaviour check, if one exists:** a parity or regression harness, golden
   outputs, a benchmark. Find it before round 1. It is what makes aggressive simplification safe
   to accept.
4. **Publishing rules:** whether you may push, force-push, edit PR descriptions, or mark ready
   for review. Default: work locally, and do not push until the loop ends and the user agrees.
5. **Shell access.** The loop needs git, the forge CLI, the build and the linters. If commands
   are being denied, stop and ask for access before doing anything else.

### Default criteria (adapt to the user's words)

1. As simple as possible. Do not reinvent the wheel: use the repo's libraries and patterns.
2. The code that does the core work is clustered together, with no needless indirection layers
   or tiny packages.
3. Comments are plain and scientific, neither patronising nor self-congratulatory. They mention
   gotchas relevant to other reviewers and maintainers, and nothing specific to how this change
   was developed.
4. A PR description lets someone understand the intent and the algorithm at a glance, without
   reading code.
5. There are no references to previous versions or past mistakes, unless the mistake is likely
   to be repeated in the future.

## The loop

Round 0 is your own review; after that, roles alternate.

| Round | Reviewer | Fixer |
|---|---|---|
| 0 | you | fresh subagent, other family |
| 1 | fresh subagent, other family (+ naive reader) | you |
| 2 | fresh subagent, other family (+ naive reader) | you, or a fresh fixer subagent |
| … | … | … |

Every reviewer and naive reader is a **new** agent, not a continued one. Launch the reviewer and
the naive reader of a round in parallel.

### Round 0: your own review

Read every layer's diff against its parent, and the PR descriptions. Write the review to a file
with this structure (template: [reference/prompts.md](reference/prompts.md#round-0-review)):
- the criteria, verbatim;
- cross-cutting findings, grouped by theme, each with concrete locations and a suggested fix;
- per-PR findings, including what the description must explain;
- process rules for the fixer.

Look especially for:
- code framed as a port of a prototype, with prototype names in comments and parity-only APIs;
- re-implementations of repo libraries;
- code one PR adds and a later PR in the stack deletes;
- tiny packages and indirection layers that exist only for "separation";
- history and people's names in comments;
- descriptions that list jargon instead of explaining the algorithm.

### Fixer rules (whoever fixes)

- **Keep the commit structure:** one commit per PR, amend, then rebase the upper branches with
  `git rebase --onto <new-lower> <old-lower> <upper>`. Record the old SHAs before amending.
- **The fixer may refuse a finding.** If a library has different semantics, or a change is not
  worth it, keep the code and say why, with the check that showed it. Never force a change to
  satisfy a reviewer.
- **Measure behaviour.** Run the objective check after any change that could alter outputs.
  Report every difference honestly (counts, examples), and say which ones are intended.
- **Write the new PR descriptions to files**, not to the forge, until publishing.
- **Verify every layer, not just the top:**
  - build and test each branch on its own;
  - grep logs for `ERROR|FAILED|TIMEOUT|NO STATUS`, never only for lowercase `error:`, which
    misses Bazel-style `ERROR:` lines and once hid a broken build behind "60/60 pass";
  - run the repo's linters and CI checks locally (lint, visibility, compatibility);
  - note that auto-fix linters often skip untracked files, so `git add` first or format new
    files explicitly.
- **Check repo rules that may have changed:** `CLAUDE.md`/`AGENTS.md` in every touched directory,
  on the current main, not only the base the stack was cut from.
- **Treat new behaviour as new code.** A fix that changes behaviour gets its own adversarial look
  in the next round. In the evidence run, a plausible "release the request early" change was
  wrong by construction, and only the next fresh reviewer caught it.

### Fresh reviewer (each round)

Prompt: [reference/prompts.md](reference/prompts.md#fresh-reviewer). Essentials:
- From scratch, read-only, against the criteria verbatim.
- **Do not tell it what earlier rounds found.** Naming past findings invites confirmation instead
  of search.
- Also ask for correctness bugs, CI failures (build, lint, visibility, compatibility, repo
  test-layout rules), dead code, and inconsistencies between layers and between description and
  code.
- When it suggests replacing code with a library, it must verify the library has the same
  semantics (boundary handling, robustness, local vs global, hot-loop cost), and say what it
  checked.
- Output: findings ranked, each marked **MUST** (a careful senior reviewer would block on it) or
  **NIT**, with location, problem and fix. "If you find nothing substantive, say so explicitly in
  the first line."

### Naive reader (rounds 1 to N, until it can explain everything)

Prompt: [reference/prompts.md](reference/prompts.md#naive-reader). It reads **only** the PR
description files: no code, git or search. It must explain:
- why each PR exists;
- the algorithm step by step;
- the behaviour change and failure modes;

and then list what it could not work out. Fix every contradiction and missing step it reports.
In later rounds, ask it to list only what would stop a reviewer understanding, plus at most 3
wording preferences, to keep the noise down.

### Triage between rounds

- Take every MUST, or refute it with a checked reason.
- Take NITs that are cheap and clearly right. Say why you skipped the rest.
- If a finding is a design decision the user should own, list it for them instead of guessing.
  Examples: behaviour changes, a reviewer's "should we", scope.

### Stop rule

Stop when a fresh reviewer, given the current state, reports no MUST. Do not stop because it
feels done or because N rounds have passed. Then:
1. Run the full verification once more on every layer.
2. Rebase onto the current main if the stack is behind, and re-verify.
3. Report to the user: what each round found, what changed, what was refused and why, what
   remains open (the last reviewer's NITs), and the decisions that are theirs.

## Publishing (only when the user says so)

- Force-push with a lease against the exact remote SHA you started from. Refuse to push if any
  remote branch moved. A script that reads `git ls-remote`, compares with the recorded heads,
  then runs `git push --force-with-lease=<ref>:<sha>` is safest.
- Update the PR descriptions from the files.
- Tell any other session that works on the same branches that they were rewritten.
- If marking ready for review restarts CI, check the runs it triggers. Re-running an old run
  replays the original event: a run recorded as "draft" stays draft. Re-run the cancelled
  `ready_for_review` run instead.

## Afterwards (optional)

If asked to watch the PRs, schedule check-ins for new comments and CI:
- fix non-contentious requests (a clear bug, a rename, a missing test, a comment fix, a CI
  failure caused by the stack) with the same verification and push rules;
- reply on the thread;
- list contentious items for the user.

## Installing this skill

Symlink the folder into a skills directory, user-wide or per repo:

    ln -s /workspaces/pknow/skills/iterative_pr_review ~/.claude/skills/iterative-pr-review
    ln -s /workspaces/pknow/skills/large_project_request ~/.claude/skills/large-project-request

`~/.claude` is wiped on this workspace's restarts, so re-run the links from a startup script (for
example the dotfiles `install.sh`), or link into a repo's `.claude/skills/` instead. Invoke the
skills as `/iterative-pr-review` and `/large-project-request`.
