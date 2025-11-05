import os
import asyncio
from uuid import uuid4
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, Request, HTTPException, Depends
from accounting_app.utils.pdf_processor import pdf_bytes_to_text

router = APIRouter(prefix="/files", tags=["files"])

DEFAULT_MAX_MB = 10
MAX_BYTES = int(float(os.getenv("MAX_UPLOAD_MB", DEFAULT_MAX_MB)) * 1024 * 1024)

async def guard_content_length(request: Request):
    cl = request.headers.get("content-length")
    if cl and int(cl) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large (max {MAX_BYTES // (1024*1024)}MB)")

TASKS: Dict[str, Dict[str, Any]] = {}

@router.post("/pdf-to-text", dependencies=[Depends(guard_content_length)])
async def pdf_to_text(file: UploadFile = File(...)):
    if file.content_type not in {"application/pdf"}:
        raise HTTPException(415, detail="Only PDF is allowed")
    data = await file.read()
    text = await asyncio.to_thread(pdf_bytes_to_text, data)
    return {"text": text}

@router.post("/pdf-to-text/submit", dependencies=[Depends(guard_content_length)])
async def submit_pdf(
    request: Request,
    file: UploadFile = File(...)
):
    if file.content_type not in {"application/pdf"}:
        raise HTTPException(415, detail="Only PDF is allowed")

    data = await file.read()
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    callback_url: str | None = payload.get("callback_url")
    notify_email: str | None = payload.get("notify_email")

    task_id = str(uuid4())
    TASKS[task_id] = {"status": "queued", "result": None, "error_msg": None}

    async def run():
        TASKS[task_id]["status"] = "processing"
        try:
            text = await asyncio.to_thread(pdf_bytes_to_text, data)
            TASKS[task_id]["status"] = "done"
            TASKS[task_id]["result"] = text

            if callback_url:
                try:
                    import httpx
                    async with httpx.AsyncClient(timeout=10) as client:
                        await client.post(callback_url, json={
                            "task_id": task_id,
                            "status": "done",
                            "result_preview": text[:1000]
                        })
                except Exception:
                    pass

            if notify_email and os.getenv("SENDGRID_API_KEY"):
                try:
                    from sendgrid import SendGridAPIClient
                    from sendgrid.helpers.mail import Mail
                    sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
                    from_email = os.getenv("FROM_EMAIL", "no-reply@example.com")
                    msg = Mail(
                        from_email=from_email,
                        to_emails=notify_email,
                        subject="Your PDF processing is complete",
                        html_content=f"<p>Task {task_id} done.</p><pre>{(text[:1000]).replace('<','&lt;')}</pre>"
                    )
                    sg.send(msg)
                except Exception:
                    pass

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
