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

  The shipped tag is **`headings-1.1`** — all seven languages in one snapshot. A tag here is a
  snapshot and not a delta: whatever the app asks for, that tag has to hold every language. Never
  move a tag that has been served; jsDelivr caches by tag, so a fix ships as a new tag and the
  app's `bibleHeadingsTag` moves with it. `headings-v1`…`v7` are the per-language tags this was
  built up under and nothing reads them; `headings-1.0` is the 66-book snapshot 1.1.3 shipped.
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

`headings/<translationId>.json` if it exists, otherwise `headings/<language>.json`. No edition
needs its own file today; the rule exists so one can be added without a code change.

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

**No mapping table exists and none is needed.** The app looks a heading up by verse, so an anchor
matching no verse renders nothing — the reader loses one heading out of three thousand and sees no
error. `validate-headings.js` fails only under 95%, which is the line between "versification" and
"the extraction broke".
