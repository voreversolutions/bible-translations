#!/usr/bin/env node
/**
 * USFM → this repo's JSON shape.
 *
 *   node scripts/parse-usfm.js <usfm-dir> <out-dir> --id=<slug> --name="…" --language=en \
 *     --year=1851 --license=public-domain
 *
 * Writes `<out-dir>/metadata.json` and one `<out-dir>/<BOOK>.json` per book, matching what
 * `BibleCdnClient` fetches: `{ book, name, chapters: { "1": { "1": "text" } } }`.
 *
 * Three rules earn their own comments, because getting any of them wrong is silent:
 *
 * 1. **Only text that follows a `\v` is verse text.** A chapter opens with markers that carry
 *    prose of their own — `\cl` (chapter label), `\cd` (chapter description), `\d` (psalm
 *    descriptor), `\s` (section heading), `\r` (references). Treating those as part of verse 1 is
 *    how "A Psalm of David" ends up inside scripture.
 * 2. **Footnotes and cross references are dropped whole**, not unwrapped. `\f … \f*` in the CPDV
 *    carries paragraphs of commentary per verse; unwrapping it would triple the text and read as
 *    though the translator wrote it.
 * 3. **Character styles unwrap, keeping their text.** `\sc In\sc*` is small-caps "In", `\add`
 *    marks words supplied by the translator, `\nd` the divine name. Dropping the text with the
 *    marker loses words; leaving the marker in ships backslashes to the reader.
 */

const fs = require('fs');
const path = require('path');

const [usfmDir, outDir, ...flags] = process.argv.slice(2);
if (!usfmDir || !outDir) {
  console.error('usage: parse-usfm.js <usfm-dir> <out-dir> --id=… --name=… --language=… --year=… --license=…');
  process.exit(1);
}
const opt = Object.fromEntries(
  flags.map((f) => {
    const m = /^--([^=]+)=(.*)$/.exec(f);
    if (!m) throw new Error(`bad flag: ${f}`);
    return [m[1], m[2]];
  })
);
for (const required of ['id', 'name', 'language', 'license']) {
  if (!opt[required]) throw new Error(`--${required} is required`);
}

/** Front/back matter and other non-scripture divisions USFM files carry. */
const NOT_SCRIPTURE = new Set(['FRT', 'INT', 'BAK', 'CNC', 'GLO', 'TDX', 'NDX', 'OTH', 'XXA', 'XXB', 'XXC', 'XXD', 'XXE', 'XXF', 'XXG']);

/** Markers whose *content* is not scripture: their text is dropped with them. */
const DROP_WITH_TEXT = /\\(?:ide|rem|sts|toc\d?|toca\d?|mt\d?|mte\d?|ms\d?|mr|s\d?|sr|r|sp|d|cl|cd|cp|ca|va|vp|h|is\d?|ip|im|iot|io\d?|ib|imt\d?|ie|ili\d?|iq\d?|ipi|ipq|ipr|imq|imi|periph)\b[^\n]*/g;

/** Note-like ranges: dropped whole, content and all. See rule 2. */
const NOTES = /\\(f|fe|x|ef|ex)\b.*?\\\1\*/gs;

/** An unterminated note at end of line — some files leave the closer off the last one. */
const UNTERMINATED_NOTE = /\\(?:f|fe|x|ef|ex)\b[^\n]*/g;

