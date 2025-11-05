import os, sqlite3, json, base64, hashlib, time
DB = "loans.db"

def _ensure():
    con = sqlite3.connect(DB)
    con.execute("""
    CREATE TABLE IF NOT EXISTS loan_share (
        code TEXT PRIMARY KEY,
        payload TEXT NOT NULL,
        created_at INTEGER NOT NULL
    )
    """)
    con.commit(); con.close()

def save_snapshot(payload: dict) -> str:
    _ensure()
    raw = json.dumps(payload, ensure_ascii=False, separators=(",",":"))
    h = hashlib.sha256((raw+str(time.time())).encode()).digest()
    code = base64.urlsafe_b64encode(h)[:10].decode()
    con = sqlite3.connect(DB)
    con.execute("INSERT OR REPLACE INTO loan_share(code,payload,created_at) VALUES(?,?,?)",
                (code, raw, int(time.time())))
    con.commit(); con.close()
    return code

def load_snapshot(code: str) -> dict | None:
    _ensure()
    con = sqlite3.connect(DB)
    cur = con.execute("SELECT payload FROM loan_share WHERE code=?", (code,))
    row = cur.fetchone()
    con.close()
    if not row: return None
    return json.loads(row[0])
