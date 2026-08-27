#!/usr/bin/env python3
"""Extract real advance widths from a TrueType font, for seo_tools/typography.py.

A development tool, not part of the runtime. The width table in typography.py was
originally hand-written from published Arial metrics, which is exactly the kind of
number this repo tells you not to trust without a source. This reads the source.

    python3 scripts/extract_font_widths.py --font /path/to/arial.ttf --verify
    python3 scripts/extract_font_widths.py --font /path/to/arial.ttf --emit cyrillic

Parses only what it needs from the font: the table directory, `head` for
unitsPerEm, `hhea` for the metric count, `hmtx` for the widths, and `cmap`
format 4 to map characters to glyphs. Standard library only, like everything else.

Metric-compatible substitutes work too. Liberation Sans is designed to match
Arial's advance widths exactly, so it produces the same table and is open licensed.
"""
from __future__ import annotations

import argparse
import struct
import sys
import unicodedata
from typing import Dict, Optional

# Ranges worth tabulating, and why each is or is not measurable per character.
SCRIPTS = {
    "latin": (0x0020, 0x024F),
    "greek": (0x0370, 0x03FF),
    "cyrillic": (0x0400, 0x04FF),
    "hebrew": (0x0590, 0x05FF),
    "arabic": (0x0600, 0x06FF),
    "devanagari": (0x0900, 0x097F),
    "punctuation": (0x2000, 0x206F),
}


class Font:
    def __init__(self, path: str) -> None:
        with open(path, "rb") as handle:
            self.data = handle.read()
        self.tables = self._read_table_directory()
        self.units_per_em = self._read_units_per_em()
        self.widths = self._read_hmtx()
        self.cmap = self._read_cmap4()

    def _read_table_directory(self) -> Dict[str, tuple]:
        tag = self.data[:4]
        if tag == b"ttcf":
            raise SystemExit("font collections (.ttc) are not supported, pass a single .ttf")
        num_tables = struct.unpack(">H", self.data[4:6])[0]
        tables = {}
        for index in range(num_tables):
            offset = 12 + index * 16
            name, _checksum, table_offset, length = struct.unpack(
                ">4sLLL", self.data[offset : offset + 16]
            )
            tables[name.decode("ascii", "replace")] = (table_offset, length)
        for required in ("head", "hhea", "hmtx", "cmap", "maxp"):
            if required not in tables:
                raise SystemExit("font is missing the {} table".format(required))
        return tables

    def _read_units_per_em(self) -> int:
        offset = self.tables["head"][0]
        return struct.unpack(">H", self.data[offset + 18 : offset + 20])[0]

    def _read_hmtx(self) -> Dict[int, int]:
        hhea = self.tables["hhea"][0]
        num_metrics = struct.unpack(">H", self.data[hhea + 34 : hhea + 36])[0]
        maxp = self.tables["maxp"][0]
        num_glyphs = struct.unpack(">H", self.data[maxp + 4 : maxp + 6])[0]
        hmtx = self.tables["hmtx"][0]

        widths: Dict[int, int] = {}
        last = 0
        for glyph in range(num_glyphs):
            if glyph < num_metrics:
                position = hmtx + glyph * 4
                last = struct.unpack(">H", self.data[position : position + 2])[0]
            # Glyphs past numberOfHMetrics all share the final advance width.
            widths[glyph] = last
        return widths

    def _read_cmap4(self) -> Dict[int, int]:
        base = self.tables["cmap"][0]
        num_subtables = struct.unpack(">H", self.data[base + 2 : base + 4])[0]
        chosen: Optional[int] = None
        for index in range(num_subtables):
            record = base + 4 + index * 8
            platform, encoding, offset = struct.unpack(">HHL", self.data[record : record + 8])
            fmt = struct.unpack(">H", self.data[base + offset : base + offset + 2])[0]
            # Prefer a Windows Unicode BMP subtable in format 4.
            if fmt == 4 and (platform, encoding) in ((3, 1), (0, 3), (0, 4), (3, 10)):
                chosen = base + offset
                break
            if fmt == 4 and chosen is None:
                chosen = base + offset
        if chosen is None:
            raise SystemExit("no format 4 cmap subtable found")

        seg_x2 = struct.unpack(">H", self.data[chosen + 6 : chosen + 8])[0]
        segments = seg_x2 // 2
        ends_at = chosen + 14
        starts_at = ends_at + seg_x2 + 2
        deltas_at = starts_at + seg_x2
        ranges_at = deltas_at + seg_x2

        mapping: Dict[int, int] = {}
        for segment in range(segments):
            end = struct.unpack(">H", self.data[ends_at + segment * 2 : ends_at + segment * 2 + 2])[0]
            start = struct.unpack(">H", self.data[starts_at + segment * 2 : starts_at + segment * 2 + 2])[0]
            delta = struct.unpack(">h", self.data[deltas_at + segment * 2 : deltas_at + segment * 2 + 2])[0]
            range_offset = struct.unpack(
                ">H", self.data[ranges_at + segment * 2 : ranges_at + segment * 2 + 2]
            )[0]
            if start == 0xFFFF:
                continue
            for code in range(start, min(end, 0xFFFE) + 1):
                if range_offset == 0:
                    glyph = (code + delta) & 0xFFFF
                else:
                    position = ranges_at + segment * 2 + range_offset + (code - start) * 2
                    if position + 2 > len(self.data):
                        continue
                    glyph = struct.unpack(">H", self.data[position : position + 2])[0]
                    if glyph:
                        glyph = (glyph + delta) & 0xFFFF
                if glyph:
                    mapping[code] = glyph
        return mapping

    def width(self, char: str) -> Optional[int]:
        """Advance width in units per 1000 em, or None if the font lacks the glyph."""
        glyph = self.cmap.get(ord(char))
        if not glyph:
            return None
        raw = self.widths.get(glyph)
        if raw is None:
            return None
        return round(raw * 1000 / self.units_per_em)


