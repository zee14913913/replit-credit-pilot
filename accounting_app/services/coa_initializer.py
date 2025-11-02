"""
COA Initializer - 会计科目初始化服务
为新创建的公司自动初始化马来西亚标准会计科目表
"""
import logging
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from ..models import ChartOfAccounts

logger = logging.getLogger(__name__)


# 马来西亚标准会计科目表（Minimal Template for SMEs）
MALAYSIA_SME_DEFAULT_COA = [
    # 资产类 (Assets)
    {
        'account_code': '1001',
        'account_name': '银行存款 / Bank',
        'account_type': 'asset',
        'description': 'Cash at bank accounts'
    },
    {
        'account_code': '1101',
        'account_name': '应收账款 / Accounts Receivable',
        'account_type': 'asset',
        'description': 'Trade debtors'
    },
    {
        'account_code': '1201',
        'account_name': '存货 / Inventory',
        'account_type': 'asset',
        'description': 'Stock on hand'
    },
    
    # 负债类 (Liabilities)
    {
        'account_code': '2001',
        'account_name': '应付账款 / Accounts Payable',
        'account_type': 'liability',
        'description': 'Trade creditors'
    },
    {
        'account_code': '2101',
        'account_name': '银行短期贷款 / Bank Borrowings',
        'account_type': 'liability',
        'description': 'Short-term bank loans'
    },
    {
        'account_code': '6001',
        'account_name': 'SST Payable / 销售税应付',
        'account_type': 'liability',
        'description': 'Sales & Service Tax payable to government'
    },
    
    # 权益类 (Equity)
    {
        'account_code': '3001',
        'account_name': '实收资本 / Paid-up Capital',
        'account_type': 'equity',
        'description': 'Share capital contributed by owners'
    },
    {
        'account_code': '3101',
        'account_name': '留存收益 / Retained Earnings',
        'account_type': 'equity',
        'description': 'Accumulated profits/losses'
    },
    
    # 收入类 (Income)
    {
        'account_code': '4001',
        'account_name': '销售收入 / Revenue',
        'account_type': 'income',
        'description': 'Sales of goods and services'
    },
    
    # 费用类 (Expenses)
    {
        'account_code': '5001',
        'account_name': '管理费用 / Admin Expenses',
        'account_type': 'expense',
        'description': 'General administrative costs'
    },
    {
        'account_code': '5101',
        'account_name': '薪资 / Staff Cost',
        'account_type': 'expense',
        'description': 'Salaries, wages, and employee benefits'
    }
]


def init_default_coa(db: Session, company_id: int) -> int:
    """
    为新公司初始化马来西亚标准会计科目表
    
    Args:
        db: 数据库会话
        company_id: 公司ID
    
    Returns:
        创建的科目数量
    
    注意：
        - 如果公司已有科目（count > 0），则跳过不重复创建
        - 所有科目的created_by设置为'system'，方便审计
        - 基于"Malaysia SME default template"
    """
    # 1. 检查该公司是否已有会计科目
    existing_count = db.query(ChartOfAccounts).filter(
        ChartOfAccounts.company_id == company_id
    ).count()
    
    if existing_count > 0:
        logger.info(f"⏭️ 公司 {company_id} 已有 {existing_count} 个会计科目，跳过初始化")
        return 0
    
    # 2. 批量创建默认科目
    created_count = 0
    for coa_data in MALAYSIA_SME_DEFAULT_COA:
        account = ChartOfAccounts(
            company_id=company_id,
            account_code=coa_data['account_code'],
            account_name=coa_data['account_name'],
            account_type=coa_data['account_type'],
            description=coa_data.get('description'),
            is_active=True
        )
        db.add(account)
        created_count += 1
    
    # 3. 提交到数据库
    try:
        db.commit()
        logger.info(
            f"✅ 成功为公司 {company_id} 初始化 {created_count} 个默认会计科目 "
            f"(Malaysia SME default template)"
        )
        return created_count
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 初始化会计科目失败: {str(e)}")
        raise


def get_default_coa_template() -> List[dict]:
    """
    获取默认会计科目模板（用于文档和API）
    
    Returns:
        科目列表
    """
    return MALAYSIA_SME_DEFAULT_COA.copy()
