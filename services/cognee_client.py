"""
Cognee API 客户端
用于与 CogneePilot 服务集成，提供客户记忆管理功能
"""

import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

COGNEE_BASE_URL = "https://cognee-pilot--business183.replit.app"


async def add_memory(customer_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    添加客户记忆
    
    Args:
        customer_id: 客户唯一标识符
        data: 要存储的记忆数据
            - content: 记忆内容（文本）
            - metadata: 可选的元数据
    
    Returns:
        Dict containing:
            - success: 是否成功
            - memory_id: 新创建的记忆ID
            - message: 操作结果消息
    
    Example:
        result = await add_memory("CUST001", {
            "content": "客户偏好高收益信用卡",
            "metadata": {"category": "preference", "date": "2025-01-01"}
        })
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{COGNEE_BASE_URL}/add",
                json={
                    "customer_id": customer_id,
                    "data": data
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"成功添加客户 {customer_id} 的记忆")
                return {
                    "success": True,
                    "memory_id": result.get("memory_id"),
                    "message": "记忆添加成功"
                }
            else:
                error_msg = f"添加记忆失败: HTTP {response.status_code}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "details": response.text
                }
                
    except httpx.TimeoutException:
        error_msg = "Cognee API 请求超时"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
        
    except httpx.RequestError as e:
        error_msg = f"Cognee API 请求错误: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
        
    except Exception as e:
        error_msg = f"添加记忆时发生未知错误: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


async def search_memory(customer_id: str, query: str) -> Dict[str, Any]:
    """
    搜索客户记忆
    
    Args:
        customer_id: 客户唯一标识符
        query: 搜索查询文本
    
    Returns:
        Dict containing:
            - success: 是否成功
            - results: 搜索结果列表
            - total_count: 结果总数
    
    Example:
        result = await search_memory("CUST001", "信用卡偏好")
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{COGNEE_BASE_URL}/search",
                json={
                    "customer_id": customer_id,
                    "query": query
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                results = result.get("results", [])
                logger.info(f"搜索客户 {customer_id} 的记忆，找到 {len(results)} 条结果")
                return {
                    "success": True,
                    "results": results,
                    "total_count": len(results),
                    "query": query
                }
            else:
                error_msg = f"搜索记忆失败: HTTP {response.status_code}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "details": response.text
                }
                
    except httpx.TimeoutException:
        error_msg = "Cognee API 搜索请求超时"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
        
    except httpx.RequestError as e:
        error_msg = f"Cognee API 搜索请求错误: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
        
    except Exception as e:
        error_msg = f"搜索记忆时发生未知错误: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


async def cognify_memory() -> Dict[str, Any]:
    """
    处理并优化所有记忆
    
    触发 Cognee 的记忆处理流程，包括：
    - 记忆向量化
    - 知识图谱构建
    - 关系提取
    
    Returns:
        Dict containing:
            - success: 是否成功
            - message: 处理结果消息
            - processed_count: 处理的记忆数量
    
    Example:
        result = await cognify_memory()
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{COGNEE_BASE_URL}/cognify"
            )
            
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
                error_msg = f"记忆处理失败: HTTP {response.status_code}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "details": response.text
                }
                
    except httpx.TimeoutException:
        error_msg = "Cognee API 处理请求超时（可能正在处理大量数据）"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
        
    except httpx.RequestError as e:
        error_msg = f"Cognee API 处理请求错误: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
        
    except Exception as e:
        error_msg = f"处理记忆时发生未知错误: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


async def get_memory_status() -> Dict[str, Any]:
    """
    获取 Cognee 服务状态
    
    Returns:
        Dict containing:
            - success: 是否成功
            - status: 服务状态
            - version: API 版本
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
