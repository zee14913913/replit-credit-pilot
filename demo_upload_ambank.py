#!/usr/bin/env python3
"""
AmBank账单批量上传演示 - DR/CR分类验证
"""
import sys
sys.path.insert(0, '.')

from ingest.statement_parser import parse_ambank_statement
from db.database import get_db
from validate.categorizer import categorize_transaction

# 账单文件列表
STATEMENT_FILES = [
    ('attached_assets/AMB 28:05:2025_1760482064241.pdf', '2025-05-28'),
    ('attached_assets/AMB 28:06:2025_1760482064242.pdf', '2025-06-28'),
    ('attached_assets/AMB 28:07:2025_1760482064243.pdf', '2025-07-28'),
    ('attached_assets/AMB 28:08:2025_1760482064243.pdf', '2025-08-28'),
    ('attached_assets/AMB 28:09:2025_1760482064243.pdf', '2025-09-28'),
]

CARD_ID = 24
CUSTOMER_ID = 6

def upload_statement(file_path, statement_date):
    """上传单个账单"""
    print(f"\n{'='*80}")
    print(f"📄 处理: {file_path.split('/')[-1]}")
    print(f"📅 账单日期: {statement_date}")
    print(f"{'='*80}")
    
    # 解析账单
    try:
        statement_info, transactions = parse_ambank_statement(file_path)
        print(f"✅ 解析成功: {len(transactions)} 笔交易")
        print(f"   账单总额: RM {statement_info['total']:,.2f}")
        
        # 统计DR/CR
        purchase_count = sum(1 for t in transactions if t.get('type') == 'debit')
        payment_count = sum(1 for t in transactions if t.get('type') == 'credit')
        purchase_total = sum(t['amount'] for t in transactions if t.get('type') == 'debit')
        payment_total = sum(t['amount'] for t in transactions if t.get('type') == 'credit')
        
        print(f"\n   📊 DR/CR分类统计:")
        print(f"      消费(DR): {purchase_count}笔, RM {purchase_total:,.2f}")
        print(f"      付款(CR): {payment_count}笔, RM {payment_total:,.2f}")
        print(f"      净额: RM {statement_info['total']:,.2f}")
        
        # 显示部分交易示例
        print(f"\n   🔍 交易示例 (前5笔):")
        for i, trans in enumerate(transactions[:5], 1):
            trans_type = "付款CR" if trans.get('type') == 'credit' else "消费DR"
            print(f"      {i}. {trans['description'][:40]:40} RM {trans['amount']:>10,.2f} [{trans_type}]")
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 插入数据库
    with get_db() as conn:
        cursor = conn.cursor()
        
        try:
            # 插入账单
            cursor.execute('''
                INSERT INTO statements 
                (card_id, statement_date, statement_total, file_path, file_type, 
                 validation_score, is_confirmed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                CARD_ID,
                statement_date,
                statement_info['total'],
                file_path,
                'pdf',
                100.0,
                1
            ))
            statement_id = cursor.lastrowid
            
            # 插入交易
            for trans in transactions:
                category, cat_confidence = categorize_transaction(trans['description'])
                
                # DR/CR分类映射 (核心逻辑)
                trans_type = trans.get('type', None)
                if trans_type == 'debit':
                    transaction_type = 'purchase'  # 消费DR
                elif trans_type == 'credit':
                    transaction_type = 'payment'  # 付款CR
                else:
                    # Fallback逻辑
                    transaction_type = 'payment' if trans['amount'] < 0 else 'purchase'
                
                cursor.execute('''
                    INSERT INTO transactions 
                    (statement_id, transaction_date, description, amount, category, 
                     category_confidence, transaction_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    statement_id,
                    trans['date'],
                    trans['description'],
                    abs(trans['amount']),
                    category,
                    cat_confidence,
                    transaction_type
                ))
            
            conn.commit()
            print(f"   ✅ 数据已保存 (账单ID: {statement_id})")
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"   ❌ 数据库错误: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """主函数"""
    print("="*80)
    print("🎯 AmBank账单批量上传演示 - DR/CR分类验证")
    print("="*80)
    print(f"👤 客户: CHEOK JUN YOON (ID: {CUSTOMER_ID})")
    print(f"💳 卡片: AmBank *6354 (ID: {CARD_ID})")
    print(f"📦 账单数量: {len(STATEMENT_FILES)} 个 (2025年5-9月)")
    
    success_count = 0
    for file_path, statement_date in STATEMENT_FILES:
        if upload_statement(file_path, statement_date):
            success_count += 1
    
    print(f"\n{'='*80}")
    print(f"✅ 上传完成: {success_count}/{len(STATEMENT_FILES)} 成功")
    print(f"{'='*80}")
    
    if success_count == len(STATEMENT_FILES):
        print("\n🎉 所有账单上传成功！DR/CR分类已应用。")
        print("\n下一步：")
        print("  1. 运行月度账本计算:")
        print("     python scripts/calculate_monthly_ledgers.py")
        print("  2. 查看客户账本:")
        print(f"     python scripts/view_monthly_ledger.py {CUSTOMER_ID}")
    else:
        print("\n⚠️ 部分账单上传失败，请检查错误信息")

if __name__ == "__main__":
    main()
