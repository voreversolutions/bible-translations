# Section headings

Short titles above a passage — "The Wedding at Cana", "Jesus and Nicodemus". They are the single
biggest readability win available to a Bible reader, and none of our ten editions carries any:
their texts are old enough to be public domain, and headings are a modern editorial layer that
open text distributions almost never include. Checked before settling on this source — the KJV's
44 `\s` markers are the Psalm 119 acrostic letters and nothing else, and the World English Bible
and Open English Bible carry only a handful of book-level divisions.

## Why they are not inside the translation folders

A heading is keyed to a **reference**, not to a text, so one file serves every edition that shares
its versification. Keeping them out of the book files has three consequences that all matter:

- **Nobody re-downloads a Bible for a heading fix.** The app treats a moved tag as "every local
  book is untrustworthy" and re-fetches the whole translation, so a heading typo shipped in a book
  file would cost every user 10–40 MB. Headings carry their own tag; the text tag never moves.

  The shipped tag is **`headings-1.5`** — all seven languages in one snapshot. A tag here is a
  snapshot and not a delta: whatever the app asks for, that tag has to hold every language. Never
  move a tag that has been served; jsDelivr caches by tag, so a fix ships as a new tag and the
  app's `bibleHeadingsTag` moves with it. `headings-v1`…`v7` are the per-language tags this was
  built up under and nothing reads them; `headings-1.0` is the 66-book snapshot 1.1.3 shipped, `headings-1.1` added the deuterocanon `headings-1.2` the first four re-anchored editions, `headings-1.3` the rest and `headings-1.4` the contiguity fix.
- **The app degrades to today's behaviour** when a heading file is missing, so a language ships
  when its translation is ready rather than all seven at once.
- One file, ~127 KB, serves every English edition together.

## Format

```json
{
  "JHN": {
    "1": { "1": "The Beginning", "14": "The Word Became Flesh" },
    "2": { "1": "The Wedding at Cana" }
  }
}
```

Book → chapter → **the verse the heading sits above** → the title. No end reference: a heading runs
until the next one or the end of the chapter.

Two titles above one verse are joined with ` · ` — that happens where a section is subdivided at
its own first verse ("Thirty Sayings of the Wise · Saying 1"). Ten anchors in the whole Bible.

### Which file the app loads

`headings/<translationId>.json` if it exists, otherwise `headings/<language>.json`. Eight editions
need their own, for three different reasons:

