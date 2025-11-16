-- ============================================================
-- 第四批次优先级1：报表中心数据库迁移
-- 用途：创建导出任务表，支持批量导出和历史记录
-- 创建时间：2025-11-16
-- ============================================================

-- 创建导出任务表
CREATE TABLE IF NOT EXISTS export_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    export_format TEXT NOT NULL DEFAULT 'Excel',
    record_count INTEGER DEFAULT 0,
    file_size TEXT,
    download_url TEXT,
    status TEXT DEFAULT 'waiting',
    error_msg TEXT,
    filter_customer_id INTEGER,
    filter_account_type TEXT,
    filter_date_from TEXT,
    filter_date_to TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (customer_id) REFERENCES customers (id)
);

-- 创建索引以提升查询性能
CREATE INDEX IF NOT EXISTS idx_export_tasks_status ON export_tasks(status);
CREATE INDEX IF NOT EXISTS idx_export_tasks_created ON export_tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_export_tasks_customer ON export_tasks(customer_id);

-- ============================================================
-- 迁移完成
-- ============================================================
