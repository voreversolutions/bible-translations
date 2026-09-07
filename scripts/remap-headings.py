#!/usr/bin/env python3
"""Re-anchor the English heading set onto a Vulgate- or Septuagint-numbered edition.

Why this is not a chapter-number remap. From Psalm 10 on, the Greek and Latin traditions number
the psalms one lower than the Hebrew, *and* they print each psalm's superscription as a numbered
verse, so the verses shift too — the KJV's 51:1 is the DRA's 50:3. Four psalms are split or merged
outright (Hebrew 9 and 10 are one psalm there; Hebrew 116 and 147 are each two), and outside the
Psalms a dozen chapters divide one verse earlier or later.

Two rules keep this honest:

1. **Every anchor is placed by aligning the words of the passage it opens**, never by
   differencing verse counts. The counts agree most of the time and are wrong exactly where the
   edition also merges a verse mid-psalm — eleven DRA psalms are that case — and a remap that
   trusted them would move a heading onto the wrong text while every anchor still resolved to a
   verse that exists.

   The verse the title *sits above* carries most of the vote, and the four verses after it only
   break ties. Scoring the five as equals blurs exactly the error that matters: a placement one
   verse out still shares four verses with the truth, so it scores nearly the same and the tie
   breaks toward not moving. That is how "The Spies Explore Canaan" stayed on the DRA's Numbers
   13:2 — "And there the Lord spoke to Moses" — when the verse it was written for is 13:3, "Send
   men to view the land of Chanaan".
2. **Evidence is required to move an anchor, never to leave it alone.** Staying put is the prior,
   so a weak alignment leaves the anchor where the mapping already put it; only a decisive win
   moves it, and an anchor with no reading at all is dropped rather than guessed. The asymmetry
   matters because the alignment goes quiet on repetitive text — genealogies, temple measurements,
   the tribal allotments — where every candidate scores alike and the runner-up is a coincidence,
   not a rival. No heading still beats a wrong heading: a missing title costs the reader nothing
   they had, a title over the wrong passage is the app lying about scripture.

Per anchor rather than per chapter, because one shift cannot describe a chapter the edition
splits in the middle: the Vulgate's Daniel 3 carries the Song of the Three at verse 24, so
anchors before it hold still while anchors after it move 67 verses.

A psalm's own heading is an exception to all of it: it goes above the psalm's first verse, not
above the verse that translates the KJV's first. These editions print the superscription as verse
1 (and sometimes 2), and the KJV prints it unnumbered above verse 1 — the same place. Following
the text alignment instead would file "Create in Me a Clean Heart, O God" at the DRA's 50:3, so
the reader meets two verses of "Unto the end, a psalm of David" before the title of the psalm
they are in. Luther and Ostervald number their superscriptions the same way and keep those
headings at verse 1, so this is also what makes the editions agree with each other.

Where the edition simply has no such verse — the Septuagint omits verses outright, so Brenton's
chapters have gaps in them — the title goes on the first verse of the passage that *is* there,
which is where the passage begins in that edition.

The neighbouring chapters are candidates too. A dozen anchors open a chapter the Vulgate ends one
verse earlier — the KJV's Job 40:1 is the DRA's Job 39:31, Ecclesiastes 5:1 is 4:17, Mark 9:1 is
8:39 — and those are the most visible headings there are, so a search confined to the chapter of
the same number would drop exactly the ones a reader opens the chapter on.

When even that finds nothing, the whole book is searched. Two books need it: the Septuagint's
Jeremiah is in a different order, with the oracles against the nations at chapters 25-32 instead
of 46-51, and its Proverbs closes chapter 24 with what the Hebrew prints as chapter 31. A jump
that far has to clear a higher bar than a neighbour does, because a book-wide search has fifty
times the chances to find a coincidence.

**A book-wide search alone is not safe, and the guard is monotonicity.** Exodus tells the
tabernacle twice, once as instruction and once as execution, in nearly the same words — "thou
shalt make the ark" against "and he made the ark" — so the search matched the construction
chapters onto the instruction chapters and scored them higher than the truth, because a repeated
formula matches better than a real translation of the same verse. Order catches what wording
cannot: headings run through a book in one direction, so any placement that goes backwards
relative to its neighbours is refused and re-searched between them.

The psalm numbering is passed in, not guessed. An edition that numbers its Psalms the Hebrew way
must not have the Greek chapter mapping applied to it, and the mistake is silent: run against the
ASV Byzantine Text with `greek`, every psalm from 10 on moves down one and Psalm 23 files under
22, with a perfect score, because the mapping was asked for.

Usage: remap-headings.py <edition> <hebrew|greek> <out.json>
"""
import json, re, sys, os

