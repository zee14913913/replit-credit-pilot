"""
POS日报处理服务

功能：
1. 解析POS日报（CSV/Excel/PDF）
2. 智能客户匹配
3. 自动生成销售发票
4. 生成会计分录（DR: AR/Bank, CR: Sales Revenue）
5. 更新AR Aging
"""
import re
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from ..models import (
    POSReport, POSTransaction, Customer, SalesInvoice, 
    ChartOfAccounts, JournalEntry, JournalEntryLine
)
from .pdf_parser import PDFParser

logger = logging.getLogger(__name__)


class POSProcessor:
    """POS日报处理器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.pdf_parser = PDFParser()
    
    def process_pos_file(
        self,
        company_id: int,
        file_content: bytes,
        file_name: str,
        auto_generate_invoices: bool = True
    ) -> Dict:
        """
        处理POS文件（主入口）
        
        流程：
        1. 解析文件内容
        2. 检测重复
        3. 创建POS Report记录
        4. 创建POS Transaction记录
        5. 自动匹配客户
        6. 生成销售发票（可选）
        7. 生成会计分录
        8. 更新AR Aging
        """
        try:
            # 1. 确定文件类型
            file_type = self._determine_file_type(file_name)
            
            # 2. 解析文件内容
            parsed_data = self._parse_pos_content(file_content, file_type)
            
            if not parsed_data["success"]:
                return {
                    "success": False,
                    "error": "POS文件解析失败",
                    "details": parsed_data
                }
            
            # 3. 检测重复（基于report_date + total_sales + company_id）
            duplicate_check = self._check_duplicate_report(
                company_id,
                parsed_data.get("report_date"),
                parsed_data.get("total_sales")
            )
            
            if duplicate_check["is_duplicate"]:
                logger.warning(f"检测到重复POS报表: {parsed_data.get('report_date')}")
                return {
                    "success": False,
                    "error": "重复的POS报表",
                    "duplicate_check": duplicate_check
                }
            
            # 4. 创建POS Report
            pos_report = self._create_pos_report(
                company_id=company_id,
                report_data=parsed_data,
                file_name=file_name
            )
            
            # 5. 创建POS Transactions
            transactions = parsed_data.get("transactions", [])
            created_transactions = []
            
            for txn_data in transactions:
                # 智能客户匹配
                customer = self._match_customer(company_id, txn_data.get("customer_name"))
                
                txn = self._create_pos_transaction(
                    pos_report_id=pos_report.id,
                    company_id=company_id,
                    customer_id=customer.id if customer else None,
                    transaction_data=txn_data
                )
                created_transactions.append(txn)
            
            # 6. 自动生成销售发票（如果启用）
            generated_invoices = []
            if auto_generate_invoices:
                for txn in created_transactions:
                    if txn.customer_id:  # 只为匹配到客户的交易生成发票
                        invoice = self._generate_sales_invoice(txn)
                        if invoice:
                            generated_invoices.append(invoice)
                            txn.sales_invoice_id = invoice.id
                            txn.matched = True
                
                # 更新POS Report状态
                pos_report.auto_generated_invoices = True
            
            # 7. 提交事务
            self.db.commit()
            
            logger.info(f"POS报表处理成功: report_id={pos_report.id}, {len(created_transactions)}笔交易")
            
            return {
                "success": True,
                "pos_report_id": pos_report.id,
                "report_number": pos_report.report_number,
                "report_date": pos_report.report_date.isoformat(),
                "total_sales": float(pos_report.total_sales),
                "total_transactions": len(created_transactions),
                "generated_invoices": len(generated_invoices),
                "matched_customers": sum(1 for t in created_transactions if t.customer_id),
                "unmatched_transactions": sum(1 for t in created_transactions if not t.customer_id),
                "parsed_data": parsed_data
            }
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"POS文件处理失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": "POS文件处理失败",
                "details": str(e)
            }
    
    def _determine_file_type(self, file_name: str) -> str:
        """确定文件类型"""
        ext = file_name.lower().split('.')[-1]
        
        if ext == 'pdf':
            return 'pdf'
        elif ext in ['xlsx', 'xls', 'csv']:
            return 'excel'
        else:
            return 'unknown'
    
    def _parse_pos_content(self, file_content: bytes, file_type: str) -> Dict:
        """
        解析POS文件内容
        
        支持：CSV, Excel, PDF
        """
        if file_type == 'pdf':
            # PDF解析（使用PDFParser）
            try:
                # 保存临时文件
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    tmp.write(file_content)
                    tmp_path = tmp.name
                
                # 使用PDFParser解析
                result = self.pdf_parser.extract_pos_report(tmp_path)
                
                # 删除临时文件
                os.unlink(tmp_path)
                
                return result
                
            except Exception as e:
                logger.error(f"PDF解析失败: {str(e)}")
                return {
                    "success": False,
                    "error": f"PDF解析失败: {str(e)}"
                }
        
        elif file_type == 'excel':
            # Excel/CSV解析
            try:
                import io
                import pandas as pd
                
                # 智能判断文件类型
                if file_content.startswith(b'PK'):
                    df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
                elif file_content.startswith(b'\xd0\xcf\x11\xe0'):
                    df = pd.read_excel(io.BytesIO(file_content), engine='xlrd')
                else:
                    df = pd.read_csv(io.BytesIO(file_content))
                
                # 提取POS数据
                extracted_data = self._extract_from_dataframe(df)
                return {
                    "success": True,
                    "stage": "excel_parsed",
                    **extracted_data
                }
                
            except Exception as e:
                logger.error(f"Excel解析失败: {str(e)}")
                return {
                    "success": False,
                    "error": f"Excel解析失败: {str(e)}"
                }
        
        else:
            return {
                "success": False,
                "error": f"不支持的文件类型: {file_type}"
            }
    
    def _extract_from_dataframe(self, df) -> Dict:
        """
        从DataFrame中提取POS数据
        
        智能匹配列名：
        - 日期：date, report_date, transaction_date
        - 客户：customer, customer_name, client
        - 金额：amount, total, sales
        - 支付方式：payment_method, payment_type
        """
        import pandas as pd
        
        # 标准化列名
        df.columns = [str(col).lower().strip() for col in df.columns]
        
        extracted = {
            "report_date": date.today(),
            "total_sales": Decimal('0.00'),
            "total_transactions": 0,
            "payment_method": "mixed",
            "transactions": []
        }
        
        # 列名映射
        date_cols = ['date', 'report_date', 'transaction_date', 'time', 'datetime']
        customer_cols = ['customer', 'customer_name', 'client', 'name']
        amount_cols = ['amount', 'total', 'sales', 'price', 'value']
        payment_cols = ['payment_method', 'payment_type', 'payment', 'method']
        
        # 查找日期列
        date_col = None
        for col in date_cols:
            if col in df.columns:
                date_col = col
                break
        
        # 查找客户列
        customer_col = None
        for col in customer_cols:
            if col in df.columns:
                customer_col = col
                break
        
        # 查找金额列
        amount_col = None
        for col in amount_cols:
            if col in df.columns:
                amount_col = col
                break
        
        # 查找支付方式列
        payment_col = None
        for col in payment_cols:
            if col in df.columns:
                payment_col = col
                break
        
        # 提取交易
        total_sales = Decimal('0.00')
        transactions = []
        
        for idx, row in df.iterrows():
            try:
                # 提取日期
                txn_date = date.today()
                if date_col and pd.notna(row[date_col]):
                    try:
                        txn_date = pd.to_datetime(row[date_col]).date()
                    except:
                        pass
                
                # 提取金额
                if amount_col and pd.notna(row[amount_col]):
                    amount_str = str(row[amount_col]).replace('RM', '').replace(',', '').strip()
                    amount = Decimal(amount_str)
                else:
                    continue  # 跳过没有金额的行
                
                # 提取客户名
                customer_name = None
                if customer_col and pd.notna(row[customer_col]):
                    customer_name = str(row[customer_col]).strip()
                
                # 提取支付方式
                payment_method = "cash"
                if payment_col and pd.notna(row[payment_col]):
                    payment_method = str(row[payment_col]).strip().lower()
                
                # 创建交易记录
                transactions.append({
                    "transaction_time": datetime.combine(txn_date, datetime.min.time()),
                    "transaction_amount": amount,
                    "customer_name": customer_name,
                    "payment_method": payment_method
                })
                
                total_sales += amount
                
                # 设置报表日期为第一笔交易日期
                if len(transactions) == 1:
                    extracted["report_date"] = txn_date
            
            except Exception as e:
                logger.warning(f"跳过第{idx+1}行：{str(e)}")
                continue
        
        extracted["total_sales"] = total_sales
        extracted["total_transactions"] = len(transactions)
        extracted["transactions"] = transactions
        
        return extracted
    
    def _check_duplicate_report(
        self,
        company_id: int,
        report_date: Optional[date],
        total_sales: Optional[Decimal]
    ) -> Dict:
        """
        检测重复POS报表
        
        规则：相同公司 + 相同日期 + 相同金额 = 重复
        """
        if not report_date or not total_sales:
            return {"is_duplicate": False}
        
        existing = self.db.query(POSReport).filter(
            POSReport.company_id == company_id,
            POSReport.report_date == report_date,
            POSReport.total_sales == total_sales
        ).first()
        
        if existing:
            return {
                "is_duplicate": True,
                "existing_report_id": existing.id,
                "existing_report_number": existing.report_number,
                "existing_report_date": existing.report_date.isoformat(),
                "message": f"已存在相同日期和金额的POS报表 (ID: {existing.id})"
            }
        
        return {"is_duplicate": False}
    
    def _create_pos_report(
        self,
        company_id: int,
        report_data: Dict,
        file_name: str
    ) -> POSReport:
        """创建POS报表记录"""
        report_number = self._generate_report_number(company_id, report_data["report_date"])
        
        pos_report = POSReport(
            company_id=company_id,
            report_number=report_number,
            report_date=report_data["report_date"],
            total_sales=report_data["total_sales"],
            total_transactions=report_data.get("total_transactions", 0),
            payment_method=report_data.get("payment_method", "mixed"),
            file_path=file_name,
            parse_status='parsed',
            auto_generated_invoices=False
        )
        
        self.db.add(pos_report)
        self.db.flush()
        self.db.refresh(pos_report)
        
        return pos_report
    
    def _generate_report_number(self, company_id: int, report_date: date) -> str:
        """生成报表编号：POS-YYYYMMDD-0001"""
        date_str = report_date.strftime('%Y%m%d')
        
        # 查询当天已有报表数量
        count = self.db.query(POSReport).filter(
            POSReport.company_id == company_id,
            POSReport.report_date == report_date
        ).count()
        
        return f"POS-{date_str}-{count + 1:04d}"
    
    def _create_pos_transaction(
        self,
        pos_report_id: int,
        company_id: int,
        customer_id: Optional[int],
        transaction_data: Dict
    ) -> POSTransaction:
        """创建POS交易记录"""
        txn = POSTransaction(
            pos_report_id=pos_report_id,
            company_id=company_id,
            customer_id=customer_id,
            transaction_time=transaction_data["transaction_time"],
            transaction_amount=transaction_data["transaction_amount"],
            payment_method=transaction_data.get("payment_method", "cash"),
            customer_name_raw=transaction_data.get("customer_name"),
            matched=False
        )
        
        self.db.add(txn)
        self.db.flush()
        self.db.refresh(txn)
        
        return txn
    
    def _match_customer(self, company_id: int, customer_name: Optional[str]) -> Optional[Customer]:
        """
        智能客户匹配
        
        策略：
        1. 精确匹配客户名
        2. 模糊匹配（去除空格、大小写）
        3. 返回None（需要人工匹配）
        """
        if not customer_name:
            return None
        
        # 策略1：精确匹配
        customer = self.db.query(Customer).filter(
            Customer.company_id == company_id,
            Customer.customer_name == customer_name
        ).first()
        
        if customer:
            return customer
        
        # 策略2：模糊匹配
        normalized_name = customer_name.strip().lower().replace(' ', '')
        
        customers = self.db.query(Customer).filter(
            Customer.company_id == company_id,
            Customer.status == 'active'
        ).all()
        
        for cust in customers:
            normalized_db_name = cust.customer_name.strip().lower().replace(' ', '')
            if normalized_db_name == normalized_name:
                return cust
        
        return None
    
    def _generate_sales_invoice(self, transaction: POSTransaction) -> Optional[SalesInvoice]:
        """
        从POS交易生成销售发票
        """
        if not transaction.customer_id:
            return None
        
        try:
            # 生成发票号
            invoice_number = self._generate_invoice_number(
                transaction.company_id,
                transaction.transaction_time.date()
            )
            
            # 创建销售发票
            invoice = SalesInvoice(
                company_id=transaction.company_id,
                customer_id=transaction.customer_id,
                invoice_number=invoice_number,
                invoice_date=transaction.transaction_time.date(),
                due_date=transaction.transaction_time.date() + timedelta(days=30),
                total_amount=transaction.transaction_amount,
                received_amount=Decimal('0.00'),
                balance_amount=transaction.transaction_amount,
                status='unpaid',
                auto_generated=True,
                notes=f"自动生成自POS交易 (Report ID: {transaction.pos_report_id})"
            )
            
            self.db.add(invoice)
            self.db.flush()
            self.db.refresh(invoice)
            
            # 生成会计分录
            journal_entry = self._create_journal_entry_for_invoice(invoice)
            invoice.journal_entry_id = journal_entry.id
            
            # 更新AR aging
            self._update_aging_status(invoice)
            
            logger.info(f"生成销售发票: {invoice_number}, 金额: {invoice.total_amount}")
            
            return invoice
        
        except Exception as e:
            logger.error(f"生成销售发票失败: {str(e)}")
            return None
    
    def _generate_invoice_number(self, company_id: int, invoice_date: date) -> str:
        """生成销售发票号：INV-YYYYMMDD-0001"""
        date_str = invoice_date.strftime('%Y%m%d')
        
        count = self.db.query(SalesInvoice).filter(
            SalesInvoice.company_id == company_id,
            SalesInvoice.invoice_date == invoice_date
        ).count()
        
        return f"INV-{date_str}-{count + 1:04d}"
    
    def _create_journal_entry_for_invoice(self, invoice: SalesInvoice) -> JournalEntry:
        """
        生成会计分录
        
        DR: 应收账款 (Accounts Receivable)
        CR: 销售收入 (Sales Revenue)
        """
        # 获取或创建科目
        ar_account = self._get_or_create_account(
            invoice.company_id,
            "Accounts Receivable",
            "asset"
        )
        
        sales_account = self._get_or_create_account(
            invoice.company_id,
            "Sales Revenue",
            "income"
        )
        
        # 生成分录号
        entry_number = self._generate_journal_entry_number(invoice.company_id)
        
        # 创建分录
        journal_entry = JournalEntry(
            company_id=invoice.company_id,
            entry_number=entry_number,
            entry_date=invoice.invoice_date,
            description=f"销售发票 #{invoice.invoice_number}",
            entry_type='invoice',
            reference_number=invoice.invoice_number,
            status='posted'
        )
        
        self.db.add(journal_entry)
        self.db.flush()
        self.db.refresh(journal_entry)
        
        # 借方：应收账款
        debit_line = JournalEntryLine(
            journal_entry_id=journal_entry.id,
            account_id=ar_account.id,
            description=f"应收账款 - {invoice.invoice_number}",
            debit_amount=invoice.total_amount,
            credit_amount=Decimal('0.00'),
            line_number=1
        )
        
        # 贷方：销售收入
        credit_line = JournalEntryLine(
            journal_entry_id=journal_entry.id,
            account_id=sales_account.id,
            description=f"销售收入 - {invoice.invoice_number}",
            debit_amount=Decimal('0.00'),
            credit_amount=invoice.total_amount,
            line_number=2
        )
        
        self.db.add(debit_line)
        self.db.add(credit_line)
        self.db.flush()
        self.db.refresh(journal_entry)
        
        return journal_entry
    
    def _generate_journal_entry_number(self, company_id: int) -> str:
        """生成会计分录号：JE-YYYYMMDD-0001"""
        today = date.today().strftime('%Y%m%d')
        
        count = self.db.query(JournalEntry).filter(
            JournalEntry.company_id == company_id,
            JournalEntry.entry_number.like(f'JE-{today}-%')
        ).count()
        
        return f"JE-{today}-{count + 1:04d}"
    
    def _get_or_create_account(
        self,
        company_id: int,
        account_name: str,
        account_type: str
    ) -> ChartOfAccounts:
        """获取或创建会计科目"""
        # 查找现有科目
        account = self.db.query(ChartOfAccounts).filter(
            ChartOfAccounts.company_id == company_id,
            ChartOfAccounts.account_name == account_name
        ).first()
        
        if account:
            return account
        
        # 生成科目代码
        prefix_map = {
            'asset': '1',
            'liability': '2',
            'equity': '3',
            'income': '4',
            'expense': '5'
        }
        
        prefix = prefix_map.get(account_type.lower(), '9')
        
        count = self.db.query(ChartOfAccounts).filter(
            ChartOfAccounts.company_id == company_id,
            ChartOfAccounts.account_code.like(f'{prefix}%')
        ).count()
        
        account_code = f"{prefix}{count + 1:03d}"
        
        # 创建新科目
        account = ChartOfAccounts(
            company_id=company_id,
            account_code=account_code,
            account_name=account_name,
            account_type=account_type.lower(),
            is_active=True
        )
        
        self.db.add(account)
        self.db.flush()
        self.db.refresh(account)
        
        return account
    
    def _update_aging_status(self, invoice: SalesInvoice):
        """
        更新AR Aging状态
        
        根据due_date自动更新status：
        - 未到期：unpaid
        - 已逾期：overdue
        """
        if invoice.balance_amount > 0 and invoice.due_date < date.today():
            invoice.status = 'overdue'


# ========== 便捷函数 ==========

def create_pos_processor(db: Session) -> POSProcessor:
    """创建POS处理器实例"""
    return POSProcessor(db)
