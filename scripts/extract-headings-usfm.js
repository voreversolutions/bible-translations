#!/usr/bin/env node
/**
 * extract-headings-usfm.js — Pull section headings out of a USFM Bible into one JSON file.
 *
 * Headings are keyed to a *reference*, not to a text, so one file serves every translation that
 * shares its versification — which is why they live in `headings/` rather than inside each
 * translation's book files. An anchor is the verse the heading sits **above**; the heading runs
 * until the next one or the end of the chapter, so no end is stored.
 *
 * Usage:
 *   node scripts/extract-headings-usfm.js <usfm-dir> <output.json>
 *
 * Example:
 *   node scripts/extract-headings-usfm.js ./eng-bsb_usfm ./headings/en.json
 */

const fs = require("fs");
const path = require("path");

const [, , inputDir, outputFile] = process.argv;

if (!inputDir || !outputFile) {
  console.error("Usage: node scripts/extract-headings-usfm.js <usfm-dir> <output.json>");
  process.exit(1);
}

/**
 * USFM heading levels. `\ms` is a major section (a handful per Bible — "Book I" over the Psalms)
 * and is deliberately left out: it names a division, not a passage, and reads as noise above a
 * verse. `\r` (the parallel-passage references under a heading) is left out for the same reason —
 * it is a different feature, not a heading.
 */
const HEADING_RE = /^\\s\d?\s+(.*)$/;
const CHAPTER_RE = /^\\c\s+(\d+)/;
const VERSE_RE = /^\\v\s+(\d+)/;
const BOOK_ID_RE = /^\\id\s+(\w+)/m;

/**
 * Strips the markup a heading can carry. Two kinds, and missing either leaves it in the output:
 * character markers (`\nd LORD\nd*`), and word-level attributes, which are `|` plus key="value"
 * hanging off a word — the BSB carries Strong's numbers that way, and without this the Song of
 * Songs ships headings reading `The|strong="H2142" Friends`.
 */
function clean(raw) {
  return raw
    .replace(/\|[^\\]*?(?=(\s|\\|$))/g, "")
    .replace(/\\\w+\*?/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

const files = fs
  .readdirSync(inputDir)
  .filter((f) => f.toLowerCase().endsWith(".usfm"))
  .sort();

if (files.length === 0) {
  console.error(`No .usfm files in ${inputDir}`);
  process.exit(1);
}

const out = {};
let anchors = 0;
let dropped = 0;

for (const file of files) {
  const text = fs.readFileSync(path.join(inputDir, file), "utf8").replace(/^﻿/, "");
  const idMatch = text.match(BOOK_ID_RE);
  if (!idMatch) continue;
  const bookId = idMatch[1].toUpperCase();

  const book = {};
  let chapter = null;
  let pending = [];

  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();

    const chapterMatch = trimmed.match(CHAPTER_RE);
    if (chapterMatch) {
      // A heading with no verse after it in its chapter anchors to nothing and is dropped rather
      // than carried into the next chapter, where it would sit above the wrong passage.
      dropped += pending.length;
      pending = [];
      chapter = chapterMatch[1];
      continue;
    }

    const headingMatch = trimmed.match(HEADING_RE);
    if (headingMatch) {
      const title = clean(headingMatch[1]);
      if (title) pending.push(title);
      continue;
    }

    const verseMatch = trimmed.match(VERSE_RE);
    if (verseMatch && pending.length > 0 && chapter) {
      if (!book[chapter]) book[chapter] = {};
      // Two headings above one verse happen where a section is subdivided at its own first verse
      // ("Thirty Sayings of the Wise" then "Saying 1"). Both are true of the passage, so both are
      // kept rather than one being picked.
      book[chapter][verseMatch[1]] = pending.join(" · ");
      anchors += pending.length > 1 ? 1 : 1;
      pending = [];
    }
  }
  dropped += pending.length;

  if (Object.keys(book).length > 0) out[bookId] = book;
}

fs.mkdirSync(path.dirname(outputFile), { recursive: true });
fs.writeFileSync(outputFile, JSON.stringify(out, null, 1) + "\n");

const bytes = fs.statSync(outputFile).size;
console.log(`Wrote ${outputFile}`);
console.log(`  books   ${Object.keys(out).length}`);
console.log(`  anchors ${anchors}`);
console.log(`  dropped ${dropped} (heading with no verse after it in its chapter)`);
console.log(`  size    ${(bytes / 1024).toFixed(1)} KB`);
