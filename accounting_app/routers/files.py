import asyncio
import os
import time
import hashlib
from uuid import uuid4
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Request, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse, RedirectResponse
from accounting_app.utils.pdf_processor import pdf_bytes_to_text
from accounting_app.core.task_store import set_task, get_task, delete_task as delete_task_store, iter_tasks
from accounting_app.core.file_store import save_original, get_local_stream, get_signed_url
from accounting_app.core.maintenance import validate_pdf_bytes
from accounting_app.core.logger import warn

# 可选通知依赖
import httpx
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

router = APIRouter(prefix="/files", tags=["files"])

# ====== 上传大小限制 ======
DEFAULT_MAX_MB = 10
MAX_BYTES = int(float(os.getenv("MAX_UPLOAD_MB", DEFAULT_MAX_MB)) * 1024 * 1024)

async def guard_content_length(request: Request):
    cl = request.headers.get("content-length")
    if cl and int(cl) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large (max {MAX_BYTES // (1024*1024)}MB)")

# ====== 全局任务存储（已迁移到 task_store）======
# TASKS: Dict[str, Dict[str, Any]] = {}

# ====== 工具函数 ======
def _notify(task_id: str, data: Dict[str, Any]):
    """可选 Webhook 或 SendGrid 邮件通知"""
    callback = data.get("callback_url") or os.getenv("CALLBACK_URL")
    email_to = data.get("notify_email") or os.getenv("NOTIFY_EMAIL")
    result_text = data.get("result") or ""
    if callback:
        try:
            asyncio.create_task(httpx.AsyncClient().post(callback, json={"task_id": task_id, "status": data["status"], "result": result_text[:500]}))
        except Exception as e:
            print("Webhook failed:", e)
    if email_to and os.getenv("SENDGRID_API_KEY"):
        try:
            sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
            msg = Mail(
                from_email=os.getenv("FROM_EMAIL", "no-reply@system.local"),
                to_emails=email_to,
                subject=f"OCR 任务完成 {task_id}",
                plain_text_content=result_text[:1000],
            )
            sg.send(msg)
        except Exception as e:
            print("Email failed:", e)

# ====== 同步直返 ======
@router.post("/pdf-to-text", dependencies=[Depends(guard_content_length)])
async def pdf_to_text(file: UploadFile = File(...)):
    if file.content_type not in {"application/pdf"}:
        raise HTTPException(415, detail="Only PDF is allowed")
    data = await file.read()
    
    ok, reason = validate_pdf_bytes(data)
    if not ok:
        warn({"bad_pdf": reason, "filename": file.filename, "size": len(data)})
        raise HTTPException(status_code=400, detail=f"Invalid PDF: {reason}")
    
    text = await asyncio.to_thread(pdf_bytes_to_text, data)
    return {"text": text}

# ====== 异步任务 ======
@router.post("/pdf-to-text/submit", dependencies=[Depends(guard_content_length)])
async def submit_pdf(
    file: UploadFile = File(...),
    request: Request = None,
    callback_url: Optional[str] = None,
    notify_email: Optional[str] = None,
):
    if file.content_type not in {"application/pdf"}:
        raise HTTPException(415, detail="Only PDF is allowed")
    data = await file.read()
    
    ok, reason = validate_pdf_bytes(data)
    if not ok:
        warn({"bad_pdf": reason, "filename": file.filename, "size": len(data)})
        raise HTTPException(status_code=400, detail=f"Invalid PDF: {reason}")
    
    # 结果去重：hash 文件，已有则直接返回旧 task_id
    file_hash = hashlib.sha256(data).hexdigest()
    for tid, info in iter_tasks():
        if info and info.get("file_hash") == file_hash and info.get("status") == "done":
            return {"task_id": tid, "status": "cached"}
    
    # 生成 task_id 并保存原件（本地或S3）
    task_id = str(uuid4())
    orig = save_original(task_id, data, file.filename, file.content_type or "application/pdf")
    
    task_data = {
        "status": "queued",
        "result": None,
        "error_msg": None,
        "filename": file.filename,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "callback_url": callback_url,
        "notify_email": notify_email,
        "file_hash": file_hash,
        "original_backend": orig.get("backend"),
        "original_path": orig.get("path"),
        "original_key": orig.get("key"),
        "original_size": orig.get("size"),
        "original_sha256": orig.get("sha256"),
        "original_filename": orig.get("filename"),
        "original_mime": orig.get("mime"),
    }
    set_task(task_id, task_data)

    async def run():
        task_info = get_task(task_id)
        if task_info:
            task_info["status"] = "processing"
            set_task(task_id, task_info)
        try:
            text = await asyncio.to_thread(pdf_bytes_to_text, data)
            task_info = get_task(task_id)
            if task_info:
                task_info["status"] = "done"
                task_info["result"] = text
                set_task(task_id, task_info)
                _notify(task_id, task_info)
        except Exception as e:
            task_info = get_task(task_id)
            if task_info:
                task_info["status"] = "error"
                task_info["error_msg"] = str(e)
                set_task(task_id, task_info)
                _notify(task_id, task_info)

    asyncio.create_task(run())
    return {"task_id": task_id, "status": "queued"}

# ====== 查询结果 ======
@router.get("/pdf-to-text/result/{task_id}")
async def get_result(task_id: str):
    info = get_task(task_id)
    if not info:
        raise HTTPException(status_code=404, detail="task not found")
    return info

# ====== 历史记录 ======
@router.get("/history")
async def list_history(
    q: Optional[str] = Query(None, description="搜索关键字"),
    skip: int = 0,
    limit: int = 20
):
    tasks = list(iter_tasks(reverse=True))  # 倒序（新到旧）
    if q:
        tasks = [(tid, t) for tid, t in tasks if t and q.lower() in (t.get("result") or "").lower()]
    sliced = tasks[skip: skip + limit]
    items = []
    for tid, info in sliced:
        if info:
            items.append({
                "task_id": tid,
                "status": info.get("status"),
                "time": info.get("time"),
                "filename": info.get("filename"),
                "preview": (info.get("result") or "")[:100],
            })
    return {"count": len(items), "total": len(tasks), "tasks": items}

# ====== 删除任务 ======
@router.delete("/history/{task_id}")
async def delete_task(task_id: str):
    if not delete_task_store(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"deleted": task_id}

# ====== 下载原件 ======
@router.get("/original/{task_id}")
async def download_original(task_id: str):
    info = get_task(task_id)
    if not info:
        raise HTTPException(status_code=404, detail="task not found")

    backend = info.get("original_backend")
    filename = info.get("original_filename") or f"{task_id}.pdf"

    if backend == "s3":
        url = get_signed_url(info.get("original_key"), ttl=3600)
        if not url:
            raise HTTPException(status_code=500, detail="cannot generate signed URL")
        return RedirectResponse(url)

    # 本地文件
    p = info.get("original_path")
    if not p or not os.path.exists(p):
        raise HTTPException(status_code=404, detail="file not found")
    
    threshold_mb = int(os.getenv("ZIP_THRESHOLD_MB", "50"))
    size = os.path.getsize(p)
    if size >= threshold_mb * 1024 * 1024:
        import io, zipfile
        bio = io.BytesIO()
        with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(p, arcname=filename or f"{task_id}.pdf")
        bio.seek(0)
        headers = {"Content-Disposition": f'attachment; filename="{(filename or task_id)+".zip"}"'}
        return StreamingResponse(bio, media_type="application/zip", headers=headers)
    
    # 小文件直接回 PDF
    stream = get_local_stream(p)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(stream, media_type="application/pdf", headers=headers)
