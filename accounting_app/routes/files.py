"""
文件管理路由 - 使用FileStorageManager统一管理
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List, Dict, Optional
import os
from datetime import datetime
from ..services.file_storage_manager import AccountingFileStorageManager

router = APIRouter()


@router.get("/list/{company_id}")
def list_company_files(
    company_id: int,
    file_type: Optional[str] = None
):
    """
    列出公司的所有文件（支持按类型过滤）
    
    Args:
        company_id: 公司ID
        file_type: 可选，文件类型（bank_statement, pos_report, management_report等）
    """
    files = AccountingFileStorageManager.list_company_files(company_id, file_type)
    
    return {
        "company_id": company_id,
        "file_type": file_type or "all",
        "total": len(files),
        "files": files
    }


@router.get("/storage-stats/{company_id}")
def get_storage_stats(company_id: int):
    """
    获取公司的存储统计信息
    """
    stats = AccountingFileStorageManager.get_storage_stats(company_id)
    
    return {
        "company_id": company_id,
        **stats
    }


@router.get("/download")
def download_file(company_id: int, file_path: str):
    """
    下载文件
    
    Args:
        company_id: 公司ID
        file_path: 文件路径
    """
    # 安全验证：确保路径在公司目录内
    if not AccountingFileStorageManager.validate_path_security(file_path, company_id):
        raise HTTPException(status_code=403, detail="Access denied: Invalid file path")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    filename = os.path.basename(file_path)
    return FileResponse(file_path, filename=filename)


@router.delete("/delete")
def delete_file(company_id: int, file_path: str):
    """
    删除文件
    
    Args:
        company_id: 公司ID
        file_path: 文件路径
    """
    # 安全验证
    if not AccountingFileStorageManager.validate_path_security(file_path, company_id):
        raise HTTPException(status_code=403, detail="Access denied: Invalid file path")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    success = AccountingFileStorageManager.delete_file(file_path, backup=False)
    
    if success:
        return {
            "success": True,
            "message": f"File deleted successfully"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to delete file")


@router.get("/view")
def view_file_content(company_id: int, file_path: str):
    """
    查看文件内容
    
    Args:
        company_id: 公司ID
        file_path: 文件路径
    """
    # 安全验证
    if not AccountingFileStorageManager.validate_path_security(file_path, company_id):
        raise HTTPException(status_code=403, detail="Access denied: Invalid file path")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        filename = os.path.basename(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 如果是CSV，解析为结构化数据
        if filename.endswith('.csv'):
            import csv
            import io
            
            csv_reader = csv.DictReader(io.StringIO(content))
            rows = list(csv_reader)
            
            return {
                "filename": filename,
                "format": "csv",
                "headers": list(rows[0].keys()) if rows else [],
                "rows": rows,
                "row_count": len(rows),
                "raw_content": content
            }
        elif filename.endswith('.json'):
            import json
            data = json.loads(content)
            return {
                "filename": filename,
                "format": "json",
                "data": data
            }
        else:
            # 纯文本文件
            return {
                "filename": filename,
                "format": "text",
                "content": content,
                "line_count": len(content.split('\n'))
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
