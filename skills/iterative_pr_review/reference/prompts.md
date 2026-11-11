# Prompt templates for iterative PR review

Replace `<…>` placeholders. Keep the criteria verbatim from the user. These templates are
generalised from prompts that worked in practice; see [evidence.md](evidence.md).

## Round-0 review

Write this to a file (for example `review_r0.md`) and give its path to the fixer.

```text
# Review round 0 (reviewer: <you>) — <PR list>

Owner's criteria (apply to code, comments and PR descriptions):
1. <criterion 1, verbatim>
2. …

## Cross-cutting
A. <theme>: <concrete locations>. <what to do instead>. <how to verify: tests, parity, counts>.
B. …

## Per PR
- <PR 1>: <findings>; the description should state <intent, algorithm in N plain steps, gotchas,
  validation>.
- …

## Process for the fixer
- Worktree <path>. Branches bottom to top: <list>. Each branch is one commit on the one below;
  keep it so (amend, then `git rebase --onto` the upper branches). Do NOT push.
- After each layer: build + tests (<commands>); lint (<command>).
- New PR descriptions go to <dir>/<number>.md. Originals are in <dir>.
```

## Fixer

```text
You are fixing a stack of <N> PRs in <repo> (<language/build>). Read the review at <path> and
address it. It contains the owner's criteria, the findings, and the process rules.

Repo rules: read <CLAUDE.md / AGENTS.md paths>. <build tool notes: run builds serially, scratch
dir, never bare `git stash`>.

Judgment calls:
- Where a finding is wrong or not worth it after you look (e.g. a library has different semantics
  or is measurably slower), keep the existing code and say why in your report. Do not force a
  change.
- For behaviour changes: find how outputs are checked (<harness / golden files>), run it, and
  report exactly what changed in the outputs. If nothing runnable exists, say so.
- Do the bottom layer first and get it green before rebasing upward.

Final report, concise:
- per finding: done / partly done / not done, with the reason;
- the commit SHAs of every branch;
- test commands and results;
- output changes;
- anything you are unsure of.
```

## Fresh reviewer

```text
Review a stack of <N> local commits in <repo>, from scratch. Worktree: <path>. Branches, bottom to
top:
- <branch 1> (PR <n>, on <base>)
- …

Each branch is one commit on the one below; diff each layer against its parent. The proposed PR
descriptions are in <dir>/<number>.md. Read <CLAUDE.md>, and any AGENTS.md or CLAUDE.md in
directories the stack touches, for repo rules.

READ ONLY: do not edit, commit, push or check out anything; use `git show <branch>:<path>`. Do not
run auto-fixers; check mode only. Builds and repo check tools are fine, but not in parallel.

Judge the code, the comments and the PR descriptions against the owner's criteria:
1. <criterion 1, verbatim>
2. …

Also report correctness bugs, CI failures (build, lint, visibility, compatibility, repo
test-layout rules), dead code, and inconsistencies between layers or between a description and
the code: names, defaults, numbers, claims.

When you suggest replacing code with a library, verify that the library really has the same
semantics (boundary handling, robustness, local vs global, performance in a hot loop). Say what
you checked.

Output a prioritised list of findings, each with file:line (or PR number), what is wrong, and the
suggested fix, marked MUST (something a careful senior reviewer would block the PR on) or NIT.
Skip praise. If there is nothing substantive, say so explicitly in the first line.
```

Never add "the previous round found X" to this prompt.

## Naive reader

```text
Read ONLY these files, which are pull request descriptions for one stack of PRs:
- <dir>/<n1>.md
- …

Do not open any other file, do not look at code or git, and do not search. Then answer from the
descriptions alone:
1. In 2-3 sentences each: why does each PR exist, and what problem does the stack as a whole
   solve?
2. Explain the algorithm step by step, in your own words.
3. How does the result change the system's behaviour? What happens if it is wrong?
4. List only the things that would actually stop a reviewer from understanding the intent or the
   algorithm: terms you could not work out, contradictions, or missing steps. Keep minor wording
   preferences to at most 3 bullets.

Be honest about gaps, and mark guesses as guesses.
```

In round 1 you can drop the "only the things that would stop a reviewer" limit, to get the full
list once.
