#!/usr/bin/env python3
"""Re-anchor the heading set onto an edition that holds the same text under a different division.

Luther, Elberfelder, Ostervald, Almeida and the BES are Masoretic Bibles like the KJV, but several
of them cut chapters the Hebrew way: the KJV's Malachi 4:1 is Luther's 3:19, its Joel 2:28 is
Luther's 3:1, its Zechariah 1:18 is Luther's 2:1, its Numbers 16:36 is Luther's 17:1. Their Psalms
also number each superscription as a verse, so the KJV's 51:1 is Luther's 51:3. Every one of those
anchors still *resolved* against a verse that exists, which is why nothing caught them: 71 of
Luther's headings sat over the wrong verse while the validator reported 99.68%.

The remap for the Vulgate editions aligns the words of each passage and cannot be used here — the
target is in German, French, Portuguese or Spanish. Aligning on the names and numbers that survive
translation was tried and does not work either: the verse a heading sits above is usually
formulaic ("And the LORD spake unto Moses, saying") and carries no name at all.

So this only claims what the numbers alone can force, and says so where they cannot:

1. **A chapter both editions cut the same way** keeps its anchors. Nothing to decide.
2. **A psalm with one or two verses more** is the superscription printed as verse 1 (and 2), so
   everything after it shifts by that much — and the psalm's own heading goes above the
   superscription rather than after it, which is where a printed Bible puts it and where the KJV's
   own unnumbered superscription sits. Confirmed by reading Psalms 3, 23 and 51 in all three
   editions that do this.
3. **Two or three adjacent chapters that hold the same verses between them**, differently cut, are
   a moved boundary and nothing else: the verse stream is identical across the span, so a verse's
   position within it identifies the verse exactly. This is the Malachi 3/4, Zechariah 1/2 and
   Numbers 16/17 class, and Joel needs three — the KJV's chapters 2 and 3 are Luther's 2, 3 and 4.
   Conservation alone is not enough, and 1 Samuel is why: Luther's chapters 21 and 23 each differ
   from the KJV's while 22 does not, so 21 to 23 balances to the verse without being one moved
   boundary at all — it is two, in opposite directions, with an untouched chapter between them.
   Counting across that says 23:7 slides back to 23:6, while Luther's 23:7 is word for word the
   KJV's ("Da ward Saul angesagt, daß David gen Kegila gekommen wäre").

   So the chapters that differ inside the span must also be **contiguous**. A gap in them means
   more than one boundary moved and the arithmetic no longer pins anything down. Deuteronomy 22
   and 23 in the Elberfelder are contiguous and the move is right (the KJV's 23:15 is its 23:16);
   1 Samuel 21 and 23 are not, and it is wrong.

4. **Anything wider is left alone and reported.** A span of ten chapters whose totals happen to
   agree proves nothing: the DRA's Numbers 11-20 balances to the verse and still differs verse by
   verse inside — it drops one in 11, one in 12, and adds one in 13 and one in 20 — which is
   exactly the trap. Three chapters is the width at which "the boundary moved" stays the only
   plausible reading. A heading one verse out is a far smaller error than a heading moved on a
   guess, so the guess is not made.

The titles come from the edition's own language file, not from `en.json`: Luther needs the German
ones. The anchors are the same in all seven, so only the placement is recomputed.

Usage: reanchor-by-structure.py <edition> <source.json> <out.json>
"""
import json, os, sys

def load(ed, b):
    p = f"{ed}/{b}.json"
    return json.load(open(p))["chapters"] if os.path.exists(p) else None

def lengths(ch):
    return {int(c): len(v) for c, v in ch.items()}

MAX_SPAN = 3

def moved_boundaries(k, t):
    """{chapter: (lo, hi)} for each chapter inside a short span that only re-cut its boundaries.

    A chapter missing on one side counts as length zero, which is how a span collapses: Malachi
    ends at 3 in Luther and at 4 in the KJV, and 3+4 there holds exactly what 3 holds here, so
    the KJV's 4:1 is Luther's 3:19.
    """
    out = {}
    chapters = sorted(set(k) | set(t))
    for lo in chapters:
        if k.get(lo, 0) == t.get(lo, 0): continue
        if lo in out: continue
        ck = ct = 0
        for hi in range(lo, lo + MAX_SPAN):
            ck += k.get(hi, 0)
            ct += t.get(hi, 0)
            if ck != ct or hi == lo: continue
            # The chapters that differ have to be contiguous: a gap means two boundaries moved,
            # not one, and then the totals balancing says nothing about any single verse.
            differing = [c for c in range(lo, hi + 1) if k.get(c, 0) != t.get(c, 0)]
            if differing != list(range(differing[0], differing[-1] + 1)): break
            for c in range(lo, hi + 1): out[c] = (lo, hi)
            break
    return out

