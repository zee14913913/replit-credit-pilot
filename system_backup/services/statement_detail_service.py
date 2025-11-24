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
        获取指定月份的详细计算数据（按银行分组）
        
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
        
        # 6. 按银行分组数据并关联PDF文件
        bank_groups = self._build_bank_groups(customer['customer_code'], year_month, monthly_statements, transactions)
        
        return {
            'customer': customer,
            'year_month': year_month,
            'monthly_statements': monthly_statements,
            'transactions': transactions,
            'statistics': statistics,
            'supplier_breakdown': supplier_breakdown,
            'bank_groups': bank_groups  # 新增：按银行分组的数据
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
        
        # 计算1%刷卡机费用（由OWNER承担，不是GZ管理费）
        # 业务逻辑：用客户信用卡刷卡购物换取现金，1%是银行征收的刷卡机费用
        card_processing_fee = total_gz_expenses * 0.01
        
        # OWNER总欠款 = OWNER消费 + 1%刷卡机费用 - OWNER付款
        owner_outstanding = total_owner_expenses + card_processing_fee - total_owner_payments
        
        # GZ欠款 = GZ消费 - GZ付款（不包含1%费用，因为这是OWNER承担的）
        gz_outstanding = total_gz_expenses - total_gz_payments
        
        return {
            'total_previous_balance': total_previous_balance,
            'total_closing_balance': total_closing_balance,
            'total_owner_expenses': total_owner_expenses,
            'total_owner_payments': total_owner_payments,
            'total_gz_expenses': total_gz_expenses,
            'total_gz_payments': total_gz_payments,
            'total_transactions': total_transactions,
            'card_processing_fee': card_processing_fee,  # 刷卡机费用（OWNER承担）
            'owner_outstanding_balance': owner_outstanding,  # OWNER总欠款
            'gz_outstanding_balance': gz_outstanding,  # GZ欠款（不含1%费用）
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
    
    def _build_bank_groups(self, customer_code: str, year_month: str, 
                          statements: List[Dict], transactions: List[Dict]) -> List[Dict[str, Any]]:
        """
        按银行分组数据并关联原始PDF文件
        
        Returns:
            列表，每个元素包含：
            - bank_name: 银行名称
            - statement: 该银行的月结单数据
            - transactions: 该银行的交易列表
            - credit_card_pdfs: 信用卡账单PDF列表
            - bank_statement_pdf: GZ bank list PDF（如果有）
        """
        bank_groups = []
        
        # 按银行分组
        for statement in statements:
            bank_name = statement['bank_name']
            
            # 过滤该银行的交易
            bank_transactions = [
                txn for txn in transactions 
                if txn['bank_name'] == bank_name
            ]
            
            # 查找该银行的PDF文件
            credit_card_pdfs = self._find_credit_card_pdfs(customer_code, bank_name, year_month)
            bank_statement_pdf = self._find_bank_statement_pdf(customer_code, year_month)
            
            bank_groups.append({
                'bank_name': bank_name,
                'statement': statement,
                'transactions': bank_transactions,
                'credit_card_pdfs': credit_card_pdfs,
                'bank_statement_pdf': bank_statement_pdf
            })
        
        return bank_groups
    
    def _find_credit_card_pdfs(self, customer_code: str, bank_name: str, year_month: str) -> List[Dict[str, Any]]:
        """查找指定银行和月份的信用卡PDF文件"""
        
        # 构建搜索路径（处理银行名称的多种格式）
        upload_base = Path('static/uploads/customers') / customer_code / 'credit_cards'
        
        # 银行名称可能的格式
        bank_variants = [
            bank_name,  # 原始名称，例如: Alliance Bank
            bank_name.replace(' ', '_'),  # 下划线格式，例如: Alliance_Bank
            bank_name.replace(' Bank', ''),  # 去掉Bank，例如: Alliance
            bank_name.upper(),  # 大写，例如: ALLIANCE BANK
            bank_name.upper().replace(' ', '_')  # 大写下划线，例如: ALLIANCE_BANK
        ]
        
        pdf_files = []
        
        for variant in bank_variants:
            search_dir = upload_base / variant / year_month
            if search_dir.exists():
                for pdf_file in search_dir.glob('*.pdf'):
                    file_stats = pdf_file.stat()
                    pdf_files.append({
                        'filename': pdf_file.name,
                        'path': str(pdf_file),
                        'size': file_stats.st_size,
                        'size_mb': round(file_stats.st_size / (1024 * 1024), 2),
                        'modified_time': file_stats.st_mtime
                    })
        
        # 去重（避免找到重复文件）
        seen_filenames = set()
        unique_pdfs = []
        for pdf in pdf_files:
            if pdf['filename'] not in seen_filenames:
                seen_filenames.add(pdf['filename'])
                unique_pdfs.append(pdf)
        
        return sorted(unique_pdfs, key=lambda x: x['filename'])
    
    def _find_bank_statement_pdf(self, customer_code: str, year_month: str) -> Optional[Dict[str, Any]]:
        """查找GZ bank list月结单PDF"""
        
        # GZ bank list通常存放在savings/Public_Bank目录
        search_dir = Path('static/uploads/customers') / customer_code / 'savings' / 'Public_Bank' / year_month
        
        if not search_dir.exists():
            return None
        
        # 查找第一个PDF文件
        for pdf_file in search_dir.glob('*.pdf'):
            file_stats = pdf_file.stat()
            return {
                'filename': pdf_file.name,
                'path': str(pdf_file),
                'size': file_stats.st_size,
                'size_mb': round(file_stats.st_size / (1024 * 1024), 2),
                'modified_time': file_stats.st_mtime
            }
        
        return None
    
    def _get_source_pdfs(self, customer_name: str, year_month: str) -> List[Dict[str, Any]]:
        """获取该月的原始PDF文件（已弃用，使用_build_bank_groups代替）"""
        
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
