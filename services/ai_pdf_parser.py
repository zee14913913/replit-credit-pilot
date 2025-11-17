"""
AI智能PDF解析服务
用途：自动解析7家银行信用卡账单，无需手动配置
使用：pdfplumber提取文本 + AI识别字段
"""
import os
import re
import logging
from typing import Dict, Optional, List, Any
from pathlib import Path
import pdfplumber
from datetime import datetime

logger = logging.getLogger(__name__)


class AIBankStatementParser:
    """AI驱动的银行账单解析器"""
    
    SUPPORTED_BANKS = {
        'AMBANK': ['AmBank', 'AMBANK'],
        'AMBANK_ISLAMIC': ['AmBank Islamic', 'AMBANK ISLAMIC'],
        'STANDARD_CHARTERED': ['Standard Chartered', 'STANDARD CHARTERED', 'SCB'],
        'UOB': ['UOB', 'United Overseas Bank'],
        'HONG_LEONG': ['Hong Leong', 'HONG LEONG', 'HLB'],
        'OCBC': ['OCBC'],
        'HSBC': ['HSBC']
    }
    
    def __init__(self):
        self.ai_available = self._check_ai_service()
    
    def _check_ai_service(self) -> bool:
        """检查AI服务是否可用"""
        openai_key = os.getenv('OPENAI_API_KEY')
        perplexity_key = os.getenv('PERPLEXITY_API_KEY')
        return bool(openai_key or perplexity_key)
    
    def detect_bank(self, text: str) -> Optional[str]:
        """
        从PDF文本中识别银行
        
        Args:
            text: PDF文本内容
        
        Returns:
            str: 银行代码（如 'AMBANK'）
        """
        text_upper = text.upper()
        
        for bank_code, keywords in self.SUPPORTED_BANKS.items():
            for keyword in keywords:
                if keyword.upper() in text_upper:
                    return bank_code
        
        return None
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        从PDF提取文本
        
        Args:
            pdf_path: PDF文件路径
        
        Returns:
            str: 提取的文本内容
        """
        try:
            text_content = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
            
            return '\n'.join(text_content)
            
        except Exception as e:
            logger.error(f"PDF文本提取失败: {e}")
            return ""
    
    def extract_card_number(self, text: str) -> Optional[str]:
        """提取卡号后4位"""
        patterns = [
            r'(?:Card|Account)\s*(?:No|Number)[:\s]*(?:xxxx|XXXX|\*{4})\s*(\d{4})',
            r'(?:xxxx|XXXX|\*{4})\s*(\d{4})',
            r'ending\s*(?:in\s*)?(\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_statement_date(self, text: str) -> Optional[str]:
        """提取账单日期"""
        patterns = [
            r'Statement\s*Date[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'Date[:\s]*(\d{1,2}\s+\w+\s+\d{4})',
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                return self._normalize_date(date_str)
        
        return None
    
    def _normalize_date(self, date_str: str) -> str:
        """统一日期格式为 YYYY-MM-DD"""
        try:
            # 尝试多种日期格式
            formats = [
                '%d/%m/%Y',
                '%d-%m-%Y',
                '%d %b %Y',
                '%d %B %Y',
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except:
                    continue
            
            return date_str
            
        except Exception as e:
            logger.error(f"日期格式化失败: {e}")
            return date_str
    
    def extract_balances(self, text: str) -> Dict[str, float]:
        """提取余额信息"""
        balances = {
            'previous_balance': 0.0,
            'total_credit': 0.0,
            'total_debit': 0.0,
            'current_balance': 0.0,
            'minimum_payment': 0.0
        }
        
        patterns = {
            'previous_balance': r'(?:Previous|Last)\s*Balance[:\s]*(?:RM|MYR)?\s*([\d,]+\.?\d*)',
            'total_credit': r'(?:Total\s*)?(?:Credits?|Payments?)[:\s]*(?:RM|MYR)?\s*([\d,]+\.?\d*)',
            'total_debit': r'(?:Total\s*)?(?:Debits?|Purchases?)[:\s]*(?:RM|MYR)?\s*([\d,]+\.?\d*)',
            'current_balance': r'(?:Current|New|Outstanding)\s*Balance[:\s]*(?:RM|MYR)?\s*([\d,]+\.?\d*)',
            'minimum_payment': r'Minimum\s*Payment[:\s]*(?:RM|MYR)?\s*([\d,]+\.?\d*)',
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    balances[field] = float(amount_str)
                except:
                    pass
        
        return balances
    
    def extract_transactions(self, text: str, pdf_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        提取交易明细（使用pdfplumber表格提取）
        
        Returns:
            List[Dict]: 交易列表
        """
        transactions = []
        
        # 方法1: 使用pdfplumber提取表格
        if pdf_path:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        tables = page.extract_tables()
                        
                        for table in tables:
                            if not table or len(table) < 2:
                                continue
                            
                            # 检测表头
                            header = [str(cell).lower() if cell else '' for cell in table[0]]
                            
                            # 查找日期、描述、金额列的索引
                            date_idx = self._find_column_index(header, ['date', 'trans', '交易'])
                            desc_idx = self._find_column_index(header, ['description', 'particular', '描述', '详情'])
                            amount_idx = self._find_column_index(header, ['amount', 'debit', 'credit', '金额'])
                            
                            # 提取数据行
                            for row in table[1:]:
                                if not row or len(row) < 2:
                                    continue
                                
                                try:
                                    trans = self._parse_transaction_row(row, date_idx, desc_idx, amount_idx)
                                    if trans:
                                        transactions.append(trans)
                                except:
                                    continue
            
            except Exception as e:
                logger.warning(f"表格提取失败: {e}")
        
        # 方法2: 正则提取（备用）
        if not transactions:
            pattern = r'(\d{1,2}[-/]\d{1,2})\s+(.+?)\s+([\d,]+\.?\d{2})(?:\s+(DR|CR))?'
            matches = re.finditer(pattern, text, re.MULTILINE)
            
            for match in matches:
                date_str = match.group(1)
                description = match.group(2).strip()
                amount_str = match.group(3).replace(',', '')
                trans_type = match.group(4) if match.group(4) else 'DR'
                
                try:
                    amount = float(amount_str)
                    
                    transactions.append({
                        'date': date_str,
                        'description': description,
                        'amount': amount,
                        'type': trans_type
                    })
                except:
                    continue
        
        return transactions
    
    def _find_column_index(self, header: List[str], keywords: List[str]) -> Optional[int]:
        """查找表头中包含关键词的列索引"""
        for i, col_name in enumerate(header):
            for keyword in keywords:
                if keyword in col_name:
                    return i
        return None
    
    def _parse_transaction_row(self, row: List, date_idx: Optional[int], 
                               desc_idx: Optional[int], amount_idx: Optional[int]) -> Optional[Dict]:
        """解析交易行"""
        if date_idx is None or desc_idx is None or amount_idx is None:
            return None
        
        try:
            date_str = str(row[date_idx]).strip() if row[date_idx] else ''
            description = str(row[desc_idx]).strip() if row[desc_idx] else ''
            amount_str = str(row[amount_idx]).strip() if row[amount_idx] else ''
            
            # 提取金额
            amount_match = re.search(r'([\d,]+\.?\d*)', amount_str)
            if not amount_match:
                return None
            
            amount = float(amount_match.group(1).replace(',', ''))
            
            # 判断DR/CR
            trans_type = 'CR' if 'CR' in amount_str or '+' in amount_str else 'DR'
            
            return {
                'date': date_str,
                'description': description,
                'amount': amount,
                'type': trans_type
            }
        except:
            return None
    
    def parse_statement(self, pdf_path: str) -> Dict[str, Any]:
        """
        解析银行账单PDF
        
        Args:
            pdf_path: PDF文件路径
        
        Returns:
            Dict: 解析结果
        """
        try:
            logger.info(f"开始解析PDF: {pdf_path}")
            
            # 提取文本
            text = self.extract_text_from_pdf(pdf_path)
            
            if not text:
                raise ValueError("无法从PDF提取文本")
            
            # 识别银行
            bank_code = self.detect_bank(text)
            
            if not bank_code:
                raise ValueError("无法识别银行")
            
            logger.info(f"识别银行: {bank_code}")
            
            # 提取字段
            result = {
                'bank_name': bank_code,
                'card_number': self.extract_card_number(text),
                'statement_date': self.extract_statement_date(text),
                'balances': self.extract_balances(text),
                'transactions': self.extract_transactions(text, pdf_path),
                'raw_text_length': len(text),
                'parser_version': '1.0.0',
                'parser_type': 'AI_LOCAL'
            }
            
            logger.info(f"✅ 解析完成: {bank_code}, 交易数: {len(result['transactions'])}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 解析失败: {e}")
            raise
    
    def parse_with_ai_enhancement(self, pdf_path: str) -> Dict[str, Any]:
        """
        使用AI增强解析（如果AI服务可用）
        
        Args:
            pdf_path: PDF文件路径
        
        Returns:
            Dict: 解析结果
        """
        # 先用规则引擎解析
        result = self.parse_statement(pdf_path)
        
        # 如果AI可用，使用AI修正/增强
        if self.ai_available:
            try:
                result = self._ai_enhance_result(result, pdf_path)
            except Exception as e:
                logger.warning(f"AI增强失败，使用原始结果: {e}")
        
        return result
    
    def _ai_enhance_result(self, result: Dict[str, Any], pdf_path: str) -> Dict[str, Any]:
        """
        使用AI增强解析结果
        """
        try:
            from services.ai_client import get_ai_client
            
            # 获取PDF文本
            text = self.extract_text_from_pdf(pdf_path)
            
            # 截取前3000字符（避免超出token限制）
            text_sample = text[:3000] if len(text) > 3000 else text
            
            # AI提示词
            prompt = f"""
你是一个银行信用卡账单解析专家。请从以下账单文本中提取关键信息：

银行账单文本：
```
{text_sample}
```

请以JSON格式返回以下信息：
{{
    "card_number": "卡号后4位",
    "statement_date": "账单日期(YYYY-MM-DD格式)",
    "statement_period": "账单周期(YYYY-MM格式)",
    "cardholder_name": "持卡人姓名",
    "previous_balance": 上期结余数字,
    "total_credit": 总贷项数字,
    "total_debit": 总借项数字,
    "current_balance": 本期结余数字,
    "minimum_payment": 最低还款额数字,
    "payment_due_date": "缴款截止日期(YYYY-MM-DD格式)"
}}

注意：
1. 所有金额仅返回数字，不要货币符号
2. 日期统一格式为 YYYY-MM-DD
3. 如果某个字段找不到，返回null
"""
            
            # 调用AI
            ai_client = get_ai_client()
            ai_response = ai_client.chat(prompt, max_tokens=500)
            
            # 解析AI响应
            import json
            ai_data = json.loads(ai_response)
            
            # 合并AI结果到原始结果
            if ai_data.get('card_number'):
                result['card_number'] = ai_data['card_number']
            
            if ai_data.get('statement_date'):
                result['statement_date'] = ai_data['statement_date']
            
            if ai_data.get('cardholder_name'):
                result['cardholder_name'] = ai_data['cardholder_name']
            
            # 更新余额信息
            for field in ['previous_balance', 'total_credit', 'total_debit', 'current_balance', 'minimum_payment']:
                if ai_data.get(field) and ai_data[field] is not None:
                    result['balances'][field] = float(ai_data[field])
            
            if ai_data.get('payment_due_date'):
                result['payment_due_date'] = ai_data['payment_due_date']
            
            result['ai_enhanced'] = True
            
            logger.info("✅ AI增强完成")
            
        except Exception as e:
            logger.warning(f"AI增强失败: {e}")
            result['ai_enhanced'] = False
        
        return result


