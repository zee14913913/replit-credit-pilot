"""
Transaction Validator - 交易验证器
双重验证机制确保数据准确性：
1. 数量验证：检查提取的交易笔数
2. 金额验证：与PDF声明的总额交叉核对
3. 完整性验证：确保无遗漏、无重复
"""

import re
from typing import List, Dict, Tuple

class ValidationResult:
    def __init__(self):
        self.is_valid = True
        self.confidence_score = 100.0
        self.errors = []
        self.warnings = []
        self.details = {}
    
    def add_error(self, message):
        self.errors.append(message)
        self.is_valid = False
        self.confidence_score -= 20
    
    def add_warning(self, message):
        self.warnings.append(message)
        self.confidence_score -= 5
    
    def get_status(self):
        if self.is_valid and self.confidence_score >= 95:
            return "PASSED"
        elif self.is_valid and self.confidence_score >= 80:
            return "WARNING"
        else:
            return "FAILED"

def extract_totals_from_pdf(pdf_text: str) -> Dict[str, float]:
    """从PDF文本中提取官方声明的总额"""
    totals = {
        'total_debit': None,
        'total_credit': None,
        'current_balance': None,
        'previous_balance': None
    }
    
    # 提取 TOTAL DEBIT THIS MONTH
    debit_match = re.search(r'TOTAL DEBIT THIS MONTH.*?([\d,]+\.\d{2})', pdf_text, re.IGNORECASE)
    if debit_match:
        totals['total_debit'] = float(debit_match.group(1).replace(',', ''))
    
    # 提取 TOTAL CREDIT THIS MONTH
    credit_match = re.search(r'TOTAL CREDIT THIS MONTH.*?([\d,]+\.\d{2})', pdf_text, re.IGNORECASE)
    if credit_match:
        totals['total_credit'] = float(credit_match.group(1).replace(',', ''))
    
    # 提取 Current Balance
    balance_match = re.search(r'Current Balance.*?([\d,]+\.\d{2})', pdf_text, re.IGNORECASE)
    if balance_match:
        totals['current_balance'] = float(balance_match.group(1).replace(',', ''))
    
    # 提取 Previous Balance
    prev_match = re.search(r'(?:PREVIOUS STATEMENT BALANCE|YOUR PREVIOUS).*?([\d,]+\.\d{2})', pdf_text, re.IGNORECASE)
    if prev_match:
        totals['previous_balance'] = float(prev_match.group(1).replace(',', ''))
    
    return totals

def validate_transactions(transactions: List[Dict], pdf_text: str) -> ValidationResult:
    """
    双重验证交易数据
    
    验证步骤：
    1. 提取PDF声明的官方总额
    2. 计算解析器提取的交易总额
    3. 交叉对比，确保一致
    4. 生成详细验证报告
    """
    result = ValidationResult()
    
    # Step 1: 从PDF提取官方总额
    pdf_totals = extract_totals_from_pdf(pdf_text)
    result.details['pdf_declared_totals'] = pdf_totals
    
    # Step 2: 计算解析器提取的总额
    expenses = [t for t in transactions if t.get('amount', 0) > 0]
    credits = [t for t in transactions if t.get('amount', 0) < 0]
    
    extracted_debit = sum(t['amount'] for t in expenses)
    extracted_credit = sum(abs(t['amount']) for t in credits)
    
    result.details['extracted_totals'] = {
        'total_debit': extracted_debit,
        'total_credit': extracted_credit,
        'debit_count': len(expenses),
        'credit_count': len(credits),
        'total_count': len(transactions)
    }
    
    # Step 3: 交叉验证
    tolerance = 0.01  # 允许0.01的浮点误差
    
    # 验证消费总额
    if pdf_totals['total_debit'] is not None:
        diff = abs(extracted_debit - pdf_totals['total_debit'])
        if diff > tolerance:
            result.add_error(
                f"消费总额不匹配！PDF声明: RM {pdf_totals['total_debit']:,.2f}, "
                f"提取结果: RM {extracted_debit:,.2f}, 差异: RM {diff:,.2f}"
            )
        else:
            result.details['debit_verified'] = True
    else:
        result.add_warning("PDF中未找到消费总额声明，无法验证")
    
    # 验证付款/退款总额
    if pdf_totals['total_credit'] is not None:
        diff = abs(extracted_credit - pdf_totals['total_credit'])
        if diff > tolerance:
            result.add_error(
                f"付款/退款总额不匹配！PDF声明: RM {pdf_totals['total_credit']:,.2f}, "
                f"提取结果: RM {extracted_credit:,.2f}, 差异: RM {diff:,.2f}"
            )
        else:
            result.details['credit_verified'] = True
    else:
        result.add_warning("PDF中未找到付款/退款总额声明，无法验证")
    
    # Step 4: 完整性检查
    if len(transactions) == 0:
        result.add_error("未提取到任何交易记录！")
    
    # 检查重复交易
    seen = set()
    duplicates = []
    for t in transactions:
        key = (t.get('date'), t.get('description'), t.get('amount'))
        if key in seen:
            duplicates.append(key)
        seen.add(key)
    
    if duplicates:
        result.add_error(f"发现 {len(duplicates)} 笔重复交易")
        result.details['duplicates'] = duplicates
    
    # 计算最终置信度
    result.confidence_score = max(0, min(100, result.confidence_score))
    
    return result

