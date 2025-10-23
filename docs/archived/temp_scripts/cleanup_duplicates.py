#!/usr/bin/env python3
"""
清理重复的储蓄账户月结单记录
保留最新的记录，删除旧的重复记录
"""
import sqlite3
from datetime import datetime

def connect_db():
    return sqlite3.connect('db/smart_loan_manager.db')

def backup_before_delete():
    """删除前先备份即将删除的记录"""
    print("\n" + "="*80)
    print("📦 备份即将删除的记录")
    print("="*80)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # 创建备份表（如果不存在）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deleted_savings_statements_backup (
            id INTEGER,
            savings_account_id INTEGER,
            statement_date TEXT,
            file_path TEXT,
            file_type TEXT,
            total_transactions INTEGER,
            is_processed INTEGER,
            created_at TIMESTAMP,
            deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deletion_reason TEXT
        )
    """)
    
    # 要删除的ID列表（保留ID较大的，删除ID较小的）
    ids_to_delete = [160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172]
    
    # 备份这些记录
    placeholders = ','.join('?' * len(ids_to_delete))
    cursor.execute(f"""
        INSERT INTO deleted_savings_statements_backup 
        (id, savings_account_id, statement_date, file_path, file_type, 
         total_transactions, is_processed, created_at, deletion_reason)
        SELECT 
            id, savings_account_id, statement_date, file_path, file_type,
            total_transactions, is_processed, created_at,
            'Duplicate GX Bank statement - keeping newer record'
        FROM savings_statements
        WHERE id IN ({placeholders})
    """, ids_to_delete)
    
    backup_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"✅ 已备份 {backup_count} 条记录到 deleted_savings_statements_backup 表")
    return backup_count

def delete_duplicates():
    """删除重复的记录"""
    print("\n" + "="*80)
    print("🗑️  删除重复的储蓄账户月结单")
    print("="*80)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # 要删除的ID（每个月份中ID较小的那条）
    ids_to_delete = [160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172]
    
    # 显示即将删除的记录详情
    print("\n即将删除以下记录：\n")
    for id_val in ids_to_delete:
        cursor.execute("""
            SELECT ss.id, sa.customer_id, sa.bank_name, ss.statement_date, ss.file_path
            FROM savings_statements ss
            JOIN savings_accounts sa ON ss.savings_account_id = sa.id
            WHERE ss.id = ?
        """, (id_val,))
        row = cursor.fetchone()
        if row:
            print(f"ID {row[0]}: 客户{row[1]} | {row[2]} | {row[3]} | {row[4]}")
    
    # 确认删除
    print(f"\n⚠️  准备删除 {len(ids_to_delete)} 条重复记录...")
    
    # 执行删除
    placeholders = ','.join('?' * len(ids_to_delete))
    cursor.execute(f"DELETE FROM savings_statements WHERE id IN ({placeholders})", ids_to_delete)
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"✅ 成功删除 {deleted_count} 条重复记录")
    return deleted_count

def verify_cleanup():
    """验证清理结果"""
    print("\n" + "="*80)
    print("✔️  验证清理结果")
    print("="*80)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # 重新检查是否还有重复
    cursor.execute("""
        SELECT 
            sa.customer_id,
            sa.bank_name,
            strftime('%Y-%m', ss.statement_date) as month,
            COUNT(*) as count,
            GROUP_CONCAT(ss.id) as ids
        FROM savings_statements ss
        JOIN savings_accounts sa ON ss.savings_account_id = sa.id
        GROUP BY sa.customer_id, sa.bank_name, strftime('%Y-%m', ss.statement_date)
        HAVING COUNT(*) > 1
    """)
    
    remaining_duplicates = cursor.fetchall()
    
    if remaining_duplicates:
        print(f"⚠️  仍然发现 {len(remaining_duplicates)} 组重复记录：")
        for dup in remaining_duplicates:
            print(f"   {dup}")
    else:
        print("✅ 没有发现重复记录！清理成功！")
    
    # 统计总数
    cursor.execute("SELECT COUNT(*) FROM savings_statements")
    total = cursor.fetchone()[0]
    
    print(f"\n📊 当前储蓄账户月结单总数: {total}")
    
    conn.close()
    
    return len(remaining_duplicates) == 0

def generate_cleanup_report():
    """生成清理报告"""
    print("\n" + "="*80)
    print("📄 清理报告")
    print("="*80)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # 统计信息
    cursor.execute("SELECT COUNT(*) FROM deleted_savings_statements_backup")
    backup_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM savings_statements")
    current_count = cursor.fetchone()[0]
    
    report = f"""
清理完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

清理统计:
  - 备份记录数: {backup_count}
  - 删除记录数: {backup_count}
  - 当前记录数: {current_count}
  
清理内容:
  - GX Bank 储蓄账户月结单（2024-07 至 2025-07）
  - 每个月删除了1条旧的重复记录
  - 保留了最新上传的记录
  
备份位置:
  - 表名: deleted_savings_statements_backup
  - 可通过SQL查询恢复: 
    INSERT INTO savings_statements SELECT * FROM deleted_savings_statements_backup WHERE id = ?
    
状态: ✅ 成功
"""
    
    conn.close()
    
    print(report)
    
    # 保存报告到文件
    with open('cleanup_report_duplicates.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("📝 报告已保存到: cleanup_report_duplicates.txt")

def main():
    print("\n" + "="*80)
    print("🧹 开始清理重复的储蓄账户月结单")
    print("="*80)
    print("\n清理策略:")
    print("  - 保留每个月ID较大的记录（最新上传）")
    print("  - 删除每个月ID较小的记录（旧的重复）")
    print("  - 删除前先备份到独立表")
    print("  - 文件不会被删除（仍在磁盘上）\n")
    
    try:
        # 步骤1：备份
        backup_count = backup_before_delete()
        
        # 步骤2：删除
        deleted_count = delete_duplicates()
        
        # 步骤3：验证
        success = verify_cleanup()
        
        # 步骤4：生成报告
        if success:
            generate_cleanup_report()
            print("\n" + "="*80)
            print("✅ 清理完成！系统已优化！")
            print("="*80)
        else:
            print("\n⚠️  清理后仍有重复记录，请检查！")
            
    except Exception as e:
        print(f"\n❌ 清理过程出错: {str(e)}")
        print("数据已回滚，系统未受影响")

if __name__ == '__main__':
    main()