def test_parser():
    """测试解析器"""
    parser = AIBankStatementParser()
    
    # 测试文件
    test_files = [
        './docparser_templates/sample_pdfs/1_AMBANK.pdf',
        './docparser_templates/sample_pdfs/7_HSBC.pdf',
    ]
    
    print("="*80)
    print("AI银行账单解析器测试")
    print("="*80)
    
    for test_file in test_files:
        if not Path(test_file).exists():
            print(f"\n⚠️  文件不存在: {test_file}")
            continue
        
        print(f"\n正在解析: {test_file}")
        print("-"*80)
        
        try:
            result = parser.parse_statement(test_file)
            
            print(f"✅ 银行: {result['bank_name']}")
            print(f"✅ 卡号: {result['card_number']}")
            print(f"✅ 日期: {result['statement_date']}")
            print(f"✅ 上期结余: RM {result['balances']['previous_balance']:.2f}")
            print(f"✅ 本期结余: RM {result['balances']['current_balance']:.2f}")
            print(f"✅ 交易数量: {len(result['transactions'])}")
            
            if result['transactions']:
                print("\n前3笔交易:")
                for i, trans in enumerate(result['transactions'][:3], 1):
                    print(f"  {i}. {trans['date']} - {trans['description'][:30]} - RM {trans['amount']}")
            
        except Exception as e:
            print(f"❌ 解析失败: {e}")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    test_parser()
