"""
任务存储模块 - 支持 Redis 和内存两种模式
优先使用 Redis（可恢复），未配置时回退到内存模式
"""
import os
from typing import Dict, Any, Optional

# 尝试导入 Redis
try:
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

REDIS_URL = os.getenv("REDIS_URL")

# 如果 Redis 可用且已配置，使用 Redis
if REDIS_AVAILABLE and REDIS_URL:
    try:
        r = Redis.from_url(REDIS_URL, decode_responses=True)
        r.ping()  # 测试连接
        USE_REDIS = True
        print("✅ 任务存储：使用 Redis（可恢复模式）")
    except Exception as e:
        USE_REDIS = False
        print(f"⚠️ Redis 连接失败，回退到内存模式: {e}")
else:
    USE_REDIS = False
    print("ℹ️ 任务存储：使用内存模式（重启后丢失）")

# 内存模式备用存储
MEMORY_TASKS: Dict[str, Dict[str, Any]] = {}


def set_task(task_id: str, data: Dict[str, Any]) -> None:
    """设置任务状态"""
    if USE_REDIS:
        r.hset(f"task:{task_id}", mapping=data)
    else:
        MEMORY_TASKS[task_id] = data


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """获取任务状态"""
    if USE_REDIS:
        data = r.hgetall(f"task:{task_id}")
        return dict(data) if data else None
    else:
        return MEMORY_TASKS.get(task_id)


def delete_task(task_id: str) -> None:
    """删除任务（可选，用于清理过期任务）"""
    if USE_REDIS:
        r.delete(f"task:{task_id}")
    else:
        MEMORY_TASKS.pop(task_id, None)
