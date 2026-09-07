#!/usr/bin/env python3
"""Compare two editions of the same tradition against each other, anchor by anchor.

Independent of every other check here: it does not read a verse, count one, or measure a length.
Two editions that divide the text the same way should put the same heading at the same reference,
so a disagreement is a place where at least one of them is wrong — or where the two genuinely
number differently, which is worth seeing either way.

This is the check that found the remap scoring a bag of words: it put "Job Humbles Himself before
the LORD" on the DRA's 39:33, "Then Job answered the Lord", four verses from "the Lord answering
Job" — same words, opposite speaker. Nothing else here had noticed.

Usage: cross-check-headings.py <edition A> <edition B> [source.json]
"""
import json, sys

def ordered(d, book):
    return [(c, v, t) for c in sorted(d.get(book, {}), key=int)
            for v in sorted(d[book][c], key=int) for t in d[book][c][v].split(" · ")]

def read(ed):
    import os
    p = f"headings/{ed}.json"
    return json.load(open(p)) if os.path.exists(p) else None

a, b = sys.argv[1], sys.argv[2]
source = json.load(open(sys.argv[3] if len(sys.argv) > 3 else "headings/en.json"))
A, B = read(a), read(b)
if A is None or B is None:
    raise SystemExit(f"no per-edition file for {a if A is None else b}")

checked, diff = 0, []
for book in source:
    sa, sb, s0 = ordered(A, book), ordered(B, book), ordered(source, book)
    if len(sa) != len(s0) or len(sb) != len(s0):
        continue                      # one of them drops anchors in this book; not comparable
    for (ca, va, ta), (cb, vb, tb), (c0, v0, _) in zip(sa, sb, s0):
        if ta != tb: continue
        checked += 1
        if (ca, va) != (cb, vb):
            diff.append(f"{book} {c0}:{v0} -> {a} {ca}:{va} vs {b} {cb}:{vb}   '{ta[:40]}'")

print(f"{a} vs {b}: {checked} comparable anchors, {len(diff)} disagree "
      f"({len(diff) / checked * 100:.2f}%)" if checked else f"{a} vs {b}: nothing comparable")
for d in diff: print("  ", d)