STOP = set("""the and of to in a is that he for it with his i they be as not was you your my me we
us him them their this but which have had are were on at by from all shall will unto o thou thee
thy ye do did done who whom what when where there here so up out into an or if then than let may
hath doth am been being also more most very much many any every no nor only own same such too""".split())

WINDOW = 5          # verses of the passage a heading opens, scored together
ANCHOR_WEIGHT = 0.7  # …but the verse the title actually sits above carries most of the vote
MIN_SCORE = 0.10    # below this the two passages have nothing in common
MIN_MARGIN = 0.04   # and the winner has to beat the runner-up by this much
FAR_SCORE = 0.20    # a jump outside the neighbouring chapters has to be this good
FAR_MARGIN = 0.08
FLOOR = 0.05        # and wherever an anchor ends up, its passage must still resemble the source
OUT_OF_ORDER_EDGE = 1.6  # how much better an out-of-order reading must be to survive the order check

_tok = {}
def tokens(s):
    t = _tok.get(s)
    if t is None:
        t = {w for w in re.findall(r"[a-z]{4,}", s.lower()) if w not in STOP}
        _tok[s] = t
    return t

def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0

def load(ed, book):
    p = f"{ed}/{book}.json"
    return json.load(open(p))["chapters"] if os.path.exists(p) else None

def opens_its_psalm(n):
    """Whether Hebrew psalm `n` starts the psalm it maps into, rather than continuing one.

    Hebrew 10 is the second half of Vulgate 9 and Hebrew 115 the second half of Vulgate 113, so
    their titles belong where their text begins — a third of the way in — and not at verse 1.
    Hebrew 116 and 147 are each split into two psalms there, and both halves do open one.
    """
    return n not in (10, 115)

def psalm_target(n, v):
    """Hebrew psalm n, verse v -> the psalm it sits in in a Greek/Vulgate edition."""
    if 1 <= n <= 9: return n
    if n == 10: return 9                      # Hebrew 9 and 10 are one psalm there
    if 11 <= n <= 113: return n - 1
    if n in (114, 115): return 113            # Hebrew 114 and 115 are one psalm there
    if n == 116: return 114 if v <= 9 else 115
    if 117 <= n <= 146: return n - 1
    if n == 147: return 146 if v <= 11 else 147
    if 148 <= n <= 150: return n
    return None

def resemblance(hv, tv, verse, target):
    """How much the passage at `target` still reads like the one the title was written for."""
    pairs = [(hv[str(verse + i)], tv[str(target + i)]) for i in range(WINDOW)
             if str(verse + i) in hv and str(target + i) in tv]
    if not pairs: return 0.0
    return sum(jaccard(tokens(a), tokens(b)) for a, b in pairs) / len(pairs)

def anchor_resemblance(hv, tv, verse, target):
    """Just the verse the title sits above — the measure a one-verse slip cannot hide from."""
    if str(verse) not in hv or str(target) not in tv: return 0.0
    return jaccard(tokens(hv[str(verse)]), tokens(tv[str(target)]))

def first_present(tv, verse):
    """`verse` if the edition has it, else the next verse of the same passage that it does."""
    for v in range(verse, verse + WINDOW):
        if str(v) in tv: return str(v)
    return None

def place(hv, chapters, home, verse, shifts, where=None):
    """Where the passage opening at `verse` sits: (chapter, target verse, score, margin).

    `home` is the chapter of the same number; its neighbours are searched too, and a tie breaks
    toward staying in `home` at the same verse, which is the null hypothesis. `where` overrides
    the chapters searched.
    """
    window = [str(verse + i) for i in range(WINDOW) if str(verse + i) in hv]
    if not window: return None, None, 0.0, 0.0
    src = [tokens(hv[v]) for v in window]
    scored = []
    for ch in (where or (home, str(int(home) - 1), str(int(home) + 1))):
        tv = chapters.get(ch)
        if not tv: continue
        cost = 0 if ch == home else 1000     # only to break ties, never to outweigh the words
        for s in shifts:
            pairs = [(i, t, str(int(v) + s)) for i, (t, v) in enumerate(zip(src, window))
                     if str(int(v) + s) in tv]
            if not pairs or pairs[0][0] != 0: continue   # the anchor verse has to have a partner
            head = jaccard(pairs[0][1], tokens(tv[pairs[0][2]]))
            rest = [jaccard(t, tokens(tv[b])) for i, t, b in pairs[1:]]
            score = ANCHOR_WEIGHT * head + (1 - ANCHOR_WEIGHT) * (sum(rest) / len(rest) if rest else head)
            scored.append((score, cost + abs(s), ch, s))
    if not scored: return None, None, 0.0, 0.0
    scored.sort(key=lambda x: (-x[0], x[1]))
    best = scored[0]
    runner = next((r[0] for r in scored[1:] if (r[2], r[3]) != (best[2], best[3])), 0.0)
    return best[2], str(verse + best[3]), best[0], best[0] - runner

