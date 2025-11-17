#!/usr/bin/env python3
"""
Cheok Jun Yoon 信用卡账单批量处理脚本
使用Document AI提取数据并进行业务计算
"""
import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.google_document_ai_service import GoogleDocumentAIService
from scripts.calculate_balances import BalanceCalculator
from config.settings_loader import get_settings


class CheokStatementProcessor:
    """Cheok Jun Yoon账单处理器"""
    
    def __init__(self):
        """初始化"""
        self.settings = get_settings()
        self.settings.load()
        
        self.doc_ai_service = GoogleDocumentAIService()
        self.calculator = BalanceCalculator()
        
        self.customer_name = "Cheok Jun Yoon"
        self.customer_code = "Be_rich_CJY"
        self.base_path = Path(f"static/uploads/customers/{self.customer_code}/credit_cards")
        self.reports_path = Path(f"reports/{self.customer_code}")
        
        # 创建报告目录
        self.reports_path.mkdir(parents=True, exist_ok=True)
        
        self.results = []
        self.errors = []
    
    def find_all_pdfs(self) -> List[Path]:
        """查找所有PDF文件"""
        pdf_files = []
        
        if not self.base_path.exists():
            print(f"❌ 客户文件夹不存在: {self.base_path}")
            return pdf_files
        
        # 递归查找所有PDF
        for pdf_file in self.base_path.rglob("*.pdf"):
            pdf_files.append(pdf_file)
        
        # 按文件名排序
        pdf_files.sort()
        
        return pdf_files
    
    def process_single_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        处理单个PDF文件
        
        Args:
            pdf_path: PDF文件路径
        
        Returns:
            处理结果
        """
        print(f"\n📄 处理: {pdf_path.name}")
        
        try:
            # 1. 使用Document AI提取数据
            print("   ├─ 提取数据...")
            raw_result = self.doc_ai_service.parse_pdf(str(pdf_path))
            
            if not raw_result:
                raise Exception("Document AI返回空结果")
            
            # 2. 提取结构化字段
            fields = self.doc_ai_service.extract_bank_statement_fields(raw_result)
            
            # 3. 验证必需字段
            required_fields = ['card_number', 'bank_name']
            missing_fields = [f for f in required_fields if not fields.get(f)]
            
            if missing_fields:
                raise Exception(f"缺少必需字段: {missing_fields}")
            
            # 4. 提取交易记录
            transactions = fields.get('transactions', [])
            print(f"   ├─ 提取交易: {len(transactions)}笔")
            
            # 5. 交易分类
            print("   ├─ 分类交易...")
            categorized = self.calculator.categorize_transactions(transactions)
            totals = self.calculator.calculate_totals(categorized)
            
            # 6. 计算余额
            previous_balance = fields.get('previous_balance', 0) or 0
            balances = self.calculator.calculate_outstanding_balance(
                previous_balance, categorized, totals
            )
            
            # 7. 生成汇总
            summary = self.calculator.generate_summary_report(
                categorized, totals, balances
            )
            
            result = {
                'file_path': str(pdf_path),
                'file_name': pdf_path.name,
                'bank_name': fields.get('bank_name', 'Unknown'),
                'card_number': fields.get('card_number', 'Unknown'),
                'statement_date': fields.get('statement_date', ''),
                'due_date': fields.get('due_date', ''),
                'fields': fields,
                'categorized_transactions': categorized,
                'totals': totals,
                'balances': balances,
                'summary': summary,
                'status': 'success'
            }
            
            print(f"   └─ ✅ 成功")
            print(f"      - 交易总数: {summary['summary']['total_transactions']}")
            print(f"      - Outstanding Balance: RM {balances['outstanding_balance']:.2f}")
            
            return result
            
        except Exception as e:
            error_result = {
                'file_path': str(pdf_path),
                'file_name': pdf_path.name,
                'status': 'error',
                'error': str(e)
            }
            
            print(f"   └─ ❌ 失败: {e}")
            
            return error_result
    
    def process_batch(self, pdf_files: List[Path], max_workers: int = 3) -> List[Dict]:
        """
        批量处理PDF文件
        
        Args:
            pdf_files: PDF文件列表
            max_workers: 最大并发数
        
        Returns:
            处理结果列表
        """
        results = []
        
        print(f"\n🚀 开始批量处理 {len(pdf_files)} 个PDF文件")
        print(f"📊 并发数: {max_workers}")
        print("="*80)
        
        # 并行处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_pdf = {
                executor.submit(self.process_single_pdf, pdf): pdf 
                for pdf in pdf_files
            }
            
            for i, future in enumerate(as_completed(future_to_pdf), 1):
                pdf = future_to_pdf[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['status'] == 'error':
                        self.errors.append(result)
                    else:
                        self.results.append(result)
                    
                    print(f"\n进度: {i}/{len(pdf_files)} ({i/len(pdf_files)*100:.1f}%)")
                    
                except Exception as e:
                    error_result = {
                        'file_path': str(pdf),
                        'file_name': pdf.name,
                        'status': 'error',
                        'error': str(e)
                    }
                    results.append(error_result)
                    self.errors.append(error_result)
                    print(f"❌ 处理失败: {pdf.name} - {e}")
        
        return results
    
    def generate_excel_report(self, results: List[Dict], output_path: Path):
        """
        生成Excel汇总报告
        
        Args:
            results: 处理结果列表
            output_path: 输出文件路径
        """
        print(f"\n📊 生成Excel报告: {output_path}")
        
        # 准备数据
        summary_data = []
        transaction_data = []
        category_summary = []
        
        for result in results:
            if result['status'] != 'success':
                continue
            
            # 账单汇总
            summary_data.append({
                '文件名': result['file_name'],
                '银行': result['bank_name'],
                '卡号': result['card_number'],
                '账单日期': result['statement_date'],
                '到期日': result['due_date'],
                '上期余额': result['balances']['previous_balance'],
                '本期消费': result['balances']['total_expenses'],
                '本期还款': result['balances']['total_payments'],
                'Outstanding Balance': result['balances']['outstanding_balance'],
                '交易笔数': result['summary']['summary']['total_transactions']
            })
            
            # 交易明细
            for category, transactions in result['categorized_transactions'].items():
                for txn in transactions:
                    transaction_data.append({
                        '文件名': result['file_name'],
                        '银行': result['bank_name'],
                        '卡号': result['card_number'],
                        '分类': category,
                        '交易日期': txn.get('transaction_date', ''),
                        '交易描述': txn.get('description', ''),
                        '金额': txn.get('amount', 0),
                        '供应商手续费': txn.get('supplier_fee', 0),
                        '是否贷记': txn.get('is_credit', False)
                    })
            
            # 分类汇总
            for category, total in result['totals'].items():
                category_summary.append({
                    '文件名': result['file_name'],
                    '银行': result['bank_name'],
                    '卡号': result['card_number'],
                    '分类': category,
                    '金额': total
                })
        
        # 创建Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 账单汇总
            if summary_data:
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='账单汇总', index=False)
            
            # 交易明细
            if transaction_data:
                df_transactions = pd.DataFrame(transaction_data)
                df_transactions.to_excel(writer, sheet_name='交易明细', index=False)
            
            # 分类汇总
            if category_summary:
                df_category = pd.DataFrame(category_summary)
                df_category.to_excel(writer, sheet_name='分类汇总', index=False)
            
            # 错误记录
            if self.errors:
                error_data = [{
                    '文件名': e['file_name'],
                    '错误信息': e['error']
                } for e in self.errors]
                df_errors = pd.DataFrame(error_data)
                df_errors.to_excel(writer, sheet_name='错误记录', index=False)
        
        print(f"✅ Excel报告已生成")
    
    def generate_json_report(self, results: List[Dict], output_path: Path):
        """生成JSON详细报告"""
        print(f"\n💾 生成JSON报告: {output_path}")
        
        report = {
            'customer_name': self.customer_name,
            'customer_code': self.customer_code,
            'processing_date': datetime.now().isoformat(),
            'total_files': len(results),
            'successful': len(self.results),
            'failed': len(self.errors),
            'results': results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON报告已生成")
    
    def print_summary(self):
        """打印处理摘要"""
        print("\n" + "="*80)
        print("📋 处理摘要")
        print("="*80)
        
        print(f"\n客户: {self.customer_name} ({self.customer_code})")
        print(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n📊 处理结果:")
        print(f"   总文件数: {len(self.results) + len(self.errors)}")
        print(f"   成功: {len(self.results)}")
        print(f"   失败: {len(self.errors)}")
        
        if self.results:
            # 汇总统计
            total_transactions = sum(
                r['summary']['summary']['total_transactions'] 
                for r in self.results
            )
            total_expenses = sum(
                r['balances']['total_expenses'] 
                for r in self.results
            )
            total_payments = sum(
                r['balances']['total_payments'] 
                for r in self.results
            )
            total_outstanding = sum(
                r['balances']['outstanding_balance'] 
                for r in self.results
            )
            
            print(f"\n💰 总体统计:")
            print(f"   交易总笔数: {total_transactions}")
            print(f"   消费总额: RM {total_expenses:,.2f}")
            print(f"   还款总额: RM {total_payments:,.2f}")
            print(f"   Outstanding Balance: RM {total_outstanding:,.2f}")
            
            # 按银行分组
            banks = {}
            for r in self.results:
                bank = r['bank_name']
                if bank not in banks:
                    banks[bank] = []
                banks[bank].append(r)
            
            print(f"\n🏦 银行分布:")
            for bank, results in banks.items():
                print(f"   {bank}: {len(results)} 份账单")
        
        if self.errors:
            print(f"\n❌ 失败文件:")
            for error in self.errors[:5]:
                print(f"   - {error['file_name']}: {error['error']}")
            if len(self.errors) > 5:
                print(f"   ... 还有 {len(self.errors)-5} 个错误")
        
        print("\n" + "="*80)


def main():
    """主函数"""
    print("="*80)
    print("Cheok Jun Yoon 信用卡账单批量处理系统")
    print("="*80)
    
    # 初始化处理器
    processor = CheokStatementProcessor()
    
    # 查找所有PDF
    pdf_files = processor.find_all_pdfs()
    
    if not pdf_files:
        print("❌ 未找到PDF文件")
        return
    
    print(f"\n找到 {len(pdf_files)} 个PDF文件")
    
    # 显示前10个文件
    print("\n📄 文件列表（前10个）:")
    for i, pdf in enumerate(pdf_files[:10], 1):
        print(f"   {i}. {pdf.name}")
    if len(pdf_files) > 10:
        print(f"   ... 还有 {len(pdf_files)-10} 个文件")
    
    # 确认处理
    print("\n⚠️  即将开始批量处理...")
    
    # 开始处理
    results = processor.process_batch(pdf_files, max_workers=3)
    
    # 生成报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    excel_path = processor.reports_path / f"settlement_report_{timestamp}.xlsx"
    json_path = processor.reports_path / f"processing_results_{timestamp}.json"
    
    processor.generate_excel_report(results, excel_path)
    processor.generate_json_report(results, json_path)
    
    # 打印摘要
    processor.print_summary()
    
    print(f"\n✅ 处理完成！")
    print(f"\n📁 报告文件:")
    print(f"   Excel: {excel_path}")
    print(f"   JSON: {json_path}")
    print("\n" + "="*80)


if __name__ == '__main__':
    main()
