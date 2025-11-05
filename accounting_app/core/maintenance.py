import os, time, zipfile, shutil
from datetime import datetime, timedelta
from typing import Tuple

# ========== PDF 字节校验 ==========
def validate_pdf_bytes(data: bytes) -> Tuple[bool, str]:
    if not data or len(data) == 0:
        return False, "Empty file"
    # 简单魔数检查
    if not data[:4] == b"%PDF":
        return False, "Not a PDF file"
    # 最小长度（避免 1~2KB 垃圾）
    if len(data) < 1024:
        return False, "PDF too small"
    return True, ""

# ========== 本地原件清理 ==========
def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

def _now_utc():
    return datetime.utcnow()

def start_local_cleanup_thread():
    """
    每日一次巡检本地原件目录：
      - ARCHIVE_AFTER_DAYS: 多少天后压缩为 zip（默认 14）
      - DELETE_AFTER_DAYS : 多少天后删除原件/zip（默认 30）
      - LOCAL_FILES_DIR   : 原件目录（你已有默认 /home/runner/files）
      - LOCAL_ARCHIVE_DIR : 归档目录（默认 /home/runner/archive）
    仅对 STORAGE_BACKEND=local 生效；S3/R2 请用桶生命周期规则。
    """
    from threading import Thread
    if os.getenv("STORAGE_BACKEND", "local").lower() != "local":
        return  # 远程存储交给对象存储的生命周期策略
    files_dir = os.getenv("LOCAL_FILES_DIR", "/home/runner/files")
    archive_dir = os.getenv("LOCAL_ARCHIVE_DIR", "/home/runner/archive")
    os.makedirs(files_dir, exist_ok=True)
    os.makedirs(archive_dir, exist_ok=True)

    ARCHIVE_AFTER_DAYS = _env_int("ARCHIVE_AFTER_DAYS", 14)
    DELETE_AFTER_DAYS  = _env_int("DELETE_AFTER_DAYS", 30)

    def loop():
        while True:
            try:
                now = _now_utc()
                # 1) 压缩超期 PDF
                for name in list(os.listdir(files_dir)):
                    if not name.endswith(".pdf"): continue
                    p = os.path.join(files_dir, name)
                    try:
                        mtime = datetime.utcfromtimestamp(os.path.getmtime(p))
                        if now - mtime > timedelta(days=ARCHIVE_AFTER_DAYS):
                            # 打包成 zip
                            zip_name = name[:-4] + ".zip"
                            zp = os.path.join(archive_dir, zip_name)
                            if not os.path.exists(zp):
                                with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
                                    z.write(p, arcname=name)
                            # 压缩后删除原 pdf，节省空间
                            try: os.remove(p)
                            except: pass
                    except Exception:
                        pass

                # 2) 删除超期 ZIP
                for name in list(os.listdir(archive_dir)):
                    if not name.endswith(".zip"): continue
                    p = os.path.join(archive_dir, name)
                    try:
                        mtime = datetime.utcfromtimestamp(os.path.getmtime(p))
                        if now - mtime > timedelta(days=DELETE_AFTER_DAYS):
                            os.remove(p)
                    except Exception:
                        pass
            except Exception:
                # 清理不影响主流程，静默即可
                pass
            time.sleep(24*3600)  # 每日一次

    Thread(target=loop, daemon=True).start()
