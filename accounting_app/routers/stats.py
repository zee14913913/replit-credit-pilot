import os
import time
from fastapi import APIRouter
from accounting_app.core.task_store import iter_tasks

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("")
async def stats():
    total = 0; done=0; err=0
    for _, t in iter_tasks():
        total += 1
        s = (t or {}).get("status")
        if s == "done": done += 1
        if s == "error": err += 1
    
    size_bytes = 0
    if os.getenv("STORAGE_BACKEND","local").lower()=="local":
        base = os.getenv("LOCAL_FILES_DIR","/home/runner/files")
        try:
            for name in os.listdir(base):
                p = os.path.join(base, name)
                if os.path.isfile(p): size_bytes += os.path.getsize(p)
        except Exception:
            pass
    
    return {
        "env": os.getenv("ENV","dev"),
        "tasks_total": total,
        "tasks_done": done,
        "tasks_error": err,
        "storage_local_bytes": size_bytes,
        "ts": int(time.time())
    }
