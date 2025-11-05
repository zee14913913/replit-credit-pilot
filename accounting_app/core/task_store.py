import os, json, time
from typing import Optional, Dict, Any

# 内存存储（默认）
_TASKS: Dict[str, Dict[str, Any]] = {}

def use_memory() -> bool:
    return not os.getenv("REDIS_URL") and not os.getenv("DB_URL")

# Redis 实现（可选）
def _redis():
    from redis import Redis
    return Redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

def set_task(task_id: str, data: Dict[str, Any]):
    data.setdefault("time", time.strftime("%Y-%m-%d %H:%M:%S"))
    if use_memory():
        _TASKS[task_id] = data; return
    if os.getenv("REDIS_URL"):
        r = _redis(); r.hset(f"task:{task_id}", mapping=data); r.sadd("tasks:index", task_id)

def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    if use_memory():
        return _TASKS.get(task_id)
    if os.getenv("REDIS_URL"):
        r = _redis(); d = r.hgetall(f"task:{task_id}"); return d or None

def delete_task(task_id: str) -> bool:
    if use_memory():
        return _TASKS.pop(task_id, None) is not None
    if os.getenv("REDIS_URL"):
        r = _redis(); r.delete(f"task:{task_id}"); r.srem("tasks:index", task_id); return True

def iter_tasks(reverse=True):
    if use_memory():
        items = list(_TASKS.items())
        return items[::-1] if reverse else items
    if os.getenv("REDIS_URL"):
        r = _redis()
        ids = list(r.smembers("tasks:index"))
        ids.sort(reverse=reverse)
        return [(tid, r.hgetall(f"task:{tid}")) for tid in ids]
