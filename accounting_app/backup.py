import os
import time
import threading
import subprocess
import datetime

def _dump():
    url = os.getenv("DATABASE_URL")
    if not url:
        return
    d = datetime.datetime.utcnow().strftime("%Y%m%d")
    out = f"/home/runner/pgdump_{d}.sql"
    subprocess.run(["pg_dump", url, "-f", out], check=False)
    base = "/home/runner"
    snaps = sorted([f for f in os.listdir(base) if f.startswith("pgdump_")])[-7:]
    for f in os.listdir(base):
        if f.startswith("pgdump_") and f not in snaps:
            try:
                os.remove(os.path.join(base, f))
            except:
                pass

def start_daily():
    def loop():
        while True:
            _dump()
            time.sleep(24 * 3600)
    threading.Thread(target=loop, daemon=True).start()
