#!/usr/bin/env python3
"""Strip thinking blocks (and optionally truncate old tool results) from a
Claude Code jsonl transcript to slim its replay cost.

Usage: strip_thinking.py <transcript.jsonl> [--keep-last N] [--truncate-tools CHARS]
  --keep-last N        keep thinking blocks in the last N assistant messages
                       (default 0 = strip all)
  --truncate-tools C   truncate tool_result content items longer than C chars
                       (default: leave tool results untouched)

Writes <file>.bak first, edits in place. Run only while the agent is cold.
The reloaded agent stays coherent on visible text but loses private memory
held only in the stripped thinking (see SKILL.md).
"""
import json, shutil, sys

args = sys.argv[1:]
if not args:
    sys.exit(__doc__)
path = args[0]
keep_last = int(args[args.index('--keep-last') + 1]) if '--keep-last' in args else 0
trunc = int(args[args.index('--truncate-tools') + 1]) if '--truncate-tools' in args else None

lines = [json.loads(l) for l in open(path) if l.strip()]

# indices of assistant messages that contain thinking, newest last
think_idx = [i for i, d in enumerate(lines)
             if d.get('type') == 'assistant' and isinstance(d.get('message'), dict)
             and any(isinstance(c, dict) and c.get('type') == 'thinking'
                     for c in d['message'].get('content') or [])]
protect = set(think_idx[-keep_last:]) if keep_last else set()

removed = truncated = 0
for i, d in enumerate(lines):
    m = d.get('message')
    if not isinstance(m, dict) or not isinstance(m.get('content'), list):
        continue
    if i not in protect:
        n = len(m['content'])
        m['content'] = [c for c in m['content']
                        if not (isinstance(c, dict) and c.get('type') == 'thinking')]
        removed += n - len(m['content'])
    if trunc is not None:
        for c in m['content']:
            if isinstance(c, dict) and c.get('type') == 'tool_result':
                v = c.get('content')
                if isinstance(v, str) and len(v) > trunc:
                    c['content'] = v[:trunc] + f"\n[...truncated {len(v)-trunc} chars by strip_thinking.py]"
                    truncated += 1

shutil.copy(path, path + '.bak')
with open(path, 'w') as f:
    for d in lines:
        f.write(json.dumps(d) + '\n')
print(f"thinking blocks removed: {removed} (protected last {len(protect)} messages); "
      f"tool results truncated: {truncated}")
print(f"backup: {path}.bak")
