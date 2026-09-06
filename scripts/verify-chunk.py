#!/usr/bin/env python3
"""Pairs a chunk of English titles with a translated list and proves the two are aligned.

The translation is emitted as a bare list in the chunk's own order, so the English is never
retyped and cannot drift. Equal line counts are not proof of alignment — a one-row slip keeps the
count — so every row whose English carries a proper noun must carry a recognisable form of it in
the translation. One slip breaks dozens of those at once.

    python3 verify-chunk.py <lang> <nn>
"""
import re
import sys
import unicodedata
from pathlib import Path

# Punctuation the Latin-script languages legitimately use. Anything else outside ASCII that is not
# a LATIN letter is a homoglyph typo — a Cyrillic а or е inside an otherwise Latin word — which
# ships a heading nobody can search for and is invisible to the eye. Three have been caught so far.
ALLOWED_NON_LATIN = set("\u2013\u2014\u2019\u2026\u00b7\u00ab\u00bb\u00bf\u00a1")

SC = Path(__file__).resolve().parent.parent
PROBES = {
    "de": {"Absalom": "Absalom", "Jeremiah": "Jeremia", "Zedekiah": "Zedekia",
           "Timothy": "Timotheus", "Babylon": "Babel", "Balaam": "Bileam", "Cain": "Kain",
           "Daniel": "Daniel", "Caleb": "Kaleb", "Boaz": "Boas", "Cyrus": "Kores",
           "Hezekiah": "Hiskia", "Samson": "Simson", "Jezebel": "Isebel", "Elijah": "Elia",
           "Elisha": "Elisa", "Jeroboam": "Jerobeam", "Rehoboam": "Rehabeam", "Paul": "Paulus",
           "Peter": "Petrus", "Ezekiel": "Hesekiel", "Isaiah": "Jesaja", "Joshua": "Josua",
           "Jehoshaphat": "Josaphat", "Xerxes": "Ahasveros", "Ezra": "Esra", "Jesus": "Jes"},
    "es": {"Absalom": "Absal", "Jeremiah": "Jerem", "Zedekiah": "Sedequ", "Babylon": "Babilon",
           "Balaam": "Balaam", "Cain": "Ca", "Daniel": "Daniel", "Caleb": "Caleb", "Boaz": "Booz",
           "Cyrus": "Ciro", "Hezekiah": "Ezequ", "Samson": "Sans", "Jezebel": "Jezabel",
           "Elijah": "El", "Elisha": "Eliseo", "Jeroboam": "Jeroboam", "Rehoboam": "Roboam",
           "Paul": "Pablo", "Peter": "Pedro", "Ezekiel": "Ezequiel", "Isaiah": "Isa",
           "Joshua": "Josu", "Jehoshaphat": "Josafat", "Xerxes": "Asuero", "Ezra": "Esdras",
           "Solomon": "Salom", "Moses": "Mois", "Aaron": "Aar", "Pharaoh": "Fara",
           "Jesus": "Jes", "Nebuchadnezzar": "Nabucodonosor"},
    "fr": {"Absalom": "Absalom", "Jeremiah": "J\u00e9r\u00e9mie", "Zedekiah": "S\u00e9d\u00e9cias",
           "Babylon": "Babylone", "Balaam": "Balaam", "Cain": "Ca\u00efn", "Daniel": "Daniel",
           "Caleb": "Caleb", "Boaz": "Booz", "Cyrus": "Cyrus", "Hezekiah": "\u00c9z\u00e9chias",
           "Samson": "Samson", "Jezebel": "J\u00e9sabel", "Elijah": "\u00c9lie",
           "Elisha": "\u00c9lis\u00e9e", "Jeroboam": "J\u00e9roboam", "Rehoboam": "Roboam",
           "Paul": "Paul", "Peter": "Pierre", "Ezekiel": "\u00c9z\u00e9chiel",
           "Isaiah": "\u00c9sa\u00efe", "Joshua": "Josu\u00e9", "Jehoshaphat": "Josaphat",
           "Xerxes": "Assu\u00e9rus", "Ezra": "Esdras", "Solomon": "Salomon", "Moses": "Mo\u00efse",
           "Aaron": "Aaron", "Pharaoh": "Pharaon", "Jesus": "J\u00e9sus",
           "Nebuchadnezzar": "N\u00e9bucadnetsar", "Delilah": "D\u00e9lila"},
    "pt": {"Absalom": "Absal\u00e3o", "Jeremiah": "Jeremias", "Zedekiah": "Zedequias",
           "Babylon": "Babil", "Balaam": "Bala\u00e3o", "Cain": "Caim", "Daniel": "Daniel",
           "Caleb": "Calebe", "Boaz": "Boaz", "Cyrus": "Ciro", "Hezekiah": "Ezequias",
           "Samson": "Sans\u00e3o", "Jezebel": "Jezabel", "Elijah": "Elias", "Elisha": "Eliseu",
           "Jeroboam": "Jeroboão", "Rehoboam": "Robo\u00e3o", "Paul": "Paulo", "Peter": "Pedro",
           "Ezekiel": "Ezequiel", "Isaiah": "Isa\u00edas", "Joshua": "Josu\u00e9",
           "Jehoshaphat": "Jeosaf\u00e1", "Xerxes": "Assuero", "Ezra": "Esdras",
           "Solomon": "Salom\u00e3o", "Moses": "Mois\u00e9s", "Aaron": "Ar\u00e3o",
           "Pharaoh": "Fara\u00f3", "Jesus": "Jesus", "Nebuchadnezzar": "Nabucodonozor",
           "Jehoiakim": "Jeoiaquim", "Jehoiada": "Jeoiada"},
}

def main() -> None:
    lang, nn = sys.argv[1], sys.argv[2]
    en = (SC / "chunks" / f"{nn}.txt").read_text(encoding="utf-8").rstrip("\n").split("\n")
    tr = (SC / "tr" / lang / f"{nn}.txt").read_text(encoding="utf-8").rstrip("\n").split("\n")
    if len(en) != len(tr):
        sys.exit(f"count mismatch: en={len(en)} {lang}={len(tr)}")

    for i, t in enumerate(tr):
        for ch in t:
            if ord(ch) > 127 and "LATIN" not in unicodedata.name(ch, "") \
                    and ch not in ALLOWED_NON_LATIN:
                sys.exit(
                    f"row {i}: {unicodedata.name(ch, '?')} ({ch!r}) in {t!r} — homoglyph typo"
                )

    probe = PROBES.get(lang, {})
    checked = bad = 0
    for i, (e, t) in enumerate(zip(en, tr)):
        if not t.strip():
            sys.exit(f"row {i} is empty: {e!r}")
        for name, form in probe.items():
            if re.search(r"\b" + name, e):
                checked += 1
                if form not in t:
                    bad += 1
                    print(f"  row {i}: {e!r} -> {t!r} (expected {form!r})")
    if bad:
        # One failure is almost always a word that disagrees with the shipped text; many at once
        # is the list having slipped a row. Both need fixing, but they are not the same problem.
        kind = "the list has slipped a row" if bad > 3 else "the wording disagrees with the edition"
        sys.exit(f"{bad} of {checked} proper-noun rows do not line up — {kind}")

    out = SC / "tr" / lang / f"{nn}.tsv"
    out.write_text("".join(f"{e}\t{t}\n" for e, t in zip(en, tr)), encoding="utf-8")
    print(f"{lang} chunk {nn}: {len(en)} pairs, {checked} proper-noun rows aligned")

if __name__ == "__main__":
    main()
