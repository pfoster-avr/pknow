#!/usr/bin/env python3
"""Estimate thinking-block token sizes in a Claude Code jsonl transcript,
despite thinking being encrypted (stored as empty text + base64 signature).

Empirical model (Fable 5, 2026-09): ciphertext ~= plaintext + ~400 bytes,
no compression => thinking_tokens ~= (sig_b64_len - 450) / 6, floor 0.

Usage: estimate_thinking.py <transcript.jsonl> [--per-block]
"""
import json, sys

path = sys.argv[1]
per_block = '--per-block' in sys.argv

est = lambda n: max(0, round((n - 450) / 6))

total_sig = total_tok = count = 0
file_bytes = 0
for l in open(path):
    file_bytes += len(l)
    if not l.strip():
        continue
    d = json.loads(l)
    m = d.get('message')
    if not isinstance(m, dict):
        continue
    for c in m.get('content') or []:
        if isinstance(c, dict) and c.get('type') == 'thinking':
            n = len(c.get('signature', ''))
            count += 1
            total_sig += n
            total_tok += est(n)
            if per_block:
                print(f"  {d.get('timestamp','')[11:19]}  sig={n:6d}  ~{est(n):4d} tokens")

print(f"blocks: {count}   est thinking tokens: {total_tok}   "
      f"sig bytes: {round(total_sig*0.75)}")
if file_bytes:
    print(f"thinking share of file: {100*total_sig*0.75/file_bytes:.1f}% "
          f"of {file_bytes} bytes")
