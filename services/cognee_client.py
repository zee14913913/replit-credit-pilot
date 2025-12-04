"""
Cognee API 客户端
用于与 CogneePilot 服务集成，提供记忆管理功能
"""

import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

COGNEE_BASE_URL = "https://cognee-pilot--business183.replit.app"


async def add_memory(content: str, dataset_name: str = "creditpilot_customers") -> Dict[str, Any]:
    """
    添加记忆到 Cognee
    
    Args:
        content: 记忆内容（文本）
        dataset_name: 数据集名称（默认 "creditpilot_customers"）
    
    Returns:
        Dict containing:
            - success: 是否成功
            - message: 操作结果消息
    
    Example:
        result = await add_memory("客户偏好高收益信用卡", "creditpilot_customers")
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{COGNEE_BASE_URL}/memory/add",
                json={
                    "content": content,
                    "dataset_name": dataset_name
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"成功添加记忆到数据集 {dataset_name}")
                return {
                    "success": True,
                    "message": "记忆添加成功",
                    "details": result
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


async def search_memory(query: str, search_type: str = "INSIGHTS") -> Dict[str, Any]:
    """
    搜索记忆
    
    Args:
        query: 搜索查询文本
        search_type: 搜索类型（如 "INSIGHTS", "SUMMARIES" 等）
    
    Returns:
        Dict containing:
            - success: 是否成功
            - results: 搜索结果列表
    
    Example:
        result = await search_memory("信用卡偏好", "INSIGHTS")
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{COGNEE_BASE_URL}/memory/search",
                json={
                    "query": query,
                    "search_type": search_type
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"搜索记忆成功，查询: {query}")
                return {
                    "success": True,
                    "results": result.get("results", result),
                    "query": query,
                    "search_type": search_type
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
    认知化处理记忆（生成知识图谱）
    
    触发 Cognee 的记忆处理流程，包括：
    - 记忆向量化
    - 知识图谱构建
    - 关系提取
    
    Returns:
        Dict containing:
            - success: 是否成功
            - message: 处理结果消息
    
    Example:
        result = await cognify_memory()
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


async def reset_memory() -> Dict[str, Any]:
    """
    重置所有记忆
    
    警告：此操作会删除所有存储的记忆数据！
    
    Returns:
        Dict containing:
            - success: 是否成功
            - message: 操作结果消息
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
                error_msg = f"重置记忆失败: HTTP {response.status_code}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "details": response.text
                }
                
    except Exception as e:
        error_msg = f"重置记忆时发生错误: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}


async def get_service_info() -> Dict[str, Any]:
    """
    获取 Cognee 服务信息
    
    Returns:
        Dict containing service information
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
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def get_health_status() -> Dict[str, Any]:
    """
    获取 Cognee 服务健康状态
    
    Returns:
        Dict containing:
            - success: 是否成功
            - status: 服务状态
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
