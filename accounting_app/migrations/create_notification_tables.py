"""
通知系统 - 数据库迁移
创建通知相关表：notifications, notification_preferences
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from accounting_app.db import engine, Base
from accounting_app.models import Notification, NotificationPreference


def create_notification_tables():
    """创建通知系统相关表"""
    
    print("=" * 80)
    print("创建通知系统数据表...")
    print("=" * 80)
    
    try:
        Base.metadata.create_all(
            bind=engine,
            tables=[
                Notification.__table__,
                NotificationPreference.__table__,
            ],
            checkfirst=True
        )
        
        print("✓ Created notifications table")
        print("✓ Created notification_preferences table")
        print("\n" + "=" * 80)
        print("✅ 通知系统表创建成功！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        raise


if __name__ == "__main__":
    create_notification_tables()
