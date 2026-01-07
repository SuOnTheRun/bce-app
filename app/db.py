import os
import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_DB_PATH = os.getenv("BCE_DB_PATH", "/tmp/bce_case_library.sqlite3")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  category TEXT,
  market TEXT,
  channels TEXT,
  objective TEXT,
  decision_type TEXT,
  primary_tension TEXT,
  decision_window TEXT,
  input_json TEXT NOT NULL,
  decision_map_json TEXT NOT NULL,
  brief_text TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cases_created_at ON cases(created_at);
CREATE INDEX IF NOT EXISTS idx_cases_core ON cases(category, market, decision_type, decision_window);
"""

def _connect(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    p = Path(db_path)
    if p.parent and str(p.parent) != ".":
        p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    conn = _connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()

def insert_case(
    input_used: Dict[str, Any],
    decision_map_json: str,
    brief_text: str,
    db_path: str = DEFAULT_DB_PATH
) -> int:
    init_db(db_path)

    campaign = (input_used or {}).get("campaign", {}) or {}

    category = (campaign.get("Category") or "").strip()
    market = (campaign.get("Market") or "").strip()
    channels = (campaign.get("Channels") or "").strip()
    objective = (campaign.get("Objective") or "").strip()

    decision_type = (campaign.get("Decision_Type") or "").strip()
    primary_tension = (campaign.get("Primary_Tension") or "").strip()
    decision_window = (campaign.get("Decision_Window") or "").strip()

    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO cases (
              category, market, channels, objective,
              decision_type, primary_tension, decision_window,
              input_json, decision_map_json, brief_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                category, market, channels, objective,
                decision_type, primary_tension, decision_window,
                json.dumps(input_used, ensure_ascii=False),
                decision_map_json,
                brief_text
            )
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()

def list_cases(
    limit: int = 100,
    offset: int = 0,
    q: Optional[str] = None,
    category: Optional[str] = None,
    market: Optional[str] = None,
    decision_type: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Tuple[List[Dict[str, Any]], int]:
    init_db(db_path)
    conn = _connect(db_path)
    try:
        where = []
        params: List[Any] = []

        if q:
            where.append("(objective LIKE ? OR channels LIKE ? OR brief_text LIKE ?)")
            like = f"%{q}%"
            params.extend([like, like, like])

        if category:
            where.append("category = ?")
            params.append(category)

        if market:
            where.append("market = ?")
            params.append(market)

        if decision_type:
            where.append("decision_type = ?")
            params.append(decision_type)

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        total = conn.execute(f"SELECT COUNT(*) AS c FROM cases {where_sql}", params).fetchone()["c"]

        rows = conn.execute(
            f"""
            SELECT id, created_at, category, market, channels, objective, decision_type, primary_tension, decision_window
            FROM cases
            {where_sql}
            ORDER BY datetime(created_at) DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        ).fetchall()

        return [dict(r) for r in rows], int(total)
    finally:
        conn.close()

def get_case(case_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    init_db(db_path)
    conn = _connect(db_path)
    try:
        row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def export_db_bytes(db_path: str = DEFAULT_DB_PATH) -> bytes:
    init_db(db_path)
    p = Path(db_path)
    return p.read_bytes()

def export_jsonl(db_path: str = DEFAULT_DB_PATH) -> str:
    init_db(db_path)
    conn = _connect(db_path)
    try:
        rows = conn.execute("SELECT * FROM cases ORDER BY datetime(created_at) DESC").fetchall()
        lines = []
        for r in rows:
            d = dict(r)
            lines.append(json.dumps(d, ensure_ascii=False))
        return "\n".join(lines)
    finally:
        conn.close()

def import_jsonl(text: str, db_path: str = DEFAULT_DB_PATH) -> int:
    init_db(db_path)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        inserted = 0
        for line in (text or "").splitlines():
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)

            # Insert into the current schema (ignore original id)
            cur.execute(
                """
                INSERT INTO cases (
                  created_at, category, market, channels, objective,
                  decision_type, primary_tension, decision_window,
                  input_json, decision_map_json, brief_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    d.get("created_at") or "datetime('now')",
                    d.get("category") or "",
                    d.get("market") or "",
                    d.get("channels") or "",
                    d.get("objective") or "",
                    d.get("decision_type") or "",
                    d.get("primary_tension") or "",
                    d.get("decision_window") or "",
                    d.get("input_json") or "{}",
                    d.get("decision_map_json") or "{}",
                    d.get("brief_text") or "",
                )
            )
            inserted += 1
        conn.commit()
        return inserted
    finally:
        conn.close()
