-- ============================================================
-- 银行贷款合规会计系统 - 扩展数据库表（Management Report功能）
-- 用途：文件解析 + 自动记账 + Management Report
-- 日期：2025-11-01
-- ============================================================

-- ============================================================
-- 1. 待人工确认文档表 (Pending Documents)
-- ============================================================
CREATE TABLE IF NOT EXISTS pending_documents (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    file_type VARCHAR(50) NOT NULL,  -- 'bank-statement', 'supplier-invoice', 'pos-report'
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size_kb INTEGER,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 解析状态
    parse_status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'failed', 'partial', 'resolved'
    failure_reason TEXT,
    confidence_score DECIMAL(5,2),  -- 0.00 - 1.00
    
    -- 部分识别的信息（JSON格式）
    extracted_data JSONB,
    
    -- 人工处理
    assigned_to VARCHAR(100),
    resolved_by VARCHAR(100),
    resolved_date TIMESTAMP,
    resolution_notes TEXT,
    
    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_pending_documents_company ON pending_documents(company_id);
CREATE INDEX idx_pending_documents_status ON pending_documents(parse_status);
CREATE INDEX idx_pending_documents_type ON pending_documents(file_type);

COMMENT ON TABLE pending_documents IS '待人工确认的文档队列 - 解析失败或置信度低的文件';

-- ============================================================
-- 2. 供应商主数据表 (Suppliers)
-- ============================================================
CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    supplier_code VARCHAR(50) NOT NULL UNIQUE,
    supplier_name VARCHAR(200) NOT NULL,
    supplier_name_chinese VARCHAR(200),
    
    -- 联系信息
    contact_person VARCHAR(100),
    phone VARCHAR(50),
    email VARCHAR(100),
    address TEXT,
    
    -- 财务信息
    tax_id VARCHAR(50),
    payment_terms VARCHAR(50),  -- 'NET30', 'NET60', 'COD'
    credit_limit DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'MYR',
    
    -- 银行信息
    bank_name VARCHAR(100),
    bank_account VARCHAR(100),
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 元数据
    notes TEXT
);

CREATE INDEX idx_suppliers_company ON suppliers(company_id);
CREATE INDEX idx_suppliers_code ON suppliers(supplier_code);
CREATE INDEX idx_suppliers_name ON suppliers(supplier_name);

COMMENT ON TABLE suppliers IS '供应商主数据';

-- ============================================================
-- 3. 客户主数据表 (Customers)
-- ============================================================
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    customer_code VARCHAR(50) NOT NULL UNIQUE,
    customer_name VARCHAR(200) NOT NULL,
    customer_name_chinese VARCHAR(200),
    
    -- 联系信息
    contact_person VARCHAR(100),
    phone VARCHAR(50),
    email VARCHAR(100),
    address TEXT,
    
    -- 财务信息
    tax_id VARCHAR(50),
    payment_terms VARCHAR(50),
    credit_limit DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'MYR',
    
    -- 会员信息（POS系统）
    member_id VARCHAR(50),
    membership_level VARCHAR(50),  -- 'Regular', 'Silver', 'Gold', 'Platinum'
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 元数据
    notes TEXT
);

CREATE INDEX idx_customers_company ON customers(company_id);
CREATE INDEX idx_customers_code ON customers(customer_code);
CREATE INDEX idx_customers_member ON customers(member_id);

COMMENT ON TABLE customers IS '客户主数据';

-- ============================================================
-- 4. 采购发票表 (Purchase Invoices)
-- ============================================================
CREATE TABLE IF NOT EXISTS purchase_invoices (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
    
    -- 发票信息
    invoice_no VARCHAR(100) NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE,
    
    -- 金额
    subtotal DECIMAL(15,2) NOT NULL,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'MYR',
    
    -- 付款信息
    payment_status VARCHAR(20) DEFAULT 'unpaid',  -- 'unpaid', 'partial', 'paid', 'overdue'
    paid_amount DECIMAL(15,2) DEFAULT 0,
    payment_date DATE,
    
    -- 会计处理
    journal_entry_id INTEGER REFERENCES journal_entries(id),
    is_posted BOOLEAN DEFAULT FALSE,
    posting_date DATE,
    
    -- 文件关联
    original_file_path VARCHAR(500),
    
    -- 元数据
    description TEXT,
    reference_no VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 重复检测约束
    CONSTRAINT unique_supplier_invoice UNIQUE(supplier_id, invoice_no, invoice_date)
);

