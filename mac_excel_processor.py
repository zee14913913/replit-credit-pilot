#!/usr/bin/env python3
"""
INFINITE GZ - Mac Excel处理器
===============================
基于现有的Excel解析器，100% Mac兼容
准确度：90-95%

处理流程：
1. 读取PDF转换后的Excel文件
2. 使用credit_card_excel_parser.py解析
3. 智能分类：Owner/GZ、Supplier识别、1% Fee计算
4. 生成标准VBA格式JSON
5. 准备上传到Replit

作者：INFINITE GZ System
日期：2024-11-15
"""

import sys
import os
sys.path.insert(0, '.')

from pathlib import Path
import json
from decimal import Decimal
from services.excel_parsers.credit_card_excel_parser import CreditCardExcelParser

# Supplier List (7家供应商)
SUPPLIER_LIST = ['7SL', 'DINAS', 'RAUB SYC HAINAN', 'AI SMART TECH', 'HUAWEI', 'PASAR RAYA', 'PUCHONG HERBS']

# GZ付款关键词
GZ_KEYWORDS = ['GZ', 'KENG CHOW', 'INFINITE']


class InfiniteGZExcelProcessor:
    """INFINITE GZ Excel处理器"""
    
    def __init__(self):
        self.parser = CreditCardExcelParser()
        self.total_files = 0
        self.success_count = 0
        self.failed_count = 0
    
    def process_excel_file(self, excel_path: Path) -> dict:
        """
        处理单个Excel文件
        
        Args:
            excel_path: Excel文件路径
            
        Returns:
            处理结果字典
        """
        try:
            print(f"  📄 解析: {excel_path.name}")
            
            # 使用现有解析器解析Excel
            result = self.parser.parse(str(excel_path))
            
            if result['status'] != 'success':
                print(f"  ❌ 解析失败: {result.get('message', 'Unknown error')}")
                return None
            
            # 增强分类：Owner/GZ + Supplier识别
            enhanced_result = self._enhance_classification(result, excel_path.name)
            
            # 验证数据质量
            quality_score = self._validate_quality(enhanced_result)
            
            print(f"  ✅ {enhanced_result['summary']['total_transactions']}笔交易 | "
                  f"质量分数: {quality_score:.1f}%")
            
            return enhanced_result
            
        except Exception as e:
            print(f"  ❌ 错误: {str(e)}")
            return None
    
    def _enhance_classification(self, parsed_data: dict, filename: str) -> dict:
        """增强分类：Owner/GZ + Supplier识别"""
        
        transactions = parsed_data.get('transactions', [])
        
        # 统计数据
        owner_expenses = Decimal('0')
        owner_payments = Decimal('0')
        gz_expenses = Decimal('0')
        gz_payments = Decimal('0')
        supplier_fees = Decimal('0')
        
        # 增强每笔交易
        for txn in transactions:
            description = txn['description']
            amount = Decimal(str(txn['amount']))
            is_payment = txn.get('cr', 0) > 0
            
            # 分类交易
            classification = self._classify_transaction(description, amount, is_payment)
            
            # 添加分类字段
            txn['owner_flag'] = classification['owner_flag']
            txn['is_supplier'] = classification['is_supplier']
            txn['supplier_name'] = classification['supplier_name']
            txn['supplier_fee'] = classification['fee']
            
            # 统计
            if is_payment:
                if classification['owner_flag'] == 'GZ':
                    gz_payments += amount
                else:
                    owner_payments += amount
            else:
                if classification['owner_flag'] == 'GZ':
                    gz_expenses += amount
                    if classification['is_supplier']:
                        supplier_fees += classification['fee']
                else:
                    owner_expenses += amount
        
        # 更新summary
        parsed_data['summary'].update({
            'owner_expenses': float(owner_expenses),
            'owner_payments': float(owner_payments),
            'gz_expenses': float(gz_expenses),
            'gz_payments': float(gz_payments),
            'supplier_fees': float(supplier_fees),
            'gz_os_balance': float(gz_expenses - gz_payments + supplier_fees)
        })
        
        # 添加元数据
        parsed_data['parsed_by'] = 'Mac Excel Processor (Python)'
        parsed_data['source_file'] = filename
        
        return parsed_data
    
    def _classify_transaction(self, description: str, amount: Decimal, is_payment: bool) -> dict:
        """分类单笔交易"""
        
        desc_upper = description.upper()
        
        # 如果是付款
        if is_payment:
            # 检查是否为GZ付款
            for keyword in GZ_KEYWORDS:
                if keyword in desc_upper:
                    return {
                        'owner_flag': 'GZ',
                        'is_supplier': False,
                        'supplier_name': None,
                        'fee': Decimal('0')
                    }
            
            # 其他付款归为Owner
            return {
                'owner_flag': 'OWNER',
                'is_supplier': False,
                'supplier_name': None,
                'fee': Decimal('0')
            }
        
        # 消费交易
        # 检查是否为Supplier
        for supplier in SUPPLIER_LIST:
            if supplier.upper() in desc_upper:
                fee = amount * Decimal('0.01')  # 1% Fee
                return {
                    'owner_flag': 'GZ',
                    'is_supplier': True,
                    'supplier_name': supplier,
                    'fee': fee
                }
        
        # 其他消费归为Owner
        return {
            'owner_flag': 'OWNER',
            'is_supplier': False,
            'supplier_name': None,
            'fee': Decimal('0')
        }
    
    def _validate_quality(self, parsed_data: dict) -> float:
        """验证数据质量"""
        
        score = 100.0
        summary = parsed_data.get('summary', {})
        account_info = parsed_data.get('account_info', {})
        
        # 检查余额验证
        if not summary.get('balance_verified', False):
            score -= 10
        
        # 检查必要字段
        if account_info.get('bank', 'Unknown') == 'Unknown Bank':
            score -= 5
        
        if account_info.get('card_last_4', 'N/A') == 'N/A':
            score -= 5
        
        # 检查交易数量
        txn_count = summary.get('total_transactions', 0)
        if txn_count < 5:
            score -= 10
        
        return max(score, 0)
    
    def process_directory(self, excel_dir: Path, json_output_dir: Path):
        """批量处理Excel文件目录"""
        
        print("=" * 100)
        print("🚀 INFINITE GZ Mac Excel处理器")
        print("=" * 100)
        print(f"\n📂 Excel目录: {excel_dir}")
        print(f"📂 JSON输出: {json_output_dir}")
        
        # 创建输出目录
        json_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 查找所有Excel文件
        excel_files = list(excel_dir.glob("**/*.xlsx")) + list(excel_dir.glob("**/*.xls"))
        
        if not excel_files:
            print(f"\n❌ 未找到Excel文件！")
            print(f"请确保Excel文件已放置在: {excel_dir}")
            return
        
        self.total_files = len(excel_files)
        print(f"\n找到 {self.total_files} 个Excel文件")
        print("=" * 100)
        
        # 处理每个Excel
        for idx, excel_path in enumerate(excel_files, 1):
            print(f"\n[{idx}/{self.total_files}] {excel_path.name}")
            
            result = self.process_excel_file(excel_path)
            
            if result:
                # 保存JSON
                json_filename = excel_path.stem + '.json'
                json_path = json_output_dir / json_filename
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                self.success_count += 1
            else:
                self.failed_count += 1
        
        # 打印统计
        self._print_summary()
    
    def _print_summary(self):
        """打印处理统计"""
        
        print("\n" + "=" * 100)
        print("📊 处理完成统计")
        print("=" * 100)
        print(f"✅ 成功: {self.success_count} 个文件")
        print(f"❌ 失败: {self.failed_count} 个文件")
        print(f"📁 总计: {self.total_files} 个文件")
        print(f"📈 成功率: {(self.success_count / self.total_files * 100):.1f}%")
        print("=" * 100)
        
        if self.success_count > 0:
            print("\n下一步:")
            print("1. 检查生成的JSON文件")
            print("2. 将JSON文件上传到Replit")
            print("3. 在Replit运行: python3 scripts/process_uploaded_json.py")
            print("=" * 100)


def main():
    """主函数"""
    
    # 设置路径
    excel_dir = Path.home() / "CCC_Processing" / "Excel_Files"
    json_output_dir = Path.home() / "CCC_Processing" / "JSON_Output"
    
    # 创建处理器
    processor = InfiniteGZExcelProcessor()
    
    # 批量处理
    processor.process_directory(excel_dir, json_output_dir)


if __name__ == '__main__':
    main()
