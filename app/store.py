"""Persistencia SQLite (sandbox). Prod: Postgres/pgvector sin cambiar la API."""
from __future__ import annotations

import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone

DB = os.environ.get("CONTESTA_DB", os.path.join(os.path.dirname(__file__), "..", "contesta.db"))
_lock = threading.Lock()


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _lock, _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS calls(
              id TEXT PRIMARY KEY, business_id TEXT, from_number TEXT,
              caller_name TEXT, transcript TEXT DEFAULT '',
              intent TEXT DEFAULT 'desconocida',
              appointment_id TEXT, escalated INTEGER DEFAULT 0,
              started_at TEXT);
            CREATE TABLE IF NOT EXISTS appointments(
              id TEXT PRIMARY KEY, business_id TEXT, call_id TEXT,
              slot TEXT, service TEXT, status TEXT DEFAULT 'propuesta');
            CREATE TABLE IF NOT EXISTS knowledge(
              id TEXT PRIMARY KEY, business_id TEXT, source TEXT,
              content TEXT, version INTEGER, created_at TEXT);
            CREATE TABLE IF NOT EXISTS voice(
              id TEXT PRIMARY KEY, business_id TEXT, voice_name TEXT,
              consent INTEGER, created_at TEXT);
            """
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---- Calls ----
def create_call(business_id: str, from_number: str, caller_name: str | None) -> dict:
    call_id = "call-" + uuid.uuid4().hex[:8]
    with _lock, _conn() as c:
        c.execute(
            "INSERT INTO calls(id,business_id,from_number,caller_name,started_at)"
            " VALUES(?,?,?,?,?)",
            (call_id, business_id, from_number, caller_name, _now()),
        )
    return get_call(call_id)


def get_call(call_id: str) -> dict | None:
    with _lock, _conn() as c:
        r = c.execute("SELECT * FROM calls WHERE id=?", (call_id,)).fetchone()
        return dict(r) if r else None


def update_call(call_id: str, **kw) -> dict:
    sets = ", ".join(f"{k}=?" for k in kw)
    with _lock, _conn() as c:
        c.execute(f"UPDATE calls SET {sets} WHERE id=?", (*kw.values(), call_id))
    return get_call(call_id)


def list_calls(business_id: str) -> list[dict]:
    with _lock, _conn() as c:
        return [dict(r) for r in
                c.execute("SELECT * FROM calls WHERE business_id=? ORDER BY started_at",
                          (business_id,))]


# ---- Appointments ----
def create_appointment(business_id: str, call_id: str, slot: str, service: str) -> dict:
    ap_id = "apt-" + uuid.uuid4().hex[:8]
    with _lock, _conn() as c:
        c.execute(
            "INSERT INTO appointments(id,business_id,call_id,slot,service,status)"
            " VALUES(?,?,?,?,?,'confirmada')",
            (ap_id, business_id, call_id, slot, service),
        )
    update_call(call_id, appointment_id=ap_id, intent="cita")
    with _lock, _conn() as c:
        r = c.execute("SELECT * FROM appointments WHERE id=?", (ap_id,)).fetchone()
        return dict(r)


def list_appointments(business_id: str) -> list[dict]:
    with _lock, _conn() as c:
        return [dict(r) for r in
                c.execute("SELECT * FROM appointments WHERE business_id=?", (business_id,))]


# ---- Knowledge (wiki auto-mantenida) ----
def add_knowledge(business_id: str, source: str, content: str) -> dict:
    with _lock, _conn() as c:
        row = c.execute(
            "SELECT MAX(version) AS v FROM knowledge WHERE business_id=? AND source=?",
            (business_id, source)).fetchone()
        version = (row["v"] or 0) + 1
        doc_id = "kb-" + uuid.uuid4().hex[:8]
        c.execute(
            "INSERT INTO knowledge(id,business_id,source,content,version,created_at)"
            " VALUES(?,?,?,?,?,?)",
            (doc_id, business_id, source, content, version, _now()),
        )
        return {"id": doc_id, "business_id": business_id, "source": source,
                "version": version}


def search_knowledge(business_id: str, query: str, limit: int = 3) -> list[dict]:
    """Sandbox: ranking por solape de palabras. Prod: embeddings pgvector (WeKnora)."""
    words = {w.strip("¿?¡!.,;:").lower() for w in query.split() if len(w) > 3}
    with _lock, _conn() as c:
        docs = [dict(r) for r in c.execute(
            "SELECT * FROM knowledge WHERE business_id=? ORDER BY version DESC",
            (business_id,))]
    scored = sorted(
        docs,
        key=lambda d: len(words & {w.lower() for w in d["content"].split()}),
        reverse=True,
    )
    return [d for d in scored
            if len(words & {w.lower() for w in d["content"].split()}) > 0][:limit]


# ---- Voice enrollments ----
def enroll_voice(business_id: str, voice_name: str) -> dict:
    v_id = "vox-" + uuid.uuid4().hex[:8]
    with _lock, _conn() as c:
        c.execute(
            "INSERT INTO voice(id,business_id,voice_name,consent,created_at)"
            " VALUES(?,?,?,1,?)",
            (v_id, business_id, voice_name, _now()),
        )
    return {"id": v_id, "business_id": business_id, "voice_name": voice_name,
            "consent": True}