| Edition | Why |
|---|---|
| dra, cpdv | Vulgate Psalms — 10-147 run a number lower, and the superscription is a verse |
| brenton, lxx2012 | Septuagint Psalms, plus a reordered Jeremiah and 151 psalms |
| luther1912, elb1905, ostervald | cut chapters the Hebrew way (Malachi 4:1 is Luther's 3:19) |
| asvbt | the Byzantine text moves the Romans doxology from 16:25 to 14:24 |

`Translation.headingSetFor` names those eight by their dataset id and everything else by its
language. **All eight of those mismatches resolved against a verse that existed**, so the
validator reported 99.7% and nothing complained while 71 of Luther's headings sat over the wrong
verse. Resolution is not correctness; only the audit scripts test correctness.

The three editions numbered exactly like the KJV — bkj, arasvd, bbe — and the two whose only
differences are single merged verses — bes, almeida — read their language's file.

## Source and licence

`en.json` is extracted from the **Berean Standard Bible** USFM published by eBible.org
(`https://ebible.org/Scriptures/engbsb_usfm.zip`), whose copyright page states **Public Domain**,
contributed by BSB Publishing, LLC.

**Only the headings are taken. No BSB verse text is extracted, stored, or shipped.**

### The deuterocanon is not from the BSB

The BSB has 66 books, so the extraction above leaves the ASV Byzantine Text's other 18 with no
titles at all — 216 chapters of Tobit, Judith, Sirach, Maccabees and the rest. No public-domain
English edition carries both those books and section headings; checked WEB, WEB (British,
Protestant), the Open English Bible, the CPDV and both Septuagints — the ones with the books have
no headings, and the one with 440 headings has no deuterocanon.

So **the 657 deuterocanonical titles in `en.json` are written for this dataset.** For the eleven
books a Catholic edition divides into sections, the *anchors* — which verse opens a section —
follow those divisions, verified verse by verse against the ASV BT text, because where a passage
breaks is a fact about the text; the wording is ours. For `1ES`, `2ES`, `3MA`, `4MA` and `PSS`,
which no edition divides, both the anchors and the titles are ours.

English only, and that is not an oversight: `Translation.headingSetFor` names a set by the
edition's language and refuses one for any edition that does not number its Psalms the Hebrew way.
ASV BT is the only edition that carries these books *and* reads a heading set — DRA, CPDV, Brenton
and LXX2012 all carry deuterocanon and all show no headings at all. A Catholic or Orthodox edition
in another language would need these titles translated, and a Vulgate- or Septuagint-numbered
anchor set besides.

> The public-domain statement above is eBible.org's, restating the publisher's terms rather than
> setting them; the publisher's own page is `bereanbible.com`. Recorded here so the provenance of
> the claim is on the record with the data it covers.

Other languages are **translations of the 66-book titles**, not extractions from another Bible — that
keeps every language pointing at the same passages, which is the whole reason one anchor set works
across ten editions.

## Regenerating

```bash
curl -LO https://ebible.org/Scriptures/engbsb_usfm.zip
unzip engbsb_usfm.zip -d eng-bsb_usfm
node scripts/extract-headings-usfm.js ./eng-bsb_usfm ./headings/en.json
node scripts/validate-headings.js
```

The source USFM is gitignored — download it locally, do not commit it.

## Versification

The anchors follow English versification. Most of our editions agree; a few split chapters the
Hebrew way, and those anchors land on a verse that does not exist there:

| Edition | Resolves | Misses |
|---|---|---|
| kjv, bbe, bkj, arasvd, bes, almeida | 100% | — |
| asvbt | 99.97% | 1 (Romans 16:25 — the Byzantine text puts the doxology at 14:24) |
| dra | 99.86% | 5 |
| cpdv | 99.77% | 8 |
| ostervald | 99.97% | 1 (Ezekiel 20:45) |
| lxx2012 | 98.74% | 33 |
| brenton | 97.94% | 53 |
| elb1905, luther1912 | 99.68% | 10 (Joel 2:28, Malachi 4, Zechariah 1:18, …) |

A **book** the edition does not carry is counted apart from these and does not move the ratio: one
English anchor set now spans two canons, so scoring Tobit against the KJV would report a broken
extraction where the only fact is that the KJV has no Tobit.

## The re-anchored sets

`dra.json` (3,446), `cpdv.json` (3,422), `brenton.json` (2,515), `lxx2012.json` (2,581) and
`asvbt.json` (3,743) are re-anchored by `scripts/remap-headings.py`, which reads the text.
`luther1912.json`, `elb1905.json` and `ostervald.json` (3,086 each) are re-anchored by
`scripts/reanchor-by-structure.py`, which cannot: the target is in German or French, so aligning
on words is noise, and aligning on the names and numbers that survive translation was tried and
fails too — the verse a heading sits above is usually formulaic ("And the LORD spake unto Moses,
saying") and carries no name at all. That script therefore claims only what the verse counts can
force and reports the rest.

Before this, the four Vulgate and Septuagint editions showed **no headings at all**.

It is not a chapter-number remap. From Psalm 10 on the Greek and Latin traditions number the psalms
one lower, *and* they print the superscription as a numbered verse, so the verses shift too — the
KJV's 51:1 is the DRA's 50:3. Four psalms are split or merged outright. Outside the Psalms the
Vulgate's Esther is rearranged wholesale (the KJV's 1:1 is the CPDV's 3:1, but its 4:1 is 7:1 and
its 5:1 is 9:17), and the Septuagint's Jeremiah is a different book order, with the oracles against
the nations at chapters 25-32 instead of 46-51.

Four rules make it verifiable rather than clever:

1. **Every anchor is placed by aligning the words of the passage it opens**, five verses of it.
   Differencing verse counts is what a careless remap does and it is wrong wherever the edition
   also merges a verse mid-psalm — eleven DRA psalms are exactly that — and the result would be a
   heading over the wrong text with every anchor still resolving to a verse that exists.
2. **Evidence moves an anchor; nothing is needed to leave it alone.** The alignment goes quiet on
   repetitive text (genealogies, temple measurements), so a weak reading leaves the anchor where
   the chapter mapping put it instead of chasing a coincidence.
3. **Order is checked, because wording can be faked.** Exodus tells the tabernacle twice, as
   instruction and as execution, in nearly the same words, and the search happily matched "and he
   made the ark" onto "thou shalt make the ark" with a better score than the truth. Headings run
   through a book one way, so a placement that goes backwards relative to its neighbours is
   refused and re-searched between them.
4. **Whatever survives is scored again where it landed and dropped under 0.05.** No heading beats
   a wrong heading.

The comparison counts word pairs as well as words, after trimming inflections, because a bag of
words cannot tell "Moreover the LORD answered Job" from "Then Job answered the Lord" — the same
three words, opposite speakers, four verses apart in the DRA — and it put a heading on the wrong
one. The trimming is what lets order decide: the DRA writes "the Lord answering Job", so without
it "answering" matches nothing while the wrong verse's "answered" matches exactly.

### The check that found what the others missed

`scripts/cross-check-headings.py` compares two editions of the same tradition anchor by anchor. It
reads no verse, counts none and measures no length, so it is independent of everything above — and
it is what caught the Job case and four more like it. Where two editions disagree, comparing their
two target verses *to each other* settles whether one is wrong or whether the editions simply
number differently.

| Pair | Comparable | Disagree | Of those, wrong |
|---|---|---|---|
| luther1912 / elb1905 | 3,096 | 0 | — |
| kjv / asvbt | 3,745 | 0 | — |
| dra / cpdv | 2,436 | 1 | 0 — both right, the editions differ |
| brenton / lxx2012 | 1,253 | 46 | 0 — all 46 hold the same verse in both |

`headings/overrides.json` holds the five that were wrong, each read verse by verse, each with the
quotation that settles it. They exist because word overlap has a floor: "Jesus rebuked the unclean
spirit" sits beside "all were astonished at the greatness of God" in one edition's verses 43 and
44, and no scoring of one verse against another separates that reliably. An override whose target
verse is missing is refused rather than applied.

A psalm's own title is the exception to all four: it goes above the psalm's **first** verse, not
above the verse that translates the KJV's first. These editions print the superscription as verse
1 (and sometimes 2) and the KJV prints it unnumbered above verse 1 — the same place. Following the
alignment instead filed "Create in Me a Clean Heart, O God" at the DRA's 50:3, so a reader met two
verses of "Unto the end, a psalm of David" before the title of the psalm they were in. Hebrew 10
and 115 are excluded, because they are the second halves of Vulgate 9 and 113 and their titles
belong where their text begins, a third of the way in.

The psalm numbering is an argument, not a guess: run against the ASV Byzantine Text with `greek`
and every psalm from 10 on moves down one, Psalm 23 files under 22, and the score is perfect —
because the mapping was asked for.

### What structure alone can and cannot settle

`reanchor-by-structure.py` accepts three things and refuses everything else:

- a chapter both editions cut the same way keeps its anchors;
- a psalm with one or two verses more has them at the front, as the superscription;
- **two or three adjacent chapters holding the same verses between them, whose differing chapters
  are contiguous**, are a moved boundary and nothing else, so position within the span identifies
  the verse exactly. Joel needs three: the KJV's chapters 2 and 3 are Luther's 2, 3 and 4.

  Contiguity is load-bearing. Luther's 1 Samuel 21 and 23 both differ from the KJV's while 22 does
  not, so 21 to 23 balances to the verse without being one moved boundary — it is two, opposed,
  with an untouched chapter between them. Counting across it slides 23:7 back to 23:6, and
  Luther's 23:7 is word for word the KJV's. The Elberfelder's Deuteronomy 22 and 23 are
  contiguous and the same arithmetic is right there (the KJV's 23:15 is its 23:16).

Anything wider is left alone. A ten-chapter span whose totals agree proves nothing — the DRA's
Numbers 11-20 balances to the verse and still differs verse by verse inside, dropping one in 11
and 12 and adding one in 13 and 20 — and that trap is why the residue below is reported rather
than guessed at.

**Residue**: 28 anchors in Luther, 35 in Elberfelder, 44 in Ostervald, 42 in Almeida and 2 in the
BES sit in a chapter whose length differs for a reason counting cannot localise, and may be one
verse out. The books are named in each `*.notes.txt`.

`scripts/audit-remapped-headings.py` re-scores a finished file from scratch, and skips the psalm
openings because they are placed by the rule above rather than by alignment. DRA lands 92.6% of
its titles above 0.30 and none below 0.05; CPDV 72.7%; Brenton 85.8%; LXX2012 84.3%; ASV BT 99.8%.

```bash
python3 scripts/remap-headings.py dra greek headings/dra.json
python3 scripts/audit-remapped-headings.py dra headings/dra.json
python3 scripts/reanchor-by-structure.py luther1912 headings/de.json headings/luther1912.json
node scripts/validate-headings.js
```

**No mapping table exists and none is needed.** The app looks a heading up by verse, so an anchor
matching no verse renders nothing — the reader loses one heading out of three thousand and sees no
error. `validate-headings.js` fails only under 95%, which is the line between "versification" and
"the extraction broke".
