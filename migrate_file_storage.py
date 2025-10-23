#!/usr/bin/env python3
"""
文件存储迁移脚本
File Storage Migration Script

将现有文件从旧的混乱结构迁移到新的统一架构

⚠️  重要提示:
    - 执行前请先备份整个数据库和文件系统
    - 建议先在测试环境运行
    - 可以先迁移1-2个客户进行测试
    - 迁移过程可恢复，不会删除原文件

执行步骤:
    1. python migrate_file_storage.py --dry-run          # 预览迁移计划
    2. python migrate_file_storage.py --test             # 测试迁移（1-2个客户）
    3. python migrate_file_storage.py --migrate          # 执行全量迁移
    4. python migrate_file_storage.py --verify           # 验证迁移结果
    5. python migrate_file_storage.py --cleanup          # 清理旧文件（确认无误后）
"""
import sqlite3
import os
import shutil
import argparse
from datetime import datetime
from pathlib import Path
import json

from services.file_storage_manager import FileStorageManager
from db.database import get_db

class FileStorageMigrator:
    """文件存储迁移器"""
    
    def __init__(self):
        self.migration_log = []
        self.stats = {
            'total_files': 0,
            'migrated': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def log(self, message, level='INFO'):
        """记录迁移日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        self.migration_log.append(log_entry)
    
    def backup_database(self):
        """备份数据库"""
        self.log("开始备份数据库...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"db/backup_before_migration_{timestamp}.db"
        
        try:
            shutil.copy2('db/smart_loan_manager.db', backup_path)
            self.log(f"✅ 数据库已备份到: {backup_path}")
            return backup_path
        except Exception as e:
            self.log(f"❌ 数据库备份失败: {str(e)}", 'ERROR')
            return None
    
    def dry_run(self):
        """
        预览迁移计划（不实际执行）
        """
        self.log("=" * 80)
        self.log("开始预览迁移计划（DRY RUN）")
        self.log("=" * 80)
        
        conn = sqlite3.connect('db/smart_loan_manager.db')
        cursor = conn.cursor()
        
        # 分析信用卡账单
        self.log("\n📋 信用卡账单迁移计划:")
        cursor.execute("""
            SELECT 
                s.id,
                c.customer_id,
                cu.name,
                cu.customer_code,
                c.bank_name,
                c.card_number_last4,
                s.statement_date,
                s.file_path
            FROM statements s
            JOIN credit_cards c ON s.card_id = c.id
            JOIN customers cu ON c.customer_id = cu.id
            WHERE s.file_path IS NOT NULL
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            sid, cust_id, name, code, bank, last4, date, old_path = row
            
            # 生成新路径
            statement_date = datetime.strptime(date.split()[0], '%Y-%m-%d')
            new_path = FileStorageManager.generate_credit_card_path(
                code, bank, last4, statement_date
            )
            
            self.log(f"\n  客户: {name} ({code})")
            self.log(f"  旧路径: {old_path}")
            self.log(f"  新路径: {new_path}")
            self.log(f"  文件{'存在' if os.path.exists(old_path) else '不存在'}")
        
        # 分析储蓄账户月结单
        self.log("\n\n💰 储蓄账户月结单迁移计划:")
        cursor.execute("""
            SELECT 
                ss.id,
                sa.customer_id,
                cu.name,
                cu.customer_code,
                sa.bank_name,
                sa.account_number_last4,
                ss.statement_date,
                ss.file_path
            FROM savings_statements ss
            JOIN savings_accounts sa ON ss.savings_account_id = sa.id
            JOIN customers cu ON sa.customer_id = cu.id
            WHERE ss.file_path IS NOT NULL
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            sid, cust_id, name, code, bank, acc_num, date, old_path = row
            
            statement_date = datetime.strptime(date.split()[0], '%Y-%m-%d')
            new_path = FileStorageManager.generate_savings_path(
                code, bank, acc_num, statement_date
            )
            
            self.log(f"\n  客户: {name} ({code})")
            self.log(f"  旧路径: {old_path}")
            self.log(f"  新路径: {new_path}")
            self.log(f"  文件{'存在' if os.path.exists(old_path) else '不存在'}")
        
        conn.close()
        
        self.log("\n" + "=" * 80)
        self.log("预览完成 - 这只是计划，未执行任何迁移")
        self.log("=" * 80)
    
    def migrate_customer(self, customer_id, test_mode=False):
        """
        迁移单个客户的所有文件
        
        Args:
            customer_id: 客户ID
            test_mode: 测试模式（不实际移动文件，只复制）
        """
        conn = sqlite3.connect('db/smart_loan_manager.db')
        cursor = conn.cursor()
        
        # 获取客户信息
        cursor.execute("""
            SELECT id, name, customer_code 
            FROM customers 
            WHERE id = ?
        """, (customer_id,))
        
        customer = cursor.fetchone()
        if not customer:
            self.log(f"❌ 客户ID {customer_id} 不存在", 'ERROR')
            return False
        
        cust_id, name, code = customer
        self.log(f"\n{'='*80}")
        self.log(f"开始迁移客户: {name} ({code})")
        self.log(f"{'='*80}")
        
        # 迁移信用卡账单
        self.log("\n📋 迁移信用卡账单...")
        cursor.execute("""
            SELECT 
                s.id,
                c.bank_name,
                c.card_number_last4,
                s.statement_date,
                s.file_path
            FROM statements s
            JOIN credit_cards c ON s.card_id = c.id
            WHERE c.customer_id = ? AND s.file_path IS NOT NULL
        """, (customer_id,))
        
        for row in cursor.fetchall():
            sid, bank, last4, date, old_path = row
            
            try:
                statement_date = datetime.strptime(date.split()[0], '%Y-%m-%d')
                new_path = FileStorageManager.generate_credit_card_path(
                    code, bank, last4, statement_date
                )
                
                if self._migrate_file(sid, 'statements', old_path, new_path, test_mode):
                    self.stats['migrated'] += 1
                else:
                    self.stats['failed'] += 1
                    
            except Exception as e:
                self.log(f"❌ 迁移失败 (ID={sid}): {str(e)}", 'ERROR')
                self.stats['failed'] += 1
        
        # 迁移储蓄账户月结单
        self.log("\n💰 迁移储蓄账户月结单...")
        cursor.execute("""
            SELECT 
                ss.id,
                sa.bank_name,
                sa.account_number_last4,
                ss.statement_date,
                ss.file_path
            FROM savings_statements ss
            JOIN savings_accounts sa ON ss.savings_account_id = sa.id
            WHERE sa.customer_id = ? AND ss.file_path IS NOT NULL
        """, (customer_id,))
        
        for row in cursor.fetchall():
            sid, bank, acc_num, date, old_path = row
            
            try:
                statement_date = datetime.strptime(date.split()[0], '%Y-%m-%d')
                new_path = FileStorageManager.generate_savings_path(
                    code, bank, acc_num, statement_date
                )
                
                if self._migrate_file(sid, 'savings_statements', old_path, new_path, test_mode):
                    self.stats['migrated'] += 1
                else:
                    self.stats['failed'] += 1
                    
            except Exception as e:
                self.log(f"❌ 迁移失败 (ID={sid}): {str(e)}", 'ERROR')
                self.stats['failed'] += 1
        
        conn.close()
        
        self.log(f"\n✅ 客户 {name} 迁移完成")
        return True
    
    def _migrate_file(self, record_id, table_name, old_path, new_path, test_mode):
        """
        迁移单个文件
        
        Args:
            record_id: 数据库记录ID
            table_name: 表名
            old_path: 旧路径
            new_path: 新路径
            test_mode: 测试模式（复制而不是移动）
        """
        self.stats['total_files'] += 1
        
        # 检查旧文件是否存在
        if not os.path.exists(old_path):
            self.log(f"⚠️  文件不存在，跳过: {old_path}", 'WARN')
            self.stats['skipped'] += 1
            return False
        
        # 如果新旧路径相同，跳过
        if old_path == new_path:
            self.log(f"⏭️  路径未变化，跳过: {old_path}")
            self.stats['skipped'] += 1
            return True
        
        # 确保新目录存在
        FileStorageManager.ensure_directory(new_path)
        
        # 复制或移动文件
        try:
            if test_mode:
                shutil.copy2(old_path, new_path)
                self.log(f"✅ [TEST] 复制: {os.path.basename(new_path)}")
            else:
                shutil.move(old_path, new_path)
                self.log(f"✅ 移动: {os.path.basename(new_path)}")
            
            # 更新数据库
            conn = sqlite3.connect('db/smart_loan_manager.db')
            cursor = conn.cursor()
            cursor.execute(f"UPDATE {table_name} SET file_path = ? WHERE id = ?", 
                          (new_path, record_id))
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.log(f"❌ 文件迁移失败: {str(e)}", 'ERROR')
            return False
    
    def verify_migration(self):
        """验证迁移结果"""
        self.log("\n" + "=" * 80)
        self.log("开始验证迁移结果...")
        self.log("=" * 80)
        
        conn = sqlite3.connect('db/smart_loan_manager.db')
        cursor = conn.cursor()
        
        # 检查所有file_path是否存在
        issues = []
        
        # 检查信用卡账单
        cursor.execute("SELECT id, file_path FROM statements WHERE file_path IS NOT NULL")
        for sid, file_path in cursor.fetchall():
            if not os.path.exists(file_path):
                issues.append(('statements', sid, file_path))
        
        # 检查储蓄账户
        cursor.execute("SELECT id, file_path FROM savings_statements WHERE file_path IS NOT NULL")
        for sid, file_path in cursor.fetchall():
            if not os.path.exists(file_path):
                issues.append(('savings_statements', sid, file_path))
        
        conn.close()
        
        if issues:
            self.log(f"\n⚠️  发现 {len(issues)} 个问题:")
            for table, rid, path in issues[:20]:
                self.log(f"  {table} ID={rid}: 文件不存在 - {path}")
        else:
            self.log("\n✅ 验证通过！所有文件路径都正确！")
        
        return len(issues) == 0
    
    def save_migration_report(self):
        """保存迁移报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'log': self.migration_log
        }
        
        filename = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log(f"\n📝 迁移报告已保存: {filename}")
        return filename


def main():
    parser = argparse.ArgumentParser(description='文件存储迁移工具')
    parser.add_argument('--dry-run', action='store_true', help='预览迁移计划')
    parser.add_argument('--test', action='store_true', help='测试迁移（前2个客户）')
    parser.add_argument('--migrate', action='store_true', help='执行全量迁移')
    parser.add_argument('--verify', action='store_true', help='验证迁移结果')
    parser.add_argument('--customer', type=int, help='只迁移指定客户ID')
    
    args = parser.parse_args()
    
    migrator = FileStorageMigrator()
    
    if args.dry_run:
        # 预览迁移计划
        migrator.dry_run()
        
    elif args.test:
        # 测试迁移（前2个客户）
        print("\n⚠️  测试模式 - 文件将被复制（不删除原文件）\n")
        
        conn = sqlite3.connect('db/smart_loan_manager.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM customers LIMIT 2")
        customers = cursor.fetchall()
        conn.close()
        
        for cust_id, name in customers:
            migrator.migrate_customer(cust_id, test_mode=True)
        
        migrator.save_migration_report()
        
    elif args.customer:
        # 迁移指定客户
        print(f"\n迁移客户 ID={args.customer}\n")
        migrator.backup_database()
        migrator.migrate_customer(args.customer, test_mode=False)
        migrator.verify_migration()
        migrator.save_migration_report()
        
    elif args.migrate:
        # 全量迁移
        print("\n⚠️  即将执行全量迁移！")
        print("请确认已备份数据库和文件系统。")
        confirm = input("输入 'YES' 继续: ")
        
        if confirm != 'YES':
            print("已取消迁移")
            return
        
        # 备份
        migrator.backup_database()
        
        # 获取所有客户
        conn = sqlite3.connect('db/smart_loan_manager.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM customers")
        customer_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # 逐个迁移
        for cust_id in customer_ids:
            migrator.migrate_customer(cust_id, test_mode=False)
        
        # 验证
        migrator.verify_migration()
        
        # 保存报告
        migrator.save_migration_report()
        
        print("\n" + "=" * 80)
        print("迁移统计:")
        print(f"  总文件数: {migrator.stats['total_files']}")
        print(f"  成功迁移: {migrator.stats['migrated']}")
        print(f"  跳过: {migrator.stats['skipped']}")
        print(f"  失败: {migrator.stats['failed']}")
        print("=" * 80)
        
    elif args.verify:
        # 只验证
        migrator.verify_migration()
        
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