CREATE INDEX idx_purchase_invoices_company ON purchase_invoices(company_id);
CREATE INDEX idx_purchase_invoices_supplier ON purchase_invoices(supplier_id);
CREATE INDEX idx_purchase_invoices_date ON purchase_invoices(invoice_date);
CREATE INDEX idx_purchase_invoices_status ON purchase_invoices(payment_status);

COMMENT ON TABLE purchase_invoices IS '采购发票 - 应付账款';

-- ============================================================
-- 5. 销售发票表 (Sales Invoices)
-- ============================================================
CREATE TABLE IF NOT EXISTS sales_invoices (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    customer_id INTEGER REFERENCES customers(id) ON DELETE RESTRICT,
    
    -- 发票信息
    invoice_no VARCHAR(100) NOT NULL UNIQUE,
    invoice_date DATE NOT NULL,
    due_date DATE,
    
    -- 金额
    subtotal DECIMAL(15,2) NOT NULL,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'MYR',
    
    -- 收款信息
    payment_status VARCHAR(20) DEFAULT 'unpaid',  -- 'unpaid', 'partial', 'paid', 'overdue'
    received_amount DECIMAL(15,2) DEFAULT 0,
    payment_date DATE,
    payment_method VARCHAR(50),  -- 'Cash', 'Card', 'Transfer', 'E-Wallet'
    
    -- 会计处理
    journal_entry_id INTEGER REFERENCES journal_entries(id),
    is_posted BOOLEAN DEFAULT FALSE,
    posting_date DATE,
    
    -- POS来源
    pos_report_id INTEGER,  -- 关联到POS日报
    pos_transaction_date DATE,
    
    -- 文件关联
    generated_pdf_path VARCHAR(500),
    
    -- 元数据
    description TEXT,
    reference_no VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_sales_invoices_company ON sales_invoices(company_id);
CREATE INDEX idx_sales_invoices_customer ON sales_invoices(customer_id);
CREATE INDEX idx_sales_invoices_date ON sales_invoices(invoice_date);
CREATE INDEX idx_sales_invoices_status ON sales_invoices(payment_status);
CREATE INDEX idx_sales_invoices_pos ON sales_invoices(pos_transaction_date);

COMMENT ON TABLE sales_invoices IS '销售发票 - 应收账款';

-- ============================================================
-- 6. 文件索引表 (File Index)
-- ============================================================
CREATE TABLE IF NOT EXISTS file_index (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- 文件分类
    file_category VARCHAR(50) NOT NULL,  -- 'bank-statement', 'supplier-invoice', 'customer-invoice', 'pos-report', 'financial-report', 'management-report'
    file_type VARCHAR(20) NOT NULL,  -- 'original', 'generated'
    
    -- 文件信息
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL UNIQUE,
    file_size_kb INTEGER,
    file_extension VARCHAR(10),
    mime_type VARCHAR(100),
    
    -- 关联实体
    related_entity_type VARCHAR(50),  -- 'bank_statement', 'purchase_invoice', 'sales_invoice'
    related_entity_id INTEGER,
    
    -- 期间
    period VARCHAR(10),  -- '2025-08'
    transaction_date DATE,
    
    -- 元数据
    upload_by VARCHAR(100),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    tags VARCHAR(200),
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_file_index_company ON file_index(company_id);
CREATE INDEX idx_file_index_category ON file_index(file_category);
CREATE INDEX idx_file_index_type ON file_index(file_type);
CREATE INDEX idx_file_index_period ON file_index(period);
CREATE INDEX idx_file_index_path ON file_index(file_path);

COMMENT ON TABLE file_index IS '文件索引表 - 统一管理所有上传和生成的文件';

-- ============================================================
-- 7. 文件处理日志表 (Processing Logs)
-- ============================================================
CREATE TABLE IF NOT EXISTS processing_logs (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    
    -- 处理任务
    task_type VARCHAR(50) NOT NULL,  -- 'parse-pdf', 'generate-invoice', 'generate-report', 'auto-match'
    task_status VARCHAR(20) NOT NULL,  -- 'pending', 'processing', 'completed', 'failed'
    
    -- 输入
    input_file_path VARCHAR(500),
    input_parameters JSONB,
    
    -- 输出
    output_file_path VARCHAR(500),
    output_data JSONB,
    
    -- 执行信息
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    
    -- 错误信息
    error_message TEXT,
    error_stack TEXT,
    
    -- 元数据
    processed_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_processing_logs_company ON processing_logs(company_id);
CREATE INDEX idx_processing_logs_type ON processing_logs(task_type);
CREATE INDEX idx_processing_logs_status ON processing_logs(task_status);
CREATE INDEX idx_processing_logs_time ON processing_logs(start_time);

COMMENT ON TABLE processing_logs IS '文件处理日志 - 记录所有自动化任务的执行情况';

-- ============================================================
-- 8. Management Report生成记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS management_reports (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- 报表期间
    report_period VARCHAR(10) NOT NULL,  -- '2025-08'
    report_type VARCHAR(50) DEFAULT 'monthly',  -- 'monthly', 'quarterly', 'ytd'
    
    -- 报表文件
    pdf_file_path VARCHAR(500),
    json_data JSONB,
    
    -- 数据来源统计
    data_sources JSONB,  -- {"bank_statements": 45, "supplier_invoices": 12, "sales": 230}
    unreconciled_count INTEGER DEFAULT 0,
    confidence_score DECIMAL(5,2),
    
    -- 生成信息
    generated_by VARCHAR(100),
    generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 状态
    report_status VARCHAR(20) DEFAULT 'draft',  -- 'draft', 'final', 'archived'
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 元数据
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_management_reports_company ON management_reports(company_id);
CREATE INDEX idx_management_reports_period ON management_reports(report_period);
CREATE INDEX idx_management_reports_status ON management_reports(report_status);

COMMENT ON TABLE management_reports IS 'Management Report生成记录表';

-- ============================================================
-- 9. 增强现有 journal_entries 表
-- ============================================================
-- 添加来源类型字段
ALTER TABLE journal_entries 
ADD COLUMN IF NOT EXISTS source_type VARCHAR(50) DEFAULT 'manual';
-- 可能值: 'manual', 'bank-statement', 'supplier-invoice', 'sales-invoice', 'pos-report', 'auto-match'

ALTER TABLE journal_entries 
ADD COLUMN IF NOT EXISTS source_id INTEGER;
-- 关联到具体的来源记录ID

ALTER TABLE journal_entries 
ADD COLUMN IF NOT EXISTS auto_generated BOOLEAN DEFAULT FALSE;
-- 是否自动生成

COMMENT ON COLUMN journal_entries.source_type IS '分录来源类型';
COMMENT ON COLUMN journal_entries.source_id IS '来源记录ID';
COMMENT ON COLUMN journal_entries.auto_generated IS '是否自动生成';

-- ============================================================
-- 10. 增强 bank_statements 表
-- ============================================================
-- 添加文件关联
ALTER TABLE bank_statements 
ADD COLUMN IF NOT EXISTS source_file_id INTEGER REFERENCES file_index(id);

COMMENT ON COLUMN bank_statements.source_file_id IS '关联的源文件ID';

-- ============================================================
-- 11. 创建视图：应收账款账龄 (AR Aging)
-- ============================================================
CREATE OR REPLACE VIEW vw_ar_aging AS
SELECT 
    si.company_id,
    si.customer_id,
    c.customer_code,
    c.customer_name,
    si.invoice_no,
    si.invoice_date,
    si.due_date,
    si.total_amount,
    si.received_amount,
    (si.total_amount - si.received_amount) as outstanding_amount,
    si.payment_status,
    CASE 
        WHEN si.payment_status = 'paid' THEN 0
        WHEN si.due_date IS NULL THEN 0
        ELSE CURRENT_DATE - si.due_date
    END as days_overdue,
    CASE
        WHEN si.payment_status = 'paid' THEN 'Paid'
        WHEN si.due_date IS NULL OR CURRENT_DATE <= si.due_date THEN 'Current'
        WHEN CURRENT_DATE - si.due_date <= 30 THEN '1-30 days'
        WHEN CURRENT_DATE - si.due_date <= 60 THEN '31-60 days'
        WHEN CURRENT_DATE - si.due_date <= 90 THEN '61-90 days'
        ELSE '90+ days'
    END as aging_category
FROM sales_invoices si
LEFT JOIN customers c ON si.customer_id = c.id
WHERE si.is_active = TRUE
  AND si.payment_status != 'paid';

COMMENT ON VIEW vw_ar_aging IS '应收账款账龄分析视图';

-- ============================================================
-- 12. 创建视图：应付账款账龄 (AP Aging)
-- ============================================================
CREATE OR REPLACE VIEW vw_ap_aging AS
SELECT 
    pi.company_id,
    pi.supplier_id,
    s.supplier_code,
    s.supplier_name,
    pi.invoice_no,
    pi.invoice_date,
    pi.due_date,
    pi.total_amount,
    pi.paid_amount,
    (pi.total_amount - pi.paid_amount) as outstanding_amount,
    pi.payment_status,
    CASE 
        WHEN pi.payment_status = 'paid' THEN 0
        WHEN pi.due_date IS NULL THEN 0
        ELSE CURRENT_DATE - pi.due_date
    END as days_overdue,
    CASE
        WHEN pi.payment_status = 'paid' THEN 'Paid'
        WHEN pi.due_date IS NULL OR CURRENT_DATE <= pi.due_date THEN 'Current'
        WHEN CURRENT_DATE - pi.due_date <= 30 THEN '1-30 days'
        WHEN CURRENT_DATE - pi.due_date <= 60 THEN '31-60 days'
        WHEN CURRENT_DATE - pi.due_date <= 90 THEN '61-90 days'
        ELSE '90+ days'
    END as aging_category
FROM purchase_invoices pi
LEFT JOIN suppliers s ON pi.supplier_id = s.id
WHERE pi.is_active = TRUE
  AND pi.payment_status != 'paid';

COMMENT ON VIEW vw_ap_aging IS '应付账款账龄分析视图';

-- ============================================================
-- 13. 创建函数：更新 updated_at 时间戳
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为相关表添加触发器
CREATE TRIGGER update_pending_documents_updated_at BEFORE UPDATE ON pending_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_suppliers_updated_at BEFORE UPDATE ON suppliers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_purchase_invoices_updated_at BEFORE UPDATE ON purchase_invoices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sales_invoices_updated_at BEFORE UPDATE ON sales_invoices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 14. 初始化示例数据
-- ============================================================

-- 插入示例供应商
INSERT INTO suppliers (company_id, supplier_code, supplier_name, payment_terms, is_active)
VALUES 
    (1, 'SUP001', 'ABC Supplier Sdn Bhd', 'NET30', TRUE),
    (1, 'SUP002', 'XYZ Trading Co', 'NET60', TRUE),
    (1, 'SUP003', 'Malaysia Parts Supply', 'COD', TRUE)
ON CONFLICT (supplier_code) DO NOTHING;

-- 插入示例客户
INSERT INTO customers (company_id, customer_code, customer_name, member_id, membership_level, is_active)
VALUES 
    (1, 'CUST001', 'Walk-in Customer', NULL, 'Regular', TRUE),
    (1, 'CUST002', 'Corporate Client A', 'M001', 'Gold', TRUE),
    (1, 'CUST003', 'Retail Customer B', 'M002', 'Silver', TRUE)
ON CONFLICT (customer_code) DO NOTHING;

-- ============================================================
-- 完成！
-- ============================================================

COMMENT ON SCHEMA public IS 'Enhanced accounting system with file parsing, auto-journaling, and management reporting capabilities';

SELECT '✅ 数据库扩展表创建完成！包含：
- pending_documents (待确认文档)
- suppliers (供应商)
- customers (客户)
- purchase_invoices (采购发票)
- sales_invoices (销售发票)
- file_index (文件索引)
- processing_logs (处理日志)
- management_reports (管理报表)
- vw_ar_aging (应收账龄视图)
- vw_ap_aging (应付账龄视图)
' as status;
