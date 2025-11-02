-- Migration 003: 修复status约束以支持所有业务状态
-- 执行日期: 2025-11-02
-- 目的: 更新chk_file_index_status约束，支持processing和failed状态

-- 删除旧的status检查约束（如果存在）
DO $$
BEGIN
    ALTER TABLE file_index DROP CONSTRAINT IF EXISTS chk_file_index_status;
    RAISE NOTICE 'Dropped old chk_file_index_status constraint';
EXCEPTION
    WHEN undefined_object THEN
        RAISE NOTICE 'Constraint chk_file_index_status does not exist, skipping drop';
END $$;

-- 创建新的status约束，支持所有业务状态
ALTER TABLE file_index ADD CONSTRAINT chk_file_index_status 
CHECK (status IN ('active', 'processing', 'failed', 'archived', 'deleted'));

-- 验证约束已正确创建
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.constraint_column_usage 
        WHERE constraint_name = 'chk_file_index_status'
    ) THEN
        RAISE EXCEPTION 'Migration failed: chk_file_index_status constraint not created';
    END IF;
    
    RAISE NOTICE 'Migration 003 completed successfully';
END $$;