ed, numbering, out = sys.argv[1], sys.argv[2], sys.argv[3]
if numbering not in ("hebrew", "greek"):
    raise SystemExit("numbering must be 'hebrew' or 'greek'")
GREEK_PSALMS = numbering == "greek"
en = json.load(open("headings/en.json"))
# Every book the source set has a title for, in the ASV BT's order, so the deuterocanon goes
# through the same mill as the rest: the Latin Tobit is a different recension from the Greek one
# and the audit is what decides whether its anchors survive, not an assumption either way.
CANON = [b["id"] for b in json.load(open("asvbt/metadata.json"))["books"]]
CANON += [b for b in en if b not in CANON]

result, notes = {}, []
stats = dict(kept=0, moved=0, joined=0, reordered=0, dropped=0, no_book=0)

def longest_monotonic(keys):
    """Indices of the longest non-decreasing run through `keys` — the placements to trust."""
    best = []
    tails = []          # tails[i] = (key, index chain) of the best run of length i+1
    for i, k in enumerate(keys):
        lo, hi = 0, len(tails)
        while lo < hi:
            mid = (lo + hi) // 2
            if tails[mid][0] <= k: lo = mid + 1
            else: hi = mid
        chain = (tails[lo - 1][1] if lo else []) + [i]
        if lo == len(tails): tails.append((k, chain))
        else: tails[lo] = (k, chain)
    return set(tails[-1][1]) if tails else set()

placed = {}     # book -> list of (src_ch, src_v, tgt_ch, tgt_v, title, score, margin)

for book in CANON:
    anchors_in_book = en.get(book)
    if not anchors_in_book: continue
    tb = load(ed, book)
    hb = load("kjv", book) or load("asvbt", book)
    if tb is None:
        n = sum(len(v) for v in anchors_in_book.values())
        stats["no_book"] += n
        notes.append(f"{book}: not in this edition ({n} anchors)")
        continue

    for ch, anchors in anchors_in_book.items():
        for v, title in sorted(anchors.items(), key=lambda kv: int(kv[0])):
            verse = int(v)
            tch = (str(psalm_target(int(ch), verse))
                   if book == "PSA" and GREEK_PSALMS else ch)
            if tch is None or tch not in tb or ch not in hb:
                stats["dropped"] += 1
                notes.append(f"{book} {ch}:{v}: no chapter to map onto")
                continue
            # Wide enough for the psalm splits (Hebrew 10 sits 21 verses into Vulgate 9) and for
            # the Song of the Three inside Daniel 3 (67); negative for the psalms cut in two.
            if (book == "PSA" and verse == min(int(x) for x in hb[ch])
                    and (opens_its_psalm(int(ch)) or not GREEK_PSALMS)
                    and "1" in tb.get(tch, {})):
                # The psalm's own title belongs at the top of the psalm, superscription included.
                # Marked `forced` so the resemblance floor leaves it alone: it is deliberately not
                # on the verse that translates the source, so scoring it there would drop it.
                placed.setdefault(book, []).append((ch, v, tch, "1", title, 1.0, 1.0, True))
                continue
            tc, tvn, score, margin = place(hb[ch], tb, tch, verse, range(-15, 71))
            decisive = tc is not None and score >= MIN_SCORE and margin >= MIN_MARGIN
            if not decisive:
                fc, fvn, fscore, fmargin = place(hb[ch], tb, tch, verse, range(-15, 71),
                                                 where=sorted(tb, key=int))
                if fc is not None and fscore >= FAR_SCORE and fmargin >= FAR_MARGIN:
                    tc, tvn, score, margin, decisive = fc, fvn, fscore, fmargin, True
                    notes.append(f"{book} {ch}:{v}: found at {fc}:{fvn} by searching the whole "
                                 f"book (score {fscore:.2f}, margin {fmargin:.2f})")
            if not decisive or (tc, tvn) == (tch, v):
                tc, tvn = tch, v          # staying put is the prior; only a decisive win moves it
                if not decisive:
                    notes.append(f"{book} {ch}:{v} -> {tch}:{v} kept; no decisive reading "
                                 f"(score {score:.2f}, margin {margin:.2f})")
            landed = first_present(tb.get(tc, {}), int(tvn))
            if landed is None:
                stats["dropped"] += 1
                notes.append(f"{book} {ch}:{v}: {tc}:{tvn} and the verses after it are absent")
                continue
            placed.setdefault(book, []).append((ch, v, tc, landed, title, score, margin, False))

