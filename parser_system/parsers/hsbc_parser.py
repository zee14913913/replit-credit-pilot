#!/usr/bin/env python3
"""
HSBC信用卡账单解析器
支持标准文本PDF格式
"""
import pdfplumber
import re
from datetime import datetime
from typing import List, Dict, Optional

class HSBCParser:
    """HSBC信用卡账单解析器"""
    
    def __init__(self):
        self.bank_name = "HSBC"
    
    def parse_statement(self, pdf_path: str) -> Dict:
        """解析HSBC PDF账单"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # 提取所有页面的文本
                all_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
                
                # 解析账单信息
                result = {
                    'bank_name': 'HSBC',
                    'card_number': self._extract_card_number(all_text),
                    'statement_date': self._extract_statement_date(all_text),
                    'statement_total': self._extract_statement_total(all_text),
                    'transactions': self._extract_transactions(all_text),
                    'raw_text': all_text
                }
                
                return result
                
        except Exception as e:
            raise Exception(f"HSBC解析失败: {str(e)}")
    
    def _extract_card_number(self, text: str) -> str:
        """提取卡号"""
        # 格式: 4386 7590 0475 2058
        match = re.search(r'(\d{4}\s+\d{4}\s+\d{4}\s+\d{4})', text)
        if match:
            return match.group(1).replace(' ', '')
        return None
    
    def _extract_statement_date(self, text: str) -> str:
        """提取账单日期"""
        # 格式: Statement Date    10 Jun 2025
        patterns = [
            r'Statement\s+Date\s+(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
            r'Statement Date\s+(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # 转换为YYYY-MM-DD格式
                try:
                    dt = datetime.strptime(date_str, '%d %b %Y')
                    return dt.strftime('%Y-%m-%d')
                except:
                    pass
        
        return None
    
    def _extract_statement_total(self, text: str) -> float:
        """提取账单总额（滚动余额）"""
        # 格式: Your statement balance   12,814.60
        match = re.search(r'Your statement balance\s+([\d,]+\.\d{2})', text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            return float(amount_str)
        
        # 备选格式: Statement Balance (RM)
        match = re.search(r'Statement\s+Balance\s*\(RM\)\s+([\d,]+\.\d{2})', text)
        if match:
            amount_str = match.group(1).replace(',', '')
            return float(amount_str)
        
        return 0.0
    
    def _extract_transactions(self, text: str) -> List[Dict]:
        """提取交易记录"""
        transactions = []
        
        # HSBC交易格式: 
        # Post date  Transaction date    Transaction details    Amount (RM)
        # 03 JUN     03 JUN              PAYMENT - THANK YOU    1,700.00 CR
        # 13 MAY     1 2 MAY             HUAWEI - I-CITY SHAH ALAM MY   10,001.00
        
        # 分行处理
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # 查找交易行（包含日期格式）
            # 灵活匹配日期格式（处理空格分隔问题）
            # 格式1: 03 JUN    03 JUN    描述    金额
            # 格式2: 13 MAY    1 2 MAY   描述    金额 (日期被空格分开)
            match = re.match(r'^\s*(\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC))\s+(\d{1,2}\s*\d*\s*(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC))?\s+(.+?)\s+([\d,]+\.\d{2})\s*(CR)?$', line, re.IGNORECASE)
            
            if match:
                post_date = match.group(1).strip()
                txn_date = match.group(2).strip() if match.group(2) else post_date
                description = match.group(3).strip()
                amount_str = match.group(4).replace(',', '')
                is_credit = match.group(5) == 'CR'
                
                # 清理描述
                description = re.sub(r'\s+', ' ', description).strip()
                
                # 跳过一些非交易行
                if len(description) < 3:
                    continue
                if description.upper() in ['PAYMENT DUE DATE', 'STATEMENT DATE', 'YOUR CREDIT LIMIT']:
                    continue
                
                try:
                    amount = float(amount_str)
                    
                    # 判断交易类型
                    if is_credit or 'PAYMENT' in description.upper() or 'THANK YOU' in description.upper():
                        txn_type = 'payment'
                    else:
                        txn_type = 'purchase'
                    
                    transactions.append({
                        'date': txn_date,
                        'description': description,
                        'amount': amount,
                        'type': txn_type
                    })
                except ValueError:
                    continue
        
        return transactions

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        parser = HSBCParser()
        result = parser.parse_statement(pdf_path)
        
        print(f"\n银行: {result['bank_name']}")
        print(f"卡号: {result['card_number']}")
        print(f"账单日期: {result['statement_date']}")
        print(f"账单总额: RM {result['statement_total']:,.2f}")
        print(f"\n交易数: {len(result['transactions'])}")
        
        for txn in result['transactions'][:20]:
            print(f"  {txn['date']:<10} {txn['description'][:50]:<50} RM {txn['amount']:>10,.2f} ({txn['type']})")
    else:
        print("用法: python hsbc_parser.py <pdf文件路径>")
