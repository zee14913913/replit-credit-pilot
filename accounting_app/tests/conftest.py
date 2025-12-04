"""
测试配置和共享fixtures
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import datetime, date
from decimal import Decimal
from types import SimpleNamespace
import logging

from accounting_app.main import app
from accounting_app.db import get_db, Base
from accounting_app.models import Company, BankStatement, JournalEntry, JournalEntryLine, ChartOfAccounts

TEST_DATABASE_URL = "sqlite:///./test_accounting.db"


@pytest.fixture(scope="function")
def test_db():
    """
    创建测试数据库会话
    每个测试函数独立数据库，测试后清理
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        
        if os.path.exists("./test_accounting.db"):
            os.remove("./test_accounting.db")


@pytest.fixture(scope="function")
def client(test_db):
    """
    FastAPI测试客户端
    自动注入测试数据库依赖，并注入一个模拟的已登录用户以避免 401/权限问题。
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db

    fake_user = SimpleNamespace(id=1, username="testuser", role="admin", is_active=True)

    try:
        from accounting_app.middleware.rbac_fixed import get_current_user as _get_current_user_dep
        app.dependency_overrides[_get_current_user_dep] = lambda: fake_user
    except Exception:
        logging.getLogger(__name__).warning("无法覆盖 get_current_user 依赖（可能文件路径不同）")

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_company(test_db):
    """
    创建测试公司数据
    """
    company = Company(
        company_code="TEST001",
        company_name="Test Company Ltd.",
        registration_number="202401234567",
        created_at=datetime.now()
    )
    test_db.add(company)
    test_db.commit()
    test_db.refresh(company)
    return company


@pytest.fixture
def sample_bank_statement(test_db, sample_company):
    """
    创建测试银行月结单记录
    """
    statement = BankStatement(
        company_id=sample_company.id,
        bank_name="Maybank",
        account_number="1234567890",
        statement_month="2025-11",
        transaction_date=date(2025, 11, 15),
        description="Test Transaction",
        debit_amount=Decimal("0.00"),
        credit_amount=Decimal("5000.00"),
        balance=Decimal("15000.00"),
        matched=False,
        created_at=datetime.now()
    )
    test_db.add(statement)
    test_db.commit()
    test_db.refresh(statement)
    return statement


@pytest.fixture
def sample_chart_of_accounts(test_db, sample_company):
    """
    创建测试会计科目
    """
    accounts = [
        ChartOfAccounts(
            company_id=sample_company.id,
            account_code="1100",
            account_name="Bank - Maybank",
            account_type="asset"
        ),
        ChartOfAccounts(
            company_id=sample_company.id,
            account_code="2100",
            account_name="Accounts Payable",
            account_type="liability"
        ),
        ChartOfAccounts(
            company_id=sample_company.id,
            account_code="4100",
            account_name="Sales Revenue",
            account_type="income"
        ),
        ChartOfAccounts(
            company_id=sample_company.id,
            account_code="5100",
            account_name="Operating Expenses",
            account_type="expense"
        ),
    ]
    
    for account in accounts:
        test_db.add(account)
    
    test_db.commit()
    
    for account in accounts:
        test_db.refresh(account)
    
    return accounts


@pytest.fixture
def sample_journal_entry(test_db, sample_company, sample_chart_of_accounts):
    """
    创建测试凭证
    """
    entry = JournalEntry(
        company_id=sample_company.id,
        entry_number="JE-2025-11-0001",
        entry_date=date(2025, 11, 1),
        description="Test Transaction",
        reference_number="JE-001",
        entry_type="manual",
        status="posted",
        created_at=datetime.now()
    )
    test_db.add(entry)
    test_db.flush()
    
    bank_account = next(a for a in sample_chart_of_accounts if a.account_code == "1100")
    revenue_account = next(a for a in sample_chart_of_accounts if a.account_code == "4100")
    
    lines = [
        JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=bank_account.id,
            description="Payment received",
            debit_amount=Decimal("5000.00"),
            credit_amount=Decimal("0.00"),
            line_number=1
        ),
        JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=revenue_account.id,
            description="Sales income",
            debit_amount=Decimal("0.00"),
            credit_amount=Decimal("5000.00"),
            line_number=2
        ),
    ]
    
    for line in lines:
        test_db.add(line)
    
    test_db.commit()
    test_db.refresh(entry)
    
    return entry
