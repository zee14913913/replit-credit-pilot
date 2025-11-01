"""
补充改进② - DataIntegrityValidator使用示例
Data Integrity Validator Usage Examples

此文件展示如何在报表生成、数据导出等场景中使用DataIntegrityValidator
确保所有数据都有完整的溯源链（Transaction → raw_line_id → raw_document）
"""
from sqlalchemy.orm import Session
from accounting_app.services.data_integrity_validator import DataIntegrityValidator
from accounting_app.models import BankStatementLines, JournalEntryLines, PurchaseInvoice, SalesInvoice


# ========== 示例1：生成银行结单报表时过滤无效数据 ==========

def generate_bank_statement_report(db: Session, company_id: int, statement_ids: list):
    """
    生成银行结单报表（过滤无效数据）
    
    Args:
        db: 数据库会话
        company_id: 公司ID
        statement_ids: 结单ID列表
    
    Returns:
        dict: 报表数据
    """
    # 1. 创建验证器
    validator = DataIntegrityValidator(db, company_id)
    
    # 2. 查询原始数据
    raw_lines = db.query(BankStatementLines).filter(
        BankStatementLines.company_id == company_id,
        BankStatementLines.id.in_(statement_ids)
    ).all()
    
    # 3. 过滤出有效数据（关键步骤）
    valid_lines = validator.filter_valid_records(raw_lines, 'bank_statement_lines')
    
    # 4. 生成报表
    report = {
        'total_records': len(raw_lines),
        'valid_records': len(valid_lines),
        'rejected_records': len(raw_lines) - len(valid_lines),
        'lines': [
            {
                'date': line.transaction_date,
                'description': line.description,
                'amount': line.amount,
                'balance': line.balance,
                'raw_line_id': line.raw_line_id  # 保证有溯源
            }
            for line in valid_lines
        ]
    }
    
    return report


# ========== 示例2：使用查询过滤器自动过滤无效数据 ==========

def get_valid_journal_entries(db: Session, company_id: int, start_date, end_date):
    """
    获取有效的会计分录（自动过滤）
    
    Args:
        db: 数据库会话
        company_id: 公司ID
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        list: 有效的会计分录列表
    """
    # 1. 创建验证器
    validator = DataIntegrityValidator(db, company_id)
    
    # 2. 获取带完整性过滤的查询对象
    query = validator.get_query_with_integrity_filter(JournalEntryLines)
    
    # 3. 添加业务条件
    valid_entries = query.filter(
        JournalEntryLines.company_id == company_id,
        JournalEntryLines.entry_date.between(start_date, end_date)
    ).all()
    
    return valid_entries


# ========== 示例3：验证单条记录 ==========

def validate_purchase_invoice(db: Session, company_id: int, invoice_id: int) -> bool:
    """
    验证单张采购发票的数据完整性
    
    Args:
        db: 数据库会话
        company_id: 公司ID
        invoice_id: 发票ID
    
    Returns:
        bool: True表示数据完整，False表示有问题（已进入异常中心）
    """
    validator = DataIntegrityValidator(db, company_id)
    
    # 验证单条记录（自动创建异常记录）
    is_valid = validator.validate_record_integrity(
        record_id=invoice_id,
        table_name='purchase_invoices',
        auto_create_exception=True
    )
    
    if not is_valid:
        print(f"⚠️ 发票 {invoice_id} 数据不完整，已拦截进入异常中心")
    
    return is_valid


# ========== 示例4：批量导出前验证 ==========

def export_sales_invoices(db: Session, company_id: int, invoice_ids: list):
    """
    导出销售发票（导出前验证数据完整性）
    
    Args:
        db: 数据库会话
        company_id: 公司ID
        invoice_ids: 发票ID列表
    
    Returns:
        dict: 导出结果
    """
    validator = DataIntegrityValidator(db, company_id)
    
    # 查询所有发票
    invoices = db.query(SalesInvoice).filter(
        SalesInvoice.company_id == company_id,
        SalesInvoice.id.in_(invoice_ids)
    ).all()
    
    # 过滤有效数据
    valid_invoices = validator.filter_valid_records(invoices, 'sales_invoices')
    
    # 统计结果
    result = {
        'requested_count': len(invoice_ids),
        'valid_count': len(valid_invoices),
        'rejected_count': len(invoices) - len(valid_invoices),
        'exported_invoices': [
            {
                'invoice_no': inv.invoice_no,
                'customer': inv.customer_name,
                'amount': inv.total_amount,
                'date': inv.invoice_date,
                'source_verified': True  # 保证有raw_line_id溯源
            }
            for inv in valid_invoices
        ]
    }
    
    return result


# ========== 示例5：装饰器模式（推荐） ==========

from accounting_app.services.data_integrity_validator import require_data_integrity

@require_data_integrity('bank_statement_lines')
def generate_monthly_report(
    db: Session, 
    company_id: int, 
    month: str,
    integrity_validator=None  # 装饰器会注入此参数
):
    """
    生成月度报表（使用装饰器自动注入验证器）
    
    Args:
        db: 数据库会话
        company_id: 公司ID
        month: 月份（如'2025-11'）
        integrity_validator: 装饰器自动注入的验证器
    
    Returns:
        dict: 月度报表
    """
    # 1. 直接使用注入的验证器
    query = integrity_validator.get_query_with_integrity_filter(BankStatementLines)
    
    # 2. 添加业务条件
    monthly_lines = query.filter(
        BankStatementLines.company_id == company_id,
        BankStatementLines.transaction_date.like(f"{month}%")
    ).all()
    
    # 3. 生成报表（所有数据都是验证过的）
    report = {
        'month': month,
        'total_transactions': len(monthly_lines),
        'total_amount': sum(line.amount for line in monthly_lines),
        'data_integrity': '100% verified'  # 保证所有数据都有溯源
    }
    
    return report


# ========== 最佳实践总结 ==========

"""
1. **报表生成必须过滤**
   - 使用 filter_valid_records() 过滤查询结果
   - 使用 get_query_with_integrity_filter() 自动过滤查询
   
2. **导出前必须验证**
   - 批量导出前先过滤无效数据
   - 返回时明确告知用户拦截了多少条记录
   
3. **单条记录操作**
   - 使用 validate_record_integrity() 验证单条
   - 开启 auto_create_exception=True 自动进入异常中心
   
4. **推荐装饰器模式**
   - 使用 @require_data_integrity 装饰器
   - 自动注入验证器，简化代码
   
5. **异常处理**
   - 所有违规数据自动进入异常中心
   - 业务代码无需手动处理异常记录
"""