def verify(font: Font) -> int:
    """Check the table in typography.py against the font. Exit 1 on a mismatch."""
    sys.path.insert(0, ".")
    from seo_tools.typography import ARIAL, DEFAULT_WIDTH

    mismatches, missing = [], []
    for char, claimed in sorted(ARIAL.items()):
        actual = font.width(char)
        if actual is None:
            missing.append(char)
        elif actual != claimed:
            mismatches.append((char, claimed, actual))

    print("{} entries checked against the font".format(len(ARIAL)))
    if missing:
        print("  not in this font: {}".format(" ".join(repr(c) for c in missing)))
    for char, claimed, actual in mismatches:
        print(
            "  MISMATCH U+{:04X} {!r}: table says {}, font says {}".format(
                ord(char), char, claimed, actual
            )
        )
    print("  DEFAULT_WIDTH is {}".format(DEFAULT_WIDTH))
    print("FAIL" if mismatches else "PASS")
    return 1 if mismatches else 0


def emit(font: Font, script: str) -> int:
    """Print a Python dict literal for one script, ready to paste."""
    if script not in SCRIPTS:
        raise SystemExit("unknown script {!r}. Known: {}".format(script, ", ".join(SCRIPTS)))
    low, high = SCRIPTS[script]
    rows, absent = [], 0
    for code in range(low, high + 1):
        char = chr(code)
        category = unicodedata.category(char)
        if category in ("Cn", "Cc", "Cf"):
            continue
        width = font.width(char)
        if width is None:
            absent += 1
            continue
        if unicodedata.combining(char):
            continue  # measured at zero by char_units, no table entry needed
        rows.append((code, char, width))

    print("# {}: {} glyphs in this font, {} absent".format(script, len(rows), absent))
    print("{}: Dict[str, int] = {{".format(script.upper()))
    line = "    "
    for code, char, width in rows:
        entry = '"\\u{:04x}": {}, '.format(code, width)
        if len(line) + len(entry) > 96:
            print(line.rstrip())
            line = "    "
        line += entry
    if line.strip():
        print(line.rstrip())
    print("}")
    return 0


