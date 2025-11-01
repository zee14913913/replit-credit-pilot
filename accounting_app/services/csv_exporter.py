"""
CSV导出服务
支持多种会计软件格式的分录导出
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import date, datetime
from decimal import Decimal
import csv
import io
import logging

logger = logging.getLogger(__name__)


class CSVExporter:
    """
    CSV分录导出器
    
    支持的模板：
    - generic_v1: 通用格式
    - sqlacc_v1: SQL Account格式
    - autocount_v1: AutoCount格式
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def export_journal_entries(
        self,
        company_id: int,
        period: str,  # 'YYYY-MM'
        template_name: str = 'generic_v1',
        output_format: str = 'string'  # 'string' or 'bytes'
    ) -> Any:
        """
        导出会计分录为CSV
        
        Args:
            company_id: 公司ID
            period: 期间（例如: '2025-08'）
            template_name: 模板名称（generic_v1, sqlacc_v1, autocount_v1）
            output_format: 输出格式 ('string' 或 'bytes')
        
        Returns:
            CSV字符串或bytes
        """
        logger.info(f"导出CSV: company_id={company_id}, period={period}, template={template_name}")
        
        # 1. 获取模板配置
        template = self._get_template(template_name)
        if not template:
            raise ValueError(f"模板 {template_name} 不存在")
        
        # 2. 获取分录数据
        entries = self._get_journal_entries(company_id, period)
        
        # 3. 转换为模板格式
        rows = self._transform_to_template(entries, template)
        
        # 4. 生成CSV
        csv_output = self._generate_csv(rows, template)
        
        if output_format == 'bytes':
            return csv_output.encode(template.get('encoding', 'UTF-8'))
        else:
            return csv_output
    
    def _get_template(self, template_name: str) -> Optional[Dict]:
        """
        从数据库获取模板配置
        
        如果数据库中没有，使用内置模板
        """
        # TODO: 从export_templates表中查询
        # 目前使用内置模板
        
        built_in_templates = {
            'generic_v1': {
                'columns': ['date', 'account_code', 'description', 'debit', 'credit', 'reference'],
                'column_mapping': {
                    'date': 'entry_date',
                    'account_code': 'account_code',
                    'description': 'description',
                    'debit': 'debit_amount',
                    'credit': 'credit_amount',
                    'reference': 'reference_no'
                },
                'date_format': '%Y-%m-%d',
                'decimal_places': 2,
                'delimiter': ',',
                'encoding': 'UTF-8',
                'include_header': True
            },
            'sqlacc_v1': {
                'columns': ['Date', 'Account', 'Description', 'Debit', 'Credit', 'Ref'],
                'column_mapping': {
                    'Date': 'entry_date',
                    'Account': 'account_code',
                    'Description': 'description',
                    'Debit': 'debit_amount',
                    'Credit': 'credit_amount',
                    'Ref': 'reference_no'
                },
                'date_format': '%d/%m/%Y',  # SQL Account使用DD/MM/YYYY
                'decimal_places': 2,
                'delimiter': ',',
                'encoding': 'UTF-8',
                'include_header': True
            },
            'autocount_v1': {
                'columns': ['DocDate', 'AccNo', 'Description', 'DrAmt', 'CrAmt', 'DocNo'],
                'column_mapping': {
                    'DocDate': 'entry_date',
                    'AccNo': 'account_code',
                    'Description': 'description',
                    'DrAmt': 'debit_amount',
                    'CrAmt': 'credit_amount',
                    'DocNo': 'reference_no'
                },
                'date_format': '%d/%m/%Y',
                'decimal_places': 2,
                'delimiter': ',',
                'encoding': 'UTF-8',
                'include_header': True
            }
        }
        
        return built_in_templates.get(template_name)
    
    def _get_journal_entries(self, company_id: int, period: str) -> List[Dict]:
        """
        获取指定期间的会计分录
        
        Returns:
            分录列表，每个分录包含借贷行
        """
        from ..models import JournalEntry, JournalEntryLine, ChartOfAccounts
        
        # 解析期间
        year, month = map(int, period.split('-'))
        period_start = date(year, month, 1)
        if month == 12:
            period_end = date(year + 1, 1, 1)
        else:
            period_end = date(year, month + 1, 1)
        
        # 查询分录
        journal_entries = self.db.query(JournalEntry).filter(
            JournalEntry.company_id == company_id,
            JournalEntry.entry_date >= period_start,
            JournalEntry.entry_date < period_end
        ).all()
        
        result = []
        
        for entry in journal_entries:
            # 获取分录行
            lines = self.db.query(JournalEntryLine).filter(
                JournalEntryLine.journal_entry_id == entry.id
            ).all()
            
            for line in lines:
                # 获取会计科目
                account = self.db.query(ChartOfAccounts).filter(
                    ChartOfAccounts.id == line.account_id
                ).first()
                
                result.append({
                    'entry_date': entry.entry_date,
                    'account_code': account.account_code if account else 'UNKNOWN',
                    'account_name': account.account_name if account else 'Unknown Account',
                    'description': line.description or entry.description,
                    'debit_amount': line.debit_amount if line.debit_amount else Decimal('0.00'),
                    'credit_amount': line.credit_amount if line.credit_amount else Decimal('0.00'),
                    'reference_no': entry.reference_number or ''
                })
        
        return result
    
    def _transform_to_template(self, entries: List[Dict], template: Dict) -> List[Dict]:
        """
        将分录数据转换为模板格式
        """
        column_mapping = template['column_mapping']
        date_format = template['date_format']
        decimal_places = template['decimal_places']
        
        transformed = []
        
        for entry in entries:
            row = {}
            
            for template_col, source_col in column_mapping.items():
                value = entry.get(source_col)
                
                # 格式化日期
                if 'date' in source_col.lower() and isinstance(value, (date, datetime)):
                    row[template_col] = value.strftime(date_format)
                
                # 格式化金额
                elif 'amount' in source_col.lower() and isinstance(value, (Decimal, float, int)):
                    # SQL Account和AutoCount: 如果金额为0，显示空字符串
                    if template.get('columns', [])[0] in ['Date', 'DocDate'] and value == 0:
                        row[template_col] = ''
                    else:
                        row[template_col] = f"{float(value):.{decimal_places}f}"
                
                # 其他字段直接转换
                else:
                    row[template_col] = str(value) if value is not None else ''
            
            transformed.append(row)
        
        return transformed
    
    def _generate_csv(self, rows: List[Dict], template: Dict) -> str:
        """
        生成CSV字符串
        """
        if not rows:
            # 空数据，只返回header
            if template.get('include_header', True):
                return template['delimiter'].join(template['columns']) + '\n'
            else:
                return ''
        
        output = io.StringIO()
        
        columns = template['columns']
        delimiter = template.get('delimiter', ',')
        
        writer = csv.DictWriter(
            output,
            fieldnames=columns,
            delimiter=delimiter,
            quoting=csv.QUOTE_MINIMAL
        )
        
        if template.get('include_header', True):
            writer.writeheader()
        
        for row in rows:
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
    
    def export_bank_statements(
        self,
        company_id: int,
        period: str,
        bank_name: Optional[str] = None,
        template_name: str = 'generic_v1'
    ) -> str:
        """
        导出银行流水为CSV
        
        这是一个额外的功能，导出原始银行流水数据
        """
        from ..models import BankStatement
        
        # 查询银行流水
        query = self.db.query(BankStatement).filter(
            BankStatement.company_id == company_id,
            BankStatement.statement_month == period
        )
        
        if bank_name:
            query = query.filter(BankStatement.bank_name == bank_name)
        
        statements = query.all()
        
        # 转换为字典列表
        data = []
        for stmt in statements:
            data.append({
                'date': stmt.transaction_date.strftime('%Y-%m-%d'),
                'bank': stmt.bank_name,
                'account': stmt.account_number,
                'description': stmt.description,
                'reference': stmt.reference_number or '',
                'debit': f"{float(stmt.debit_amount):.2f}" if stmt.debit_amount else '0.00',
                'credit': f"{float(stmt.credit_amount):.2f}" if stmt.credit_amount else '0.00',
                'balance': f"{float(stmt.balance):.2f}" if stmt.balance else '',
                'matched': 'Yes' if stmt.matched else 'No',
                'category': stmt.auto_category or ''
            })
        
        # 生成CSV
        output = io.StringIO()
        
        # 定义固定的列名（即使没有数据也要输出header）
        fieldnames = ['date', 'bank', 'account', 'description', 'reference', 
                     'debit', 'credit', 'balance', 'matched', 'category']
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        if data:
            writer.writerows(data)
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content


# ========== 便捷函数 ==========

def export_to_csv(
    db: Session,
    company_id: int,
    period: str,
    template_name: str = 'generic_v1',
    export_type: str = 'journal'  # 'journal' or 'bank'
) -> str:
    """
    便捷函数：导出CSV
    
    使用示例:
    csv_data = export_to_csv(db, company_id=1, period='2025-08', template_name='sqlacc_v1')
    """
    exporter = CSVExporter(db)
    
    if export_type == 'journal':
        return exporter.export_journal_entries(company_id, period, template_name)
    elif export_type == 'bank':
        return exporter.export_bank_statements(company_id, period, template_name=template_name)
    else:
        raise ValueError(f"不支持的导出类型: {export_type}")


# ========== 使用示例 ==========

"""
在路由中使用:

from accounting_app.services.csv_exporter import export_to_csv

@router.get("/export/journal/csv")
def export_journal_csv(
    period: str,
    template: str = 'generic_v1',
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    csv_data = export_to_csv(db, company_id, period, template, export_type='journal')
    
    return Response(
        content=csv_data,
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="journal_{period}.csv"'}
    )
"""
