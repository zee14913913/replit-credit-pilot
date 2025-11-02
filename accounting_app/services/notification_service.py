"""
通知服务：管理系统通知（上传指引 + 日报摘要）
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models import Notification, NotificationPreference, User


logger = logging.getLogger(__name__)


def create_upload_notification(
    db: Session,
    company_id: int,
    user_id: int,
    success: bool,
    upload_result: Dict[str, Any]
) -> Notification:
    """
    创建上传通知（成功或失败）
    
    Args:
        db: 数据库session
        company_id: 公司ID
        user_id: 用户ID
        success: 是否上传成功
        upload_result: 上传结果详情（银行、账号、月份、交易数等）
    
    Returns:
        Notification对象
    """
    
    if success:
        title = "✅ 文件上传成功"
        message = (
            f"您的银行账单已成功上传并分析。\n"
            f"银行: {upload_result.get('bank_name', 'N/A')}\n"
            f"账号: {upload_result.get('account_number', 'N/A')}\n"
            f"月份: {upload_result.get('statement_month', 'N/A')}\n"
            f"导入交易: {upload_result.get('transaction_count', 0)} 笔"
        )
        notification_type = "upload_success"
        action_url = f"/company/{company_id}/bank-statements"
        action_label = "查看账单详情"
        priority = "normal"
    else:
        title = "❌ 文件上传失败"
        message = (
            f"您的文件上传失败，需要处理。\n"
            f"错误原因: {upload_result.get('error_message', '未知错误')}\n\n"
            f"建议: {upload_result.get('suggestion', '请联系技术支持')}"
        )
        notification_type = "upload_failure"
        action_url = f"/company/{company_id}/files"
        action_label = "重新上传"
        priority = "high"
    
    # 创建通知记录
    notification = Notification(
        company_id=company_id,
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        payload=upload_result,
        priority=priority,
        status="unread",
        action_url=action_url,
        action_label=action_label,
        expires_at=datetime.utcnow() + timedelta(days=30)  # 30天后过期
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    logger.info(f"Created {notification_type} notification for user {user_id}")
    
    return notification


def create_daily_digest_notification(
    db: Session,
    company_id: int,
    user_id: int,
    digest_data: Dict[str, Any]
) -> Notification:
    """
    创建每日摘要通知（管理员）
    
    Args:
        db: 数据库session
        company_id: 公司ID
        user_id: 管理员用户ID
        digest_data: 摘要数据（上传活动统计）
    
    Returns:
        Notification对象
    """
    
    total_uploads = digest_data.get('total_uploads', 0)
    success_count = digest_data.get('success_count', 0)
    failure_count = digest_data.get('failure_count', 0)
    
    title = f"📊 每日上传活动摘要 ({digest_data.get('date', 'Today')})"
    message = (
        f"今日上传活动统计：\n\n"
        f"总上传数: {total_uploads} 个文件\n"
        f"成功: {success_count} 个\n"
        f"失败: {failure_count} 个\n"
        f"成功率: {(success_count/total_uploads*100) if total_uploads > 0 else 0:.1f}%\n\n"
        f"需要关注的客户: {len(digest_data.get('customers_with_failures', []))} 位"
    )
    
    notification = Notification(
        company_id=company_id,
        user_id=user_id,
        notification_type="daily_digest",
        title=title,
        message=message,
        payload=digest_data,
        priority="normal",
        status="unread",
        action_url=f"/company/{company_id}/audit-logs",
        action_label="查看详细日志",
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    logger.info(f"Created daily digest notification for admin user {user_id}")
    
    return notification


def get_unread_notifications(
    db: Session,
    user_id: int,
    limit: int = 50
) -> List[Notification]:
    """
    获取用户未读通知
    
    Args:
        db: 数据库session
        user_id: 用户ID
        limit: 返回数量限制
    
    Returns:
        通知列表
    """
    
    notifications = db.query(Notification).filter(
        and_(
            Notification.user_id == user_id,
            Notification.status == 'unread',
            or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        )
    ).order_by(
        Notification.created_at.desc()
    ).limit(limit).all()
    
    return notifications


def get_unread_count(db: Session, user_id: int) -> int:
    """
    获取用户未读通知数量
    
    Args:
        db: 数据库session
        user_id: 用户ID
    
    Returns:
        未读通知数量
    """
    
    count = db.query(Notification).filter(
        and_(
            Notification.user_id == user_id,
            Notification.status == 'unread',
            or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        )
    ).count()
    
    return count


def mark_as_read(
    db: Session,
    notification_id: int,
    user_id: int
) -> Optional[Notification]:
    """
    标记通知为已读
    
    Args:
        db: 数据库session
        notification_id: 通知ID
        user_id: 用户ID（用于验证权限）
    
    Returns:
        更新后的通知对象，如果未找到则返回None
    """
    
    notification = db.query(Notification).filter(
        and_(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
    ).first()
    
    if notification:
        notification.status = 'read'
        notification.read_at = datetime.utcnow()
        db.commit()
        db.refresh(notification)
        logger.info(f"Marked notification {notification_id} as read")
    
    return notification


def mark_all_as_read(db: Session, user_id: int) -> int:
    """
    标记用户所有通知为已读
    
    Args:
        db: 数据库session
        user_id: 用户ID
    
    Returns:
        更新的通知数量
    """
    
    updated_count = db.query(Notification).filter(
        and_(
            Notification.user_id == user_id,
            Notification.status == 'unread'
        )
    ).update({
        'status': 'read',
        'read_at': datetime.utcnow()
    }, synchronize_session=False)
    
    db.commit()
    
    logger.info(f"Marked {updated_count} notifications as read for user {user_id}")
    
    return updated_count


def get_notification_preferences(
    db: Session,
    user_id: int
) -> Optional[NotificationPreference]:
    """
    获取用户通知偏好设置
    
    Args:
        db: 数据库session
        user_id: 用户ID
    
    Returns:
        NotificationPreference对象，如果不存在则返回None
    """
    
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == user_id
    ).first()
    
    return preferences


def create_or_update_preferences(
    db: Session,
    user_id: int,
    preferences_data: Dict[str, Any]
) -> NotificationPreference:
    """
    创建或更新用户通知偏好
    
    Args:
        db: 数据库session
        user_id: 用户ID
        preferences_data: 偏好设置数据
    
    Returns:
        NotificationPreference对象
    """
    
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == user_id
    ).first()
    
    if preferences:
        # 更新现有偏好
        for key, value in preferences_data.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)
        preferences.updated_at = datetime.utcnow()
    else:
        # 创建新偏好
        preferences = NotificationPreference(
            user_id=user_id,
            **preferences_data
        )
        db.add(preferences)
    
    db.commit()
    db.refresh(preferences)
    
    logger.info(f"Updated notification preferences for user {user_id}")
    
    return preferences


def delete_old_notifications(db: Session, days_old: int = 90) -> int:
    """
    删除过期的旧通知（清理任务）
    
    Args:
        db: 数据库session
        days_old: 删除多少天前的已读/已归档通知
    
    Returns:
        删除的通知数量
    """
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    
    deleted_count = db.query(Notification).filter(
        and_(
            Notification.status.in_(['read', 'archived']),
            Notification.created_at < cutoff_date
        )
    ).delete(synchronize_session=False)
    
    db.commit()
    
    logger.info(f"Deleted {deleted_count} old notifications (>{days_old} days)")
    
    return deleted_count
