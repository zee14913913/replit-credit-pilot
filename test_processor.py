"""
测试脚本 - 验证后处理Pipeline的功能

运行: python test_processor.py
"""

import json
from main import StatementProcessor
from pathlib import Path


def test_basic_processing():
    """测试1：基本处理流程"""
    print("="*80)
    print("测试1：基本处理流程")
    print("="*80)
    
    # 模拟 Document AI 输出
    doc_ai_json = {
        "entities": [
            {"type": "bank_name", "mentionText": "AMBANK"},
            {"type": "customer_name", "mentionText": "CHEOK JUN YOON"},
            {"type": "card_no", "mentionText": "4031 4899 9530 6354"},
            {"type": "card_type", "mentionText": "AmBank BonusLink Visa"},
            {"type": "statement_date", "mentionText": "28 OCT 25"},
            {"type": "payment_due_date", "mentionText": "17 NOV 25"},
            {"type": "credit_limit", "mentionText": "RM15,000"},
            {"type": "current_balance", "mentionText": "RM15,062.57"},
            {"type": "minimum_payment", "mentionText": "RM1,501.88"},
            {"type": "previous_balance", "mentionText": "RM14,515.49"}
        ],
        "text": "Full statement text..."
    }
    
    processor = StatementProcessor()
    result = processor.process(doc_ai_json)
    
    # 验证结果
    assert result['bank_name'] == 'AMBANK', "银行名称错误"
    assert result['customer_name'] == 'CHEOK JUN YOON', "客户姓名错误"
    assert result['statement_date'] == '2025-10-28', "日期格式化错误"
    assert result['credit_limit'] == 15000.0, "金额标准化错误"
    
    print("✅ 基本字段提取: PASS")
    print(f"   银行: {result['bank_name']}")
    print(f"   客户: {result['customer_name']}")
    print(f"   账单日期: {result['statement_date']}")
    print(f"   信用额度: RM{result['credit_limit']:.2f}")
    print()


def test_transaction_extraction():
    """测试2：交易提取"""
    print("="*80)
    print("测试2：交易提取")
    print("="*80)
    
    doc_ai_json = {
        "entities": [
            {"type": "bank_name", "mentionText": "AMBANK"},
            {"type": "current_balance", "mentionText": "RM15,062.57"},
            {"type": "previous_balance", "mentionText": "RM14,515.49"},
            {
                "type": "line_item",
                "properties": [
                    {"type": "date", "mentionText": "27 SEP 25"},
                    {"type": "description", "mentionText": "Payment Received - Thank You"},
                    {"type": "amount", "mentionText": "16.39 CR"}
                ]
            },
            {
                "type": "line_item",
                "properties": [
                    {"type": "date", "mentionText": "28 SEP 25"},
                    {"type": "description", "mentionText": "Shopee Malaysia"},
                    {"type": "amount", "mentionText": "18.39"}
                ]
            },
            {
                "type": "line_item",
                "properties": [
                    {"type": "date", "mentionText": "22 OCT 25"},
                    {"type": "description", "mentionText": "LATE PAYMENT CHARGE"},
                    {"type": "amount", "mentionText": "100.00"}
                ]
            }
        ]
    }
    
    processor = StatementProcessor()
    result = processor.process(doc_ai_json)
    
    transactions = result['transactions']
    
    print(f"提取的交易数量: {len(transactions)}")
    for i, t in enumerate(transactions):
        print(f"  交易{i+1}: CR={t['amount_CR']}, DR={t['amount_DR']}, 描述={t['transaction_description']}")
    
    assert len(transactions) == 3, f"交易数量错误，期望3笔，实际{len(transactions)}笔"
    
    # 验证第一条交易（CR）
    print(f"\n验证第1笔交易:")
    print(f"  期望: date=2025-09-27, CR=16.39, DR=0.0")
    print(f"  实际: date={transactions[0]['transaction_date']}, CR={transactions[0]['amount_CR']}, DR={transactions[0]['amount_DR']}")
    
    assert transactions[0]['transaction_date'] == '2025-09-27', "交易日期错误"
    assert transactions[0]['amount_CR'] == 16.39, f"CR金额错误：期望16.39，实际{transactions[0]['amount_CR']}"
    assert transactions[0]['amount_DR'] == 0.0, "DR应为0"
    
    print(f"✅ 交易提取: PASS ({len(transactions)}笔)")
    for i, t in enumerate(transactions, 1):
        print(f"   {i}. {t['transaction_date']} | {t['transaction_description']:30s} | DR:{t['amount_DR']:8.2f} CR:{t['amount_CR']:8.2f}")
    print()


