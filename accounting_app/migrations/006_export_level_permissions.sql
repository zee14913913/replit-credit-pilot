-- ============================================================
-- Migration 006: 导出分级控制 (Export-Level Permissions)
-- Purpose: 添加基于角色的导出权限控制
-- ============================================================

-- ============================================================
-- Part 1: 导出权限矩阵
-- ============================================================

-- viewer: 禁止所有导出
INSERT INTO permissions (role, resource, action, allowed, description) VALUES
('viewer', 'export:journal_entries', 'read', false, 'Viewer禁止导出会计分录'),
('viewer', 'export:bank_statements', 'read', false, 'Viewer禁止导出银行流水'),
('viewer', 'export:invoices', 'read', false, 'Viewer禁止导出发票'),
('viewer', 'export:pos_reports', 'read', false, 'Viewer禁止导出POS报表'),
('viewer', 'export:raw_documents', 'read', false, 'Viewer禁止导出原始文件'),
('viewer', 'export:audit_logs', 'read', false, 'Viewer禁止导出审计日志'),
('viewer', 'export:management_reports', 'read', false, 'Viewer禁止导出管理报表')
ON CONFLICT (role, resource, action) DO NOTHING;

-- data_entry: 可以导出自己录入的基础数据
INSERT INTO permissions (role, resource, action, allowed, description) VALUES
('data_entry', 'export:journal_entries', 'read', false, 'Data Entry禁止导出会计分录（敏感财务数据）'),
('data_entry', 'export:bank_statements', 'read', true, 'Data Entry可以导出银行流水（基础数据）'),
('data_entry', 'export:invoices', 'read', true, 'Data Entry可以导出发票（自己录入的数据）'),
('data_entry', 'export:pos_reports', 'read', true, 'Data Entry可以导出POS报表（基础数据）'),
('data_entry', 'export:raw_documents', 'read', false, 'Data Entry禁止导出原始文件（敏感）'),
('data_entry', 'export:audit_logs', 'read', false, 'Data Entry禁止导出审计日志（敏感）'),
('data_entry', 'export:management_reports', 'read', false, 'Data Entry禁止导出管理报表（敏感）')
ON CONFLICT (role, resource, action) DO NOTHING;

-- loan_officer: 可以导出贷款相关数据
INSERT INTO permissions (role, resource, action, allowed, description) VALUES
('loan_officer', 'export:journal_entries', 'read', false, 'Loan Officer禁止导出会计分录'),
('loan_officer', 'export:bank_statements', 'read', true, 'Loan Officer可以导出银行流水（用于贷款审核）'),
('loan_officer', 'export:invoices', 'read', true, 'Loan Officer可以导出发票（用于贷款审核）'),
('loan_officer', 'export:pos_reports', 'read', true, 'Loan Officer可以导出POS报表（用于贷款审核）'),
('loan_officer', 'export:raw_documents', 'read', false, 'Loan Officer禁止导出原始文件'),
('loan_officer', 'export:audit_logs', 'read', false, 'Loan Officer禁止导出审计日志'),
('loan_officer', 'export:management_reports', 'read', true, 'Loan Officer可以导出管理报表（用于贷款审核）')
ON CONFLICT (role, resource, action) DO NOTHING;

-- accountant: 可以导出所有会计数据
INSERT INTO permissions (role, resource, action, allowed, description) VALUES
('accountant', 'export:journal_entries', 'read', true, 'Accountant可以导出会计分录（核心权限）'),
('accountant', 'export:bank_statements', 'read', true, 'Accountant可以导出银行流水'),
('accountant', 'export:invoices', 'read', true, 'Accountant可以导出发票'),
('accountant', 'export:pos_reports', 'read', true, 'Accountant可以导出POS报表'),
('accountant', 'export:raw_documents', 'read', false, 'Accountant禁止导出原始文件（只有Admin可以）'),
('accountant', 'export:audit_logs', 'read', false, 'Accountant禁止导出审计日志（只有Admin可以）'),
('accountant', 'export:management_reports', 'read', true, 'Accountant可以导出管理报表')
ON CONFLICT (role, resource, action) DO NOTHING;

-- admin: 可以导出所有数据（包括敏感数据）
INSERT INTO permissions (role, resource, action, allowed, description) VALUES
('admin', 'export:journal_entries', 'read', true, 'Admin可以导出会计分录'),
('admin', 'export:bank_statements', 'read', true, 'Admin可以导出银行流水'),
('admin', 'export:invoices', 'read', true, 'Admin可以导出发票'),
('admin', 'export:pos_reports', 'read', true, 'Admin可以导出POS报表'),
('admin', 'export:raw_documents', 'read', true, 'Admin可以导出原始文件（最高权限）'),
('admin', 'export:audit_logs', 'read', true, 'Admin可以导出审计日志（合规要求）'),
('admin', 'export:management_reports', 'read', true, 'Admin可以导出管理报表')
ON CONFLICT (role, resource, action) DO NOTHING;


-- ============================================================
-- Part 2: 导出权限总结表（用于文档和查询）
-- ============================================================

-- 权限矩阵总结（Markdown格式，用于生成文档）
-- | 角色 | 会计分录 | 银行流水 | 发票 | POS报表 | 原始文件 | 审计日志 | 管理报表 |
-- |------|---------|---------|------|---------|---------|---------|---------|
-- | viewer | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
-- | data_entry | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
-- | loan_officer | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
-- | accountant | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
-- | admin | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

-- ============================================================
-- Part 3: 验证查询（可选，用于测试）
-- ============================================================

-- 验证所有角色的导出权限
-- SELECT 
--     role,
--     resource,
--     action,
--     allowed,
--     description
-- FROM permissions
-- WHERE resource LIKE 'export:%'
-- ORDER BY role, resource;
