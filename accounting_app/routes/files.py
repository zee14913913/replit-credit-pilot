"""
文件管理路由 - 统一管理上传的月结单和生成的报告
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List, Dict
import os
from datetime import datetime

router = APIRouter()

STORAGE_BASE = "/home/runner/workspace/accounting_data"
STATEMENTS_DIR = os.path.join(STORAGE_BASE, "statements")
REPORTS_DIR = os.path.join(STORAGE_BASE, "reports")


def get_file_info(file_path: str, file_type: str) -> Dict:
    """获取文件信息"""
    stat = os.stat(file_path)
    filename = os.path.basename(file_path)
    
    return {
        "filename": filename,
        "type": file_type,
        "size": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "created_at": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
        "modified_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "path": file_path
    }


@router.get("/list")
def list_all_files():
    """
    列出所有上传的月结单和生成的报告
    """
    files = []
    
    # 扫描statements目录
    if os.path.exists(STATEMENTS_DIR):
        for filename in os.listdir(STATEMENTS_DIR):
            if filename.endswith('.csv'):
                file_path = os.path.join(STATEMENTS_DIR, filename)
                files.append(get_file_info(file_path, "bank_statement"))
    
    # 扫描reports目录
    if os.path.exists(REPORTS_DIR):
        for filename in os.listdir(REPORTS_DIR):
            if filename.endswith('.txt') or filename.endswith('.pdf'):
                file_path = os.path.join(REPORTS_DIR, filename)
                files.append(get_file_info(file_path, "test_report"))
    
    # 按修改时间倒序排列
    files.sort(key=lambda x: x['modified_at'], reverse=True)
    
    return {
        "total": len(files),
        "statements_count": sum(1 for f in files if f['type'] == 'bank_statement'),
        "reports_count": sum(1 for f in files if f['type'] == 'test_report'),
        "files": files
    }


@router.get("/download/{file_type}/{filename}")
def download_file(file_type: str, filename: str):
    """
    下载文件
    """
    if file_type == "bank_statement":
        file_path = os.path.join(STATEMENTS_DIR, filename)
    elif file_type == "test_report":
        file_path = os.path.join(REPORTS_DIR, filename)
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # 安全检查：确保文件在允许的目录内
    if not os.path.abspath(file_path).startswith(STORAGE_BASE):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(file_path, filename=filename)


@router.delete("/delete/{file_type}/{filename}")
def delete_file(file_type: str, filename: str):
    """
    删除文件
    """
    if file_type == "bank_statement":
        file_path = os.path.join(STATEMENTS_DIR, filename)
    elif file_type == "test_report":
        file_path = os.path.join(REPORTS_DIR, filename)
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # 安全检查
    if not os.path.abspath(file_path).startswith(STORAGE_BASE):
        raise HTTPException(status_code=403, detail="Access denied")
    
    os.remove(file_path)
    
    return {
        "success": True,
        "message": f"文件 {filename} 已删除"
    }


@router.get("/storage-info")
def get_storage_info():
    """
    获取存储信息
    """
    def get_dir_size(directory):
        total_size = 0
        if os.path.exists(directory):
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
        return total_size
    
    statements_size = get_dir_size(STATEMENTS_DIR)
    reports_size = get_dir_size(REPORTS_DIR)
    total_size = statements_size + reports_size
    
    return {
        "storage_base": STORAGE_BASE,
        "statements_dir": STATEMENTS_DIR,
        "reports_dir": REPORTS_DIR,
        "statements_size_mb": round(statements_size / (1024 * 1024), 2),
        "reports_size_mb": round(reports_size / (1024 * 1024), 2),
        "total_size_mb": round(total_size / (1024 * 1024), 2)
    }
