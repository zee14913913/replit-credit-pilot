"""
Phase 1: Pydantic Schemas
用于API请求/响应验证和数据传输对象(DTO)
"""

# 从accounting_app/schemas.py重新导出所有内容以保持向后兼容
# 使用importlib动态导入避免循环导入问题
import importlib.util
import sys
from pathlib import Path

# 构建schemas.py的绝对路径
schemas_file = Path(__file__).parent.parent / "schemas.py"

# 动态加载schemas.py模块
spec = importlib.util.spec_from_file_location("old_schemas", schemas_file)
if spec is None or spec.loader is None:
    raise ImportError(f"无法加载schemas.py from {schemas_file}")
old_schemas = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old_schemas)

# 重新导出所有公开的类和函数
for name in dir(old_schemas):
    if not name.startswith('_'):
        globals()[name] = getattr(old_schemas, name)

# 明确列出所有导出
__all__ = [
    'CompanyBase', 'CompanyCreate', 'CompanyResponse',
    'BankStatementImport', 'BankStatementRow', 'BankStatementResponse',
    'ChartOfAccountsCreate', 'ChartOfAccountsResponse',
    'JournalEntryLineCreate', 'JournalEntryCreate', 'JournalEntryResponse',
    'SupplierCreate', 'SupplierResponse',
    'AgingBracket', 'SupplierAgingDetail', 'SuppliersAgingReport',
    'CustomerAgingDetail', 'CustomersAgingReport',
    'CustomerTransactionDetail', 'CustomerLedgerReport',
]
