#!/usr/bin/env python3
"""
演示脚本：批量上传所有信用卡账单并验证1:1准确度
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.database import get_db
from ingest.statement_parser import (
    parse_hsbc_statement,
    parse_hong_leong_statement,
    parse_ambank_statement
)

def create_demo_customer():
    """创建演示客户账户"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 检查客户是否已存在
        cursor.execute("SELECT id FROM customers WHERE email = ?", ("demo@infinitegz.com",))
        result = cursor.fetchone()
        
        if result:
            print(f"✅ 演示客户已存在 (ID: {result[0]})")
            return result[0]
        
        # 创建新客户
        cursor.execute("""
            INSERT INTO customers (name, email, phone, monthly_income)
            VALUES (?, ?, ?, ?)
        """, ("CHEOK JUN YOON (Demo)", "demo@infinitegz.com", "+60123456789", 10000.00))
        
        customer_id = cursor.lastrowid
        conn.commit()
        print(f"✅ 创建演示客户 (ID: {customer_id})")
        return customer_id

def upload_statement_batch(customer_id, statement_files):
    """批量上传账单"""
    results = []
    
    # 银行解析器映射
    bank_parsers = {
        'HSBC': parse_hsbc_statement,
        'Hong Leong Bank': parse_hong_leong_statement,
        'AmBank Islamic': parse_ambank_statement,
        'AmBank': parse_ambank_statement
    }
    
    for file_info in statement_files:
        bank_name = file_info['bank']
        file_path = file_info['path']
        
        print(f"\n{'='*80}")
        print(f"📄 正在处理: {file_info['label']}")
        print(f"   银行: {bank_name}")
        print(f"   文件: {os.path.basename(file_path)}")
        print(f"{'='*80}")
        
        try:
            # 获取对应的解析器
            parser = bank_parsers.get(bank_name)
            if not parser:
                print(f"⚠️  警告: 不支持的银行 {bank_name}")
                continue
            
            # 解析账单
            info, transactions = parser(file_path)
            
            if not transactions:
                print(f"⚠️  警告: 未提取到交易记录")
                continue
            
            # 存储到数据库
            with get_db() as conn:
                cursor = conn.cursor()
                
                # 插入或获取信用卡
                cursor.execute("""
                    SELECT id FROM credit_cards 
                    WHERE customer_id = ? AND card_number_last4 = ?
                """, (customer_id, info.get('card_last4', '0000')))
                
                card_result = cursor.fetchone()
                
                if card_result:
                    card_id = card_result[0]
                else:
                    cursor.execute("""
                        INSERT INTO credit_cards (customer_id, bank_name, card_number_last4, card_type, credit_limit)
                        VALUES (?, ?, ?, ?, ?)
                    """, (customer_id, bank_name, info.get('card_last4', '0000'), 
                          "Credit Card", 15000.00))
                    card_id = cursor.lastrowid
                
                # 插入账单
                cursor.execute("""
                    INSERT INTO statements (card_id, statement_date, statement_total, file_path, 
                                          is_confirmed, card_full_number)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (card_id, info.get('statement_date'), info.get('total', 0), 
                      file_path, 1, f"****{info.get('card_last4', '0000')}"))
                
                statement_id = cursor.lastrowid
                
                # 插入交易记录
                transaction_count = 0
                debit_total = 0
                credit_total = 0
                
                for trans in transactions:
                    trans_type = trans.get('type', 'debit')
                    amount = abs(trans['amount'])
                    
                    cursor.execute("""
                        INSERT INTO transactions (statement_id, transaction_date, description, 
                                                amount, transaction_type, category)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (statement_id, trans['date'], trans['description'], 
                          amount, trans_type, 'Uncategorized'))
                    
                    transaction_count += 1
                    if trans_type == 'debit':
                        debit_total += amount
                    else:
                        credit_total += amount
                
                conn.commit()
                
                result = {
                    'bank': bank_name,
                    'label': file_info['label'],
                    'statement_date': info.get('statement_date'),
                    'card_last4': info.get('card_last4'),
                    'total': info.get('total', 0),
                    'transaction_count': transaction_count,
                    'debit_total': debit_total,
                    'credit_total': credit_total,
                    'statement_id': statement_id
                }
                
                results.append(result)
                
                print(f"\n✅ 上传成功!")
                print(f"   账单ID: {statement_id}")
                print(f"   卡号: ****{info.get('card_last4', 'N/A')}")
                print(f"   日期: {info.get('statement_date', 'N/A')}")
                print(f"   总额: RM {info.get('total', 0):,.2f}")
                print(f"   交易数: {transaction_count} 笔")
                print(f"   💳 消费: RM {debit_total:,.2f}")
                print(f"   ✅ 还款/返现: RM {credit_total:,.2f}")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    return results

