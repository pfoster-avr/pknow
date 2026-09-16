#!/usr/bin/env python3
"""Bridge a compaction boundary in a Claude Code session jsonl.

Finding: compaction is APPEND-ONLY. The full pre-compaction history stays in
the file; compaction appends (1) a `system` line with subtype
"compact_boundary" and (2) a `user` line with isCompactSummary: true.
The boundary line is what makes the loader cut context.

So bridging = remove the boundary line(s), re-parent the summary line onto
the boundary's parent so the chain stays walkable, and strip the
isCompactSummary / isVisibleInTranscriptOnly flags so the summary reads as a
normal user message. All pre- and post-compaction turns are left untouched.

Usage: python3 bridge_compaction.py [session_jsonl]
  default = path in active_session_path.txt (same dir as this script)
Writes <file>.pre_bridge backup first. Run only while the session is cold,
then: claude --resume <session-id>
"""
import json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
path = sys.argv[1] if len(sys.argv) > 1 else open(
    os.path.join(HERE, 'active_session_path.txt')).read().strip()

lines = [json.loads(l) for l in open(path) if l.strip()]

out, removed, summaries = [], 0, 0
reparent = {}  # boundary uuid -> boundary's parentUuid
for d in lines:
    if d.get('type') == 'system' and d.get('subtype') == 'compact_boundary':
        # boundary parentUuid is null (starts a fresh chain); the real
        # pre-compaction tail is in logicalParentUuid
        reparent[d.get('uuid')] = d.get('logicalParentUuid') or d.get('parentUuid')
        removed += 1
        continue
    if d.get('parentUuid') in reparent:
        d['parentUuid'] = reparent[d['parentUuid']]
    if d.pop('isCompactSummary', None):
        d.pop('isVisibleInTranscriptOnly', None)
        summaries += 1
    out.append(d)

print(f"lines: {len(lines)} -> {len(out)}  boundaries removed: {removed}  "
      f"summary lines normalized: {summaries}")
if removed == 0:
    sys.exit("no compact_boundary found; nothing to do")

shutil.copy(path, path + '.pre_bridge')
with open(path, 'w') as f:
    for d in out:
        f.write(json.dumps(d) + '\n')
print("bridged:", path)
print("backup :", path + '.pre_bridge')
print("resume :", os.path.basename(path).removesuffix('.jsonl'))
