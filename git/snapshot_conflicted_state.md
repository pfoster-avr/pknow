# Snapshot a Conflicted State

Capture the exact working-tree state mid-conflict — including the conflict markers — as a real, addressable git tree, **without** clearing the conflict or touching the in-progress merge/rebase. Later you can diff against the snapshot to record how you resolved it.

```bash
IDX=$(git rev-parse --git-path index)   # path to the active index (worktree/GIT_INDEX_FILE aware)
cp "$IDX" /tmp/index.conflicted          # stash the conflicted index aside
git add -A && SNAP=$(git write-tree)     # collapse to stage 0 + write a tree object from it
cp /tmp/index.conflicted "$IDX"          # restore the conflicted index — merge state untouched
echo "snapshot tree: $SNAP"
```

After you finish resolving the conflicts, save the resolution for posterity:

```bash
git diff $SNAP > resolution.patch        # how the markered state became the resolved state
```

## How it works

- During a conflict the index holds *unmerged* entries (stages 1/2/3) for each conflicted path, and git tracks the in-progress operation via `MERGE_HEAD`/`REBASE_HEAD`. The working-tree files contain literal `<<<<<<<`/`=======`/`>>>>>>>` markers.
- `git rev-parse --git-path index` resolves the real index path (respects linked worktrees and `GIT_INDEX_FILE`), so the copy targets the right file.
- `git add -A` re-stages every path at **stage 0** using the current worktree content — i.e. the marker-laden files as they are right now. `git write-tree` then serializes the index into a tree object and prints its SHA. That SHA is a genuine, content-addressable snapshot.
- Restoring `/tmp/index.conflicted` over the index puts the unmerged stages back, so git still believes you are mid-conflict — nothing about the merge/rebase is lost.
- `$SNAP` now points at a tree capturing the conflicted-with-markers state. Once conflicts are resolved, `git diff $SNAP` shows precisely the edits that turned the markered state into the resolution.

## Caveats

- The snapshot tree is **dangling** and can be garbage-collected. If you need it to survive a while, anchor it: `git tag conflict-snap $SNAP` (delete the tag when done). Generating `resolution.patch` promptly is usually enough.
- `git add -A` stages *all* changes, not just conflicted files — that's fine here because the index is restored immediately, but don't interrupt the script between the `add` and the `cp` restore.
- The diff captures whatever you changed between snapshot and resolution, including any unrelated edits made in that window.

## When to use

- You want a durable record of *how* a tricky conflict was resolved — to document the decision, replay it on a similar conflict, or review it later — without disrupting the live merge/rebase.
- Complements [Fully Manual Merge](manual_merge.md): use that to force every hunk to conflict, and this to snapshot/record the hand-resolution.
