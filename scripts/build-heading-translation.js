#!/usr/bin/env node
/**
 * build-heading-translation.js — Turn an english→target glossary into a heading file.
 *
 * Headings repeat across the canon — "The Bride" fifteen times, "A Call to Repentance" seven —
 * so a language is translated once per *distinct* title (2,648 of them) rather than once per
 * anchor (3,086), and this expands the glossary back over `headings/en.json`'s anchors. Titles
 * joined with " · " are two independent titles and are looked up as such.
 *
 * The glossary is TSV: english<TAB>translation, one per line.
 *
 * Usage:
 *   node scripts/build-heading-translation.js <glossary.tsv> <headings/hr.json>
 *
 * Fails rather than writing a partial file: a heading falling back to English mid-chapter is
 * worse than a language that is not there at all, because the reader cannot tell it is a gap.
 */

const fs = require("fs");
const path = require("path");

const [, , glossaryFile, outputFile] = process.argv;

if (!glossaryFile || !outputFile) {
  console.error("Usage: node scripts/build-heading-translation.js <glossary.tsv> <out.json>");
  process.exit(1);
}

const SOURCE = path.join(__dirname, "..", "headings", "en.json");
const JOIN = " · ";

const glossary = new Map();
for (const line of fs.readFileSync(glossaryFile, "utf8").split(/\r?\n/)) {
  if (!line.trim()) continue;
  const [english, translated] = line.split("\t");
  if (!english || !translated) {
    console.error(`Malformed glossary line: ${JSON.stringify(line)}`);
    process.exit(1);
  }
  glossary.set(english, translated);
}

const source = JSON.parse(fs.readFileSync(SOURCE, "utf8"));
const out = {};
const missing = new Set();
let anchors = 0;

for (const [bookId, chapters] of Object.entries(source)) {
  for (const [chapter, verses] of Object.entries(chapters)) {
    for (const [verse, title] of Object.entries(verses)) {
      const parts = title.split(JOIN);
      const translated = parts.map((part) => {
        if (!glossary.has(part)) missing.add(part);
        return glossary.get(part);
      });
      if (translated.some((t) => t === undefined)) continue;
      if (!out[bookId]) out[bookId] = {};
      if (!out[bookId][chapter]) out[bookId][chapter] = {};
      out[bookId][chapter][verse] = translated.join(JOIN);
      anchors++;
    }
  }
}

if (missing.size > 0) {
  console.error(`${missing.size} title(s) missing from the glossary:`);
  for (const m of [...missing].slice(0, 20)) console.error(`  ${m}`);
  process.exit(1);
}

fs.mkdirSync(path.dirname(outputFile), { recursive: true });
fs.writeFileSync(outputFile, JSON.stringify(out, null, 1) + "\n");
console.log(`Wrote ${outputFile}`);
console.log(`  books   ${Object.keys(out).length}`);
console.log(`  anchors ${anchors}`);
console.log(`  size    ${(fs.statSync(outputFile).size / 1024).toFixed(1)} KB`);
