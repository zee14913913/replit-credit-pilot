-- Migration: 扩展文件状态枚举，支持完整生命周期
-- Date: 2025-11-02
-- Purpose: 从简单的active扩展到uploaded/validated/posted/exception/archived，实现状态→动作引导

-- 1. 删除旧的状态约束
ALTER TABLE file_index DROP CONSTRAINT IF EXISTS file_index_status_check;

-- 2. 添加新的扩展状态约束
ALTER TABLE file_index ADD CONSTRAINT file_index_status_check 
    CHECK (status IN ('uploaded', 'active', 'validated', 'posted', 'exception', 'archived', 'processing', 'failed'));

-- 3. 添加is_primary标记字段（用于标记同月份的主对账单）
ALTER TABLE file_index ADD COLUMN IF NOT EXISTS is_primary BOOLEAN DEFAULT FALSE;

-- 4. 添加duplicate_warning字段（标记是否存在同月多份对账单）
ALTER TABLE file_index ADD COLUMN IF NOT EXISTS duplicate_warning BOOLEAN DEFAULT FALSE;

-- 5. 添加status_reason字段（解释"为什么还是这个状态"）
ALTER TABLE file_index ADD COLUMN IF NOT EXISTS status_reason TEXT;

-- 6. 添加account_number字段（用于检测同月多份对账单）
ALTER TABLE file_index ADD COLUMN IF NOT EXISTS account_number VARCHAR(100);

-- 7. 创建索引以提高同月对账单检测性能
CREATE INDEX IF NOT EXISTS idx_file_index_month_account ON file_index(company_id, period, account_number) WHERE module = 'bank';

-- 8. 更新现有的'active'状态记录，添加默认status_reason
UPDATE file_index 
SET status_reason = '文件已上传，等待数据验证' 
WHERE status = 'active' AND status_reason IS NULL;

COMMENT ON COLUMN file_index.is_primary IS '是否为本月主对账单（当同月存在多份时）';
COMMENT ON COLUMN file_index.duplicate_warning IS '是否存在同月多份对账单警告';
COMMENT ON COLUMN file_index.status_reason IS '状态说明：解释为什么还是当前状态';
COMMENT ON COLUMN file_index.account_number IS '银行账号（用于检测同月重复上传）';