def length_profile(ch, verse, n=5):
    return [len(ch[str(verse + i)]) for i in range(n) if str(verse + i) in ch]

def length_fit(a, b):
    """How well two length profiles agree once scaled to each other. 1.0 identical, 0 disjoint."""
    n = min(len(a), len(b))
    if n < 3: return None
    a, b = a[:n], b[:n]
    sa, sb = sum(a), sum(b)
    if not sa or not sb: return None
    a = [x / sa for x in a]
    b = [x / sb for x in b]
    return 1 - sum(abs(x - y) for x, y in zip(a, b)) / 2

def sequence(ch, lo, hi):
    return [(str(c), v) for c in range(lo, hi + 1) if str(c) in ch
            for v in sorted(ch[str(c)], key=int)]

ed, source, out = sys.argv[1], sys.argv[2], sys.argv[3]
en = json.load(open(source))
result, notes = {}, []
stats = dict(unchanged=0, boundary=0, psalm=0, left=0, dropped=0, no_book=0)

for book, chapters in en.items():
    tb, hb = load(ed, book), (load("kjv", book) or load("asvbt", book))
    if tb is None or hb is None:
        n = sum(len(v) for v in chapters.values())
        stats["no_book"] += n
        notes.append(f"{book}: not in this edition ({n} anchors)")
        continue

    k, t = lengths(hb), lengths(tb)
    pairs = moved_boundaries(k, t)

    for ch, anchors in sorted(chapters.items(), key=lambda kv: int(kv[0])):
        c = int(ch)
        for v, title in sorted(anchors.items(), key=lambda kv: int(kv[0])):
            if k.get(c) == t.get(c):
                tc, tv, why = ch, v, None
                stats["unchanged"] += 1
            elif book == "PSA" and 1 <= (t.get(c, 0) - k.get(c, 0)) <= 2:
                shift = t[c] - k[c]
                tc, tv = ch, ("1" if v == "1" else str(int(v) + shift))
                why = (f"the superscription takes {shift} verse{'s' if shift > 1 else ''} here"
                       if tv != v else None)
                stats["psalm"] += 1
            elif c in pairs:
                lo, hi = pairs[c]
                src, dst = sequence(hb, lo, hi), sequence(tb, lo, hi)
                i = src.index((ch, v)) if (ch, v) in src else None
                if i is None or i >= len(dst):
                    stats["dropped"] += 1
                    notes.append(f"{book} {ch}:{v}: inside the {lo}/{hi} boundary but unplaceable")
                    continue
                tc, tv = dst[i]
                why = f"chapters {lo} to {hi} are cut differently; verse #{i + 1} of the span"
                stats["boundary"] += 1
            else:
                tc, tv, why = ch, v, None
                stats["left"] += 1
                notes.append(f"{book} {ch}:{v}: chapter has {t.get(c)} verses against the KJV's "
                             f"{k.get(c)} and the difference is not an isolated moved boundary; "
                             f"left where it is")
            if tc not in tb or tv not in tb[tc]:
                stats["dropped"] += 1
                notes.append(f"{book} {ch}:{v} -> {tc}:{tv}: no such verse here")
                continue
            if why: notes.append(f"{book} {ch}:{v} -> {tc}:{tv} ({why})")
            slot = result.setdefault(book, {}).setdefault(tc, {})
            slot[tv] = f"{slot[tv]} · {title}" if tv in slot and slot[tv] != title else title

order = [b["id"] for b in json.load(open(f"{ed}/metadata.json"))["books"]]
ordered = {b: {c: dict(sorted(result[b][c].items(), key=lambda kv: int(kv[0])))
               for c in sorted(result[b], key=int)} for b in order if b in result}
open(out, "w", encoding="utf-8").write(json.dumps(ordered, ensure_ascii=False, indent=1) + "\n")
total = sum(len(v) for b in ordered.values() for v in b.values())
print(f"{ed}: {total} anchors — unchanged {stats['unchanged']}, moved boundary {stats['boundary']}, "
      f"psalm superscription {stats['psalm']}, left in place {stats['left']}, "
      f"dropped {stats['dropped']}, book absent {stats['no_book']}")
open(out.replace(".json", ".notes.txt"), "w", encoding="utf-8").write("\n".join(notes) + "\n")
