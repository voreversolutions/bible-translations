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

  The shipped tag is **`headings-1.2`** — all seven languages in one snapshot. A tag here is a
  snapshot and not a delta: whatever the app asks for, that tag has to hold every language. Never
  move a tag that has been served; jsDelivr caches by tag, so a fix ships as a new tag and the
  app's `bibleHeadingsTag` moves with it. `headings-v1`…`v7` are the per-language tags this was
  built up under and nothing reads them; `headings-1.0` is the 66-book snapshot 1.1.3 shipped, and `headings-1.1` added the deuterocanon.
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

`headings/<translationId>.json` if it exists, otherwise `headings/<language>.json`. Four editions
need their own: **dra, cpdv, brenton and lxx2012** number their Psalms the Vulgate's or the
Septuagint's way, so the English anchors would sit over the wrong psalm in them from Psalm 10 on.
`Translation.headingSetFor` names those four by their dataset id and everything else by its
language.

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

## The Vulgate and Septuagint sets

`dra.json` (3,447 anchors), `cpdv.json` (3,439), `brenton.json` (2,503) and `lxx2012.json` (2,577)
are `en.json` re-anchored onto those editions by `scripts/remap-headings.py`. Before them those
four showed **no headings at all**, which was the larger of the two gaps this data has had.

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

`scripts/audit-remapped-headings.py` re-scores a finished file from scratch. DRA lands 92.9% of
its titles above 0.30 and none below 0.05; CPDV 71.8% and none; Brenton 87.0%; LXX2012 84.7%.

```bash
python3 scripts/remap-headings.py dra headings/dra.json
python3 scripts/audit-remapped-headings.py dra headings/dra.json
node scripts/validate-headings.js
```

**No mapping table exists and none is needed.** The app looks a heading up by verse, so an anchor
matching no verse renders nothing — the reader loses one heading out of three thousand and sees no
error. `validate-headings.js` fails only under 95%, which is the line between "versification" and
"the extraction broke".