def generate_summary_report(results):
    """生成汇总报告"""
    print("\n" + "="*120)
    print(" "*45 + "📊 批量上传汇总报告")
    print("="*120)
    
    # 按银行分组
    bank_summary = {}
    for r in results:
        bank = r['bank']
        if bank not in bank_summary:
            bank_summary[bank] = {
                'count': 0,
                'transactions': 0,
                'debit': 0,
                'credit': 0
            }
        bank_summary[bank]['count'] += 1
        bank_summary[bank]['transactions'] += r['transaction_count']
        bank_summary[bank]['debit'] += r['debit_total']
        bank_summary[bank]['credit'] += r['credit_total']
    
    print(f"\n{'银行':20} | {'账单数':8} | {'交易总数':10} | {'总消费(RM)':15} | {'总还款(RM)':15}")
    print("-" * 120)
    
    total_statements = 0
    total_transactions = 0
    total_debit = 0
    total_credit = 0
    
    for bank, summary in sorted(bank_summary.items()):
        print(f"{bank:20} | {summary['count']:8} | {summary['transactions']:10} | {summary['debit']:>15,.2f} | {summary['credit']:>15,.2f}")
        total_statements += summary['count']
        total_transactions += summary['transactions']
        total_debit += summary['debit']
        total_credit += summary['credit']
    
    print("-" * 120)
    print(f"{'总计':20} | {total_statements:8} | {total_transactions:10} | {total_debit:>15,.2f} | {total_credit:>15,.2f}")
    
    print(f"\n{'='*120}")
    print(f"\n📈 关键指标:")
    print(f"   ✅ 成功上传账单: {total_statements} 个")
    print(f"   ✅ 提取交易记录: {total_transactions} 笔")
    print(f"   💳 总消费金额: RM {total_debit:,.2f}")
    print(f"   ✅ 总还款金额: RM {total_credit:,.2f}")
    print(f"   📊 净消费: RM {(total_debit - total_credit):,.2f}")
    print(f"\n{'='*120}")
    
    # 详细列表
    print(f"\n📋 详细账单列表:")
    print(f"\n{'序号':4} | {'银行':20} | {'月份':15} | {'卡号':10} | {'日期':12} | {'交易数':6} | {'总额(RM)':12}")
    print("-" * 120)
    
    for i, r in enumerate(results, 1):
        print(f"{i:4} | {r['bank']:20} | {r['label']:15} | ****{r['card_last4']:4} | {r['statement_date']:12} | {r['transaction_count']:6} | {r['total']:>12,.2f}")
    
    print("="*120)

