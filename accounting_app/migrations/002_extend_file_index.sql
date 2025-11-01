-- Phase 1-3: 扩展file_index表，支持软删除和回收站功能
-- 执行日期: 2025-01-XX
-- 目的: 为Flask和FastAPI提供统一的文件索引系统

-- 添加status字段（active/archived/deleted）
DO $$
BEGIN
    -- 添加status字段
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'file_index' AND column_name = 'status'
    ) THEN
        ALTER TABLE file_index ADD COLUMN status VARCHAR(20) DEFAULT 'active';
    END IF;
    
    -- 添加约束
    BEGIN
        ALTER TABLE file_index ADD CONSTRAINT chk_file_index_status 
        CHECK (status IN ('active', 'archived', 'deleted'));
    EXCEPTION
        WHEN duplicate_object THEN NULL;
    END;
END $$;

-- 添加deleted_at字段
ALTER TABLE file_index 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

-- 创建索引提升查询性能
CREATE INDEX IF NOT EXISTS idx_file_index_status ON file_index(status);
CREATE INDEX IF NOT EXISTS idx_file_index_deleted_at ON file_index(deleted_at);
CREATE INDEX IF NOT EXISTS idx_file_index_company_module ON file_index(company_id, module);

-- 验证迁移结果
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'file_index' AND column_name = 'status'
    ) THEN
        RAISE EXCEPTION 'Migration failed: status column not created';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'file_index' AND column_name = 'deleted_at'
    ) THEN
        RAISE EXCEPTION 'Migration failed: deleted_at column not created';
    END IF;
END $$;

-- 迁移完成
-- Phase 1-3 file_index扩展已完成
