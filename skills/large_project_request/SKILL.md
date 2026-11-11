---
name: large-project-request
description: >-
  Turn research or a prototype into a production change of several PRs from one dense request,
  and carry it out autonomously: write the request (goal, measurable bar with a fallback, allowed
  assumptions, a gate before PRs, reuse rules), then execute it. Survey first, split the work
  between parallel builder agents, build an objective parity check against the prototype, and
  open a stack of off-by-default draft PRs ready for /iterative-PR-review. Use when the user says
  "make a production version of X overnight", "port this to the online system and draft PRs", or
  runs /large-project-request, or when you are asked to help phrase such a request. Not for
  single-file fixes.
---

# Large project request

Use this skill in either of two modes:
- **Compose:** the user wants help writing a request for a large, multi-PR project.
- **Execute:** you have received such a request.

Both modes come from one run in which a single prompt produced a stack of four draft PRs overnight.
That stack was already above average before review. After
[/iterative-PR-review](../iterative_pr_review/SKILL.md) its owner judged the core PR
"almost human quality". The original request is quoted in
[reference/example_request.md](reference/example_request.md).

## Compose: what a good request contains

Write it as one message. Each part below did work in the example; keep them even when short.

1. **The goal in one sentence**, naming the existing thing to build from. Example: "make a
   version of the lane closure detector that is good for online".
2. **A time frame and the autonomy it implies.** Example: "I am out of time today, so overnight…"
   tells the agent to make decisions instead of asking.
3. **Technology constraints and preferences.** Standard libraries, language, the target runtime.
   Name the ones you expect, and let the agent find better in-repo equivalents.
4. **A measurable bar with an explicit fallback.** Example: "<100 ms of single CPU per image after
   warm-up… Even if not possible, see how close we can get." The bar focuses the work; the
   fallback stops the agent from either giving up or faking success.
5. **Allowed assumptions** that cut scope without cutting the design. Example: "Assume we can
   solve the problem of delivering nearby intersections… efficiently". Then say which of those
   assumptions the PRs must still solve, if any.
6. **A gate before PRs.** Example: "If that all looks good though, draft a PR that makes it part of
   our online pipeline". The agent proves the core first and only then integrates.
7. **Reuse rule.** Example: "while reusing existing code as much as possible".
8. Optionally, **where it must not change behaviour.** For example "off by default", or "no change
   to production with the flag off".

Things that helped in the example even though the request did not spell them out:
- **Send the request from a fork of the session that did the research.** The fork inherited the
  prototype, the labelled data, the spec and the evaluation, about half a 1M context. That made
  the builders correct.
  - The cost: the code came out framed as a port of the prototype, with prototype names, parity
    APIs and history in comments. The review loop had to remove that.
  - If you fork, plan on running /iterative-PR-review from a fresh session afterwards.
- **Short steering replies afterwards.** The example needed three: "test on the rail examples",
  "use a routing API instead of fake blockages — another draft PR?", "split the flag". Each
  changed a design decision in one line.

A template is in [reference/example_request.md](reference/example_request.md#template).

## Execute: how to carry out such a request

### 1. Survey before building

Spawn one read-only explorer to map the target system:
- runtime framework and node pattern;
- message and topic conventions;
- the map or data access the change needs;
- build rules;
- existing libraries for geometry, math and IO;
- CI checks and repo rules (`CLAUDE.md`/`AGENTS.md` in each touched directory).

Read its report before designing anything.

### 2. Fix the seams, then build in parallel

Choose the split:
- **the core:** pure library, plain structs, no framework;
- **the integration:** node or operation, adapters, data delivery;
- **any API change in another component**, as its own PR.

Then:
- Write the interface between core and integration (headers or types) first, and commit it. Then
  run the builders in parallel.
- Give each builder its own worktree, or its own paths within a shared one. Relay their interface
  questions between them yourself.
- Tell builders the memory and CPU limits of the machine before they start large batch runs.

### 3. Build an objective check against the prototype

Before optimising or simplifying, build a harness that runs the new core on the prototype's
recorded inputs and compares outputs. Use all of them, not a sample. In the example that meant
150k recorded cases.
- Report exact agreement counts and explain every difference.
- Keep the harness outside the PR, as a scratch tool, but keep its source somewhere durable. The
  review loop will reuse it to prove refactors output-neutral.
- Also measure the bar from the request (latency, memory) and report it honestly, including the
  "how close" case.

### 4. Integrate behind flags

- Production behaviour must not change by default: add a flag that defaults off. Check that the
  repo's configuration and canon tests pass unchanged, and that turning the flag on gives only
  the expected differences.
- When the work touches another team's component (routing, planning…), make that change a small,
  general API extension in its own PR, not a hack through an existing input.

### 5. Open a stack of draft PRs

- Use one PR per layer: core → messages → integration → cross-component API. Each PR is one
  commit on the one below, so reviewers can read each layer alone.
- Each description must say why the PR exists, the algorithm in plain numbered steps, the
  gotchas, and the validation. Do not include development history.
- Leave the PRs as drafts. Then tell the user the stack is ready for
  [/iterative-PR-review](../iterative_pr_review/SKILL.md). Do not call it finished: the review
  loop is where it goes from good to human quality.

### 6. Report

Report:
- what was built;
- the measured result against the bar;
- the parity numbers;
- the PR list with branches and SHAs;
- assumptions made;
- what the user must decide.

## Pitfalls seen in practice

- **Code shaped by the prototype.** A port drags in the prototype's names, quirks (even its
  hash-iteration order) and parity-only APIs. Keep parity in the harness, not in the product
  code.
- **Code added in one PR and removed in the next.** Within a stack, rewrite the lower PR instead.
- **Heavy batch runs can exhaust the machine.** Set limits up front.
- **Sessions can restart mid-task.** Write progress to durable files, and on restart re-read them
  rather than trusting memory.
