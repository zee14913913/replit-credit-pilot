#!/usr/bin/env python3
"""
HSBC OCR Parser - 处理扫描PDF格式的HSBC信用卡账单
使用PyMuPDF + Tesseract OCR
"""
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re
from datetime import datetime
from typing import List, Dict, Optional

class HSBCOCRParser:
    """HSBC扫描PDF账单OCR解析器"""
    
    def __init__(self):
        self.bank_name = "HSBC"
    
    def parse_statement(self, pdf_path: str) -> Dict:
        """解析HSBC扫描PDF账单"""
        try:
            doc = fitz.open(pdf_path)
            
            # 提取所有页面的文本
            all_text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                text = pytesseract.image_to_string(image, lang='eng')
                all_text += text + "\n"
            
            doc.close()
            
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
            raise Exception(f"HSBC OCR解析失败: {str(e)}")
    
    def _extract_card_number(self, text: str) -> str:
        """提取卡号"""
        # 格式: 4386 7590 0475 2058
        patterns = [
            r'(\d{4}\s+\d{4}\s+\d{4}\s+\d{4})',
            r'Card\s+Number[:\s]+(\d{4}\s+\d{4}\s+\d{4}\s+\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).replace(' ', '')
        
        return None
    
    def _extract_statement_date(self, text: str) -> str:
        """提取账单日期"""
        # 格式: 10 Jun 2025 或 Statement Date 10 Jun 2025
        patterns = [
            r'Statement\s+Date\s+(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})'
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
        """提取账单总额"""
        # 格式: Statement Balance (RM) 12,814.60
        patterns = [
            r'Statement\s+Balance\s*\(RM\)\s+([\d,]+\.\d{2})',
            r'Balance\s*\(RM\)\s+([\d,]+\.\d{2})',
            r'Total\s+Amount\s+Due\s*\(RM\)\s+([\d,]+\.\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                return float(amount_str)
        
        return 0.0
    
    def _extract_transactions(self, text: str) -> List[Dict]:
        """提取交易记录"""
        transactions = []
        
        # HSBC交易格式: DD Mon DESCRIPTION AMOUNT
        # 例如: 15 May AI SMART TECH SDN 4,299.00
        pattern = r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))\s+([A-Z][A-Za-z\s&\.\-]+?)\s+([\d,]+\.\d{2})'
        
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        for match in matches:
            date_str = match[0].strip()
            description = match[1].strip()
            amount_str = match[2].replace(',', '')
            
            # 清理描述（移除多余空格）
            description = re.sub(r'\s+', ' ', description).strip()
            
            # 跳过一些非交易行
            if len(description) < 3:
                continue
            if description.upper() in ['PAYMENT', 'BALANCE', 'TOTAL', 'AMOUNT']:
                continue
            
            try:
                amount = float(amount_str)
                
                # 判断交易类型（HSBC付款通常有PAYMENT关键字）
                txn_type = 'payment' if 'PAYMENT' in description.upper() or 'PAY' in description.upper() else 'purchase'
                
                transactions.append({
                    'date': date_str,
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
        parser = HSBCOCRParser()
        result = parser.parse_statement(pdf_path)
        
        print(f"\n银行: {result['bank_name']}")
        print(f"卡号: {result['card_number']}")
        print(f"账单日期: {result['statement_date']}")
        print(f"账单总额: RM {result['statement_total']:,.2f}")
        print(f"\n交易数: {len(result['transactions'])}")
        
        for txn in result['transactions'][:10]:
            print(f"  {txn['date']} {txn['description'][:40]:<40} RM {txn['amount']:>10,.2f} ({txn['type']})")
    else:
        print("用法: python hsbc_ocr_parser.py <pdf文件路径>")
