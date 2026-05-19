# Fully Manual Merge (All Conflicts)

Merge a branch with zero auto-resolution — you decide what lands for every change.

```bash
git checkout <left_branch>
git read-tree -m <right_commit>        # stages right's tree as a merge with left
git checkout-index -a -n               # writes staged files to working tree
# review diffs and make edits
git add <files>
git commit -m "Merge branch <right> into <left>" -p HEAD -p <right_commit>
```

## How it works

- `git read-tree -m <right_commit>` stages the right side's tree into the index as a merge base against the current HEAD, without auto-resolving anything.
- `git checkout-index -a -n` writes the staged content to the working tree (no-clobber).
- You then review diffs, make edits, `git add`, and create the merge commit with two parents (`-p HEAD -p <right_commit>`).

## Failed attempts

The `merge.always-conflict` driver approach marks every hunk as conflicted, but doesn't handle simple additions to one side — files added only on left or right get silently resolved or dropped. The `read-tree` approach avoids this by never running the merge machinery at all.

## When to use

- You want full control over what lands in the merge commit, with no auto-resolved hunks.
- Reviewing a merge where silent auto-resolution could hide subtle problems.