def generate_validation_report(result: ValidationResult) -> str:
    """生成人类可读的验证报告"""
    
    status_icon = {
        "PASSED": "✅",
        "WARNING": "⚠️",
        "FAILED": "❌"
    }
    
    status = result.get_status()
    icon = status_icon.get(status, "❓")
    
    report = f"\n{'='*80}\n"
    report += f"{icon} 交易验证报告 - 状态: {status}\n"
    report += f"{'='*80}\n\n"
    
    report += f"📊 置信度评分: {result.confidence_score:.1f}/100\n\n"
    
    # PDF声明的总额
    if 'pdf_declared_totals' in result.details:
        pdf_totals = result.details['pdf_declared_totals']
        report += "【PDF官方声明】\n"
        report += "-"*80 + "\n"
        if pdf_totals['total_debit']:
            report += f"  消费总额 (TOTAL DEBIT):     RM {pdf_totals['total_debit']:>12,.2f}\n"
        if pdf_totals['total_credit']:
            report += f"  付款/退款 (TOTAL CREDIT):    RM {pdf_totals['total_credit']:>12,.2f}\n"
        if pdf_totals['current_balance']:
            report += f"  账单余额 (Current Balance): RM {pdf_totals['current_balance']:>12,.2f}\n"
        if pdf_totals['previous_balance']:
            report += f"  上期余额 (Previous Balance): RM {pdf_totals['previous_balance']:>12,.2f}\n"
        report += "\n"
    
    # 提取的总额
    if 'extracted_totals' in result.details:
        ext_totals = result.details['extracted_totals']
        report += "【解析器提取结果】\n"
        report += "-"*80 + "\n"
        report += f"  消费总额:     RM {ext_totals['total_debit']:>12,.2f} ({ext_totals['debit_count']} 笔)\n"
        report += f"  付款/退款:     RM {ext_totals['total_credit']:>12,.2f} ({ext_totals['credit_count']} 笔)\n"
        report += f"  总交易数:     {ext_totals['total_count']} 笔\n"
        report += "\n"
    
    # 验证结果
    report += "【验证结果】\n"
    report += "-"*80 + "\n"
    
    if result.details.get('debit_verified'):
        report += "  ✅ 消费总额验证通过\n"
    if result.details.get('credit_verified'):
        report += "  ✅ 付款/退款总额验证通过\n"
    
    # 错误信息
    if result.errors:
        report += "\n❌ 错误 ({}):\n".format(len(result.errors))
        for i, error in enumerate(result.errors, 1):
            report += f"  {i}. {error}\n"
    
    # 警告信息
    if result.warnings:
        report += "\n⚠️  警告 ({}):\n".format(len(result.warnings))
        for i, warning in enumerate(result.warnings, 1):
            report += f"  {i}. {warning}\n"
    
    # 建议
    report += "\n【处理建议】\n"
    report += "-"*80 + "\n"
    if status == "PASSED":
        report += "  ✅ 数据验证通过，可以安全入库\n"
    elif status == "WARNING":
        report += "  ⚠️  建议人工复核后再入库\n"
    else:
        report += "  ❌ 数据验证失败，必须人工审核\n"
        report += "  📋 请检查上述错误，确认PDF是否正确解析\n"
    
    report += "\n" + "="*80 + "\n"
    
    return report
