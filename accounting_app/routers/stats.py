import os, time
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
    return {
        "env": os.getenv("ENV","dev"),
        "tasks_total": total,
        "tasks_done": done,
        "tasks_error": err,
        "ts": int(time.time())
    }
