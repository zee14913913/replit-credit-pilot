"""
批量导入Yeo Chee Wang 2025年GX Bank储蓄账户月结单
确保100%准确度 - 使用AutoVerifier v3.0验证
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import get_db
from ingest.savings_parser import parse_savings_statement
from services.auto_verifier import AutoVerifier
from services.file_storage_manager import FileStorageManager
import shutil
from datetime import datetime

# 客户信息
CUSTOMER_ID = 7
CUSTOMER_CODE = 'Be_rich_YCW'
CUSTOMER_NAME = 'YEO CHEE WANG'
BANK_NAME = 'GX Bank'

# PDF文件列表（按月份顺序）
PDF_FILES = [
    'attached_assets/JAN 2025_1761777193753.pdf',
    'attached_assets/FEB 2025_1761777193753.pdf',
    'attached_assets/MAR 2025_1761777193753.pdf',
    'attached_assets/APR 2025_1761777193753.pdf',
    'attached_assets/MAY 2025_1761777193754.pdf',
    'attached_assets/JUNE 2025_1761777193753.pdf',
    'attached_assets/JULY 2025_1761777193753.pdf',
]

def import_statement(pdf_path: str, customer_id: int, bank_name: str):
    """导入单个月结单"""
    print(f"\n{'='*80}")
    print(f"📄 处理文件: {pdf_path}")
    print(f"{'='*80}")
    
    # 解析PDF
    try:
        info, transactions = parse_savings_statement(pdf_path, bank_name)
        print(f"✅ 解析成功: {info['statement_date']}")
        print(f"   - 账户后4位: {info['account_last4']}")
        print(f"   - 交易数量: {len(transactions)}")
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return None
    
    # 存入数据库
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 检查或创建储蓄账户
        cursor.execute('''
            SELECT id FROM savings_accounts 
            WHERE bank_name = ? AND account_number_last4 = ? AND customer_id = ?
        ''', (bank_name, info.get('account_last4', ''), customer_id))
        
        account = cursor.fetchone()
        
        if not account:
            cursor.execute('''
                INSERT INTO savings_accounts (customer_id, bank_name, account_number_last4)
                VALUES (?, ?, ?)
            ''', (customer_id, bank_name, info.get('account_last4', '')))
            savings_account_id = cursor.lastrowid
            print(f"   - 新建储蓄账户 ID: {savings_account_id}")
        else:
            savings_account_id = account['id']
            print(f"   - 使用已有账户 ID: {savings_account_id}")
        
        # 检查是否已存在此月的月结单
        cursor.execute('''
            SELECT id FROM savings_statements 
            WHERE savings_account_id = ? AND statement_date = ?
        ''', (savings_account_id, info['statement_date']))
        
        existing = cursor.fetchone()
        if existing:
            print(f"⚠️  警告: {info['statement_date']} 月结单已存在 (ID: {existing['id']})")
            choice = input("是否覆盖? (y/n): ")
            if choice.lower() != 'y':
                print("⏭️  跳过此月结单")
                return None
            # 删除旧记录
            cursor.execute('DELETE FROM savings_transactions WHERE savings_statement_id = ?', (existing['id'],))
            cursor.execute('DELETE FROM savings_statements WHERE id = ?', (existing['id'],))
            conn.commit()
            print(f"   - 已删除旧记录")
        
        # 获取客户信息
        cursor.execute('SELECT customer_code FROM customers WHERE id = ?', (customer_id,))
        customer = cursor.fetchone()
        customer_code = customer['customer_code'] if customer else 'Unknown'
        
        # 文件组织：复制PDF到标准位置
        storage_manager = FileStorageManager()
        filename = os.path.basename(pdf_path)
        
        # 使用标准化路径（不使用store_savings_statement，直接生成路径）
        dest_dir = f"static/uploads/customers/{customer_code}/savings"
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, filename)
        
        # 复制文件
        shutil.copy2(pdf_path, dest_path)
        print(f"   - 文件已保存: {dest_path}")
        
        # 插入月结单记录
        cursor.execute('''
            INSERT INTO savings_statements 
            (savings_account_id, statement_date, total_transactions, file_path, verification_status)
            VALUES (?, ?, ?, ?, ?)
        ''', (savings_account_id, info['statement_date'], len(transactions), dest_path, 'pending'))
        
        statement_id = cursor.lastrowid
        print(f"   - 月结单 ID: {statement_id}")
        
        # 插入交易记录
        inserted_count = 0
        for txn in transactions:
            cursor.execute('''
                INSERT INTO savings_transactions 
                (savings_statement_id, transaction_date, description, amount, transaction_type, balance)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (statement_id, txn['date'], txn['description'], txn['amount'], 
                  txn['type'], txn['balance']))
            inserted_count += 1
        
        conn.commit()
        print(f"   - 已插入 {inserted_count} 笔交易记录")
    
    # 🚀 AutoVerifier v3.0 验证
    print(f"\n🔍 AutoVerifier v3.0 验证中...")
    verifier = AutoVerifier()
    result = verifier.verify_statement(statement_id)
    
    if result['status'] == 'verified':
        print(f"✅ 验证通过！")
        print(f"   - 交易数量验证: ✓")
        print(f"   - 余额连续性验证: ✓")
        print(f"   - 数据完整性验证: ✓")
    else:
        print(f"❌ 验证失败!")
        if result.get('errors'):
            for error in result['errors']:
                print(f"   ❌ {error}")
        if result.get('warnings'):
            for warning in result['warnings']:
                print(f"   ⚠️  {warning}")
    
    return {
        'statement_id': statement_id,
        'month': info['statement_date'],
        'transactions': len(transactions),
        'verification': result['status']
    }

def main():
    """批量导入所有月结单"""
    print(f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                  Yeo Chee Wang GX Bank 月结单批量导入系统                        ║
║                         AutoVerifier v3.0 - 100% 准确度保证                     ║
╚═══════════════════════════════════════════════════════════════════════════════╝

客户信息:
  - 姓名: {CUSTOMER_NAME}
  - 代码: {CUSTOMER_CODE}
  - ID: {CUSTOMER_ID}
  - 银行: {BANK_NAME}

待处理月份: 2025年 1-7月 (共7个月)
""")
    
    results = []
    success_count = 0
    failed_count = 0
    
    for pdf_path in PDF_FILES:
        if not os.path.exists(pdf_path):
            print(f"❌ 文件不存在: {pdf_path}")
            failed_count += 1
            continue
        
        result = import_statement(pdf_path, CUSTOMER_ID, BANK_NAME)
        
        if result:
            results.append(result)
            if result['verification'] == 'verified':
                success_count += 1
            else:
                failed_count += 1
    
    # 生成汇总报告
    print(f"\n\n{'='*80}")
    print(f"📊 批量导入汇总报告")
    print(f"{'='*80}")
    print(f"总月份数: {len(PDF_FILES)}")
    print(f"成功验证: {success_count}")
    print(f"失败/警告: {failed_count}")
    print(f"\n详细结果:")
    print(f"{'-'*80}")
    print(f"{'月份':<15} {'交易数':<10} {'验证状态':<15}")
    print(f"{'-'*80}")
    for r in results:
        status_icon = '✅' if r['verification'] == 'verified' else '❌'
        print(f"{r['month']:<15} {r['transactions']:<10} {status_icon} {r['verification']}")
    print(f"{'-'*80}")
    
    if success_count == len(PDF_FILES):
        print(f"\n🎉 完美！所有月结单已100%准确导入并验证通过！")
    else:
        print(f"\n⚠️  部分月结单需要人工复核")

if __name__ == '__main__':
    main()
