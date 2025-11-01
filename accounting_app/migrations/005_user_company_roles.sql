-- ============================================================
-- Phase 2-1 增强：公司维度权限（Multi-tenant Role Binding）
-- 用途：支持同一用户在不同公司拥有不同角色
-- 示例：张三在A公司是accountant，在B公司是viewer
-- ============================================================

-- 1. 创建 user_company_roles 表（多对多关系）
CREATE TABLE IF NOT EXISTS user_company_roles (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id INT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    role VARCHAR(30) NOT NULL,
    
    -- 权限相关字段
    created_at TIMESTAMP DEFAULT now(),
    created_by INT REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT now(),
    
    -- 唯一约束：同一用户在同一公司只能有一个角色
    CONSTRAINT unique_user_company UNIQUE (user_id, company_id),
    
    -- 角色枚举检查
    CONSTRAINT check_valid_role CHECK (
        role IN ('admin', 'accountant', 'viewer', 'data_entry', 'loan_officer')
    )
);

-- 2. 创建索引（优化查询性能）
CREATE INDEX IF NOT EXISTS idx_user_company_roles_user_id ON user_company_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_company_roles_company_id ON user_company_roles(company_id);
CREATE INDEX IF NOT EXISTS idx_user_company_roles_role ON user_company_roles(role);

-- 3. 数据迁移：将现有用户的角色迁移到 user_company_roles
-- 现有 users 表有 company_id 和 role 字段，需要迁移过来
INSERT INTO user_company_roles (user_id, company_id, role, created_at)
SELECT 
    u.id AS user_id,
    u.company_id,
    u.role,
    u.created_at
FROM users u
WHERE u.is_active = TRUE
ON CONFLICT (user_id, company_id) DO NOTHING;

-- 4. 为已存在的用户添加审计字段注释
COMMENT ON TABLE user_company_roles IS 'Phase 2-1增强：多租户角色绑定表，支持同一用户在不同公司拥有不同角色';
COMMENT ON COLUMN user_company_roles.user_id IS '用户ID';
COMMENT ON COLUMN user_company_roles.company_id IS '公司ID';
COMMENT ON COLUMN user_company_roles.role IS '角色：admin/accountant/viewer/data_entry/loan_officer';
COMMENT ON COLUMN user_company_roles.created_by IS '创建人ID（如果是admin手动分配）';

-- 5. 向后兼容：保留 users 表的 role 和 company_id 字段
-- 说明：为了不破坏现有代码，暂时保留这两个字段
-- 后续可以逐步迁移为只使用 user_company_roles
