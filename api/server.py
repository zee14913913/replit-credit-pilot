"""
FastAPI Server - Credit Card Statement Processing API
提供 RESTful API endpoint 供前端调用

Endpoints:
- POST /parse - 处理单个 Document AI JSON
- POST /parse/batch - 批量处理多个账单
- GET /health - 健康检查
"""

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import json
import tempfile
from pathlib import Path
import sys

# 添加父目录到路径以导入 main.py
sys.path.append(str(Path(__file__).parent.parent))

from main import StatementProcessor
from services.cognee_client import add_memory, search_memory, cognify_memory, get_memory_status


# FastAPI 应用初始化
app = FastAPI(
    title="CreditPilot Statement Parser API",
    description="Google Document AI 后处理 API - 信用卡账单解析",
    version="1.0.0"
)

# CORS 配置（允许前端调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局处理器实例
processor = StatementProcessor()


# ============================================================================
# Pydantic Models (请求/响应结构)
# ============================================================================

class DocumentAIInput(BaseModel):
    """Document AI JSON 输入格式"""
    entities: List[Dict[str, Any]] = Field(..., description="Document AI entities")
    text: Optional[str] = Field(None, description="Full text content")
    
    class Config:
        schema_extra = {
            "example": {
                "entities": [
                    {"type": "bank_name", "mentionText": "AMBANK"},
                    {"type": "customer_name", "mentionText": "CHEOK JUN YOON"},
                    {"type": "card_no", "mentionText": "4031 4899 9530 6354"}
                ],
                "text": "Statement text..."
            }
        }


class ParseRequest(BaseModel):
    """单个账单解析请求"""
    document_ai_json: Dict[str, Any] = Field(..., description="Document AI JSON output")
    output_format: str = Field("json", description="Output format: json or csv")
    
    class Config:
        schema_extra = {
            "example": {
                "document_ai_json": {
                    "entities": [],
                    "text": "..."
                },
                "output_format": "json"
            }
        }


class BatchParseRequest(BaseModel):
    """批量账单解析请求"""
    statements: List[Dict[str, Any]] = Field(..., description="List of Document AI JSONs")
    merge_output: bool = Field(True, description="Merge all statements into one CSV")


class ParseResponse(BaseModel):
    """解析响应"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    validation: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class CogneeAddRequest(BaseModel):
    """Cognee 添加记忆请求"""
    customer_id: str = Field(..., description="客户唯一标识符")
    data: Dict[str, Any] = Field(..., description="记忆数据")
    
    class Config:
        schema_extra = {
            "example": {
                "customer_id": "CUST001",
                "data": {
                    "content": "客户偏好高收益信用卡",
                    "metadata": {"category": "preference"}
                }
            }
        }


class CogneeSearchRequest(BaseModel):
    """Cognee 搜索记忆请求"""
    customer_id: str = Field(..., description="客户唯一标识符")
    query: str = Field(..., description="搜索查询文本")
    
    class Config:
        schema_extra = {
            "example": {
                "customer_id": "CUST001",
                "query": "信用卡偏好"
            }
        }


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API 根路径"""
    return {
        "service": "CreditPilot Statement Parser API",
        "version": "1.0.0",
        "endpoints": {
            "parse": "POST /parse",
            "batch_parse": "POST /parse/batch",
            "health": "GET /health",
            "cognee_add": "POST /cognee/add",
            "cognee_search": "POST /cognee/search",
            "cognee_cognify": "POST /cognee/cognify",
            "cognee_status": "GET /cognee/status"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "statement-parser",
        "version": "1.0.0"
    }


@app.post("/parse", response_model=ParseResponse)
async def parse_statement(request: ParseRequest):
    """
    解析单个信用卡账单
    
    接收 Document AI JSON，返回处理后的结构化数据
    
    Args:
        request: ParseRequest 对象
            - document_ai_json: Document AI 的 JSON 输出
            - output_format: "json" 或 "csv"
    
    Returns:
        ParseResponse:
        {
            "success": true,
            "data": {...},
            "validation": {...},
            "metadata": {...}
        }
    """
    try:
        # 处理账单
        result = processor.process(request.document_ai_json)
        
        # 返回结果
        return ParseResponse(
            success=True,
            data=result,
            validation=result.get('validation'),
            metadata=result.get('metadata')
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )


@app.post("/parse/batch")
async def parse_batch(request: BatchParseRequest):
    """
    批量解析多个信用卡账单
    
    Args:
        request: BatchParseRequest
            - statements: Document AI JSON 列表
            - merge_output: 是否合并为单个输出
    
    Returns:
        {
            "success": true,
            "total_statements": 41,
            "successful": 40,
            "failed": 1,
            "results": [...]
        }
    """
    try:
        results = []
        successful = 0
        failed = 0
        
        for i, statement_json in enumerate(request.statements):
            try:
                result = processor.process(statement_json)
                results.append({
                    "index": i,
                    "success": True,
                    "data": result
                })
                successful += 1
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e)
                })
                failed += 1
        
        return {
            "success": True,
            "total_statements": len(request.statements),
            "successful": successful,
            "failed": failed,
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch processing failed: {str(e)}"
        )


