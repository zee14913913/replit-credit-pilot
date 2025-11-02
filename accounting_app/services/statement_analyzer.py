"""
银行月结单智能分析器
自动识别CSV和PDF文件的银行、账号、月份等信息
"""
import csv
import io
import re
from datetime import datetime
from typing import Dict, Optional, List
from .bank_statement_pdf_parser import BankStatementPDFParser


def analyze_csv_content(csv_content: str) -> Dict:
    """
    分析CSV内容，自动识别银行、账号、月份
    
    返回:
    {
        "bank_name": "Maybank",
        "account_number": "3824549009",
        "statement_month": "2024-07",
        "transaction_count": 10,
        "date_range": {"start": "2024-07-01", "end": "2024-07-31"},
        "total_debit": 61629.03,
        "confidence": 0.95
    }
    """
    result = {
        "bank_name": None,
        "account_number": None,
        "statement_month": None,
        "transaction_count": 0,
        "date_range": {"start": None, "end": None},
        "total_debit": 0,
        "total_credit": 0,
        "confidence": 0,
        "analysis": []
    }
    
    try:
        # 解析CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)
        
        if not rows:
            result["analysis"].append("CSV文件为空")
            return result
        
        result["transaction_count"] = len(rows)
        
        # 分析日期范围和月份
        dates = []
        for row in rows:
            date_str = row.get('Date', '')
            if date_str:
                # 清理Excel公式格式
                date_str = _clean_excel_formula(date_str)
                # 尝试多种日期格式
                date_obj = _parse_date_flexible(date_str)
                if date_obj:
                    dates.append(date_obj)
        
        if dates:
            dates.sort()
            result["date_range"]["start"] = dates[0].strftime('%Y-%m-%d')
            result["date_range"]["end"] = dates[-1].strftime('%Y-%m-%d')
            
            # 确定月份（使用最多交易的月份）
            month_counts = {}
            for date in dates:
                month_key = date.strftime('%Y-%m')
                month_counts[month_key] = month_counts.get(month_key, 0) + 1
            
            if month_counts:
                result["statement_month"] = max(month_counts, key=month_counts.get)
                result["analysis"].append(f"识别月份: {result['statement_month']}")
        
        # 计算总金额
        for row in rows:
            try:
                # 清理Excel公式格式
                debit_str = _clean_excel_formula(row.get('Debit', '') or '')
                credit_str = _clean_excel_formula(row.get('Credit', '') or '')
                withdrawal_str = _clean_excel_formula(row.get('Withdrawal', '') or '')
                deposit_str = _clean_excel_formula(row.get('Deposit', '') or '')
                
                # 支持Debit/Credit或Withdrawal/Deposit列名
                debit = float(debit_str or withdrawal_str or 0)
                credit = float(credit_str or deposit_str or 0)
                result["total_debit"] += debit
                result["total_credit"] += credit
            except:
                pass
        
        # 识别银行名称（从描述中查找）
        bank_keywords = {
            'maybank': 'Maybank',
            'public bank': 'Public Bank',
            'cimb': 'CIMB',
            'hong leong': 'Hong Leong Bank',
            'rhb': 'RHB Bank',
            'ambank': 'AmBank',
            'uob': 'UOB',
            'ocbc': 'OCBC',
            'hsbc': 'HSBC',
            'standard chartered': 'Standard Chartered',
            'alliance': 'Alliance Bank',
            'affin': 'Affin Bank',
            'bank islam': 'Bank Islam',
            'bank rakyat': 'Bank Rakyat',
            'bsn': 'BSN'
        }
        
        # 从描述中查找银行关键词
        all_descriptions = ' '.join([row.get('Description', '').lower() for row in rows[:20]])
        
        for keyword, bank_name in bank_keywords.items():
            if keyword in all_descriptions:
                result["bank_name"] = bank_name
                result["analysis"].append(f"从交易描述识别银行: {bank_name}")
                break
        
        # 尝试从文件内容识别账号（查找连续数字）
        account_patterns = [
            r'\b\d{10,16}\b',  # 10-16位数字
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4,8}\b'  # 带分隔符的账号
        ]
        
        for row in rows[:10]:  # 只检查前10行
            desc = row.get('Description', '')
            for pattern in account_patterns:
                matches = re.findall(pattern, desc)
                if matches:
                    # 清理账号格式
                    account = re.sub(r'[-\s]', '', matches[0])
                    if len(account) >= 10:
                        result["account_number"] = account
                        result["analysis"].append(f"从描述识别账号: {account}")
                        break
            if result["account_number"]:
                break
        
        # 计算置信度
        confidence_score = 0
        if result["bank_name"]:
            confidence_score += 0.3
        if result["account_number"]:
            confidence_score += 0.3
        if result["statement_month"]:
            confidence_score += 0.2
        if result["transaction_count"] > 0:
            confidence_score += 0.2
        
        result["confidence"] = round(confidence_score, 2)
        result["analysis"].append(f"识别置信度: {result['confidence']*100:.0f}%")
        
    except Exception as e:
        result["analysis"].append(f"分析错误: {str(e)}")
    
    return result


