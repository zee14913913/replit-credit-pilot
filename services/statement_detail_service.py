#!/usr/bin/env python3
"""
Statement Detail Service - 月度账单详情服务
=============================================
为月度详情页面提供：
1. 月度计算表格（Previous Balance、DR/CR分类、30+分类、Supplier匹配、1% Fee）
2. 原始PDF文件列表
"""

from db.database import get_db
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any, Optional


class StatementDetailService:
    """月度账单详情服务"""
    
    SUPPLIER_LIST = ['7SL', 'DINAS', 'RAUB SYC HAINAN', 'AI SMART TECH', 
                     'HUAWEI', 'PASAR RAYA', 'PUCHONG HERBS']
    
    def __init__(self):
        self.base_dir = Path('credit_card_files')
    
    def get_monthly_detail(self, customer_id: int, year_month: str) -> Optional[Dict[str, Any]]:
        """
        获取指定月份的详细计算数据
        
        Args:
            customer_id: 客户ID
            year_month: 年月 (格式: YYYY-MM, 例如: 2024-09)
        
        Returns:
            包含计算详情和PDF列表的字典，如果没有数据则返回None
        """
        
        # 1. 获取客户信息
        customer = self._get_customer_info(customer_id)
        if not customer:
            return None
        
        # 2. 获取该月的所有银行账单
        monthly_statements = self._get_monthly_statements(customer_id, year_month)
        if not monthly_statements:
            return None
        
        # 3. 获取该月的所有交易
        transactions = self._get_monthly_transactions(customer_id, year_month)
        
        # 4. 计算统计数据
        statistics = self._calculate_monthly_statistics(monthly_statements, transactions)
        
        # 5. 获取Supplier明细
        supplier_breakdown = self._get_supplier_breakdown(transactions)
        
        # 6. 获取原始PDF文件
        source_pdfs = self._get_source_pdfs(customer['name'], year_month)
        
        return {
            'customer': customer,
            'year_month': year_month,
            'monthly_statements': monthly_statements,
            'transactions': transactions,
            'statistics': statistics,
            'supplier_breakdown': supplier_breakdown,
            'source_pdfs': source_pdfs
        }
    
    def _get_customer_info(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """获取客户信息"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, customer_code FROM customers WHERE id = ?",
                (customer_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return {
                'id': row[0],
                'name': row[1],
                'customer_code': row[2]
            }
    
    def _get_monthly_statements(self, customer_id: int, year_month: str) -> List[Dict[str, Any]]:
        """获取指定月份的所有银行账单"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id,
                    bank_name,
                    statement_month,
                    previous_balance_total,
                    closing_balance_total,
                    owner_expenses,
                    owner_payments,
                    gz_expenses,
                    gz_payments,
                    transaction_count
                FROM monthly_statements
                WHERE customer_id = ? AND statement_month = ?
                ORDER BY bank_name
            """, (customer_id, year_month))
            
            rows = cursor.fetchall()
            
            return [{
                'id': row[0],
                'bank_name': row[1],
                'statement_month': row[2],
                'previous_balance': float(row[3] or 0),
                'closing_balance': float(row[4] or 0),
                'owner_expenses': float(row[5] or 0),
                'owner_payments': float(row[6] or 0),
                'gz_expenses': float(row[7] or 0),
                'gz_payments': float(row[8] or 0),
                'transaction_count': row[9] or 0
            } for row in rows]
    
    def _get_monthly_transactions(self, customer_id: int, year_month: str) -> List[Dict[str, Any]]:
        """获取指定月份的所有交易"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    t.id,
                    t.transaction_date,
                    t.description,
                    t.amount,
                    t.category,
                    ms.bank_name
                FROM transactions t
                JOIN monthly_statements ms ON t.monthly_statement_id = ms.id
                WHERE ms.customer_id = ? AND ms.statement_month = ?
                ORDER BY t.transaction_date, t.id
            """, (customer_id, year_month))
            
            rows = cursor.fetchall()
            
            return [{
                'id': row[0],
                'transaction_date': row[1],
                'description': row[2],
                'amount': float(row[3] or 0),
                'category': row[4] or 'UNCATEGORIZED',
                'bank_name': row[5]
            } for row in rows]
    
    def _calculate_monthly_statistics(self, statements: List[Dict], transactions: List[Dict]) -> Dict[str, Any]:
        """计算月度统计数据"""
        
        # 汇总所有银行数据
        total_previous_balance = sum(s['previous_balance'] for s in statements)
        total_closing_balance = sum(s['closing_balance'] for s in statements)
        total_owner_expenses = sum(s['owner_expenses'] for s in statements)
        total_owner_payments = sum(s['owner_payments'] for s in statements)
        total_gz_expenses = sum(s['gz_expenses'] for s in statements)
        total_gz_payments = sum(s['gz_payments'] for s in statements)
        total_transactions = sum(s['transaction_count'] for s in statements)
        
        # 按分类统计交易
        category_breakdown = {}
        for txn in transactions:
            category = txn['category']
            if category not in category_breakdown:
                category_breakdown[category] = {
                    'count': 0,
                    'total_amount': 0
                }
            category_breakdown[category]['count'] += 1
            category_breakdown[category]['total_amount'] += txn['amount']
        
        # 计算1% Management Fee (基于GZ Expenses)
        management_fee = total_gz_expenses * 0.01
        
        # 计算GZ Outstanding Balance
        gz_outstanding = total_previous_balance + total_gz_expenses - total_gz_payments + management_fee
        
        return {
            'total_previous_balance': total_previous_balance,
            'total_closing_balance': total_closing_balance,
            'total_owner_expenses': total_owner_expenses,
            'total_owner_payments': total_owner_payments,
            'total_gz_expenses': total_gz_expenses,
            'total_gz_payments': total_gz_payments,
            'total_transactions': total_transactions,
            'management_fee': management_fee,
            'gz_outstanding_balance': gz_outstanding,
            'category_breakdown': category_breakdown,
            'bank_count': len(statements)
        }
    
    def _get_supplier_breakdown(self, transactions: List[Dict]) -> Dict[str, Any]:
        """获取Supplier明细（7家公司）"""
        
        supplier_data = {}
        
        for supplier in self.SUPPLIER_LIST:
            supplier_txns = [
                txn for txn in transactions 
                if supplier.lower() in txn['description'].lower()
            ]
            
            if supplier_txns:
                supplier_data[supplier] = {
                    'count': len(supplier_txns),
                    'total_amount': sum(txn['amount'] for txn in supplier_txns),
                    'transactions': supplier_txns
                }
        
        return supplier_data
    
    def _get_source_pdfs(self, customer_name: str, year_month: str) -> List[Dict[str, Any]]:
        """获取该月的原始PDF文件"""
        
        customer_dir = self.base_dir / customer_name / 'source_pdfs'
        
        if not customer_dir.exists():
            return []
        
        pdf_files = []
        
        # 查找该月的所有PDF文件（文件名包含年月，例如：2024-09_Alliance_Bank.pdf）
        for pdf_file in customer_dir.glob(f'{year_month}*.pdf'):
            file_stats = pdf_file.stat()
            pdf_files.append({
                'filename': pdf_file.name,
                'path': str(pdf_file),
                'size': file_stats.st_size,
                'size_mb': round(file_stats.st_size / (1024 * 1024), 2),
                'modified_time': file_stats.st_mtime
            })
        
        # 按文件名排序
        pdf_files.sort(key=lambda x: x['filename'])
        
        return pdf_files
