"""
Phase 1-1: 分块文件Hash工具
用途：避免大文件一次性读入内存导致超时
规则：必须使用分块SHA256，不允许一次性读完
"""
import hashlib
from pathlib import Path
from typing import Union, BinaryIO


def calculate_file_hash_chunked(file_path: Union[str, Path, None] = None, file_obj: Union[BinaryIO, None] = None, chunk_size: int = 8192) -> str:
    """
    分块计算文件SHA256哈希值
    
    Args:
        file_path: 文件路径（二选一）
        file_obj: 文件对象（二选一）
        chunk_size: 分块大小（默认8KB）
    
    Returns:
        SHA256哈希值（十六进制字符串）
    
    Raises:
        ValueError: 如果两个参数都未提供
    
    Example:
        # 方式1：通过文件路径
        file_hash = calculate_file_hash_chunked(file_path="statement.pdf")
        
        # 方式2：通过文件对象（适用于上传流）
        with open("statement.pdf", "rb") as f:
            file_hash = calculate_file_hash_chunked(file_obj=f)
    """
    if file_path is None and file_obj is None:
        raise ValueError("必须提供file_path或file_obj之一")
    
    sha256_hash = hashlib.sha256()
    
    # 如果提供文件路径，打开文件
    if file_path:
        with open(file_path, "rb") as f:
            _hash_file_chunks(f, sha256_hash, chunk_size)
    elif file_obj:
        # 使用提供的文件对象
        _hash_file_chunks(file_obj, sha256_hash, chunk_size)
    
    return sha256_hash.hexdigest()


def _hash_file_chunks(file_obj: BinaryIO, hash_obj, chunk_size: int):
    """
    内部函数：分块读取文件并更新hash
    
    Args:
        file_obj: 文件对象
        hash_obj: hash对象
        chunk_size: 分块大小
    """
    while True:
        chunk = file_obj.read(chunk_size)
        if not chunk:
            break
        hash_obj.update(chunk)


def calculate_uploaded_file_hash(file_obj: BinaryIO) -> tuple[str, int]:
    """
    计算上传文件的hash和大小（一次遍历完成）
    适用于FastAPI UploadFile
    
    Args:
        file_obj: 上传的文件对象
    
    Returns:
        tuple: (file_hash, file_size)
    
    Example:
        from fastapi import UploadFile
        
        async def upload_statement(file: UploadFile):
            file_hash, file_size = calculate_uploaded_file_hash(file.file)
            # 注意：读取后需要seek(0)才能再次读取
            file.file.seek(0)
    """
    sha256_hash = hashlib.sha256()
    file_size = 0
    chunk_size = 8192
    
    while True:
        chunk = file_obj.read(chunk_size)
        if not chunk:
            break
        sha256_hash.update(chunk)
        file_size += len(chunk)
    
    # 重置文件指针到开头，允许后续操作
    file_obj.seek(0)
    
    return sha256_hash.hexdigest(), file_size


def verify_file_hash(file_path: Union[str, Path], expected_hash: str) -> bool:
    """
    验证文件hash是否与预期一致
    用于迁移后校验、Architect审查等场景
    
    Args:
        file_path: 文件路径
        expected_hash: 预期的hash值
    
    Returns:
        bool: hash是否一致
    
    Example:
        # 迁移后验证
        if verify_file_hash("/files/new/path.pdf", original_hash):
            print("迁移成功，hash一致")
        else:
            print("迁移失败，文件已损坏")
    """
    actual_hash = calculate_file_hash_chunked(file_path=file_path)
    return actual_hash == expected_hash
