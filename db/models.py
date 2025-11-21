
"""
Infinite GZ 系统 - SQLAlchemy ORM 模型定义
用于与 db/schema.sql 对应的 Python 对象映射
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class User(Base):
    """用户信息表"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    ic_number = Column(String, unique=True)
    phone = Column(String)
    email = Column(String, unique=True)
    company_name = Column(String)
    role = Column(String, default='customer')
    
    # 财务评估指标
    ctos_score = Column(Integer)
    dsr = Column(Float)
    monthly_income = Column(Float, default=0)
    
    # 系统字段
    password_hash = Column(String)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    credit_cards = relationship('CreditCard', back_populates='user', cascade='all, delete-orphan')
    statements = relationship('Statement', back_populates='user', cascade='all, delete-orphan')
    settlements = relationship('Settlement', back_populates='user', cascade='all, delete-orphan')
    reminders = relationship('Reminder', back_populates='user', cascade='all, delete-orphan')
    contracts = relationship('Contract', back_populates='user', cascade='all, delete-orphan')
    tax_records = relationship('TaxRecord', back_populates='user', cascade='all, delete-orphan')
    
    __table_args__ = (
        CheckConstraint("role IN ('customer', 'admin', 'accountant', 'viewer')"),
        Index('idx_users_email', 'email'),
        Index('idx_users_ic_number', 'ic_number'),
        Index('idx_users_role', 'role'),
    )


class CreditCard(Base):
    """信用卡账户表"""
    __tablename__ = 'credit_cards'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # 卡片信息
    bank_name = Column(String, nullable=False)
    card_number_last4 = Column(String, nullable=False)
    card_full_number = Column(String)
    card_type = Column(String)
    
    # 额度信息
    credit_limit = Column(Float, default=0)
    available_credit = Column(Float, default=0)
    
    # 账单日期配置
    statement_cutoff_day = Column(Integer)
    payment_due_day = Column(Integer)
    min_payment_rate = Column(Float, default=0.05)
    
    # 积分配置
    points_balance = Column(Float, default=0)
    
    # 系统字段
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    user = relationship('User', back_populates='credit_cards')
    statements = relationship('Statement', back_populates='credit_card', cascade='all, delete-orphan')
    monthly_statements = relationship('MonthlyStatement', back_populates='credit_card', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_credit_cards_user', 'user_id'),
        Index('idx_credit_cards_bank', 'bank_name'),
    )


class Statement(Base):
    """账单主表"""
    __tablename__ = 'statements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    card_id = Column(Integer, ForeignKey('credit_cards.id', ondelete='CASCADE'), nullable=False)
    
    # 账单信息
    statement_date = Column(String, nullable=False)
    due_date = Column(String, nullable=False)
    statement_month = Column(String, nullable=False)
    
    # 金额信息
    previous_balance = Column(Float, default=0)
    total_spent = Column(Float, default=0)
    total_payment = Column(Float, default=0)
    total_amount = Column(Float, nullable=False)
    min_payment = Column(Float, nullable=False)
    current_balance = Column(Float, default=0)
    
    # 积分信息
    points_earned = Column(Float, default=0)
    
    # 文件信息
    upload_filename = Column(String)
    file_path = Column(String)
    file_type = Column(String)
    
    # 解析状态
    parse_status = Column(String, default='pending')
    validation_score = Column(Float, default=0)
    inconsistencies = Column(Text)
    
    # 确认状态
    is_confirmed = Column(Integer, default=0)
    confirmed_by = Column(String)
    confirmed_at = Column(DateTime)
    
    # 系统字段
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship('User', back_populates='statements')
    credit_card = relationship('CreditCard', back_populates='statements')
    transactions = relationship('Transaction', back_populates='statement', cascade='all, delete-orphan')
    monthly_statement = relationship('MonthlyStatement', back_populates='statement', uselist=False)
    
    __table_args__ = (
        CheckConstraint("parse_status IN ('pending', 'parsed', 'failed', 'verified')"),
        Index('idx_statements_user', 'user_id'),
        Index('idx_statements_card', 'card_id'),
        Index('idx_statements_month', 'statement_month'),
        Index('idx_statements_status', 'parse_status'),
    )


