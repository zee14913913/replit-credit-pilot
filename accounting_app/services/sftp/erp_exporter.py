"""
ERP 数据导出格式化模块
将数据库中的会计数据格式化为 SQL ACC ERP Edition 可导入的 CSV 格式
"""
import os
import csv
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ...models import (
    JournalEntry, JournalEntryLine, SalesInvoice, PurchaseInvoice,
    BankStatement, POSReport, ChartOfAccounts
)

logger = logging.getLogger(__name__)


class ERPExporter:
    """SQL Account ERP 数据导出器"""
    
    def __init__(self, db_session: Session, company_id: int):
        """
        初始化导出器
        
        Args:
            db_session: 数据库会话
            company_id: 公司ID
        """
        self.db = db_session
        self.company_id = company_id
    
    def export_sales_invoices_to_csv(self, output_path: str, start_date: Optional[str] = None, 
                                     end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        导出销售发票到CSV（SQL Account格式）
        
        Args:
            output_path: 输出文件路径
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
        
        Returns:
            导出结果统计
        """
        try:
            query = self.db.query(SalesInvoice).filter(
                SalesInvoice.company_id == self.company_id
            )
            
            if start_date:
                query = query.filter(SalesInvoice.invoice_date >= start_date)
            if end_date:
                query = query.filter(SalesInvoice.invoice_date <= end_date)
            
            invoices = query.all()
            
            # SQL Account 销售发票格式
            headers = [
                "Invoice No", "Invoice Date", "Customer Code", "Customer Name",
                "Total Amount", "Received Amount", "Balance", "Status", "Due Date"
            ]
            
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
                for inv in invoices:
                    customer = inv.customer if hasattr(inv, 'customer') else None
                    writer.writerow([
                        inv.invoice_number,
                        inv.invoice_date.strftime('%Y-%m-%d') if inv.invoice_date else '',
                        customer.customer_code if customer else '',
                        customer.customer_name if customer else '',
                        float(inv.total_amount) if inv.total_amount else 0.00,
                        float(inv.received_amount) if inv.received_amount else 0.00,
                        float(inv.balance_amount) if inv.balance_amount else 0.00,
                        inv.status or 'unpaid',
                        inv.due_date.strftime('%Y-%m-%d') if inv.due_date else ''
                    ])
            
            logger.info(f"✅ Exported {len(invoices)} sales invoices to {output_path}")
            
            return {
                "success": True,
                "file_path": output_path,
                "record_count": len(invoices),
                "file_size": os.path.getsize(output_path)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to export sales invoices: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def export_journal_entries_to_csv(self, output_path: str, start_date: Optional[str] = None,
                                      end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        导出日记账分录到CSV（SQL Account格式）
        
        Args:
            output_path: 输出文件路径
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            导出结果统计
        """
        try:
            query = self.db.query(JournalEntry).filter(
                JournalEntry.company_id == self.company_id
            )
            
            if start_date:
                query = query.filter(JournalEntry.entry_date >= start_date)
            if end_date:
                query = query.filter(JournalEntry.entry_date <= end_date)
            
            entries = query.all()
            
            # SQL Account Journal Entry格式
            headers = [
                "Entry No", "Entry Date", "Description", "Entry Type",
                "Account Code", "Account Name", "Debit", "Credit", "Line Description"
            ]
            
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
                for entry in entries:
                    # 获取分录明细
                    lines = self.db.query(JournalEntryLine).filter(
                        JournalEntryLine.journal_entry_id == entry.id
                    ).all()
                    
                    for line in lines:
                        account = self.db.query(ChartOfAccounts).filter(
                            ChartOfAccounts.id == line.account_id
                        ).first()
                        
                        writer.writerow([
                            entry.entry_number,
                            entry.entry_date.strftime('%Y-%m-%d') if entry.entry_date else '',
                            entry.description or '',
                            entry.entry_type or 'manual',
                            account.account_code if account else '',
                            account.account_name if account else '',
                            float(line.debit_amount) if line.debit_amount else 0.00,
                            float(line.credit_amount) if line.credit_amount else 0.00,
                            line.description or ''
                        ])
            
            logger.info(f"✅ Exported journal entries to {output_path}")
            
            return {
                "success": True,
                "file_path": output_path,
                "record_count": len(entries),
                "file_size": os.path.getsize(output_path)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to export journal entries: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def export_bank_statements_to_csv(self, output_path: str, statement_month: Optional[str] = None) -> Dict[str, Any]:
        """
        导出银行对账单到CSV
        
        Args:
            output_path: 输出文件路径
            statement_month: 对账单月份（YYYY-MM）
        
        Returns:
            导出结果统计
        """
        try:
            query = self.db.query(BankStatement).filter(
                BankStatement.company_id == self.company_id
            )
            
            if statement_month:
                query = query.filter(BankStatement.statement_month == statement_month)
            
            statements = query.all()
            
            # SQL Account Bank Reconciliation格式
            headers = [
                "Transaction Date", "Description", "Reference No", 
                "Debit", "Credit", "Balance", "Bank Name", "Account Number"
            ]
            
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
                for stmt in statements:
                    writer.writerow([
                        stmt.transaction_date.strftime('%Y-%m-%d') if stmt.transaction_date else '',
                        stmt.description or '',
                        stmt.reference_number or '',
                        float(stmt.debit_amount) if stmt.debit_amount else 0.00,
                        float(stmt.credit_amount) if stmt.credit_amount else 0.00,
                        float(stmt.balance) if stmt.balance else 0.00,
                        stmt.bank_name or '',
                        stmt.account_number or ''
                    ])
            
            logger.info(f"✅ Exported {len(statements)} bank statements to {output_path}")
            
            return {
                "success": True,
                "file_path": output_path,
                "record_count": len(statements),
                "file_size": os.path.getsize(output_path)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to export bank statements: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def export_supplier_invoices_to_csv(self, output_path: str, start_date: Optional[str] = None,
                                        end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        导出供应商发票到CSV
        
        Args:
            output_path: 输出文件路径
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            导出结果统计
        """
        try:
            query = self.db.query(PurchaseInvoice).filter(
                PurchaseInvoice.company_id == self.company_id
            )
            
            if start_date:
                query = query.filter(PurchaseInvoice.invoice_date >= start_date)
            if end_date:
                query = query.filter(PurchaseInvoice.invoice_date <= end_date)
            
            invoices = query.all()
            
            # SQL Account 采购发票格式
            headers = [
                "Invoice No", "Invoice Date", "Supplier Code", "Supplier Name",
                "Total Amount", "Paid Amount", "Balance", "Status", "Due Date"
            ]
            
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
                for inv in invoices:
                    supplier = inv.supplier if hasattr(inv, 'supplier') else None
                    writer.writerow([
                        inv.invoice_number,
                        inv.invoice_date.strftime('%Y-%m-%d') if inv.invoice_date else '',
                        supplier.supplier_code if supplier else '',
                        supplier.supplier_name if supplier else '',
                        float(inv.total_amount) if inv.total_amount else 0.00,
                        float(inv.paid_amount) if inv.paid_amount else 0.00,
                        float(inv.balance_amount) if inv.balance_amount else 0.00,
                        inv.status or 'unpaid',
                        inv.due_date.strftime('%Y-%m-%d') if inv.due_date else ''
                    ])
            
            logger.info(f"✅ Exported {len(invoices)} supplier invoices to {output_path}")
            
            return {
                "success": True,
                "file_path": output_path,
                "record_count": len(invoices),
                "file_size": os.path.getsize(output_path)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to export supplier invoices: {e}")
            return {
                "success": False,
                "error": str(e)
            }
