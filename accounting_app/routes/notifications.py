"""
通知系统路由：获取、标记、管理通知
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from ..db import get_db
from ..models import User
from ..services import notification_service
from ..middleware.rbac_fixed import require_auth


router = APIRouter()


class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    title: str
    message: str
    priority: str
    status: str
    action_url: str | None
    action_label: str | None
    created_at: str
    
    class Config:
        from_attributes = True


class UnreadCountResponse(BaseModel):
    unread_count: int


class MarkAsReadRequest(BaseModel):
    notification_id: int


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    获取当前用户未读通知数量
    用于显示通知角标
    """
    unread_count = notification_service.get_unread_count(db, current_user.id)
    
    return {"unread_count": unread_count}


@router.get("/list", response_model=List[NotificationResponse])
def list_notifications(
    limit: int = 50,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    获取当前用户未读通知列表
    """
    notifications = notification_service.get_unread_notifications(
        db, current_user.id, limit
    )
    
    return [
        {
            "id": n.id,
            "notification_type": n.notification_type,
            "title": n.title,
            "message": n.message,
            "priority": n.priority,
            "status": n.status,
            "action_url": n.action_url,
            "action_label": n.action_label,
            "created_at": n.created_at.isoformat() if n.created_at else None
        }
        for n in notifications
    ]


@router.post("/mark-as-read")
def mark_notification_as_read(
    request: MarkAsReadRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    标记通知为已读
    """
    notification = notification_service.mark_as_read(
        db, request.notification_id, current_user.id
    )
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在或无权访问")
    
    return {"success": True, "message": "已标记为已读"}


@router.post("/mark-all-as-read")
def mark_all_notifications_as_read(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    标记所有通知为已读
    """
    updated_count = notification_service.mark_all_as_read(db, current_user.id)
    
    return {
        "success": True,
        "message": f"已标记 {updated_count} 条通知为已读",
        "updated_count": updated_count
    }


@router.get("/history", response_model=List[NotificationResponse])
def get_notification_history(
    status: str = "all",
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    获取用户通知历史（包含已读和未读）
    
    Args:
        status: 过滤条件 ('all', 'read', 'unread')
        limit: 返回数量限制
        offset: 分页偏移量
    """
    from ..models import Notification
    
    # 构建查询
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id
    )
    
    # 状态过滤
    if status == "read":
        query = query.filter(Notification.status == 'read')
    elif status == "unread":
        query = query.filter(Notification.status == 'unread')
    
    # 按创建时间倒序排列
    notifications = query.order_by(
        Notification.created_at.desc()
    ).limit(limit).offset(offset).all()
    
    return [
        {
            "id": n.id,
            "notification_type": n.notification_type,
            "title": n.title,
            "message": n.message,
            "priority": n.priority,
            "status": n.status,
            "action_url": n.action_url,
            "action_label": n.action_label,
            "created_at": n.created_at.isoformat() if n.created_at else None
        }
        for n in notifications
    ]
