# Find Reverted Commits and Files

When squashing a long chain of commits (e.g. before a PR), this script identifies commits and files that were fully reverted by later commits. The output guides an interactive rebase — these commits can be dropped or squashed away.

```bash
for commit in $(git rev-list --reverse main..HEAD); do
    for file in $(git diff-tree --no-commit-id --name-only -r $commit); do
        if git diff --quiet $commit^..HEAD -- $file; then
            echo "$(git --no-pager log -1 --format="%h %s" $commit) $file"
        fi
    done
done
```

## How it works

For each commit on the branch (oldest first), it checks every file that commit touched. If `git diff --quiet $commit^..HEAD` is silent for a file, that means the file's state before the commit is identical to its state at HEAD — the change was fully reverted by subsequent commits.

## Reading the output

Each line shows `<short-hash> <commit-subject> <file>`. If every file in a commit appears in the output, the entire commit is a no-op and can be dropped in a rebase. If only some files appear, the commit is partially reverted — consider splitting or squashing it.
