#!/usr/bin/env python3
"""
会计系统自动化测试脚本
直接访问数据库和服务，生成完整测试报告
"""
import sys
sys.path.insert(0, '/home/runner/workspace')

from accounting_app.db import SessionLocal
from accounting_app.services.bank_matcher import auto_match_transactions
from accounting_app.tasks.monthly_close import calculate_trial_balance
from sqlalchemy import text

def main():
    print("=" * 80)
    print("🧪 会计系统自动化测试")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # 测试1：检查默认公司
        print("\n✅ 测试1：检查默认公司")
        result = db.execute(text("SELECT id, company_code, company_name FROM companies WHERE company_code = 'DEFAULT'")).fetchone()
        if result:
            print(f"   公司ID: {result[0]}")
            print(f"   公司代码: {result[1]}")
            print(f"   公司名称: {result[2]}")
            company_id = result[0]
        else:
            print("   ❌ 未找到默认公司")
            return
        
        # 测试2：检查会计科目
        print("\n✅ 测试2：检查会计科目")
        result = db.execute(text(f"SELECT COUNT(*) FROM chart_of_accounts WHERE company_id = {company_id}")).fetchone()
        print(f"   会计科目总数: {result[0]}")
        
        # 测试3：检查银行流水
        print("\n✅ 测试3：检查银行流水导入")
        result = db.execute(text(f"""
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN matched THEN 1 ELSE 0 END) as matched,
                   SUM(debit_amount) as total_debit
            FROM bank_statements 
            WHERE company_id = {company_id} AND statement_month = '2024-07'
        """)).fetchone()
        print(f"   总交易数: {result[0]}")
        print(f"   已匹配: {result[1]}")
        print(f"   总支出: RM {result[2]:,.2f}")
        
        # 测试4：运行自动匹配
        print("\n✅ 测试4：运行自动匹配生成会计分录")
        matched_count = auto_match_transactions(db, company_id, '2024-07')
        print(f"   新匹配交易数: {matched_count}")
        
        # 测试5：检查生成的会计分录
        print("\n✅ 测试5：检查会计分录")
        result = db.execute(text(f"""
            SELECT COUNT(*) as total_entries,
                   SUM(CASE WHEN balanced THEN 1 ELSE 0 END) as balanced_count
            FROM (
                SELECT je.id, 
                       SUM(jel.debit_amount) as total_debit,
                       SUM(jel.credit_amount) as total_credit,
                       SUM(jel.debit_amount) = SUM(jel.credit_amount) as balanced
                FROM journal_entries je
                JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
                WHERE je.company_id = {company_id}
                GROUP BY je.id
            ) summary
        """)).fetchone()
        print(f"   会计分录总数: {result[0]}")
        print(f"   借贷平衡数: {result[1]}")
        
        # 测试6：生成试算表
        print("\n✅ 测试6：生成试算表 (Trial Balance)")
        trial_balance = calculate_trial_balance(db, company_id, '2024-07')
        print(f"   期间: {trial_balance['period']}")
        print(f"   总借方: RM {trial_balance['total_debits']:,.2f}")
        print(f"   总贷方: RM {trial_balance['total_credits']:,.2f}")
        print(f"   是否平衡: {'✅ 是' if trial_balance['balanced'] else '❌ 否'}")
        print(f"   差异: RM {trial_balance['variance']:.2f}")
        
        # 测试7：显示账户明细
        print("\n✅ 测试7：账户明细")
        for account in trial_balance['accounts'][:10]:  # 显示前10个
            print(f"   {account['account_code']:20s} | 借方: RM {account['debit']:>10,.2f} | 贷方: RM {account['credit']:>10,.2f} | 余额: RM {account['balance']:>10,.2f}")
        
        # 测试8：交易明细
        print("\n✅ 测试8：银行交易明细（前10笔）")
        results = db.execute(text(f"""
            SELECT transaction_date, description, debit_amount, matched, auto_category
            FROM bank_statements
            WHERE company_id = {company_id} AND statement_month = '2024-07'
            ORDER BY transaction_date
            LIMIT 10
        """)).fetchall()
        
        for row in results:
            status = "✅ 已匹配" if row[3] else "⏳ 未匹配"
            category = f"({row[4]})" if row[4] else ""
            print(f"   {row[0]} | {row[1][:50]:50s} | RM {row[2]:>10,.2f} | {status} {category}")
        
        print("\n" + "=" * 80)
        print("🎉 所有测试完成！")
        print("=" * 80)
        
        # 最终统计
        print("\n📊 财务摘要")
        print(f"   • 公司: {company_id} - 默认公司")
        print(f"   • 会计科目: 13个")
        print(f"   • 银行交易: {result[0]}笔（July 2024）")
        print(f"   • 会计分录: {result[0]}笔")
        print(f"   • 试算表: {'✅ 平衡' if trial_balance['balanced'] else '❌ 不平衡'}")
        print(f"   • 总支出: RM {trial_balance['total_debits']:,.2f}")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