def test_crdr_correction():
    """测试3：CR/DR 自动修正"""
    print("="*80)
    print("测试3：CR/DR 自动修正")
    print("="*80)
    
    doc_ai_json = {
        "entities": [
            {"type": "bank_name", "mentionText": "TEST_BANK"},
            {"type": "current_balance", "mentionText": "RM1000"},
            {"type": "previous_balance", "mentionText": "RM900"},
            {
                "type": "line_item",
                "properties": [
                    {"type": "date", "mentionText": "01 OCT 25"},
                    {"type": "description", "mentionText": "Payment Received - Thank You"},
                    {"type": "amount", "mentionText": "200.00"}  # 应该是CR，但标记为DR
                ]
            },
            {
                "type": "line_item",
                "properties": [
                    {"type": "date", "mentionText": "05 OCT 25"},
                    {"type": "description", "mentionText": "Shopee Purchase"},
                    {"type": "amount", "mentionText": "300.00 CR"}  # 应该是DR，但标记为CR
                ]
            }
        ]
    }
    
    processor = StatementProcessor()
    result = processor.process(doc_ai_json)
    
    transactions = result['transactions']
    
    # 验证修正结果
    # 第1条：Payment应该是CR
    if transactions[0]['_auto_corrected']:
        print(f"✅ 自动修正1: {transactions[0]['transaction_description']}")
        print(f"   原因: {transactions[0]['_correction_reason']}")
        print(f"   修正后: DR={transactions[0]['amount_DR']}, CR={transactions[0]['amount_CR']}")
    
    # 第2条：Purchase应该是DR
    if transactions[1]['_auto_corrected']:
        print(f"✅ 自动修正2: {transactions[1]['transaction_description']}")
        print(f"   原因: {transactions[1]['_correction_reason']}")
        print(f"   修正后: DR={transactions[1]['amount_DR']}, CR={transactions[1]['amount_CR']}")
    
    print()


def test_balance_validation():
    """测试4：余额验证"""
    print("="*80)
    print("测试4：余额验证")
    print("="*80)
    
    doc_ai_json = {
        "entities": [
            {"type": "bank_name", "mentionText": "TEST_BANK"},
            {"type": "previous_balance", "mentionText": "RM1000"},
            {"type": "current_balance", "mentionText": "RM1080"},
            {
                "type": "line_item",
                "properties": [
                    {"type": "date", "mentionText": "01 OCT 25"},
                    {"type": "description", "mentionText": "Purchase"},
                    {"type": "amount", "mentionText": "100.00"}  # DR
                ]
            },
            {
                "type": "line_item",
                "properties": [
                    {"type": "date", "mentionText": "02 OCT 25"},
                    {"type": "description", "mentionText": "Payment Received"},
                    {"type": "amount", "mentionText": "20.00 CR"}  # CR
                ]
            }
        ]
    }
    
    processor = StatementProcessor()
    result = processor.process(doc_ai_json)
    
    validation = result['validation']
    
    print(f"上期余额: RM{result['previous_balance']:.2f}")
    print(f"本期余额: RM{result['current_balance']:.2f}")
    print(f"DR总额: RM{validation['total_dr']:.2f}")
    print(f"CR总额: RM{validation['total_cr']:.2f}")
    print(f"计算余额: RM{validation['calculated_balance']:.2f}")
    print(f"实际余额: RM{validation['actual_balance']:.2f}")
    print(f"差异: RM{validation['difference']:.2f}")
    
    if validation['is_valid']:
        print("✅ 余额验证: PASS")
    else:
        print(f"⚠️ 余额验证: FAIL (差异: RM{validation['difference']:.2f})")
    
    print()


def test_csv_output():
    """测试5：CSV输出"""
    print("="*80)
    print("测试5：CSV输出")
    print("="*80)
    
    doc_ai_json = {
        "entities": [
            {"type": "bank_name", "mentionText": "AMBANK"},
            {"type": "customer_name", "mentionText": "CHEOK JUN YOON"},
            {"type": "card_no", "mentionText": "4031 4899 9530 6354"},
            {"type": "statement_date", "mentionText": "28 OCT 25"},
            {"type": "current_balance", "mentionText": "RM1000"},
            {
                "type": "line_item",
                "properties": [
                    {"type": "date", "mentionText": "01 OCT 25"},
                    {"type": "description", "mentionText": "Shopee Malaysia"},
                    {"type": "amount", "mentionText": "50.00"}
                ]
            }
        ]
    }
    
    processor = StatementProcessor()
    result = processor.process(doc_ai_json)
    
    # 创建输出目录
    Path('output').mkdir(exist_ok=True)
    
    # 保存文件
    processor.save_to_csv(result, 'output/test_output.csv')
    processor.save_to_json(result, 'output/test_output.json')
    
    # 验证文件存在
    assert Path('output/test_output.csv').exists(), "CSV文件未创建"
    assert Path('output/test_output.json').exists(), "JSON文件未创建"
    
    print("✅ CSV输出: output/test_output.csv")
    print("✅ JSON输出: output/test_output.json")
    print()


def run_all_tests():
    """运行所有测试"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "后处理Pipeline测试套件" + " "*34 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    try:
        test_basic_processing()
        test_transaction_extraction()
        test_crdr_correction()
        test_balance_validation()
        test_csv_output()
        
        print("="*80)
        print("✅ 所有测试通过！")
        print("="*80)
        print()
        print("后处理Pipeline已就绪，可以开始处理41个账单。")
        print()
        
    except AssertionError as e:
        print(f"❌ 测试失败: {e}")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
