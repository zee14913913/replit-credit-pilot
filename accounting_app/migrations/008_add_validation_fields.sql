-- =====================================================================
-- 补充改进③：添加raw_documents验证字段
-- Migration: 008_add_validation_fields.sql
-- Date: 2025-11-01
-- 
-- 目的：
-- 1. 添加validation_status字段追踪行数对账结果
-- 2. 添加validation_failed_at时间戳
-- 3. 添加validation_error_message详细错误信息
-- 
-- 业务规则：
-- - validation_status IN ('passed', 'failed', 'pending')
-- - 默认值为'pending'
-- - 对账失败时记录失败时间和原因
-- =====================================================================

-- 1. 添加validation_status字段
ALTER TABLE raw_documents 
ADD COLUMN IF NOT EXISTS validation_status VARCHAR(20) DEFAULT 'pending';

-- 2. 添加validation_failed_at时间戳
ALTER TABLE raw_documents 
ADD COLUMN IF NOT EXISTS validation_failed_at TIMESTAMP WITH TIME ZONE;

-- 3. 添加validation_error_message详细错误信息
ALTER TABLE raw_documents 
ADD COLUMN IF NOT EXISTS validation_error_message TEXT;

-- 4. 创建索引以优化查询性能
CREATE INDEX IF NOT EXISTS idx_raw_documents_validation_status 
ON raw_documents(validation_status);

-- 5. 添加CHECK约束确保validation_status值有效
ALTER TABLE raw_documents 
ADD CONSTRAINT chk_validation_status 
CHECK (validation_status IN ('passed', 'failed', 'pending'));

-- 6. 为现有记录设置validation_status
-- 如果reconciliation_status='match'，则标记为'passed'
UPDATE raw_documents 
SET validation_status = 'passed' 
WHERE reconciliation_status = 'match' 
  AND validation_status = 'pending';

-- 如果reconciliation_status='mismatch'，则标记为'failed'
UPDATE raw_documents 
SET validation_status = 'failed',
    validation_error_message = '历史数据：行数对账失败'
WHERE reconciliation_status = 'mismatch' 
  AND validation_status = 'pending';

-- 7. 添加注释
COMMENT ON COLUMN raw_documents.validation_status IS '补充改进③：行数对账结果标记 - passed（通过）| failed（失败）| pending（待验证）';
COMMENT ON COLUMN raw_documents.validation_failed_at IS '补充改进③：验证失败时间戳';
COMMENT ON COLUMN raw_documents.validation_error_message IS '补充改进③：验证失败详细原因';

-- 8. 验证迁移结果
DO $$
DECLARE
    total_count INTEGER;
    passed_count INTEGER;
    failed_count INTEGER;
    pending_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_count FROM raw_documents;
    SELECT COUNT(*) INTO passed_count FROM raw_documents WHERE validation_status = 'passed';
    SELECT COUNT(*) INTO failed_count FROM raw_documents WHERE validation_status = 'failed';
    SELECT COUNT(*) INTO pending_count FROM raw_documents WHERE validation_status = 'pending';
    
    RAISE NOTICE '========================================';
    RAISE NOTICE '补充改进③ - 迁移完成统计:';
    RAISE NOTICE '----------------------------------------';
    RAISE NOTICE '总记录数: %', total_count;
    RAISE NOTICE '验证通过: %', passed_count;
    RAISE NOTICE '验证失败: %', failed_count;
    RAISE NOTICE '待验证: %', pending_count;
    RAISE NOTICE '========================================';
END $$;