# Order is the one check that wording cannot fake. Anything that runs backwards through the book
# is re-searched between the placements around it, and only kept if it reads better there.
for book, rows in placed.items():
    tb, hb = load(ed, book), (load("kjv", book) or load("asvbt", book))
    rows.sort(key=lambda r: (int(r[0]), int(r[1])))
    trusted = longest_monotonic([(int(r[2]), int(r[3])) for r in rows])
    for i, r in enumerate(rows):
        if i in trusted: continue
        prev = next((rows[j] for j in range(i - 1, -1, -1) if j in trusted), None)
        nxt = next((rows[j] for j in range(i + 1, len(rows)) if j in trusted), None)
        lo = int(prev[2]) if prev else 1
        hi = int(nxt[2]) if nxt else max(int(c) for c in tb)
        window = [c for c in sorted(tb, key=int) if lo <= int(c) <= hi]
        if r[7]: continue
        tc, tvn, score, margin = place(hb[r[0]], tb, r[2], int(r[1]), range(-15, 71), where=window)
        # Order is a heuristic and the words are the evidence. Where the out-of-order reading is
        # far better than anything in order, it stays: the Byzantine text really does move the
        # Romans doxology backwards, from 16:25 to 14:24, and no in-order placement comes close.
        if tc is not None and r[5] > OUT_OF_ORDER_EDGE * score:
            notes.append(f"{book} {r[0]}:{r[1]}: out of order at {r[2]}:{r[3]} but nothing in "
                         f"order reads nearly as well ({r[5]:.2f} against {score:.2f}); kept")
            continue
        if tc is None or score < MIN_SCORE:
            notes.append(f"{book} {r[0]}:{r[1]}: out of order at {r[2]}:{r[3]} and nothing "
                         f"between {lo} and {hi} reads better; dropped")
            rows[i] = None
            stats["dropped"] += 1
            continue
        landed = first_present(tb.get(tc, {}), int(tvn)) or tvn
        notes.append(f"{book} {r[0]}:{r[1]}: was out of order at {r[2]}:{r[3]} "
                     f"(score {r[5]:.2f}); re-placed at {tc}:{landed} (score {score:.2f})")
        rows[i] = (r[0], r[1], tc, landed, r[4], score, margin, False)
        stats["reordered"] += 1

# The last word belongs to the text. The fallbacks above can leave an anchor where the chapter
# mapping pointed without ever having read well there, so every placement is scored one final
# time where it actually landed and dropped if the two passages have nothing in common.
for book, rows in placed.items():
    tb, hb = load(ed, book), (load("kjv", book) or load("asvbt", book))
    for i, r in enumerate(rows):
        if r is None or r[7]: continue
        got = resemblance(hb[r[0]], tb[r[2]], int(r[1]), int(r[3]))
        if got < FLOOR:
            notes.append(f"{book} {r[0]}:{r[1]} -> {r[2]}:{r[3]}: the passage there reads "
                         f"nothing like it ({got:.3f}); dropped")
            rows[i] = None
            stats["dropped"] += 1

for book, rows in placed.items():
    for r in rows:
        if r is None: continue
        ch, v, tc, landed, title, score, margin, _ = r
        # Two sources can land on one verse where the edition merges verses. The set already
        # joins co-located titles with " · " (Proverbs' "Thirty Sayings" does it), so follow
        # that rather than let one silently overwrite the other.
        slot = result.setdefault(book, {}).setdefault(tc, {})
        if landed in slot and slot[landed] != title:
            notes.append(f"{book} {ch}:{v}: joined onto {tc}:{landed}, already '{slot[landed]}'")
            slot[landed] = f"{slot[landed]} · {title}"
            stats["joined"] += 1
            continue
        slot[landed] = title
        if (tc, landed) == (ch, v): stats["kept"] += 1
        else:
            stats["moved"] += 1
            notes.append(f"{book} {ch}:{v} -> {tc}:{landed} "
                         f"(score {score:.2f}, margin {margin:.2f})")

order = [b["id"] for b in json.load(open(f"{ed}/metadata.json"))["books"]]
ordered = {}
for b in order:
    if b in result:
        ordered[b] = {c: dict(sorted(v.items(), key=lambda kv: int(kv[0])))
                      for c, v in sorted(result[b].items(), key=lambda kv: int(kv[0]))}
open(out, "w", encoding="utf-8").write(json.dumps(ordered, ensure_ascii=False, indent=1) + "\n")

total = sum(len(v) for b in ordered.values() for v in b.values())
print(f"{ed}: {total} anchors over {len(ordered)} books — "
      f"kept {stats['kept']}, moved {stats['moved']}, joined {stats['joined']}, "
      f"re-placed for order {stats['reordered']}, dropped {stats['dropped']}, "
      f"book absent {stats['no_book']}")
open(out.replace(".json", ".notes.txt"), "w", encoding="utf-8").write("\n".join(notes) + "\n")
print(f"notes -> {out.replace('.json', '.notes.txt')} ({len(notes)} lines)")
