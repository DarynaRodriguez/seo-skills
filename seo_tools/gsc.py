"""Search Console CSV analysis, so the pack is useful with no paid connector.

Anyone with a verified property can export a CSV. That export is real received
traffic, which makes it the only trustworthy number in most SEO work, and it
costs nothing. Everything here runs on those files.

Tolerant about input because the export differs by locale and by where it came
from: the GSC UI, the API, Looker Studio, or a tool re-export. Column names are
matched loosely, numbers are parsed with either decimal separator, and any
column that is missing simply disables the analyses that need it rather than
failing the run.
"""
from __future__ import annotations

import csv
import io
import pathlib
import re
import statistics
from typing import Dict, Iterable, List, Optional, Sequence

# Header aliases, lowercased and stripped of punctuation before matching.
# English and German cover the GSC UI exports this is most likely to meet.
# Search Console localises its export headers, so an English-only alias list makes
# the whole module English-only. These cover the UI export in the languages most
# likely to turn up. Anything unlisted is handled by --columns, so a locale that
# is missing here is an inconvenience rather than a wall.
COLUMN_ALIASES: Dict[str, Sequence[str]] = {
    "query": (
        "query", "queries", "top queries", "search query", "keyword", "keywords",
        "suchanfrage", "suchanfragen", "haufigste suchanfragen",          # de
        "requete", "requetes", "requetes les plus frequentes",            # fr
        "consulta", "consultas", "consultas principales",                 # es
        "query principali",                                              # it
        "zoekopdracht", "populairste zoekopdrachten",                     # nl
        "consultas mais frequentes", "principais consultas",              # pt
        "zapytanie", "najpopularniejsze zapytania",                       # pl
        "sokfraga", "vanligaste sokfragorna",                             # sv
        "sogeord", "mest almindelige sogeord",                            # da
        "hakusanat", "suosituimmat kyselyt",                              # fi
        "sorgu", "en populer sorgular",                                   # tr
        "dotaz", "nejcastejsi dotazy",                                    # cs
        "zapros", "zaprosy", "poiskovyy zapros",                          # ru transliterated
        "поисковый запрос", "запрос", "запросы",              # ru
        "上位のクエリ", "クエリ",                                            # ja
        "인기 검색어", "검색어",                                             # ko
        "热门查询", "查询",                                                 # zh
    ),
    "page": (
        "page", "pages", "top pages", "landing page", "url", "urls", "address",
        "seite", "seiten", "haufigste seiten",                             # de
        "pages les plus frequentes", "page de destination",                # fr
        "paginas principales", "pagina",                                   # es
        "pagine principali",                                              # it
        "populairste paginas",                                            # nl
        "paginas mais frequentes",                                        # pt
        "najpopularniejsze strony", "strona",                              # pl
        "vanligaste sidorna", "sida",                                      # sv
        "mest almindelige sider",                                          # da
        "suosituimmat sivut",                                              # fi
        "en populer sayfalar", "sayfa",                                    # tr
        "nejcastejsi stranky",                                             # cs
        "上位のページ", "ページ",                                            # ja
        "인기 페이지", "페이지",                                              # ko
        "热门网页", "网页",                                                  # zh
        "страница", "страницы",                                     # ru
    ),
    "clicks": (
        "clicks", "click", "klicks", "clics", "clic", "kliks", "klikken",
        "cliques", "klikniecia", "klick", "klik", "napsautukset", "tiklama",
        "kliknuti", "клики", "クリック数", "클릭수", "点击次数",
    ),
    "impressions": (
        "impressions", "impression", "impressionen", "impresiones", "impressioni",
        "vertoningen", "impressoes", "wyswietlenia", "visningar", "eksponeringar",
        "nayttokerrat", "goruntuleme", "zobrazeni", "показы",
        "表示回数", "노출수", "展示次数",
    ),
    "ctr": (
        "ctr", "click through rate", "clickthrough rate", "klickrate",
        "taux de clics", "porcentaje de clics", "percentuale di clic",
        "doorklikratio", "taxa de cliques", "wspolczynnik klikniec",
        "klickfrekvens", "napsautussuhde", "tiklama orani", "mira prokliku",
        "ctr（クリック率）", "클릭률", "点击率",
    ),
    "position": (
        "position", "average position", "avg position", "pos",
        "durchschnittliche position", "position moyenne", "posicion",
        "posicion media", "posizione", "posizione media", "positie",
        "posicao", "pozycja", "genomsnittlig position", "keskimaarainen sijainti",
        "ortalama konum", "prumerna pozice", "позиция",
        "掲載順位", "平均掲載順位", "掲出順位",           # ja
        "평균 게재순위", "게재순위",                                # ko
        "平均排名",                                                  # zh
    ),
    "country": ("country", "land", "pays", "pais", "paese", "kraj", "ulke", "国", "국가", "国家/地区"),
    "device": ("device", "gerat", "appareil", "dispositivo", "apparaat", "urzadzenie", "cihaz", "デバイス", "기기", "设备"),
    "date": ("date", "datum", "fecha", "data", "tarih", "日付", "날짜", "日期"),
}

