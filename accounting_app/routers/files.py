import asyncio
from uuid import uuid4
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, Request, HTTPException, Depends
from accounting_app.utils.pdf_processor import pdf_bytes_to_text
from accounting_app.utils.tasks_store import set_task, get_task

router = APIRouter(prefix="/files", tags=["files"])

# 1) 上传大小限流
DEFAULT_MAX_MB = 10
import os as _os
MAX_BYTES = int(float(_os.getenv("MAX_UPLOAD_MB", DEFAULT_MAX_MB)) * 1024 * 1024)

async def guard_content_length(request: Request):
    cl = request.headers.get("content-length")
    if cl and int(cl) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large (max {MAX_BYTES // (1024*1024)}MB)")

# 3) 同步直返：小文件直接返回文本
@router.post("/pdf-to-text", dependencies=[Depends(guard_content_length)])
async def pdf_to_text(file: UploadFile = File(...)):
    data = await file.read()
    text = await asyncio.to_thread(pdf_bytes_to_text, data)
    return {"text": text}

# 4) 异步队列：大文件更友好（使用可恢复存储）
@router.post("/pdf-to-text/submit", dependencies=[Depends(guard_content_length)])
async def submit_pdf(file: UploadFile = File(...)):
    data = await file.read()
    task_id = str(uuid4())
    set_task(task_id, {"status": "queued", "result": "", "error_msg": ""})

    async def run():
        set_task(task_id, {"status": "processing", "result": "", "error_msg": ""})
        try:
            text = await asyncio.to_thread(pdf_bytes_to_text, data)
            set_task(task_id, {"status": "done", "result": text, "error_msg": ""})
        except Exception as e:
            set_task(task_id, {"status": "error", "result": "", "error_msg": str(e)})

    asyncio.create_task(run())
    return {"task_id": task_id, "status": "queued"}

@router.get("/pdf-to-text/result/{task_id}")
async def get_result(task_id: str):
    info = get_task(task_id)
    if not info:
        raise HTTPException(status_code=404, detail="task not found")
    return info
