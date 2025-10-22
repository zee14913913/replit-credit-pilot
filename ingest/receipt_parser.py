"""
Receipt OCR Parser
用于识别商家刷卡收据和信用卡还款收据
"""

import re
from PIL import Image
import pytesseract
from datetime import datetime
from typing import Dict, Optional, Tuple

class ReceiptParser:
    
    def __init__(self):
        self.date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',
            r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b'
        ]
        
        self.amount_patterns = [
            r'(?:RM|MYR)\s*([\d,]+\.?\d{0,2})',
            r'(?:Total|Amount|TOTAL|AMOUNT)[:\s]*([\d,]+\.?\d{0,2})',
            r'\b([\d,]+\.\d{2})\b'
        ]
        
        self.card_patterns = [
            r'\*+(\d{4})',
            r'[Xx]{4,}\s*(\d{4})',
            r'Card\s*(?:No|Number)?[:\s]*\*+(\d{4})',
            r'(\d{4})\s*$'
        ]
    
    def parse_image(self, image_path: str, receipt_type: str = 'merchant_swipe') -> Dict:
        """
        解析收据图片
        
        Args:
            image_path: 图片路径
            receipt_type: 'merchant_swipe' 或 'payment'
        
        Returns:
            dict: {
                'success': bool,
                'ocr_text': str,
                'card_last4': str,
                'transaction_date': str,
                'amount': float,
                'merchant_name': str,
                'confidence': float
            }
        """
        result = {
            'success': False,
            'ocr_text': '',
            'card_last4': None,
            'transaction_date': None,
            'amount': None,
            'merchant_name': None,
            'confidence': 0.0
        }
        
        try:
            # 打开图片
            image = Image.open(image_path)
            
            # 执行OCR
            ocr_text = pytesseract.image_to_string(image)
            result['ocr_text'] = ocr_text
            
            if not ocr_text.strip():
                return result
            
            # 提取卡号后4位
            card_last4 = self._extract_card_last4(ocr_text)
            if card_last4:
                result['card_last4'] = card_last4
                result['confidence'] += 0.3
            
            # 提取日期
            transaction_date = self._extract_date(ocr_text)
            if transaction_date:
                result['transaction_date'] = transaction_date
                result['confidence'] += 0.3
            
            # 提取金额
            amount = self._extract_amount(ocr_text)
            if amount:
                result['amount'] = amount
                result['confidence'] += 0.3
            
            # 提取商家名称（仅限merchant_swipe类型）
            if receipt_type == 'merchant_swipe':
                merchant_name = self._extract_merchant_name(ocr_text)
                if merchant_name:
                    result['merchant_name'] = merchant_name
                    result['confidence'] += 0.1
            
            # 如果至少提取到2个关键信息，认为解析成功
            if result['confidence'] >= 0.5:
                result['success'] = True
            
            return result
            
        except Exception as e:
            print(f"❌ 解析收据失败: {e}")
            return result
    
    def _extract_card_last4(self, text: str) -> Optional[str]:
        """提取卡号后4位"""
        for pattern in self.card_patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                digits = match.group(1)
                if digits and len(digits) == 4 and digits.isdigit():
                    return digits
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """提取交易日期"""
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                
                # 尝试解析日期
                parsed_date = self._parse_date_string(date_str)
                if parsed_date:
                    return parsed_date.strftime('%Y-%m-%d')
        
        return None
    
    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        date_formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d',
            '%d/%m/%y', '%d-%m-%y', '%y/%m/%d', '%y-%m-%d',
            '%d %b %Y', '%d %B %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """提取金额"""
        amounts = []
        
        for pattern in self.amount_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = float(amount_str)
                    if 0 < amount < 1000000:  # 合理的金额范围
                        amounts.append(amount)
                except ValueError:
                    continue
        
        # 返回最大的金额（通常是总额）
        return max(amounts) if amounts else None
    
    def _extract_merchant_name(self, text: str) -> Optional[str]:
        """提取商家名称（通常在收据顶部）"""
        lines = text.strip().split('\n')
        
        # 取前5行中最长的一行作为商家名
        top_lines = [line.strip() for line in lines[:5] if line.strip()]
        
        if not top_lines:
            return None
        
        # 过滤掉纯数字和太短的行
        valid_lines = [
            line for line in top_lines 
            if len(line) > 5 and not line.replace(' ', '').isdigit()
        ]
        
        if valid_lines:
            # 返回最长的一行
            merchant_name = max(valid_lines, key=len)
            # 限制长度
            return merchant_name[:100]
        
        return None
    
    def batch_parse(self, image_paths: list) -> list:
        """批量解析收据"""
        results = []
        
        for i, image_path in enumerate(image_paths):
            print(f"解析 {i+1}/{len(image_paths)}: {image_path}")
            result = self.parse_image(image_path)
            results.append({
                'file_path': image_path,
                'parse_result': result
            })
        
        return results


# 便捷函数
def parse_receipt(image_path: str, receipt_type: str = 'merchant_swipe') -> Dict:
    """解析单个收据"""
    parser = ReceiptParser()
    return parser.parse_image(image_path, receipt_type)


def parse_receipts_batch(image_paths: list) -> list:
    """批量解析收据"""
    parser = ReceiptParser()
    return parser.batch_parse(image_paths)


# 测试代码
if __name__ == "__main__":
    parser = ReceiptParser()
    
    # 测试文本
    test_text = """
    MERCHANT ABC SDN BHD
    123 Main Street, KL
    
    Date: 15/10/2024
    Time: 14:30:25
    
    Card No: ****4514
    
    Amount: RM 125.50
    
    APPROVED
    Thank you!
    """
    
    print("=== 测试OCR解析 ===")
    print(f"卡号后4位: {parser._extract_card_last4(test_text)}")
    print(f"日期: {parser._extract_date(test_text)}")
    print(f"金额: {parser._extract_amount(test_text)}")
    print(f"商家: {parser._extract_merchant_name(test_text)}")