_PUNCT = re.compile(r"[^a-z0-9 ]+")


class GscError(ValueError):
    """Raised when a file cannot be read as a Search Console export."""


ACCENT_FOLD = {
    # German, Nordic
    "ä": "a", "ö": "o", "ü": "u", "ß": "ss", "å": "a", "ø": "o", "æ": "ae",
    # Romance
    "á": "a", "à": "a", "â": "a", "ã": "a", "é": "e", "è": "e", "ê": "e",
    "ë": "e", "í": "i", "ì": "i", "î": "i", "ï": "i", "ó": "o", "ò": "o",
    "ô": "o", "õ": "o", "ú": "u", "ù": "u", "û": "u", "ñ": "n", "ç": "c",
    # Polish
    "ł": "l", "ę": "e", "ą": "a", "ś": "s", "ż": "z", "ź": "z", "ć": "c", "ń": "n",
    # Czech, Slovak
    "č": "c", "ř": "r", "š": "s", "ž": "z", "ý": "y", "ď": "d", "ť": "t",
    "ň": "n", "ů": "u", "ě": "e",
    # Turkish
    "ı": "i", "ş": "s", "ğ": "g", "İ": "i",
    # Romanian, Baltic
    "ă": "a", "ș": "s", "ț": "t", "ū": "u", "ė": "e", "į": "i",
}

# Strip punctuation and symbols, keep letters and digits of every script. The
# previous ASCII-only class deleted CJK, Cyrillic and Greek headers entirely,
# which silently made this module Latin-only.
_NON_WORD = re.compile(r"[^\w\s]+", re.UNICODE)


def _canonical_header(raw: str) -> Optional[str]:
    """Match a header cell to a canonical column name.

    Two ordering traps, both of which produced silent failures:

    Accents are folded before punctuation is stripped. The other order deletes
    them, turning "Haufigste" spelled with an umlaut into "h ufigste".

    Punctuation stripping is Unicode-aware. An ASCII-only class removes every
    Japanese, Korean, Chinese and Cyrillic character, so those headers reduce to
    an empty string and never match anything.
    """
    cleaned = (raw or "").strip().lower()
    for accented, plain in ACCENT_FOLD.items():
        cleaned = cleaned.replace(accented, plain)
    cleaned = " ".join(_NON_WORD.sub(" ", cleaned).split())
    if not cleaned:
        return None
    for canonical, aliases in COLUMN_ALIASES.items():
        if cleaned in aliases:
            return canonical
    return None


CANONICAL_COLUMNS = tuple(COLUMN_ALIASES)


