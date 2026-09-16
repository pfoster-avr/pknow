#!/usr/bin/env python3
"""Transplant a donor transcript into a target subagent: stamp every line
with the target's agentId + isSidechain and install it (with meta.json) into
a resolver-visible session directory.

Usage: transplant.py <donor.jsonl> <target_agent_id> <session_dir>
  session_dir = ~/.claude/projects/<proj>/<sessionId>  (of the session that
  will resume the target — resolver only sees its own lineage)

The target must be COLD (no live container) and must not be resumed between
transplant and the first post-transplant message, or its own appended turns
become the chain tail and bury the donor history. Cross-model note: encrypted
thinking does not survive to a different model family (see SKILL.md).
"""
import json, os, shutil, sys

donor, agent_id, session_dir = sys.argv[1], sys.argv[2], sys.argv[3]
sub = os.path.join(os.path.expanduser(session_dir), 'subagents')
os.makedirs(sub, exist_ok=True)
dst = os.path.join(sub, f'agent-{agent_id}.jsonl')
meta = os.path.join(sub, f'agent-{agent_id}.meta.json')

if os.path.exists(dst):
    shutil.copy(dst, dst + '.bak')
    print("backed up existing transcript to", dst + '.bak')

with open(donor) as fin, open(dst, 'w') as fout:
    n = 0
    for l in fin:
        if not l.strip():
            continue
        d = json.loads(l)
        d['agentId'] = agent_id
        d['isSidechain'] = True
        fout.write(json.dumps(d) + '\n')
        n += 1
print(f"installed {n} stamped lines -> {dst}")

if not os.path.exists(meta):
    with open(meta, 'w') as f:
        json.dump({"agentType": "general-purpose",
                   "description": "transplanted agent", "spawnDepth": 1}, f)
    print("wrote minimal meta.json (add \"model\" to pin the serving model):", meta)
else:
    print("meta.json present (serving model comes from it):", meta)
print("now resume with SendMessage to", agent_id)
