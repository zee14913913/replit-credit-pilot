"""
Credit Card Statement Post-processing Pipeline
将 Google Document AI 的 JSON 输出转换为统一的大表格结构

完整流程:
1. 接收 Document AI JSON
2. 提取 16 个字段
3. 标准化格式（日期、金额、卡号）
4. CR/DR 自动修正
5. 余额验证
6. 扁平化交易表格
7. 输出 CSV/JSON

Author: CreditPilot System
Version: 1.0
"""

import json
import csv
from typing import Dict, List, Any
from pathlib import Path

from utils.extract import DocumentAIExtractor
from utils.normalize import FieldNormalizer
from utils.crdr_fix import CRDRFixer


class StatementProcessor:
    """信用卡账单后处理主处理器"""
    
    def __init__(self):
        self.extractor = DocumentAIExtractor()
        self.normalizer = FieldNormalizer()
        self.crdr_fixer = CRDRFixer()
    
    def process(self, doc_ai_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        完整的后处理流程
        
        Args:
            doc_ai_json: Google Document AI 返回的 JSON
                格式: {"entities": [...], "text": "..."}
        
        Returns:
            处理后的结构化数据:
            {
                "bank_name": str,
                "customer_name": str,
                "ic_no": str,
                "card_type": str,
                "card_no": str,
                "credit_limit": float,
                "statement_date": "YYYY-MM-DD",
                "payment_due_date": "YYYY-MM-DD",
                "previous_balance": float,
                "current_balance": float,
                "minimum_payment": float,
                "earned_point": str,
                "transactions": [
                    {
                        "transaction_date": "YYYY-MM-DD",
                        "transaction_description": str,
                        "amount_CR": float,
                        "amount_DR": float,
                        "earned_point": str
                    }
                ],
                "validation": {
                    "is_valid": bool,
                    "calculated_balance": float,
                    "difference": float,
                    "message": str
                },
                "metadata": {
                    "total_transactions": int,
                    "auto_corrected_count": int,
                    "processing_timestamp": str
                }
            }
        """
        # Step 1: 提取字段
        extracted_data = self.extractor.extract_fields(doc_ai_json)
        
        # Step 2: 标准化格式
        normalized_data = self.normalizer.normalize_all_fields(extracted_data)
        
        # Step 3: CR/DR 自动修正
        if normalized_data.get('transactions'):
            normalized_data['transactions'] = self.crdr_fixer.fix_all_transactions(
                normalized_data['transactions']
            )
        
        # Step 4: 余额验证
        validation_result = self.crdr_fixer.validate_balance(
            previous_balance=normalized_data.get('previous_balance', 0),
            current_balance=normalized_data.get('current_balance', 0),
            transactions=normalized_data.get('transactions', [])
        )
        
        normalized_data['validation'] = validation_result
        
        # Step 5: 添加元数据
        auto_corrected = sum(
            1 for t in normalized_data.get('transactions', [])
            if t.get('_auto_corrected', False)
        )
        
        normalized_data['metadata'] = {
            "total_transactions": len(normalized_data.get('transactions', [])),
            "auto_corrected_count": auto_corrected,
            "processing_timestamp": self._get_timestamp()
        }
        
        return normalized_data
    
    def flatten_to_rows(self, processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        将处理后的数据扁平化为行记录（用于 CSV 输出）
        
        每条交易生成一行，包含账单基本信息 + 交易详情
        
        Returns:
            扁平化的行列表，每行包含所有 16 个字段
        """
        rows = []
        
        # 基本信息（账单级别）
        base_info = {
            'bank_name': processed_data.get('bank_name', ''),
            'customer_name': processed_data.get('customer_name', ''),
            'ic_no': processed_data.get('ic_no', ''),
            'card_type': processed_data.get('card_type', ''),
            'card_no': processed_data.get('card_no', ''),
            'credit_limit': processed_data.get('credit_limit', 0),
            'statement_date': processed_data.get('statement_date', ''),
            'payment_due_date': processed_data.get('payment_due_date', ''),
            'previous_balance': processed_data.get('previous_balance', 0),
            'current_balance': processed_data.get('current_balance', 0),
            'minimum_payment': processed_data.get('minimum_payment', 0),
        }
        
        # 为每条交易生成一行
        transactions = processed_data.get('transactions', [])
        
        if not transactions:
            # 如果没有交易，至少输出一行基本信息
            row = base_info.copy()
            row.update({
                'transaction_date': '',
                'transaction_description': '',
                'amount_CR': 0,
                'amount_DR': 0,
                'earned_point': processed_data.get('earned_point', '')
            })
            rows.append(row)
        else:
            for transaction in transactions:
                row = base_info.copy()
                row.update({
                    'transaction_date': transaction.get('transaction_date', ''),
                    'transaction_description': transaction.get('transaction_description', ''),
                    'amount_CR': transaction.get('amount_CR', 0),
                    'amount_DR': transaction.get('amount_DR', 0),
                    'earned_point': transaction.get('earned_point', '')
                })
                rows.append(row)
        
        return rows
    
    def save_to_csv(self, processed_data: Dict[str, Any], output_path: str):
        """
        保存为 CSV 文件
        
        Args:
            processed_data: 处理后的数据
            output_path: 输出文件路径
        """
        rows = self.flatten_to_rows(processed_data)
        
        if not rows:
            print("No data to save")
            return
        
        # CSV 列顺序（16个字段）
        fieldnames = [
            'bank_name',
            'customer_name',
            'ic_no',
            'card_type',
            'card_no',
            'credit_limit',
            'statement_date',
            'payment_due_date',
            'previous_balance',
            'current_balance',
            'minimum_payment',
            'transaction_date',
            'transaction_description',
            'amount_CR',
            'amount_DR',
            'earned_point'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"✅ CSV saved to: {output_path}")
    
    def save_to_json(self, processed_data: Dict[str, Any], output_path: str):
        """
        保存为 JSON 文件
        
        Args:
            processed_data: 处理后的数据
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(processed_data, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"✅ JSON saved to: {output_path}")
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    """主函数示例"""
    
    # 示例: 读取 Document AI 的 JSON 输出
    sample_doc_ai_json = {
        "entities": [
            {"type": "bank_name", "mentionText": "AMBANK"},
            {"type": "customer_name", "mentionText": "CHEOK JUN YOON"},
            {"type": "card_no", "mentionText": "4031 4899 9530 6354"},
            {"type": "statement_date", "mentionText": "28 OCT 25"},
            {"type": "payment_due_date", "mentionText": "17 NOV 25"},
            {"type": "credit_limit", "mentionText": "RM15,000"},
            {"type": "current_balance", "mentionText": "RM15,062.57"},
            {"type": "minimum_payment", "mentionText": "RM1,501.88"},
            {"type": "previous_balance", "mentionText": "RM14,515.49"},
            {
                "type": "line_item",
                "properties": [
                    {"type": "date", "mentionText": "27 SEP 25"},
                    {"type": "description", "mentionText": "Shopee Malaysia"},
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
            }
        ],
        "text": "Full statement text..."
    }
    
    # 初始化处理器
    processor = StatementProcessor()
    
    # 处理
    result = processor.process(sample_doc_ai_json)
    
    # 输出结果
    print("="*80)
    print("处理结果:")
    print("="*80)
    print(f"银行: {result['bank_name']}")
    print(f"客户: {result['customer_name']}")
    print(f"卡号: {result['card_no']}")
    print(f"账单日期: {result['statement_date']}")
    print(f"到期日: {result['payment_due_date']}")
    print(f"本期余额: RM{result['current_balance']:.2f}")
    print(f"最低还款: RM{result['minimum_payment']:.2f}")
    print(f"\n交易数量: {result['metadata']['total_transactions']}")
    print(f"自动修正: {result['metadata']['auto_corrected_count']}")
    
    if result['validation']['is_valid']:
        print(f"\n✅ 余额验证: 通过")
    else:
        print(f"\n⚠️ 余额验证: 失败 (差异: RM{result['validation']['difference']})")
    
    # 保存文件
    processor.save_to_json(result, 'output/processed_statement.json')
    processor.save_to_csv(result, 'output/processed_statement.csv')


# ============================================
# 新增的API端点 - 用于前端对接
# ============================================

if __name__ == "__main__":
    # 创建输出目录
    Path('output').mkdir(exist_ok=True)
    
    main()