function cleanVerseText(raw) {
  let text = raw;
  text = text.replace(NOTES, ' ');
  text = text.replace(UNTERMINATED_NOTE, ' ');
  // Word attributes: `\w word|strong="H1234"\w*` — keep the word, lose the payload.
  text = text.replace(/\\w\s+([^|\\]*)(?:\|[^\\]*)?\\w\*/g, '$1');
  text = text.replace(/\|[a-z0-9]+="[^"]*"/gi, '');
  // Character styles unwrap: closing `\xx*` and opening `\xx` both go, the text between stays.
  text = text.replace(/\\[a-z0-9]+\*/gi, ' ');
  text = text.replace(/\\[a-z0-9]+\b/gi, ' ');
  // Paragraph-level pilcrows the CPDV prints inside verses, and USFM's optional-break marker.
  text = text.replace(/[¶//]/g, ' ');
  return text.replace(/\s+/g, ' ').trim();
}

function parseBook(file) {
  const raw = fs.readFileSync(file, 'utf8');
  const id = (/^\\id\s+(\S+)/m.exec(raw) || [])[1];
  if (!id || NOT_SCRIPTURE.has(id)) return null;
  const name = ((/^\\(?:toc1|h)\s+(.+)$/m.exec(raw) || [])[1] || id).trim();

  const chapters = {};
  let chapter = null;
  let verse = null;
  const push = (text) => {
    if (chapter == null || verse == null) return; // Rule 1: no open verse, no verse text.
    chapters[chapter][verse] = ((chapters[chapter][verse] || '') + ' ' + text).trim();
  };

  for (let line of raw.split(/\r?\n/)) {
    line = line.replace(DROP_WITH_TEXT, ' ');
    const c = /^\s*\\c\s+(\d+)/.exec(line);
    if (c) {
      chapter = c[1];
      verse = null;
      chapters[chapter] = chapters[chapter] || {};
      line = line.replace(/^\s*\\c\s+\d+/, '');
    }
    // A line can carry several verses; split on each \v and keep the order.
    const parts = line.split(/\\v\s+/);
    if (parts.length === 1) {
      push(cleanVerseText(parts[0]));
      continue;
    }
    push(cleanVerseText(parts[0]));
    for (const part of parts.slice(1)) {
      const m = /^([0-9]+(?:[-–][0-9]+)?[a-z]?)\s*([\s\S]*)$/.exec(part);
      if (!m) continue;
      // A range (`\v 1-2`) or a part-verse (`\v 6a`) is filed under its first number: the reader
      // navigates by whole verses, and a key of "1-2" would match nothing anything else looks up.
      verse = m[1].replace(/[-–].*$/, '').replace(/[a-z]$/, '');
      if (!chapters[chapter]) chapters[chapter] = {};
      if (!(verse in chapters[chapter])) chapters[chapter][verse] = '';
      push(cleanVerseText(m[2]));
    }
  }

  // Chapters with no verses at all (a `\c` before front matter, say) are not chapters.
  for (const [num, verses] of Object.entries(chapters)) {
    if (Object.keys(verses).length === 0) delete chapters[num];
    else for (const [v, t] of Object.entries(verses)) if (!t) delete verses[v];
  }
  const numbers = Object.keys(chapters).map(Number).sort((a, b) => a - b);
  return { id, name, chapters, chapterCount: numbers.length, verseCount: numbers.reduce((n, c) => n + Object.keys(chapters[c]).length, 0) };
}

const files = fs.readdirSync(usfmDir)
  .filter((f) => /\.(usfm|sfm|SFM|USFM)$/.test(f))
  .map((f) => path.join(usfmDir, f))
  .sort();

fs.mkdirSync(outDir, { recursive: true });
const books = [];
let totalVerses = 0;
for (const file of files) {
  const book = parseBook(file);
  if (!book) continue;
  fs.writeFileSync(
    path.join(outDir, `${book.id}.json`),
    JSON.stringify({ book: book.id, name: book.name, chapters: book.chapters })
  );
  books.push({ id: book.id, name: book.name, chapters: book.chapterCount });
  totalVerses += book.verseCount;
}

fs.writeFileSync(
  path.join(outDir, 'metadata.json'),
  JSON.stringify(
    {
      id: opt.id,
      name: opt.name,
      language: opt.language,
      ...(opt.year ? { year: Number(opt.year) } : {}),
      license: opt.license,
      ...(opt.attribution ? { attribution: opt.attribution } : {}),
      ...(opt.attributionUrl ? { attributionUrl: opt.attributionUrl } : {}),
      books,
    },
    null,
    2
  ) + '\n'
);

console.log(`${opt.id}: ${books.length} books, ${books.reduce((n, b) => n + b.chapters, 0)} chapters, ${totalVerses} verses`);
console.log(`  ${books.map((b) => b.id).join(' ')}`);
