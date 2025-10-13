"""
账单处理器 - Statement Processor
集成所有服务：解析 → 分类 → 生成发票 → 组织文件 → 生成报告
"""

from typing import Dict, List
from db.database import get_db
from services.transaction_classifier import classify_and_save_transactions
from services.invoice_generator import generate_supplier_invoices_for_statement
from services.customer_folder_manager import CustomerFolderManager
from services.monthly_summary_generator import generate_monthly_summary_for_customer


class ComprehensiveStatementProcessor:
    """综合账单处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.folder_manager = CustomerFolderManager()
    
    def process_statement_complete(self, customer_id: int, statement_id: int,
                                  original_pdf_path: str) -> Dict:
        """
        完整处理账单：分类 → 发票 → 组织 → 验证
        
        Args:
            customer_id: 客户ID
            statement_id: 账单ID
            original_pdf_path: 原始PDF路径
            
        Returns:
            处理结果字典
        """
        results = {
            'step_1_classify': None,
            'step_2_invoices': None,
            'step_3_organize': None,
            'step_4_validate': None,
            'success': False,
            'errors': []
        }
        
        try:
            # Step 1: 分类所有交易
            print(f"📋 Step 1/4: 分类账单 #{statement_id} 的交易...")
            classification_stats = classify_and_save_transactions(statement_id, customer_id)
            results['step_1_classify'] = classification_stats
            
            if 'error' in classification_stats:
                results['errors'].append(f"分类失败: {classification_stats['error']}")
                return results
            
            print(f"   ✅ 分类完成: {classification_stats['total_transactions']} 笔交易")
            print(f"      - Supplier Debit: {classification_stats['supplier_debit']} 笔")
            print(f"      - Unclassified Debit: {classification_stats['unclassified_debit']} 笔")
            print(f"      - 3rd Party Credit: {classification_stats['third_party_credit']} 笔")
            print(f"      - Owner Credit: {classification_stats['owner_credit']} 笔")
            
            # Step 2: 生成供应商发票
            print(f"📄 Step 2/4: 生成供应商发票...")
            invoice_paths = []
            if classification_stats['supplier_debit'] > 0:
                invoice_paths = generate_supplier_invoices_for_statement(customer_id, statement_id)
                print(f"   ✅ 生成了 {len(invoice_paths)} 张供应商发票")
            else:
                print(f"   ℹ️  无供应商交易，跳过发票生成")
            
            results['step_2_invoices'] = invoice_paths
            
            # Step 3: 组织文件到客户文件夹
            print(f"📁 Step 3/4: 组织文件到客户文件夹...")
            organization_result = self.folder_manager.organize_statement_files(
                customer_id, statement_id, original_pdf_path,
                invoice_paths=invoice_paths
            )
            results['step_3_organize'] = organization_result
            
            if 'error' in organization_result:
                results['errors'].append(f"文件组织失败: {organization_result['error']}")
            else:
                print(f"   ✅ 文件已组织到月份文件夹")
            
            # Step 4: 三次验证数据准确性
            print(f"🔍 Step 4/4: 三次验证数据准确性...")
            validation_result = self._triple_validate(statement_id, customer_id)
            results['step_4_validate'] = validation_result
            
            if validation_result['is_valid']:
                print(f"   ✅ 验证通过: 100% 数据准确")
                results['success'] = True
            else:
                print(f"   ⚠️  验证发现问题:")
                for issue in validation_result['issues']:
                    print(f"      - {issue}")
                results['errors'].extend(validation_result['issues'])
            
        except Exception as e:
            results['errors'].append(f"处理异常: {str(e)}")
            print(f"   ❌ 处理失败: {str(e)}")
        
        return results
    
    def _triple_validate(self, statement_id: int, customer_id: int) -> Dict:
        """
        三次验证机制：确保数据100%准确
        
        验证项：
        1. 交易数量匹配
        2. 金额总计匹配
        3. 分类完整性检查
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取原始交易数量和总额
            cursor.execute('''
                SELECT COUNT(*), SUM(ABS(amount))
                FROM transactions
                WHERE statement_id = ?
            ''', (statement_id,))
            original_count, original_total = cursor.fetchone()
            
            # 获取账单总额
            cursor.execute('''
                SELECT statement_total
                FROM statements
                WHERE id = ?
            ''', (statement_id,))
            statement_total = cursor.fetchone()[0]
            
            # 验证1: 检查消费记录数量
            cursor.execute('''
                SELECT COUNT(*)
                FROM consumption_records
                WHERE statement_id = ? AND customer_id = ?
            ''', (statement_id, customer_id))
            consumption_count = cursor.fetchone()[0]
            
            # 验证2: 检查付款记录数量
            cursor.execute('''
                SELECT COUNT(*)
                FROM payment_records
                WHERE statement_id = ? AND customer_id = ?
            ''', (statement_id, customer_id))
            payment_count = cursor.fetchone()[0]
            
            # 验证3: 检查金额总计
            cursor.execute('''
                SELECT SUM(amount)
                FROM consumption_records
                WHERE statement_id = ? AND customer_id = ?
            ''', (statement_id, customer_id))
            consumption_total = cursor.fetchone()[0] or 0
            
            cursor.execute('''
                SELECT SUM(payment_amount)
                FROM payment_records
                WHERE statement_id = ? AND customer_id = ?
            ''', (statement_id, customer_id))
            payment_total = cursor.fetchone()[0] or 0
            
            # 分析验证结果
            issues = []
            
            # 检查1: 记录数量完整性
            classified_total = consumption_count + payment_count
            if classified_total != original_count:
                issues.append(
                    f"交易数量不匹配: 原始 {original_count} vs 分类 {classified_total} "
                    f"(消费 {consumption_count} + 付款 {payment_count})"
                )
            
            # 检查2: 金额准确性（允许小额误差）
            total_classified = consumption_total + payment_total
            if abs(total_classified - original_total) > 0.1:
                issues.append(
                    f"金额总计不匹配: 原始 RM {original_total:.2f} vs "
                    f"分类 RM {total_classified:.2f}"
                )
            
            # 检查3: 与账单总额对比
            if abs(consumption_total - statement_total) > 0.1:
                issues.append(
                    f"消费总额与账单不符: 账单 RM {statement_total:.2f} vs "
                    f"消费记录 RM {consumption_total:.2f}"
                )
            
            return {
                'is_valid': len(issues) == 0,
                'issues': issues,
                'stats': {
                    'original_count': original_count,
                    'consumption_count': consumption_count,
                    'payment_count': payment_count,
                    'original_total': original_total,
                    'consumption_total': consumption_total,
                    'payment_total': payment_total,
                    'statement_total': statement_total
                }
            }
    
    def generate_monthly_report(self, customer_id: int, month: str) -> str:
        """
        生成月度汇总报告
        
        Args:
            customer_id: 客户ID
            month: 月份 (YYYY-MM)
            
        Returns:
            PDF文件路径
        """
        print(f"📊 生成 {month} 月度汇总报告...")
        report_path = generate_monthly_summary_for_customer(customer_id, month)
        
        if report_path:
            print(f"   ✅ 报告已生成: {report_path}")
        else:
            print(f"   ⚠️  该月无数据")
        
        return report_path


def process_uploaded_statement(customer_id: int, statement_id: int, 
                              pdf_path: str) -> Dict:
    """
    处理上传的账单（便捷函数）
    
    Args:
        customer_id: 客户ID
        statement_id: 账单ID
        pdf_path: PDF文件路径
        
    Returns:
        处理结果
    """
    processor = ComprehensiveStatementProcessor()
    return processor.process_statement_complete(customer_id, statement_id, pdf_path)


def generate_customer_monthly_report(customer_id: int, month: str) -> str:
    """
    生成客户月度报告（便捷函数）
    
    Args:
        customer_id: 客户ID
        month: 月份 (YYYY-MM)
        
    Returns:
        PDF路径
    """
    processor = ComprehensiveStatementProcessor()
    return processor.generate_monthly_report(customer_id, month)
