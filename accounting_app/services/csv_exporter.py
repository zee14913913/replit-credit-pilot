"""
CSV导出服务
支持多种会计软件格式的分录导出
集成TemplateEngine实现表驱动导出
"""
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from datetime import date, datetime
from decimal import Decimal
import csv
import io
import logging

from ..models import ExportTemplate
from .template_engine import TemplateEngine

logger = logging.getLogger(__name__)


class CSVExporter:
    """
    CSV分录导出器
    
    支持的模板：
    - 数据库动态模板（推荐）：通过TemplateEngine使用export_templates表
    - 硬编码模板（兼容）：generic_v1, sqlacc_v1, autocount_v1
    """
    
    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id
        self.template_engine = TemplateEngine(db, company_id)
    
    def export_journal_entries(
        self,
        period: str,  # 'YYYY-MM'
        template_id: Optional[int] = None,
        template_name: Optional[str] = None,
        output_format: str = 'string'  # 'string' or 'bytes'
    ) -> Union[str, bytes]:
        """
        导出会计分录为CSV（表驱动化）
        
        Args:
            period: 期间（例如: '2025-08'）
            template_id: 模板ID（优先使用）
            template_name: 模板名称（fallback兼容旧系统）
            output_format: 输出格式 ('string' 或 'bytes')
        
        Returns:
            CSV字符串或bytes
        """
        logger.info(f"导出CSV: company_id={self.company_id}, period={period}, template_id={template_id}, template_name={template_name}")
        
        # 1. 获取模板（优先数据库模板）
        if template_id:
            template_obj = self.db.query(ExportTemplate).filter(
                ExportTemplate.id == template_id,
                ExportTemplate.company_id == self.company_id,
                ExportTemplate.is_active == True
            ).first()
            
            if not template_obj:
                raise ValueError(f"模板ID {template_id} 不存在或已禁用")
            
            # 2. 获取分录数据
            entries = self._get_journal_entries(period)
            
            # 3. 使用TemplateEngine生成CSV
            csv_output = self.template_engine.apply_template(template_obj, entries)
            
            # 4. 更新使用统计
            self.template_engine.update_usage_stats(template_id)
            
        else:
            # Fallback: 使用旧的硬编码模板系统
            template = self._get_template(template_name or 'generic_v1')
            if not template:
                raise ValueError(f"模板 {template_name} 不存在")
            
            entries = self._get_journal_entries(period)
            rows = self._transform_to_template(entries, template)
            csv_output = self._generate_csv(rows, template)
            encoding = template.get('encoding', 'UTF-8')
        
            if output_format == 'bytes':
                return csv_output.encode(encoding)
            else:
                return csv_output
        
        # For template_id path
        if output_format == 'bytes':
            encoding_str: str = str(template_obj.encoding) if template_obj.encoding is not None else 'utf-8'
            return csv_output.encode(encoding_str)
        else:
            return csv_output
    
    def _get_journal_entries(self, period: str) -> List[Dict[str, Any]]:
        """
        获取指定期间的会计分录
        
        Args:
            period: 'YYYY-MM'
        
        Returns:
            分录数据列表（字典格式）
        """
        from ..models import JournalEntry, JournalEntryLine, ChartOfAccounts
        
        # 解析期间
        year, month = map(int, period.split('-'))
        
        # 查询分录
        query = self.db.query(
            JournalEntryLine,
            JournalEntry,
            ChartOfAccounts
        ).join(
            JournalEntry, JournalEntryLine.entry_id == JournalEntry.id
        ).join(
            ChartOfAccounts, JournalEntryLine.account_code == ChartOfAccounts.account_code
        ).filter(
            JournalEntry.company_id == self.company_id,
            JournalEntry.entry_date.between(
                date(year, month, 1),
                date(year, month, 28 if month == 2 else 30 if month in [4, 6, 9, 11] else 31)
            )
        ).order_by(JournalEntry.entry_date, JournalEntry.id, JournalEntryLine.line_number)
        
        # 转换为字典列表
        entries = []
        for line, entry, account in query.all():
            entries.append({
                'entry_number': entry.entry_number,
                'entry_date': entry.entry_date,
                'account_code': line.account_code,
                'account_name': account.account_name,
                'description': line.description or entry.description,
                'debit_amount': float(line.debit_amount) if line.debit_amount else 0,
                'credit_amount': float(line.credit_amount) if line.credit_amount else 0,
                'reference_number': entry.reference_number,
                'entry_type': entry.entry_type
            })
        
        logger.info(f"查询到 {len(entries)} 条分录")
        return entries
    
    def _get_template(self, template_name: str) -> Optional[Dict]:
        """
        从数据库获取模板配置（兼容旧系统）
        
        如果数据库中没有，使用内置模板
        """
        # 尝试从数据库获取
        db_template = self.db.query(ExportTemplate).filter(
            ExportTemplate.company_id == self.company_id,
            ExportTemplate.template_name == template_name,
            ExportTemplate.is_active == True
        ).first()
        
        if db_template:
            return {
                'columns': list(db_template.column_mappings.keys()),
                'field_mapping': db_template.column_mappings,
                'delimiter': db_template.delimiter,
                'date_format': db_template.date_format,
                'encoding': db_template.encoding
            }
        
        # Fallback: 内置模板
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
            BankStatement.company_id == self.company_id,
            BankStatement.statement_month == period
        )
        
        if bank_name:
            query = query.filter(BankStatement.bank_name == bank_name)
        
        statements = query.all()
        
        # 转换为字典列表
        data = []
        for stmt in statements:
            # 提取值并进行类型转换（避免SQLAlchemy Column类型问题）
            bank_val: str = str(stmt.bank_name) if stmt.bank_name is not None else ''
            account_val: str = str(stmt.account_number) if stmt.account_number is not None else ''
            desc_val: str = str(stmt.description) if stmt.description is not None else ''
            ref_val: str = str(stmt.reference_number) if stmt.reference_number is not None else ''
            # type: ignore用于SQLAlchemy Column类型推断问题
            debit_val: float = float(stmt.debit_amount if stmt.debit_amount is not None else 0)  # type: ignore
            credit_val: float = float(stmt.credit_amount if stmt.credit_amount is not None else 0)  # type: ignore
            balance_val: float = float(stmt.balance if stmt.balance is not None else 0)  # type: ignore
            matched_val: bool = bool(stmt.matched) if stmt.matched is not None else False
            category_val: str = str(stmt.auto_category) if stmt.auto_category is not None else ''
            
            data.append({
                'date': stmt.transaction_date.strftime('%Y-%m-%d'),
                'bank': bank_val,
                'account': account_val,
                'description': desc_val,
                'reference': ref_val,
                'debit': f"{debit_val:.2f}",
                'credit': f"{credit_val:.2f}",
                'balance': f"{balance_val:.2f}" if balance_val != 0.0 else '',
                'matched': 'Yes' if matched_val else 'No',
                'category': category_val
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
    template_id: Optional[int] = None,
    template_name: str = 'generic_v1',
    export_type: str = 'journal'  # 'journal' or 'bank'
) -> Union[str, bytes]:
    """
    便捷函数：导出CSV（支持模板引擎）
    
    使用示例:
    csv_data = export_to_csv(db, company_id=1, period='2025-08', template_id=5)
    csv_data = export_to_csv(db, company_id=1, period='2025-08', template_name='sqlacc_v1')
    """
    exporter = CSVExporter(db, company_id)
    
    if export_type == 'journal':
        return exporter.export_journal_entries(period, template_id, template_name)
    elif export_type == 'bank':
        return exporter.export_bank_statements(period, template_name=template_name)
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
