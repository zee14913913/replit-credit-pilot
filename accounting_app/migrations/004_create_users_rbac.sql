-- ============================================================
-- Phase 2-1: RBAC权限系统
-- 创建users表、roles枚举、permissions表
-- ============================================================

-- Step 1: 创建角色枚举类型
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM (
        'admin',         -- 系统管理员：完全权限
        'accountant',    -- 会计师：财务数据读写权限
        'viewer',        -- 查看者：只读权限
        'data_entry',    -- 数据录入员：上传和录入权限
        'loan_officer'   -- 贷款专员：贷款业务管理权限
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Step 2: 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- SHA-256 hashed
    full_name VARCHAR(200),
    role user_role NOT NULL DEFAULT 'viewer',  -- 默认最低权限
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 唯一约束：同一公司内username和email唯一
    CONSTRAINT uq_users_company_username UNIQUE(company_id, username),
    CONSTRAINT uq_users_company_email UNIQUE(company_id, email)
);

-- Step 3: 创建权限矩阵表（资源级权限控制）
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    role user_role NOT NULL,
    resource VARCHAR(100) NOT NULL,  -- 资源名称（如：bank_statements, invoices）
    action VARCHAR(50) NOT NULL,     -- 操作类型（create, read, update, delete, export）
    allowed BOOLEAN DEFAULT true,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 唯一约束：role + resource + action组合唯一
    CONSTRAINT uq_permissions_role_resource_action UNIQUE(role, resource, action)
);

-- Step 4: 索引优化
CREATE INDEX IF NOT EXISTS idx_users_company_role ON users(company_id, role);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_permissions_role_resource ON permissions(role, resource);

-- Step 5: 默认权限矩阵种子数据
-- admin: 完全权限
INSERT INTO permissions (role, resource, action, description) VALUES
    ('admin', '*', '*', '管理员拥有所有资源的所有权限')
ON CONFLICT (role, resource, action) DO NOTHING;

-- accountant: 财务核心权限
INSERT INTO permissions (role, resource, action, description) VALUES
    ('accountant', 'bank_statements', 'create', '会计师可以上传银行月结单'),
    ('accountant', 'bank_statements', 'read', '会计师可以查看银行月结单'),
    ('accountant', 'bank_statements', 'update', '会计师可以修改银行月结单'),
    ('accountant', 'bank_statements', 'delete', '会计师可以删除银行月结单'),
    ('accountant', 'invoices', 'create', '会计师可以创建发票'),
    ('accountant', 'invoices', 'read', '会计师可以查看发票'),
    ('accountant', 'invoices', 'update', '会计师可以修改发票'),
    ('accountant', 'journal_entries', 'create', '会计师可以创建分录'),
    ('accountant', 'journal_entries', 'read', '会计师可以查看分录'),
    ('accountant', 'reports', 'read', '会计师可以查看报表'),
    ('accountant', 'reports', 'export', '会计师可以导出报表'),
    ('accountant', 'exceptions', 'read', '会计师可以查看异常'),
    ('accountant', 'exceptions', 'update', '会计师可以处理异常')
ON CONFLICT (role, resource, action) DO NOTHING;

-- viewer: 只读权限
INSERT INTO permissions (role, resource, action, description) VALUES
    ('viewer', 'bank_statements', 'read', '查看者可以查看银行月结单'),
    ('viewer', 'invoices', 'read', '查看者可以查看发票'),
    ('viewer', 'journal_entries', 'read', '查看者可以查看分录'),
    ('viewer', 'reports', 'read', '查看者可以查看报表'),
    ('viewer', 'exceptions', 'read', '查看者可以查看异常')
ON CONFLICT (role, resource, action) DO NOTHING;

-- data_entry: 数据录入权限
INSERT INTO permissions (role, resource, action, description) VALUES
    ('data_entry', 'bank_statements', 'create', '录入员可以上传银行月结单'),
    ('data_entry', 'bank_statements', 'read', '录入员可以查看银行月结单'),
    ('data_entry', 'invoices', 'create', '录入员可以创建发票'),
    ('data_entry', 'invoices', 'read', '录入员可以查看发票'),
    ('data_entry', 'pos_reports', 'create', '录入员可以上传POS报表'),
    ('data_entry', 'pos_reports', 'read', '录入员可以查看POS报表')
ON CONFLICT (role, resource, action) DO NOTHING;

-- loan_officer: 贷款业务权限
INSERT INTO permissions (role, resource, action, description) VALUES
    ('loan_officer', 'loan_applications', 'create', '贷款专员可以创建贷款申请'),
    ('loan_officer', 'loan_applications', 'read', '贷款专员可以查看贷款申请'),
    ('loan_officer', 'loan_applications', 'update', '贷款专员可以修改贷款申请'),
    ('loan_officer', 'bank_statements', 'read', '贷款专员可以查看银行月结单'),
    ('loan_officer', 'reports', 'read', '贷款专员可以查看报表')
ON CONFLICT (role, resource, action) DO NOTHING;

-- Step 6: 创建默认管理员账户（密码: admin123，SHA-256）
-- 注意：生产环境必须修改默认密码！
INSERT INTO users (company_id, username, email, password_hash, full_name, role) 
VALUES (
    1,  -- 假设company_id=1存在
    'admin',
    'admin@company.com',
    'SHA256:240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9',  -- admin123的SHA-256
    'System Administrator',
    'admin'
)
ON CONFLICT (company_id, username) DO NOTHING;

-- Step 7: 添加更新时间戳触发器
CREATE OR REPLACE FUNCTION update_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_users_updated_at ON users;
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_users_updated_at();

-- Step 8: 数据完整性检查注释
COMMENT ON TABLE users IS 'Phase 2-1: 用户表（RBAC权限系统核心）';
COMMENT ON TABLE permissions IS 'Phase 2-1: 权限矩阵表（资源级权限控制）';
COMMENT ON COLUMN users.role IS '用户角色：admin/accountant/viewer/data_entry/loan_officer';
COMMENT ON COLUMN permissions.resource IS '资源名称，* 表示所有资源';
COMMENT ON COLUMN permissions.action IS '操作类型，* 表示所有操作';
