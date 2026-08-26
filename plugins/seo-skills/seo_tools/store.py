"""Baseline storage in SQLite, so a run can be compared with the last one.

Without this the pack has no memory: every audit starts from nothing and
"did anything change" is unanswerable. With it, /technical-audit can open with
what moved since the last check instead of a fresh inventory.

Location, in order: SEO_SKILLS_HOME if set, then a project-local .seo/
directory if one exists (which is also where the site profile lives, and which
.gitignore already excludes), then the user cache directory. Project-local is
preferred so a baseline travels with the project it describes.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .safety import normalise_url

SCHEMA_VERSION = 1

TRACKED_FIELDS = (
    "status",
    "title",
    "meta_description",
    "canonical",
    "meta_robots",
    "html_lang",
    "h1",
    "h2",
    "h3",
    "schema_types",
    "open_graph",
    "word_count",
    "main_word_count",
    "links_internal",
    "links_external",
    "images",
    "images_missing_alt",
    "requires_js",
)

DDL = """
CREATE TABLE IF NOT EXISTS baselines (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    url_key      TEXT NOT NULL,
    url          TEXT NOT NULL,
    captured_at  TEXT NOT NULL,
    label        TEXT,
    status       INTEGER,
    html_hash    TEXT,
    schema_hash  TEXT,
    payload      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS baselines_url_key ON baselines (url_key, captured_at);

CREATE TABLE IF NOT EXISTS comparisons (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    url_key        TEXT NOT NULL,
    baseline_id    INTEGER NOT NULL,
    compared_at    TEXT NOT NULL,
    critical       INTEGER NOT NULL DEFAULT 0,
    warning        INTEGER NOT NULL DEFAULT 0,
    info           INTEGER NOT NULL DEFAULT 0,
    payload        TEXT NOT NULL,
    FOREIGN KEY (baseline_id) REFERENCES baselines (id)
);
CREATE INDEX IF NOT EXISTS comparisons_url_key ON comparisons (url_key, compared_at);

CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def default_home() -> pathlib.Path:
    override = os.environ.get("SEO_SKILLS_HOME")
    if override:
        return pathlib.Path(override).expanduser()
    project = pathlib.Path.cwd() / ".seo"
    if project.is_dir():
        return project
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or (pathlib.Path.home() / "AppData" / "Local")
        return pathlib.Path(base) / "seo-skills"
    return pathlib.Path(
        os.environ.get("XDG_CACHE_HOME") or (pathlib.Path.home() / ".cache")
    ) / "seo-skills"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Store:
    """Thin wrapper over SQLite. Parameterised queries only, no interpolation."""

    def __init__(self, home: Optional[pathlib.Path] = None) -> None:
        self.home = pathlib.Path(home) if home else default_home()
        self.home.mkdir(parents=True, exist_ok=True)
        self.path = self.home / "baselines.db"
        self.connection = sqlite3.connect(str(self.path))
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(DDL)
        self.connection.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            ("schema_version", str(SCHEMA_VERSION)),
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- writes ----------------------------------------------------------

    def save_baseline(
        self, url: str, page: Dict[str, object], html: str, label: Optional[str] = None
    ) -> Dict[str, object]:
        snapshot = {field: page.get(field) for field in TRACKED_FIELDS}
        html_hash = hashlib.sha256((html or "").encode("utf-8", "replace")).hexdigest()
        schema_hash = hashlib.sha256(
            json.dumps(page.get("schema_blocks") or [], sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        captured_at = now_iso()
        cursor = self.connection.execute(
            "INSERT INTO baselines (url_key, url, captured_at, label, status, html_hash, schema_hash, payload)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                normalise_url(url),
                url,
                captured_at,
                label,
                page.get("status"),
                html_hash,
                schema_hash,
                json.dumps(snapshot, sort_keys=True, default=str),
            ),
        )
        self.connection.commit()
        return {
            "baseline_id": cursor.lastrowid,
            "url": url,
            "url_key": normalise_url(url),
            "captured_at": captured_at,
            "label": label,
            "html_hash": html_hash,
            "schema_hash": schema_hash,
            "fields_captured": len(snapshot),
            "database": str(self.path),
        }

    def save_comparison(self, url: str, baseline_id: int, result: Dict[str, object]) -> int:
        counts = result.get("counts") or {}
        cursor = self.connection.execute(
            "INSERT INTO comparisons (url_key, baseline_id, compared_at, critical, warning, info, payload)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                normalise_url(url),
                baseline_id,
                now_iso(),
                int(counts.get("critical", 0)),
                int(counts.get("warning", 0)),
                int(counts.get("info", 0)),
                json.dumps(result, sort_keys=True, default=str),
            ),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    # -- reads -----------------------------------------------------------

    def latest_baseline(self, url: str) -> Optional[Dict[str, object]]:
        row = self.connection.execute(
            "SELECT * FROM baselines WHERE url_key = ? ORDER BY captured_at DESC, id DESC LIMIT 1",
            (normalise_url(url),),
        ).fetchone()
        return self._row_to_baseline(row) if row else None

    def baseline_by_id(self, baseline_id: int) -> Optional[Dict[str, object]]:
        row = self.connection.execute(
            "SELECT * FROM baselines WHERE id = ?", (int(baseline_id),)
        ).fetchone()
        return self._row_to_baseline(row) if row else None

    def history(self, url: str, limit: int = 20) -> Dict[str, object]:
        key = normalise_url(url)
        baselines = [
            self._row_to_baseline(row)
            for row in self.connection.execute(
                "SELECT * FROM baselines WHERE url_key = ? ORDER BY captured_at DESC, id DESC LIMIT ?",
                (key, int(limit)),
            ).fetchall()
        ]
        comparisons = [
            {
                "id": row["id"],
                "baseline_id": row["baseline_id"],
                "compared_at": row["compared_at"],
                "critical": row["critical"],
                "warning": row["warning"],
                "info": row["info"],
            }
            for row in self.connection.execute(
                "SELECT id, baseline_id, compared_at, critical, warning, info FROM comparisons"
                " WHERE url_key = ? ORDER BY compared_at DESC, id DESC LIMIT ?",
                (key, int(limit)),
            ).fetchall()
        ]
        return {
            "url": url,
            "url_key": key,
            "database": str(self.path),
            "baselines": baselines,
            "comparisons": comparisons,
        }

    @staticmethod
    def _row_to_baseline(row: sqlite3.Row) -> Dict[str, object]:
        return {
            "baseline_id": row["id"],
            "url": row["url"],
            "url_key": row["url_key"],
            "captured_at": row["captured_at"],
            "label": row["label"],
            "status": row["status"],
            "html_hash": row["html_hash"],
            "schema_hash": row["schema_hash"],
            "snapshot": json.loads(row["payload"]),
        }
