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

  The shipped tag is **`headings-1.0`** — all seven languages in one snapshot. A tag here is a
  snapshot and not a delta: whatever the app asks for, that tag has to hold every language. Never
  move a tag that has been served; jsDelivr caches by tag, so a fix ships as a new tag and the
  app's `bibleHeadingsTag` moves with it. `headings-v1`…`v7` are the per-language tags this was
  built up under and nothing reads them.
- **The app degrades to today's behaviour** when a heading file is missing, so a language ships
  when its translation is ready rather than all seven at once.
- One file, ~126 KB, serves KJV, BBE and DRA together.

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

> The public-domain statement above is eBible.org's, restating the publisher's terms rather than
> setting them; the publisher's own page is `bereanbible.com`. Recorded here so the provenance of
> the claim is on the record with the data it covers.

Other languages are **translations of these titles**, not extractions from another Bible — that
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
| dra | 99.94% | 2 (Song of Songs) |
| ostervald | 99.97% | 1 (Ezekiel 20:45) |
| elb1905, luther1912 | 99.68% | 10 (Joel 2:28, Malachi 4, Zechariah 1:18, …) |

**No mapping table exists and none is needed.** The app looks a heading up by verse, so an anchor
matching no verse renders nothing — the reader loses one heading out of three thousand and sees no
error. `validate-headings.js` fails only under 95%, which is the line between "versification" and
"the extraction broke".
