"""
银行月结单智能分析器
自动识别CSV文件的银行、账号、月份等信息
"""
import csv
import io
import re
from datetime import datetime
from typing import Dict, Optional, List


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
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    dates.append(date_obj)
                except:
                    pass
        
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
                debit = float(row.get('Debit', 0) or 0)
                credit = float(row.get('Credit', 0) or 0)
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
