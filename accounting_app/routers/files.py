import asyncio
from uuid import uuid4
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, Request, HTTPException, Depends
from accounting_app.utils.pdf_processor import pdf_bytes_to_text

router = APIRouter(prefix="/files", tags=["files"])

# 1) 上传大小限流
DEFAULT_MAX_MB = 10
import os as _os
MAX_BYTES = int(float(_os.getenv("MAX_UPLOAD_MB", DEFAULT_MAX_MB)) * 1024 * 1024)

async def guard_content_length(request: Request):
    cl = request.headers.get("content-length")
    if cl and int(cl) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large (max {MAX_BYTES // (1024*1024)}MB)")

# 2) 简易任务存储（内存）
TASKS: Dict[str, Dict[str, Any]] = {}

# 3) 同步直返：小文件直接返回文本
@router.post("/pdf-to-text", dependencies=[Depends(guard_content_length)])
async def pdf_to_text(file: UploadFile = File(...)):
    data = await file.read()
    text = await asyncio.to_thread(pdf_bytes_to_text, data)
    return {"text": text}

# 4) 异步队列：大文件更友好
@router.post("/pdf-to-text/submit", dependencies=[Depends(guard_content_length)])
async def submit_pdf(file: UploadFile = File(...)):
    data = await file.read()
    task_id = str(uuid4())
    TASKS[task_id] = {"status": "queued", "result": None, "error_msg": None}

    async def run():
        TASKS[task_id]["status"] = "processing"
        try:
            text = await asyncio.to_thread(pdf_bytes_to_text, data)
            TASKS[task_id]["status"] = "done"
            TASKS[task_id]["result"] = text
        except Exception as e:
            TASKS[task_id]["status"] = "error"
            TASKS[task_id]["error_msg"] = str(e)

    asyncio.create_task(run())
    return {"task_id": task_id, "status": "queued"}

@router.get("/pdf-to-text/result/{task_id}")
async def get_result(task_id: str):
    info = TASKS.get(task_id)
    if not info:
        raise HTTPException(status_code=404, detail="task not found")
    return info
