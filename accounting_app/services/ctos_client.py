import os, sqlite3, uuid, time
from typing import Optional
from .crypto_box import enc

DB = os.getenv("CTOS_DB_PATH","/home/runner/ctos.db")

def _conn():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init():
    con=_conn(); cur=con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS ctos_queue(
        id TEXT PRIMARY KEY,
        ctype TEXT, name_enc TEXT, idnum_enc TEXT, email_enc TEXT, phone_enc TEXT,
        doc_path TEXT, status TEXT, created_at TEXT
    )""")
    con.commit(); con.close()

def enqueue(ctype:str, name:str, idnum:str, email:str, phone:str, doc_path:str) -> str:
    init()
    jid=str(uuid.uuid4())
    con=_conn(); cur=con.cursor()
    cur.execute("""INSERT INTO ctos_queue(id,ctype,name_enc,idnum_enc,email_enc,phone_enc,doc_path,status,created_at)
                   VALUES(?,?,?,?,?,?,?,?,datetime('now'))""",
                (jid, ctype, enc(name), enc(idnum), enc(email), enc(phone), doc_path, "PENDING"))
    con.commit(); con.close()
    return jid

def list_jobs(limit:int=100):
    init()
    con=_conn(); cur=con.cursor()
    cur.execute("SELECT id,ctype,doc_path,status,created_at FROM ctos_queue ORDER BY created_at DESC LIMIT ?",(limit,))
    rows=[dict(r) for r in cur.fetchall()]
    con.close(); return rows

def mark_done(jid:str):
    con=_conn(); cur=con.cursor()
    cur.execute("UPDATE ctos_queue SET status='DONE' WHERE id=?",(jid,))
    con.commit(); con.close()