class Transaction(Base):
    """交易明细表"""
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    statement_id = Column(Integer, ForeignKey('statements.id', ondelete='CASCADE'), nullable=False)
    
    # 交易信息
    transaction_date = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    merchant = Column(String)
    
    # 金额信息
    debit_amount = Column(Float, default=0)
    credit_amount = Column(Float, default=0)
    
    # Infinite GZ 分类核心字段
    classification = Column(String)  # Owner/GZ
    transaction_type = Column(String)  # Expense/Payment
    
    # 详细分类
    transaction_subtype = Column(String)
    supplier_name = Column(String)
    supplier_fee = Column(Float, default=0)
    
    # 付款人信息
    payment_user = Column(String)
    
    # AI分类
    category = Column(String)
    category_confidence = Column(Float, default=0)
    
    # 积分
    points_earned = Column(Float, default=0)
    
    # 处理状态
    is_processed = Column(Integer, default=0)
    notes = Column(Text)
    
    # 系统字段
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    statement = relationship('Statement', back_populates='transactions')
    
    __table_args__ = (
        CheckConstraint("classification IN ('Owner', 'GZ')"),
        CheckConstraint("transaction_type IN ('Expense', 'Payment')"),
        Index('idx_transactions_statement', 'statement_id'),
        Index('idx_transactions_date', 'transaction_date'),
        Index('idx_transactions_classification', 'classification'),
        Index('idx_transactions_type', 'transaction_type'),
        Index('idx_transactions_supplier', 'supplier_name'),
    )


class Settlement(Base):
    """月结算表"""
    __tablename__ = 'settlements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # 结算期间
    settlement_month = Column(String, nullable=False)
    
    # Owner's Account 流水账
    owner_previous_balance = Column(Float, default=0)
    owner_expenses = Column(Float, default=0)
    owner_payments = Column(Float, default=0)
    owner_outstanding_balance = Column(Float, default=0)
    
    # GZ's Account 流水账
    gz_previous_balance = Column(Float, default=0)
    gz_expenses = Column(Float, default=0)
    gz_payments = Column(Float, default=0)
    gz_outstanding_balance = Column(Float, default=0)
    
    # 供应商费用
    total_supplier_fee = Column(Float, default=0)
    
    # 优化节省
    optimization_savings = Column(Float, default=0)
    platform_commission = Column(Float, default=0)
    customer_savings = Column(Float, default=0)
    
    # 积分
    total_points_earned = Column(Float, default=0)
    
    # 状态
    settlement_status = Column(String, default='draft')
    
    # 报告文件
    report_pdf_path = Column(String)
    
    # 系统字段
    created_at = Column(DateTime, default=func.now())
    confirmed_at = Column(DateTime)
    paid_at = Column(DateTime)
    
    # 关系
    user = relationship('User', back_populates='settlements')
    
    __table_args__ = (
        CheckConstraint("settlement_status IN ('draft', 'confirmed', 'paid', 'cancelled')"),
        Index('idx_settlements_user', 'user_id'),
        Index('idx_settlements_month', 'settlement_month'),
        Index('idx_settlements_status', 'settlement_status'),
    )


class Supplier(Base):
    """供应商列表"""
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 供应商信息
    supplier_name = Column(String, unique=True, nullable=False)
    supplier_aliases = Column(Text)  # JSON数组
    supplier_category = Column(String)
    
    # 费用配置
    fee_percentage = Column(Float, default=1.0)
    is_active = Column(Integer, default=1)
    
    # 系统字段
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_suppliers_name', 'supplier_name'),
        Index('idx_suppliers_category', 'supplier_category'),
    )


class Reminder(Base):
    """提醒记录表"""
    __tablename__ = 'reminders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # 提醒信息
    reminder_type = Column(String, nullable=False)
    reminder_content = Column(Text, nullable=False)
    
    # 时间配置
    scheduled_time = Column(DateTime, nullable=False)
    sent_at = Column(DateTime)
    
    # 发送状态
    send_status = Column(String, default='pending')
    send_channel = Column(String)
    
    # 关联实体
    related_entity_type = Column(String)
    related_entity_id = Column(Integer)
    
    # 系统字段
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    user = relationship('User', back_populates='reminders')
    
    __table_args__ = (
        CheckConstraint("reminder_type IN ('payment_due', 'statement_upload', 'settlement', 'custom')"),
        CheckConstraint("send_status IN ('pending', 'sent', 'failed', 'cancelled')"),
        CheckConstraint("send_channel IN ('email', 'sms', 'in_app', 'all')"),
        Index('idx_reminders_user', 'user_id'),
        Index('idx_reminders_type', 'reminder_type'),
        Index('idx_reminders_status', 'send_status'),
        Index('idx_reminders_scheduled', 'scheduled_time'),
    )


class Contract(Base):
    """合同签约表"""
    __tablename__ = 'contracts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # 合同信息
    contract_type = Column(String, nullable=False)
    contract_number = Column(String, unique=True, nullable=False)
    contract_content = Column(Text, nullable=False)
    
    # 签署信息
    signed_at = Column(DateTime)
    signature_image_path = Column(String)
    ip_address = Column(String)
    
    # 合同状态
    contract_status = Column(String, default='draft')
    
    # 有效期
    effective_date = Column(String)
    expiration_date = Column(String)
    
    # 文件路径
    pdf_path = Column(String)
    
    # 系统字段
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship('User', back_populates='contracts')
    
    __table_args__ = (
        CheckConstraint("contract_type IN ('service_agreement', 'optimization_proposal', 'payment_on_behalf', 'other')"),
        CheckConstraint("contract_status IN ('draft', 'pending_signature', 'signed', 'expired', 'terminated')"),
        Index('idx_contracts_user', 'user_id'),
        Index('idx_contracts_type', 'contract_type'),
        Index('idx_contracts_status', 'contract_status'),
        Index('idx_contracts_number', 'contract_number'),
    )


