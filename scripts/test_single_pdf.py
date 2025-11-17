#!/usr/bin/env python3
"""
单个PDF测试脚本
用于测试Document AI提取和业务计算逻辑
"""
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.google_document_ai_service import GoogleDocumentAIService
from scripts.calculate_balances import BalanceCalculator


def test_single_pdf(pdf_path: str):
    """
    测试单个PDF文件
    
    Args:
        pdf_path: PDF文件路径
    """
    print("="*80)
    print("单个PDF测试")
    print("="*80)
    
    pdf_file = Path(pdf_path)
    
    if not pdf_file.exists():
        print(f"❌ 文件不存在: {pdf_path}")
        return
    
    print(f"\n📄 测试文件: {pdf_file.name}")
    print(f"   路径: {pdf_file}")
    print(f"   大小: {pdf_file.stat().st_size / 1024:.2f} KB")
    
    # 1. 初始化服务
    print("\n🔧 初始化服务...")
    doc_ai_service = GoogleDocumentAIService()
    calculator = BalanceCalculator()
    
    # 2. 提取数据
    print("\n📤 使用Document AI提取数据...")
    try:
        raw_result = doc_ai_service.parse_pdf(str(pdf_file))
        
        if not raw_result:
            print("❌ Document AI返回空结果")
            return
        
        print("✅ Document AI提取成功")
        
    except Exception as e:
        print(f"❌ Document AI提取失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. 提取结构化字段
    print("\n🔍 提取结构化字段...")
    fields = doc_ai_service.extract_bank_statement_fields(raw_result)
    
    print("\n基本信息:")
    print(f"   银行: {fields.get('bank_name', 'N/A')}")
    print(f"   卡号: {fields.get('card_number', 'N/A')}")
    print(f"   账单日期: {fields.get('statement_date', 'N/A')}")
    print(f"   到期日: {fields.get('due_date', 'N/A')}")
    print(f"   持卡人: {fields.get('cardholder_name', 'N/A')}")
    
    print("\n金额信息:")
    print(f"   总金额: RM {fields.get('total_amount', 0):.2f}")
    print(f"   最低还款: RM {fields.get('minimum_payment', 0):.2f}")
    print(f"   上期余额: RM {fields.get('previous_balance', 0):.2f}")
    print(f"   本期消费: RM {fields.get('new_charges', 0):.2f}")
    print(f"   本期还款: RM {fields.get('payments_credits', 0):.2f}")
    
    transactions = fields.get('transactions', [])
    print(f"\n交易记录: {len(transactions)} 笔")
    
    if transactions:
        print("\n前5笔交易:")
        for i, txn in enumerate(transactions[:5], 1):
            credit_mark = " CR" if txn.get('is_credit', False) else ""
            print(f"   {i}. {txn.get('transaction_date', 'N/A'):8s} "
                  f"{txn.get('description', 'N/A')[:40]:40s} "
                  f"RM {txn.get('amount', 0):8.2f}{credit_mark}")
        
        if len(transactions) > 5:
            print(f"   ... 还有 {len(transactions) - 5} 笔交易")
    
    # 4. 交易分类
    print("\n🏷️  交易分类...")
    categorized = calculator.categorize_transactions(transactions)
    
    print("\n分类结果:")
    for category, txns in categorized.items():
        if txns:
            print(f"\n   {category} ({len(txns)} 笔):")
            for txn in txns[:3]:
                fee_info = f" (Fee: RM {txn.get('supplier_fee', 0):.2f})" if 'supplier_fee' in txn else ""
                print(f"      - {txn.get('description', 'N/A')[:40]}: RM {txn.get('amount', 0):.2f}{fee_info}")
            if len(txns) > 3:
                print(f"      ... 还有 {len(txns) - 3} 笔")
    
    # 5. 计算总额
    print("\n💰 计算各分类总额...")
    totals = calculator.calculate_totals(categorized)
    
    print("\n总额统计:")
    for category, total in totals.items():
        print(f"   {category:25s}: RM {total:10.2f}")
    
    # 6. 计算余额
    print("\n📊 计算Outstanding Balance...")
    previous_balance = fields.get('previous_balance', 0) or 0
    balances = calculator.calculate_outstanding_balance(previous_balance, categorized, totals)
    
    print("\n余额详情:")
    print(f"   上期余额:              RM {balances['previous_balance']:10.2f}")
    print(f"   本期消费总额:          RM {balances['total_expenses']:10.2f}")
    print(f"   本期还款总额:          RM {balances['total_payments']:10.2f}")
    print(f"   Outstanding Balance:   RM {balances['outstanding_balance']:10.2f}")
    
    print("\n分项余额:")
    print(f"   Owners Balance:        RM {balances['owners_balance']:10.2f}")
    print(f"   GZ Balance:            RM {balances['gz_balance']:10.2f}")
    print(f"   Suppliers Balance:     RM {balances['suppliers_balance']:10.2f}")
    
    # 7. 验证
    bank_total = fields.get('total_amount', 0) or 0
    if bank_total > 0:
        is_match, difference = calculator.verify_balance(
            balances['outstanding_balance'], 
            bank_total
        )
        
        print("\n✅ 余额验证:")
        print(f"   计算余额: RM {balances['outstanding_balance']:.2f}")
        print(f"   银行余额: RM {bank_total:.2f}")
        print(f"   差异:     RM {difference:.2f}")
        
        if is_match:
            print("   ✅ 匹配成功！")
        else:
            print("   ⚠️  存在差异，需要人工检查")
    
    # 8. 生成JSON输出
    output_file = Path("reports/test_result.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        'file_name': pdf_file.name,
        'fields': fields,
        'categorized_transactions': {
            k: [{
                'description': t.get('description', ''),
                'amount': t.get('amount', 0),
                'is_credit': t.get('is_credit', False),
                'supplier_fee': t.get('supplier_fee', 0)
            } for t in v]
            for k, v in categorized.items()
        },
        'totals': totals,
        'balances': balances
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 详细结果已保存到: {output_file}")
    
    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


def main():
    """主函数"""
    # 查找第一个PDF文件进行测试
    base_path = Path("static/uploads/customers/Be_rich_CJY/credit_cards")
    
    if not base_path.exists():
        print(f"❌ 客户文件夹不存在: {base_path}")
        return
    
    # 查找第一个PDF
    pdf_files = list(base_path.rglob("*.pdf"))
    
    if not pdf_files:
        print("❌ 未找到PDF文件")
        return
    
    # 测试第一个文件
    test_pdf = pdf_files[0]
    
    print(f"\n找到 {len(pdf_files)} 个PDF文件")
    print(f"使用第一个文件进行测试: {test_pdf.name}\n")
    
    test_single_pdf(str(test_pdf))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # 指定PDF文件
        test_single_pdf(sys.argv[1])
    else:
        # 自动查找第一个PDF
        main()