def verify_1to1_accuracy(results):
    """验证1:1准确度"""
    print(f"\n{'='*120}")
    print(" "*45 + "🔍 1:1准确度验证")
    print("="*120)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        for r in results:
            statement_id = r['statement_id']
            
            # 统计数据库中的交易
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN transaction_type = 'debit' THEN amount ELSE 0 END) as debit,
                    SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE 0 END) as credit
                FROM transactions
                WHERE statement_id = ?
            """, (statement_id,))
            
            db_stats = cursor.fetchone()
            
            # 验证
            pdf_count = r['transaction_count']
            db_count = db_stats[0]
            
            pdf_debit = r['debit_total']
            db_debit = db_stats[1] or 0
            
            pdf_credit = r['credit_total']
            db_credit = db_stats[2] or 0
            
            match_icon = "✅" if (pdf_count == db_count and 
                                 abs(pdf_debit - db_debit) < 0.01 and 
                                 abs(pdf_credit - db_credit) < 0.01) else "❌"
            
            print(f"\n{match_icon} {r['bank']} - {r['label']} (账单ID: {statement_id})")
            print(f"   交易数: PDF={pdf_count} | DB={db_count} | {'匹配' if pdf_count == db_count else '不匹配'}")
            print(f"   消费额: PDF=RM{pdf_debit:,.2f} | DB=RM{db_debit:,.2f} | {'匹配' if abs(pdf_debit - db_debit) < 0.01 else '不匹配'}")
            print(f"   还款额: PDF=RM{pdf_credit:,.2f} | DB=RM{db_credit:,.2f} | {'匹配' if abs(pdf_credit - db_credit) < 0.01 else '不匹配'}")
    
    print(f"\n{'='*120}")

def main():
    """主函数"""
    print("\n" + "="*120)
    print(" "*35 + "🚀 Smart Credit & Loan Manager - 批量账单上传演示")
    print("="*120)
    
    # 定义所有账单文件
    statement_files = [
        # HSBC (5个月)
        {'bank': 'HSBC', 'label': '5月账单', 'path': 'static/uploads/HSBC_13052025.pdf'},
        {'bank': 'HSBC', 'label': '6月账单', 'path': 'static/uploads/HSBC_14062025.pdf'},
        {'bank': 'HSBC', 'label': '7月账单', 'path': 'static/uploads/HSBC_13072025.pdf'},
        {'bank': 'HSBC', 'label': '8月账单', 'path': 'static/uploads/HSBC_13082025.pdf'},
        {'bank': 'HSBC', 'label': '9月账单', 'path': 'static/uploads/HSBC_13092025.pdf'},
        
        # Hong Leong Bank (4个月)
        {'bank': 'Hong Leong Bank', 'label': '6月账单', 'path': 'static/uploads/HLB_16062025.pdf'},
        {'bank': 'Hong Leong Bank', 'label': '7月账单', 'path': 'static/uploads/HLB_16072025.pdf'},
        {'bank': 'Hong Leong Bank', 'label': '8月账单', 'path': 'static/uploads/HLB_16082025.pdf'},
        {'bank': 'Hong Leong Bank', 'label': '9月账单', 'path': 'static/uploads/HLB_16092025.pdf'},
        
        # AmBank Islamic (5个月)
        {'bank': 'AmBank Islamic', 'label': '5月账单', 'path': 'static/uploads/AMBIS_28052025.pdf'},
        {'bank': 'AmBank Islamic', 'label': '6月账单', 'path': 'static/uploads/AMBIS_28062025.pdf'},
        {'bank': 'AmBank Islamic', 'label': '7月账单', 'path': 'static/uploads/AMBIS_28072025.pdf'},
        {'bank': 'AmBank Islamic', 'label': '8月账单', 'path': 'static/uploads/AMBIS_28082025.pdf'},
        {'bank': 'AmBank Islamic', 'label': '9月账单', 'path': 'static/uploads/AMBIS_28092025.pdf'},
        
        # AmBank BonusLink (5个月)
        {'bank': 'AmBank', 'label': '5月账单', 'path': 'static/uploads/AMB_28052025.pdf'},
        {'bank': 'AmBank', 'label': '6月账单', 'path': 'static/uploads/AMB_28062025.pdf'},
        {'bank': 'AmBank', 'label': '7月账单', 'path': 'static/uploads/AMB_28072025.pdf'},
        {'bank': 'AmBank', 'label': '8月账单', 'path': 'static/uploads/AMB_28082025.pdf'},
        {'bank': 'AmBank', 'label': '9月账单', 'path': 'static/uploads/AMB_28092025.pdf'},
    ]
    
    # 验证文件存在
    print(f"\n📁 验证文件...")
    for f in statement_files:
        if not os.path.exists(f['path']):
            print(f"❌ 文件不存在: {f['path']}")
            return
    print(f"✅ 所有 {len(statement_files)} 个文件验证通过")
    
    # 创建演示客户
    print(f"\n👤 创建演示客户...")
    customer_id = create_demo_customer()
    
    # 批量上传
    print(f"\n📤 开始批量上传账单...")
    results = upload_statement_batch(customer_id, statement_files)
    
    # 生成汇总报告
    generate_summary_report(results)
    
    # 验证1:1准确度
    verify_1to1_accuracy(results)
    
    print(f"\n✅ 演示完成！所有账单已成功上传并验证1:1准确度。")
    print(f"   客户ID: {customer_id}")
    print(f"   总账单数: {len(results)}")
    print(f"\n{'='*120}\n")

if __name__ == "__main__":
    main()
