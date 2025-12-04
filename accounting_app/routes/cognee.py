"""
Cognee API 路由
客户记忆管理 - 与 CogneePilot 服务集成
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

COGNEE_BASE_URL = "https://cognee-pilot--business183.replit.app"


class CogneeAddRequest(BaseModel):
    """添加记忆请求"""
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
    """搜索记忆请求"""
    customer_id: str = Field(..., description="客户唯一标识符")
    query: str = Field(..., description="搜索查询文本")
    
    class Config:
        schema_extra = {
            "example": {
                "customer_id": "CUST001",
                "query": "信用卡偏好"
            }
        }


@router.post("/add")
async def add_memory(request: CogneeAddRequest):
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
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{COGNEE_BASE_URL}/add",
                json={
                    "customer_id": request.customer_id,
                    "data": request.data
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"成功添加客户 {request.customer_id} 的记忆")
                return {
                    "success": True,
                    "memory_id": result.get("memory_id"),
                    "message": "记忆添加成功"
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"添加记忆失败: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Cognee API 请求超时")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Cognee API 请求错误: {str(e)}")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"添加记忆失败: {str(e)}")


@router.post("/search")
async def search_memory(request: CogneeSearchRequest):
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
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{COGNEE_BASE_URL}/search",
                json={
                    "customer_id": request.customer_id,
                    "query": request.query
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                results = result.get("results", [])
                logger.info(f"搜索客户 {request.customer_id} 的记忆，找到 {len(results)} 条结果")
                return {
                    "success": True,
                    "results": results,
                    "total_count": len(results),
                    "query": request.query
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"搜索记忆失败: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Cognee API 搜索请求超时")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Cognee API 搜索请求错误: {str(e)}")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"搜索记忆失败: {str(e)}")


@router.post("/cognify")
async def cognify_memory():
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
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{COGNEE_BASE_URL}/cognify")
            
            if response.status_code == 200:
                result = response.json()
                logger.info("记忆处理完成")
                return {
                    "success": True,
                    "message": "记忆处理完成",
                    "processed_count": result.get("processed_count", 0),
                    "details": result
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"记忆处理失败: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Cognee API 处理请求超时")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Cognee API 处理请求错误: {str(e)}")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"记忆处理失败: {str(e)}")


@router.get("/status")
async def get_status():
    """
    获取 Cognee 服务状态
    
    Returns:
        {
            "success": true,
            "status": "healthy"
        }
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{COGNEE_BASE_URL}/health")
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "status": "healthy",
                    "details": result
                }
            else:
                return {
                    "success": False,
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
                
    except Exception as e:
        return {
            "success": False,
            "status": "unreachable",
            "error": str(e)
        }