def suggest_customer_match(analysis: Dict, db) -> Optional[Dict]:
    """
    根据分析结果建议匹配的客户
    """
    from ..models import Company
    
    suggestions = []
    
    # 查询所有公司
    companies = db.query(Company).all()
    
    for company in companies:
        score = 0
        reasons = []
        
        # 这里可以添加更复杂的匹配逻辑
        # 例如：匹配公司名称、银行账号等
        
        if score > 0:
            suggestions.append({
                "company_id": company.id,
                "company_name": company.company_name,
                "company_code": company.company_code,
                "match_score": score,
                "reasons": reasons
            })
    
    # 按匹配分数排序
    suggestions.sort(key=lambda x: x['match_score'], reverse=True)
    
    return suggestions[0] if suggestions else None


def analyze_pdf_content(pdf_path: str) -> Dict:
    """
    分析PDF银行月结单内容
    
    返回与analyze_csv_content相同的格式
    """
    parser = BankStatementPDFParser()
    pdf_result = parser.parse_bank_statement(pdf_path)
    
    if not pdf_result["success"]:
        return {
            "bank_name": None,
            "account_number": None,
            "statement_month": None,
            "transaction_count": 0,
            "date_range": {"start": None, "end": None},
            "total_debit": 0,
            "total_credit": 0,
            "confidence": 0,
            "analysis": [f"PDF解析失败: {pdf_result.get('error_message', '未知错误')}"],
            "transactions": []
        }
    
    # 转换为统一格式
    transactions = pdf_result.get("transactions", [])
    
    # 计算日期范围
    dates = [txn["date"] for txn in transactions if "date" in txn]
    date_range = {
        "start": min(dates) if dates else None,
        "end": max(dates) if dates else None
    }
    
    # 计算总金额
    total_debit = sum(txn.get("debit", 0) for txn in transactions)
    total_credit = sum(txn.get("credit", 0) for txn in transactions)
    
    return {
        "bank_name": pdf_result.get("bank_name"),
        "account_number": pdf_result.get("account_number"),
        "statement_month": pdf_result.get("statement_month"),
        "transaction_count": len(transactions),
        "date_range": date_range,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "confidence": pdf_result.get("confidence", 0),
        "analysis": [f"PDF解析成功，识别{len(transactions)}笔交易"],
        "transactions": transactions  # 传递交易数据供后续使用
    }


def _clean_excel_formula(value: str) -> str:
    """清理Excel公式格式 =""value"" """
    if not value or not isinstance(value, str):
        return value or ''
    
    # 移除Excel公式格式
    cleaned = re.sub(r'^="(.*)"$', r'\1', value.strip())
    return cleaned


def _parse_date_flexible(date_str: str) -> Optional[datetime]:
    """
    支持多种日期格式的解析
    - YYYY-MM-DD
    - DD-MM-YYYY
    - DD/MM/YYYY
    - DD MMM YYYY
    """
    if not date_str:
        return None
    
    date_formats = [
        '%Y-%m-%d',
        '%d-%m-%Y',
        '%d/%m/%Y',
        '%Y/%m/%d',
        '%d %b %Y',
        '%d %B %Y'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    
    return None