def parse_column_override(spec: str, header_length: int) -> Dict[int, str]:
    """Turn a --columns spec into a positional mapping.

    The escape hatch for any locale or tool export the aliases do not cover:
    name the columns in order, using `-` to skip one.

        --columns query,clicks,impressions,-,position
    """
    names = [part.strip().lower() for part in (spec or "").split(",")]
    mapping: Dict[int, str] = {}
    for index, name in enumerate(names):
        if not name or name == "-":
            continue
        if name not in CANONICAL_COLUMNS:
            raise GscError(
                "unknown column name {!r} in --columns. Valid names: {}".format(
                    name, ", ".join(CANONICAL_COLUMNS)
                )
            )
        if index >= header_length:
            raise GscError(
                "--columns names {} columns but the file has {}".format(
                    len(names), header_length
                )
            )
        mapping[index] = name
    if not mapping:
        raise GscError("--columns did not name any usable column")
    return mapping


_GROUPED_DOT = re.compile(r"^\d{1,3}(\.\d{3})+$")
_GROUPED_COMMA = re.compile(r"^\d{1,3}(,\d{3})+$")
_DECIMAL_COMMA = re.compile(r"\d,\d{1,2}(?!\d)")
_SPACES = (" ", " ", " ")


def parse_number(raw, decimal_comma=None):
    """Parse a number out of a CSV cell, tolerating locale and percent signs.

    `decimal_comma` resolves the one genuinely ambiguous case. "4.000" is four
    thousand in a German export and four in an English one, and no amount of
    staring at that cell alone will tell you which. load_csv decides once per
    file and passes the answer down. When it is None the digit grouping pattern
    decides, which reads "4.000" as four thousand.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip()
    if not text or text in ("-", "--"):
        return None
    percent = text.endswith("%")
    text = text.rstrip("%").strip()
    for space in _SPACES:
        text = text.replace(space, "")

    if "," in text and "." in text:
        # Both present: whichever sits further right is the decimal separator.
        if text.rfind(".") > text.rfind(","):
            text = text.replace(",", "")
        else:
            text = text.replace(".", "").replace(",", ".")
    elif decimal_comma is True:
        # European: the dot groups thousands, the comma is the decimal point.
        if _GROUPED_DOT.match(text):
            text = text.replace(".", "")
        text = text.replace(",", ".")
    elif decimal_comma is False:
        # Anglo: the comma groups thousands, the dot is the decimal point.
        text = text.replace(",", "")
    elif _GROUPED_DOT.match(text):
        text = text.replace(".", "")
    elif _GROUPED_COMMA.match(text):
        text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")

    try:
        value = float(text)
    except ValueError:
        return None
    return value / 100.0 if percent else value


def detect_decimal_comma(text, delimiter):
    """Decide once per file whether commas are decimal points.

    A semicolon delimiter is the strongest signal: that is what a spreadsheet
    writes when the locale already spends the comma on decimals. Failing that,
    look for a value shaped like "4,2" or "0,5" in the body.
    """
    if delimiter == ";":
        return True
    if _DECIMAL_COMMA.search(text):
        return True
    return False


def load_csv(path: str, columns: Optional[str] = None) -> Dict[str, object]:
    """Read one export. Returns rows with canonical keys plus what was detected.

    `columns` is the positional override for a locale or tool the aliases do
    not cover. See parse_column_override.
    """
    file_path = pathlib.Path(path)
    if not file_path.is_file():
        raise GscError("no such file: {}".format(path))
    raw = file_path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise GscError("could not decode {} as text".format(path))

    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";" if sample.count(";") > sample.count(",") else ","

    decimal_comma = detect_decimal_comma(text, delimiter)

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    try:
        header = next(reader)
    except StopIteration:
        raise GscError("{} is empty".format(path))

    if columns:
        mapping = parse_column_override(columns, len(header))
        resolved_by = "the --columns override"
    else:
        mapping = {}
        for index, cell in enumerate(header):
            canonical = _canonical_header(cell)
            if canonical and canonical not in mapping.values():
                mapping[index] = canonical
        resolved_by = "header names"
        if not mapping:
            raise GscError(
                "no recognisable columns in {}. Header was: {}. If this export is in a "
                "language the aliases do not cover, name the columns positionally with "
                "--columns query,clicks,impressions,ctr,position (use - to skip one).".format(
                    path, ", ".join(header[:8])
                )
            )

    rows: List[Dict[str, object]] = []
    for values in reader:
        if not any(str(v).strip() for v in values):
            continue
        row: Dict[str, object] = {}
        for index, canonical in mapping.items():
            if index >= len(values):
                continue
            cell = values[index]
            if canonical in ("clicks", "impressions", "ctr", "position"):
                row[canonical] = parse_number(cell, decimal_comma)
            else:
                row[canonical] = str(cell).strip()
        rows.append(row)

    # Recompute CTR wherever it is absent but derivable, so analyses can rely on it.
    for row in rows:
        if row.get("ctr") is None:
            clicks = row.get("clicks")
            impressions = row.get("impressions")
            if isinstance(clicks, float) and isinstance(impressions, float) and impressions:
                row["ctr"] = clicks / impressions

    return {
        "path": str(file_path),
        "delimiter": delimiter,
        "decimal_comma": decimal_comma,
        "columns_resolved_by": resolved_by,
        "columns_detected": sorted(set(mapping.values())),
        "columns_ignored": [
            header[i] for i in range(len(header)) if i not in mapping and str(header[i]).strip()
        ],
        "row_count": len(rows),
        "rows": rows,
    }


def summarise(rows: Iterable[Dict[str, object]]) -> Dict[str, object]:
    """Totals and weighted average position, which is not the mean of positions."""
    clicks = impressions = 0.0
    weighted_position = 0.0
    positioned_impressions = 0.0
    for row in rows:
        row_clicks = row.get("clicks") or 0
        row_impressions = row.get("impressions") or 0
        clicks += float(row_clicks)
        impressions += float(row_impressions)
        position = row.get("position")
        if isinstance(position, float) and row_impressions:
            weighted_position += position * float(row_impressions)
            positioned_impressions += float(row_impressions)
    return {
        "clicks": int(clicks),
        "impressions": int(impressions),
        "ctr": round(clicks / impressions, 4) if impressions else None,
        "avg_position_impression_weighted": (
            round(weighted_position / positioned_impressions, 2) if positioned_impressions else None
        ),
    }


def striking_distance(
    rows: Sequence[Dict[str, object]], low: float = 8.0, high: float = 20.0, min_impressions: float = 100
) -> List[Dict[str, object]]:
    """Rows ranking just off the visible part of page one, ordered by impressions.

    No claim that these are easy wins. They are the rows where a position gain
    would convert existing impressions into clicks, which is a different and
    checkable statement.
    """
    out = []
    for row in rows:
        position = row.get("position")
        impressions = row.get("impressions") or 0
        if not isinstance(position, float) or not (low <= position <= high):
            continue
        if float(impressions) < min_impressions:
            continue
        out.append(
            {
                "query": row.get("query"),
                "page": row.get("page"),
                "position": round(position, 1),
                "impressions": int(impressions),
                "clicks": int(row.get("clicks") or 0),
                "ctr": round(float(row.get("ctr") or 0), 4),
            }
        )
    out.sort(key=lambda r: r["impressions"], reverse=True)
    return out


def ctr_outliers(
    rows: Sequence[Dict[str, object]], min_impressions: float = 100, tolerance: float = 0.5
) -> Dict[str, object]:
    """Rows whose CTR is far below the median for their own position band.

    The benchmark is this dataset, not an industry curve. That keeps the finding
    honest: nothing here depends on a published CTR table whose provenance the
    reader cannot check.
    """
    bands: Dict[int, List[float]] = {}
    eligible = []
    for row in rows:
        position = row.get("position")
        impressions = float(row.get("impressions") or 0)
        ctr = row.get("ctr")
        if not isinstance(position, float) or not isinstance(ctr, float):
            continue
        if impressions < min_impressions:
            continue
        band = int(position) if position < 21 else 21
        bands.setdefault(band, []).append(ctr)
        eligible.append((band, row, ctr))

    medians = {band: statistics.median(values) for band, values in bands.items() if len(values) >= 3}
    findings = []
    for band, row, ctr in eligible:
        median = medians.get(band)
        if median is None or median <= 0:
            continue
        if ctr < median * tolerance:
            findings.append(
                {
                    "query": row.get("query"),
                    "page": row.get("page"),
                    "position": round(float(row["position"]), 1),
                    "impressions": int(row.get("impressions") or 0),
                    "ctr": round(ctr, 4),
                    "band_median_ctr": round(median, 4),
                    "shortfall_pct": round((1 - ctr / median) * 100, 1),
                }
            )
    findings.sort(key=lambda r: r["impressions"], reverse=True)
    return {
        "band_medians": {str(k): round(v, 4) for k, v in sorted(medians.items())},
        "benchmark": "median CTR per whole-number position band within this export",
        "min_impressions": min_impressions,
        "tolerance": tolerance,
        "findings": findings,
    }


def cannibalisation(
    rows: Sequence[Dict[str, object]], min_impressions: float = 50, min_share: float = 0.1
) -> Dict[str, object]:
    """Queries where more than one URL takes a real share of the impressions.

    Requires an export carrying both query and page, which the GSC UI does not
    produce directly: use the API with dimensions query and page, or a Looker
    Studio export. Without those columns this returns a note, not a guess.
    """
    have_query = any(row.get("query") for row in rows)
    have_page = any(row.get("page") for row in rows)
    if not (have_query and have_page):
        return {
            "supported": False,
            "note": "This export has {}. Cannibalisation needs both query and page on the same row: "
            "export with dimensions query and page from the Search Console API, or from Looker Studio.".format(
                "queries only" if have_query else "pages only" if have_page else "neither query nor page"
            ),
            "groups": [],
        }

    grouped: Dict[str, List[Dict[str, object]]] = {}
    for row in rows:
        query = str(row.get("query") or "").strip().lower()
        page = str(row.get("page") or "").strip()
        if not query or not page:
            continue
        grouped.setdefault(query, []).append(row)

    groups = []
    for query, entries in grouped.items():
        by_page: Dict[str, Dict[str, float]] = {}
        for entry in entries:
            page = str(entry.get("page"))
            bucket = by_page.setdefault(page, {"clicks": 0.0, "impressions": 0.0, "position_sum": 0.0, "weight": 0.0})
            impressions = float(entry.get("impressions") or 0)
            bucket["clicks"] += float(entry.get("clicks") or 0)
            bucket["impressions"] += impressions
            position = entry.get("position")
            if isinstance(position, float) and impressions:
                bucket["position_sum"] += position * impressions
                bucket["weight"] += impressions

        total_impressions = sum(b["impressions"] for b in by_page.values())
        if total_impressions < min_impressions or len(by_page) < 2:
            continue
        competing = []
        for page, bucket in by_page.items():
            share = bucket["impressions"] / total_impressions if total_impressions else 0
            if share < min_share:
                continue
            competing.append(
                {
                    "page": page,
                    "clicks": int(bucket["clicks"]),
                    "impressions": int(bucket["impressions"]),
                    "impression_share": round(share, 3),
                    "avg_position": (
                        round(bucket["position_sum"] / bucket["weight"], 1) if bucket["weight"] else None
                    ),
                }
            )
        if len(competing) < 2:
            continue
        competing.sort(key=lambda p: p["impressions"], reverse=True)
        groups.append(
            {
                "query": query,
                "pages_competing": len(competing),
                "total_impressions": int(total_impressions),
                "total_clicks": int(sum(b["clicks"] for b in by_page.values())),
                "pages": competing,
            }
        )
    groups.sort(key=lambda g: g["total_impressions"], reverse=True)
    return {
        "supported": True,
        "min_impressions": min_impressions,
        "min_share": min_share,
        "group_count": len(groups),
        "groups": groups,
    }


def _key_of(row: Dict[str, object], dimension: str) -> Optional[str]:
    value = row.get(dimension)
    if value is None:
        return None
    text = str(value).strip()
    return text.lower() if dimension == "query" else text


def compare_periods(
    current: Sequence[Dict[str, object]],
    previous: Sequence[Dict[str, object]],
    dimension: str = "page",
    min_impressions: float = 50,
) -> Dict[str, object]:
    """Join two exports on page or query and rank what moved.

    This is what /content-decay and /performance-report need and cannot get
    from one export. The two files must cover equal-length, non-overlapping
    periods, which the caller has to arrange; nothing here can verify it, so
    the output says so.
    """
    def fold(rows: Sequence[Dict[str, object]]) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {}
        for row in rows:
            key = _key_of(row, dimension)
            if not key:
                continue
            bucket = out.setdefault(key, {"clicks": 0.0, "impressions": 0.0, "position_sum": 0.0, "weight": 0.0})
            impressions = float(row.get("impressions") or 0)
            bucket["clicks"] += float(row.get("clicks") or 0)
            bucket["impressions"] += impressions
            position = row.get("position")
            if isinstance(position, float) and impressions:
                bucket["position_sum"] += position * impressions
                bucket["weight"] += impressions
        return out

    now = fold(current)
    then = fold(previous)
    if not now or not then:
        return {
            "supported": False,
            "note": "One of the two exports has no {} column, so they cannot be joined.".format(dimension),
            "rows": [],
        }

    rows_out = []
    for key in set(now) | set(then):
        a = now.get(key, {"clicks": 0.0, "impressions": 0.0, "position_sum": 0.0, "weight": 0.0})
        b = then.get(key, {"clicks": 0.0, "impressions": 0.0, "position_sum": 0.0, "weight": 0.0})
        if max(a["impressions"], b["impressions"]) < min_impressions:
            continue
        position_now = a["position_sum"] / a["weight"] if a["weight"] else None
        position_then = b["position_sum"] / b["weight"] if b["weight"] else None
        rows_out.append(
            {
                dimension: key,
                "clicks_now": int(a["clicks"]),
                "clicks_before": int(b["clicks"]),
                "clicks_delta": int(a["clicks"] - b["clicks"]),
                "clicks_delta_pct": (
                    round((a["clicks"] - b["clicks"]) / b["clicks"] * 100, 1) if b["clicks"] else None
                ),
                "impressions_now": int(a["impressions"]),
                "impressions_before": int(b["impressions"]),
                "impressions_delta": int(a["impressions"] - b["impressions"]),
                "position_now": round(position_now, 1) if position_now else None,
                "position_before": round(position_then, 1) if position_then else None,
                "position_delta": (
                    round(position_now - position_then, 1) if position_now and position_then else None
                ),
                "status": (
                    "gone" if a["impressions"] == 0 else "new" if b["impressions"] == 0 else "changed"
                ),
            }
        )

    losers = sorted([r for r in rows_out if r["clicks_delta"] < 0], key=lambda r: r["clicks_delta"])
    winners = sorted([r for r in rows_out if r["clicks_delta"] > 0], key=lambda r: -r["clicks_delta"])
    return {
        "supported": True,
        "dimension": dimension,
        "caveat": "Assumes the two exports cover equal-length, non-overlapping periods. Nothing here can verify that.",
        "totals_now": summarise(current),
        "totals_before": summarise(previous),
        "rows_compared": len(rows_out),
        "biggest_losses": losers[:50],
        "biggest_gains": winners[:50],
        "lost_entirely": [r for r in rows_out if r["status"] == "gone"][:50],
    }