@app.post("/parse/csv")
async def parse_and_download_csv(request: ParseRequest):
    """
    解析账单并返回 CSV 文件下载
    
    Returns:
        CSV 文件下载
    """
    try:
        # 处理账单
        result = processor.process(request.document_ai_json)
        
        # 创建临时 CSV 文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as tmp:
            csv_path = tmp.name
        
        # 保存到 CSV
        processor.save_to_csv(result, csv_path)
        
        # 返回文件下载
        return FileResponse(
            csv_path,
            media_type='text/csv',
            filename=f"statement_{result.get('statement_date', 'export')}.csv"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"CSV generation failed: {str(e)}"
        )


@app.post("/validate")
async def validate_balance(
    previous_balance: float,
    current_balance: float,
    transactions: List[Dict[str, Any]]
):
    """
    独立的余额验证 endpoint
    
    Args:
        previous_balance: 上期余额
        current_balance: 本期余额
        transactions: 交易列表
    
    Returns:
        验证结果
    """
    from utils.crdr_fix import CRDRFixer
    
    fixer = CRDRFixer()
    validation = fixer.validate_balance(
        previous_balance,
        current_balance,
        transactions
    )
    
    return validation


# ============================================================================
# Cognee API Endpoints (客户记忆管理)
# ============================================================================

@app.post("/cognee/add")
async def cognee_add_memory(request: CogneeAddRequest):
    """
    添加客户记忆到 Cognee
    
    Args:
        request: CogneeAddRequest
            - customer_id: 客户唯一标识符
            - data: 记忆数据（包含 content 和可选 metadata）
    
    Returns:
        {
            "success": true,
            "memory_id": "...",
            "message": "记忆添加成功"
        }
    """
    result = await add_memory(request.customer_id, request.data)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "添加记忆失败")
        )
    
    return result


@app.post("/cognee/search")
async def cognee_search_memory(request: CogneeSearchRequest):
    """
    搜索客户记忆
    
    Args:
        request: CogneeSearchRequest
            - customer_id: 客户唯一标识符
            - query: 搜索查询文本
    
    Returns:
        {
            "success": true,
            "results": [...],
            "total_count": 5,
            "query": "..."
        }
    """
    result = await search_memory(request.customer_id, request.query)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "搜索记忆失败")
        )
    
    return result


@app.post("/cognee/cognify")
async def cognee_process_memory():
    """
    处理并优化所有记忆
    
    触发 Cognee 的记忆处理流程，包括向量化和知识图谱构建
    
    Returns:
        {
            "success": true,
            "message": "记忆处理完成",
            "processed_count": 10
        }
    """
    result = await cognify_memory()
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "记忆处理失败")
        )
    
    return result


@app.get("/cognee/status")
async def cognee_get_status():
    """
    获取 Cognee 服务状态
    
    Returns:
        {
            "success": true,
            "status": "healthy"
        }
    """
    return await get_memory_status()


# ============================================================================
# Server 启动
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
