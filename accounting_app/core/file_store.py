import os, io, hashlib, time
from typing import Dict, Any, Optional, Tuple

BACKEND = os.getenv("STORAGE_BACKEND", "local").lower()  # local 或 s3

# ==== 公共工具 ====
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

# ==== 本地实现 ====
def _local_base() -> str:
    base = os.getenv("LOCAL_FILES_DIR", "/home/runner/files")
    os.makedirs(base, exist_ok=True)
    return base

def _local_save(task_id: str, data: bytes, filename: str, mime: str) -> Dict[str, Any]:
    base = _local_base()
    path = os.path.join(base, f"{task_id}.pdf")
    with open(path, "wb") as f:
        f.write(data)
    return {
        "backend": "local",
        "path": path,
        "key": None,
        "size": len(data),
        "sha256": sha256_bytes(data),
        "filename": filename,
        "mime": mime or "application/pdf",
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

def _local_open(path: str):
    return open(path, "rb")

# ==== S3/R2 实现（可选） ====
def _s3_client():
    import boto3
    ep = os.getenv("S3_ENDPOINT")
    region = os.getenv("S3_REGION", "auto")
    ak = os.getenv("S3_ACCESS_KEY")
    sk = os.getenv("S3_SECRET_KEY")
    session = boto3.session.Session()
    return session.client(
        "s3",
        region_name=region if region != "auto" else None,
        endpoint_url=ep if ep else None,
        aws_access_key_id=ak,
        aws_secret_access_key=sk,
    )

def _s3_bucket_key(task_id: str, filename: str) -> Tuple[str, str]:
    bucket = os.getenv("S3_BUCKET", "")
    prefix = os.getenv("S3_PATH_PREFIX", "uploads/")
    safe_name = filename or f"{task_id}.pdf"
    key = f"{prefix}{task_id}/{safe_name}"
    return bucket, key

def _s3_save(task_id: str, data: bytes, filename: str, mime: str) -> Dict[str, Any]:
    import boto3  # 仅为确保缺包时报错提示
    s3 = _s3_client()
    bucket, key = _s3_bucket_key(task_id, filename or f"{task_id}.pdf")
    s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType=mime or "application/pdf")
    return {
        "backend": "s3",
        "path": None,
        "key": key,
        "size": len(data),
        "sha256": sha256_bytes(data),
        "filename": filename,
        "mime": mime or "application/pdf",
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

def _s3_presign_download(key: str, expires: int = 3600) -> str:
    s3 = _s3_client()
    bucket = os.getenv("S3_BUCKET", "")
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires,
    )

# ==== 对外API ====
def save_original(task_id: str, data: bytes, filename: str, mime: str) -> Dict[str, Any]:
    if BACKEND == "s3":
        return _s3_save(task_id, data, filename, mime)
    return _local_save(task_id, data, filename, mime)

def get_local_stream(path: str):
    return _local_open(path)

def get_signed_url(key: str, ttl: int = 3600) -> Optional[str]:
    if BACKEND != "s3" or not key:
        return None
    return _s3_presign_download(key, ttl)
