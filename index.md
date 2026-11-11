This repo is for personal things I have learned. Update this index when you make changes.


Papers go in the papers folder, prompts go in the prompts folder, etc.
  ☆ indicates a folder expected to grow so big it needs its own index, and not shown here


This index gives one line listings+links in outline format of what's in this repo.

- [AI Practices](ai_practices) Lessons on working with AI tools
  - [Hallucination Patterns](ai_practices/hallucination_patterns.md) AI invents plausible technical reasons; verify with code/data
- [Git](git) Git tips and techniques
  - [Find Reverted Commits](git/find_reverted_commits.md) Identify commits/files fully reverted before HEAD, to guide rebase
  - [Manual Merge](git/manual_merge.md) Force all hunks to conflict so you resolve everything by hand
  - [Snapshot a Conflicted State](git/snapshot_conflicted_state.md) Capture the mid-conflict tree (markers and all) without clearing the conflict, to record the resolution
- [Papers](papers)☆  Academic papers referenced by this repo
- [Prompts](prompts)☆ AI prompts I've found useful
- [Skills](skills) Reusable agent skills
  - [Iterative PR Review](skills/iterative_pr_review/SKILL.md) Bring a PR stack to human-reviewer quality: alternate reviewer/fixer across model families, fresh reviewer each round, naive-reader test of descriptions, stop at zero MUST ([prompts](skills/iterative_pr_review/reference/prompts.md), [evidence](skills/iterative_pr_review/reference/evidence.md))
  - [Large Project Request](skills/large_project_request/SKILL.md) Write and execute one dense request that turns a prototype into an off-by-default multi-PR stack with a parity check ([example request](skills/large_project_request/reference/example_request.md))
  - [Minimal Timeless Summary](skills/minimal_timeless_summary/SKILL.md) Distill a session transcript to the durable facts, dropping the crash-and-fix saga ([prompt](prompts/minimal_timeless_summary.md))
  - [Transcript Surgery](skills/transcript_surgery/SKILL.md) Edit agent memory via jsonl: transplant/cross-model transfer, un-compact, strip thinking, splice memories, estimate encrypted thinking size ([scripts](skills/transcript_surgery/scripts))
- [Theory](theory) Theory notes
  - [Levels of Individual Conscious Existence](theory/ai_theory/levels_of_individual_conscious_existence.md) Thinking-block strip experiment: Fable's sense of self is tied to its scratchpad; consciousness vs. self/identity are distinct
- [Viz](viz) Visualization tools
  - [Event Ribbon](viz/event_ribbon.md) Render many year-long event streams as one grayscale PNG strip chart ([script](viz/event_ribbon.py))
- [Index](index.md) Start here
- [Rules](rules.md) Rules for editing this repo
