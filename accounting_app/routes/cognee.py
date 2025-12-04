"""
Cognee API 路由
记忆管理 - 与 CogneePilot 服务集成
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

COGNEE_BASE_URL = "https://cognee-pilot--business183.replit.app"


class MemoryAddRequest(BaseModel):
    """添加记忆请求"""
    content: str = Field(..., description="记忆内容")
    dataset_name: str = Field(default="credit_pilot", description="数据集名称")
    
    class Config:
        schema_extra = {
            "example": {
                "content": "客户偏好高收益信用卡，月消费约 RM 5000",
                "dataset_name": "credit_pilot"
            }
        }


class MemorySearchRequest(BaseModel):
    """搜索记忆请求"""
    query: str = Field(..., description="搜索查询文本")
    search_type: str = Field(default="INSIGHTS", description="搜索类型")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "信用卡偏好",
                "search_type": "INSIGHTS"
            }
        }


@router.get("/status")
async def get_status():
    """
    获取 CogneePilot 服务状态
    
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


@router.get("/info")
async def get_service_info():
    """
    获取 CogneePilot 服务信息
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{COGNEE_BASE_URL}/")
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "info": response.json()
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="获取服务信息失败"
                )
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"请求错误: {str(e)}")


@router.post("/add")
async def add_memory(request: MemoryAddRequest):
    """
    添加记忆到 CogneePilot
    
    Args:
        request: MemoryAddRequest
            - content: 记忆内容
            - dataset_name: 数据集名称（默认 "credit_pilot"）
    
    Returns:
        {
            "success": true,
            "message": "记忆添加成功"
        }
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{COGNEE_BASE_URL}/memory/add",
                json={
                    "content": request.content,
                    "dataset_name": request.dataset_name
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"成功添加记忆到数据集 {request.dataset_name}")
                return {
                    "success": True,
                    "message": "记忆添加成功",
                    "details": result
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"添加记忆失败: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="请求超时")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"请求错误: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加记忆失败: {str(e)}")


@router.post("/search")
async def search_memory(request: MemorySearchRequest):
    """
    搜索记忆
    
    Args:
        request: MemorySearchRequest
            - query: 搜索查询文本
            - search_type: 搜索类型（如 "INSIGHTS", "SUMMARIES"）
    
    Returns:
        {
            "success": true,
            "results": [...],
            "query": "..."
        }
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{COGNEE_BASE_URL}/memory/search",
                json={
                    "query": request.query,
                    "search_type": request.search_type
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"搜索记忆成功，查询: {request.query}")
                return {
                    "success": True,
                    "results": result.get("results", result),
                    "query": request.query,
                    "search_type": request.search_type
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"搜索记忆失败: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="搜索请求超时")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"搜索请求错误: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索记忆失败: {str(e)}")


@router.post("/cognify")
async def cognify_memory():
    """
    认知化处理记忆（生成知识图谱）
    
    触发 Cognee 的记忆处理流程，包括向量化和知识图谱构建。
    此操作可能需要较长时间。
    
    Returns:
        {
            "success": true,
            "message": "记忆认知化处理完成"
        }
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{COGNEE_BASE_URL}/memory/cognify")
            
            if response.status_code == 200:
                result = response.json()
                logger.info("记忆认知化处理完成")
                return {
                    "success": True,
                    "message": "记忆认知化处理完成",
                    "details": result
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"认知化处理失败: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="处理请求超时（可能正在处理大量数据）")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"处理请求错误: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"认知化处理失败: {str(e)}")


@router.post("/reset")
async def reset_memory():
    """
    重置所有记忆
    
    ⚠️ 警告：此操作会删除所有存储的记忆数据！
    
    Returns:
        {
            "success": true,
            "message": "所有记忆已重置"
        }
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{COGNEE_BASE_URL}/memory/reset")
            
            if response.status_code == 200:
                result = response.json()
                logger.warning("所有记忆已重置")
                return {
                    "success": True,
                    "message": "所有记忆已重置",
                    "details": result
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"重置记忆失败: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="重置请求超时")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"重置请求错误: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置记忆失败: {str(e)}")
