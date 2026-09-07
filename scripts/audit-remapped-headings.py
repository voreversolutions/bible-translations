#!/usr/bin/env python3
"""Audit a re-anchored heading set: does each title still open the passage it was written for?

Independent of the remap — it re-reads the two editions and scores the five verses under every
placed title against the five under the English anchor it came from. A remap that moved a heading
onto the wrong psalm scores near zero here, and the point of the audit is that it says so without
being told where the remap thought the verse was.
"""
import json, re, sys, os

STOP = set("""the and of to in a is that he for it with his i they be as not was you your my me we
us him them their this but which have had are were on at by from all shall will unto o thou thee
thy ye do did done who whom what when where there here so up out into an or if then than let may
hath doth am been being also more most very much many any every no nor only own same such too""".split())

def toks(s): return {w for w in re.findall(r"[a-z]{4,}", s.lower()) if w not in STOP}
def jac(a, b): return len(a & b) / len(a | b) if a and b else 0.0
def load(ed, b):
    p = f"{ed}/{b}.json"
    return json.load(open(p))["chapters"] if os.path.exists(p) else None

def passage(ch, verse, n=5):
    return " ".join(ch.get(str(verse + i), "") for i in range(n))

ed, path = sys.argv[1], sys.argv[2]
en = json.load(open("headings/en.json"))
out = json.load(open(path))

# title -> every English anchor that carries it, so a placed title can be traced back
src = {}
for b, chs in en.items():
    for c, vs in chs.items():
        for v, t in vs.items():
            src.setdefault((b, t), []).append((c, v))

buckets = {"0.30+": 0, "0.15-0.30": 0, "0.05-0.15": 0, "under 0.05": 0}
worst = []
checked = 0
for b, chs in out.items():
    tb, hb = load(ed, b), (load("kjv", b) or load("asvbt", b))
    if not tb or not hb: continue
    for c, vs in chs.items():
        for v, title in vs.items():
            for t in title.split(" · "):
                anchors = src.get((b, t))
                if not anchors: continue
                best = max(jac(toks(passage(hb[hc], int(hv))), toks(passage(tb[c], int(v))))
                           for hc, hv in anchors if hc in hb)
                checked += 1
                key = ("0.30+" if best >= 0.30 else "0.15-0.30" if best >= 0.15
                       else "0.05-0.15" if best >= 0.05 else "under 0.05")
                buckets[key] += 1
                if best < 0.05: worst.append((best, f"{b} {c}:{v} '{t}'"))

print(f"{ed}: {checked} placed titles re-scored against their English passage")
for k in ("0.30+", "0.15-0.30", "0.05-0.15", "under 0.05"):
    print(f"   {k:>10}: {buckets[k]:5}  ({buckets[k]/checked*100:.1f}%)")
worst.sort()
print(f"   weakest {min(len(worst), 12)}:")
for s, w in worst[:12]:
    print(f"      {s:.3f}  {w}")

import statistics, collections
per = collections.defaultdict(list)
for b, chs in out.items():
    tb, hb = load(ed, b), (load("kjv", b) or load("asvbt", b))
    if not tb or not hb: continue
    for c, vs in chs.items():
        for v, title in vs.items():
            for t in title.split(" · "):
                a = src.get((b, t))
                if not a: continue
                per[b].append(max(jac(toks(passage(hb[hc], int(hv))), toks(passage(tb[c], int(v))))
                                  for hc, hv in a if hc in hb))
rows = sorted((statistics.median(v), b, len(v), sum(1 for x in v if x < 0.10)) for b, v in per.items() if v)
print("   books by median (worst 10):")
for m, b, n, low in rows[:10]:
    print(f"      {b:4} median {m:.2f}  n={n:3}  below 0.10: {low}")
