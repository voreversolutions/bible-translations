#!/usr/bin/env node
/**
 * validate-headings.js — Check that every heading anchor points at a verse that actually exists.
 *
 * A file named after an edition (`dra.json`) is checked against that edition alone, and an edition
 * with its own file is not checked against its language's file — that is the rule the app uses to
 * pick one, so checking any other pairing would report on a combination nothing loads.
 *
 * A heading file is keyed by reference, so it is only correct relative to a versification. Most
 * of our editions agree with the English one; a few split a handful of chapters the Hebrew way
 * (Joel 2:28 is Joel 3:1 in Luther, Malachi 4 does not exist there at all). An anchor that lands
 * nowhere is harmless at runtime — the app looks headings up by verse, so one that matches no
 * verse simply never renders — but the *count* is worth watching: a dozen is versification, a
 * thousand is a broken extraction.
 *
 * A book the edition does not contain at all is counted separately and does not move the ratio.
 * English now carries one anchor set over two canons: the ASV Byzantine Text has 84 books, the
 * KJV 66, so scoring the deuterocanon against the KJV would report a broken extraction where the
 * only fact is that the KJV has no Tobit.
 *
 * Usage:
 *   node scripts/validate-headings.js [headings/en.json ...]
 *
 * With no arguments it checks every file in headings/ against every translation of that language.
 * Exits non-zero if any translation resolves fewer than MIN_RESOLVED of its anchors.
 */

const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const HEADINGS_DIR = path.join(ROOT, "headings");
const MIN_RESOLVED = 0.95;

function translations() {
  return fs
    .readdirSync(ROOT, { withFileTypes: true })
    .filter((e) => e.isDirectory() && fs.existsSync(path.join(ROOT, e.name, "metadata.json")))
    .map((e) => {
      const meta = JSON.parse(fs.readFileSync(path.join(ROOT, e.name, "metadata.json"), "utf8"));
      return { id: e.name, language: meta.language, name: meta.name };
    });
}

function check(headingsFile, translation) {
  const headings = JSON.parse(fs.readFileSync(headingsFile, "utf8"));
  let total = 0;
  let resolved = 0;
  let outOfCanon = 0;
  const absentBooks = [];
  const misses = [];

  for (const [bookId, chapters] of Object.entries(headings)) {
    const bookFile = path.join(ROOT, translation.id, `${bookId}.json`);
    const book = fs.existsSync(bookFile)
      ? JSON.parse(fs.readFileSync(bookFile, "utf8")).chapters
      : null;

    if (!book) {
      const anchors = Object.values(chapters).reduce((n, v) => n + Object.keys(v).length, 0);
      outOfCanon += anchors;
      absentBooks.push(`${bookId} (${anchors})`);
      continue;
    }

    for (const [chapter, verses] of Object.entries(chapters)) {
      for (const verse of Object.keys(verses)) {
        total++;
        if (book[chapter] && book[chapter][verse]) {
          resolved++;
          continue;
        }
        const last = book[chapter] ? Math.max(...Object.keys(book[chapter]).map(Number)) : 0;
        misses.push(
          book[chapter]
            ? `${bookId} ${chapter}:${verse} — chapter ends at verse ${last}`
            : `${bookId} ${chapter}:${verse} — chapter not in this edition`
        );
      }
    }
  }
  return { total, resolved, outOfCanon, absentBooks, misses };
}

const files =
  process.argv.slice(2).length > 0
    ? process.argv.slice(2)
    : fs
        .readdirSync(HEADINGS_DIR)
        .filter((f) => f.endsWith(".json") && f !== "index.json")
        .map((f) => path.join(HEADINGS_DIR, f));

let failed = false;

const hasOwnFile = (id) => fs.existsSync(path.join(HEADINGS_DIR, `${id}.json`));

for (const file of files) {
  const setId = path.basename(file, ".json");
  const all = translations();
  const own = all.find((t) => t.id === setId);
  const targets = own ? [own] : all.filter((t) => t.language === setId && !hasOwnFile(t.id));
  const what = own ? `the ${setId} edition` : `${targets.length} translation(s) in "${setId}"`;
  console.log(`\n${path.relative(ROOT, file)} → ${what}`);

  if (targets.length === 0) {
    console.log("  (nothing loads this file — no translation reads it)");
    continue;
  }

  for (const translation of targets) {
    const { total, resolved, outOfCanon, absentBooks, misses } = check(file, translation);
    const ratio = total === 0 ? 0 : resolved / total;
    const flag = ratio < MIN_RESOLVED ? "FAIL" : "ok";
    if (ratio < MIN_RESOLVED) failed = true;
    console.log(
      `  ${flag.padEnd(4)} ${translation.id.padEnd(11)} ${resolved}/${total} ` +
        `(${(ratio * 100).toFixed(2)}%)` +
        (outOfCanon > 0 ? `  +${outOfCanon} anchors outside this canon` : "")
    );
    if (absentBooks.length > 0) {
      console.log(`         books absent: ${absentBooks.join(", ")}`);
    }
    for (const miss of misses) console.log(`         ${miss}`);
  }
}

if (failed) {
  console.error(`\nA translation resolved under ${MIN_RESOLVED * 100}% of its anchors.`);
  process.exit(1);
}
console.log("\nAll translations within tolerance.");