class LoanProduct(Base):
    """贷款产品知识库"""
    __tablename__ = 'loan_products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 机构信息
    institution_name = Column(String, nullable=False)
    institution_type = Column(String)
    
    # 产品信息
    product_name = Column(String, nullable=False)
    product_type = Column(String)
    
    # 利率信息
    interest_rate_min = Column(Float)
    interest_rate_max = Column(Float)
    interest_rate_type = Column(String)
    
    # 额度信息
    loan_amount_min = Column(Float)
    loan_amount_max = Column(Float)
    
    # 期限信息
    loan_term_min = Column(Integer)
    loan_term_max = Column(Integer)
    
    # 申请条件
    min_income = Column(Float)
    min_ctos_score = Column(Integer)
    max_dsr = Column(Float)
    
    # 产品特色
    features = Column(Text)  # JSON格式
    fees = Column(Text)  # JSON格式
    
    # 状态
    is_active = Column(Integer, default=1)
    
    # 系统字段
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_verified_at = Column(DateTime)
    
    __table_args__ = (
        CheckConstraint("institution_type IN ('bank', 'fintech', 'credit_cooperative', 'other')"),
        CheckConstraint("product_type IN ('personal_loan', 'sme_loan', 'housing_loan', 'car_loan', 'credit_card', 'other')"),
        CheckConstraint("interest_rate_type IN ('fixed', 'floating', 'hybrid')"),
        Index('idx_loan_products_institution', 'institution_name'),
        Index('idx_loan_products_type', 'product_type'),
        Index('idx_loan_products_active', 'is_active'),
    )


class TaxRecord(Base):
    """税务记录表"""
    __tablename__ = 'tax_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # 税务年度
    tax_year = Column(Integer, nullable=False)
    
    # 收入信息
    total_income = Column(Float, default=0)
    employment_income = Column(Float, default=0)
    business_income = Column(Float, default=0)
    other_income = Column(Float, default=0)
    
    # 扣除项
    total_deductions = Column(Float, default=0)
    epf_deduction = Column(Float, default=0)
    insurance_deduction = Column(Float, default=0)
    education_deduction = Column(Float, default=0)
    other_deductions = Column(Float, default=0)
    
    # 应纳税额
    taxable_income = Column(Float, default=0)
    tax_payable = Column(Float, default=0)
    tax_paid = Column(Float, default=0)
    tax_refund = Column(Float, default=0)
    
    # 状态
    tax_status = Column(String, default='draft')
    
    # 文件
    tax_return_path = Column(String)
    
    # 系统字段
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    submitted_at = Column(DateTime)
    
    # 关系
    user = relationship('User', back_populates='tax_records')
    
    __table_args__ = (
        CheckConstraint("tax_status IN ('draft', 'submitted', 'approved', 'rejected')"),
        Index('idx_tax_records_user', 'user_id'),
        Index('idx_tax_records_year', 'tax_year'),
        Index('idx_tax_records_status', 'tax_status'),
    )


class MonthlyStatement(Base):
    """月度账本汇总表 - Module 4 核心"""
    __tablename__ = 'monthly_statements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    card_id = Column(Integer, ForeignKey('credit_cards.id', ondelete='CASCADE'), nullable=False)
    statement_id = Column(Integer, ForeignKey('statements.id', ondelete='SET NULL'))
    
    # 月份信息
    statement_month = Column(String, nullable=False)
    
    # Module 4: 6个强制字段
    total_spent = Column(Float, nullable=False, default=0)
    total_fees = Column(Float, nullable=False, default=0)
    total_supplier_consumption = Column(Float, nullable=False, default=0)
    total_customer_payment = Column(Float, nullable=False, default=0)
    total_revenue = Column(Float, nullable=False, default=0)
    total_refunds = Column(Float, nullable=False, default=0)
    
    # 额外统计字段
    previous_balance = Column(Float, default=0)
    current_balance = Column(Float, default=0)
    
    # 系统字段
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship('User')
    credit_card = relationship('CreditCard', back_populates='monthly_statements')
    statement = relationship('Statement', back_populates='monthly_statement')
    
    __table_args__ = (
        Index('idx_monthly_statements_user', 'user_id'),
        Index('idx_monthly_statements_card', 'card_id'),
        Index('idx_monthly_statements_month', 'statement_month'),
    )


# ============================================================
# 工具函数
# ============================================================

def init_database(engine):
    """初始化数据库表结构"""
    Base.metadata.create_all(engine)
    print("✅ 数据库表结构初始化完成")


def get_or_create(session, model, **kwargs):
    """获取或创建记录（避免重复）"""
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        session.add(instance)
        return instance, True