MODULE_HEADER = '''"""Advance widths extracted from a font. GENERATED, do not edit by hand.

Regenerate with:

    python3 scripts/extract_font_widths.py --font <font.ttf> --write-module

Only scripts where one codepoint renders as one glyph with a fixed advance are
included, because that is the condition under which summing per-character widths
means anything. Cyrillic, Greek and Hebrew satisfy it. Arabic does not: it is
cursive, letters change form and join depending on neighbours, so the isolated
advance width of each codepoint is not what renders. Devanagari and the other
Indic scripts are absent from Arial entirely, so anything measured there is a
different font's metrics. Both are reported as unreliable rather than guessed at.

Source font: {source}, {units} units per em, {count} widths.
Liberation Sans is metrically compatible with Arial and openly licensed, so it
regenerates an identical table if you would rather not read a proprietary font.
"""

'''


def write_module(font: Font, source: str) -> int:
    """Generate seo_tools/_widths.py from the font, so nothing is transcribed by hand."""
    import pathlib

    measurable = ("cyrillic", "greek", "hebrew")
    tables: Dict[str, Dict[str, int]] = {}
    for script in measurable:
        low, high = SCRIPTS[script]
        entries: Dict[str, int] = {}
        for code in range(low, high + 1):
            char = chr(code)
            if unicodedata.category(char) in ("Cn", "Cc", "Cf") or unicodedata.combining(char):
                continue
            width = font.width(char)
            if width is not None:
                entries[char] = width
        tables[script] = entries

    total = sum(len(v) for v in tables.values())
    lines = [MODULE_HEADER.format(source=source, units=font.units_per_em, count=total)]
    lines.append("from typing import Dict\n")
    for script in measurable:
        lines.append("\n{}: Dict[str, int] = {{".format(script.upper()))
        line = "    "
        for char, width in sorted(tables[script].items()):
            entry = '"\\u{:04x}": {}, '.format(ord(char), width)
            if len(line) + len(entry) > 96:
                lines.append(line.rstrip())
                line = "    "
            line += entry
        if line.strip():
            lines.append(line.rstrip())
        lines.append("}\n")

    lines.append("\n# Everything measurable, merged.")
    lines.append("EXTRA_WIDTHS: Dict[str, int] = {}")
    lines.append("for _table in (CYRILLIC, GREEK, HEBREW):")
    lines.append("    EXTRA_WIDTHS.update(_table)")
    lines.append("")

    target = pathlib.Path("seo_tools/_widths.py")
    target.write_text("\n".join(lines), encoding="utf-8")
    print("wrote {} with {} widths across {}".format(target, total, ", ".join(measurable)))
    for script in measurable:
        print("  {}: {}".format(script, len(tables[script])))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--font", required=True, help="path to a .ttf file")
    parser.add_argument("--verify", action="store_true", help="check typography.py against it")
    parser.add_argument("--emit", help="print a table for one script: " + ", ".join(SCRIPTS))
    parser.add_argument("--char", help="print the width of one character and exit")
    parser.add_argument(
        "--write-module", action="store_true", help="generate seo_tools/_widths.py"
    )
    args = parser.parse_args()

    font = Font(args.font)
    print("# {} unitsPerEm, {} mapped characters".format(font.units_per_em, len(font.cmap)))

    if args.char:
        for char in args.char:
            print("U+{:04X} {!r}  {}".format(ord(char), char, font.width(char)))
        return 0
    if args.verify:
        return verify(font)
    if args.emit:
        return emit(font, args.emit)
    if args.write_module:
        return write_module(font, args.font)
    parser.error("pass --verify, --emit, --char or --write-module")


if __name__ == "__main__":
    sys.exit(main())
