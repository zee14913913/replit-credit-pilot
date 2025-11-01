-- Phase 2-2 Task 5: 创建API密钥表
-- 执行日期: 2025-11-01
-- 目的: 支持程序化API访问，提供API密钥认证机制

CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 密钥信息（SHA-256哈希存储，不存储明文）
    key_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA-256生成64字符哈希
    key_prefix VARCHAR(20) NOT NULL,  -- 前8-12字符用于快速查找 (sk_live_xxxx, sk_test_xxxx)
    
    -- 元数据
    name VARCHAR(255) NOT NULL,  -- 密钥名称/描述（如"Production API Key", "CI/CD Pipeline"）
    environment VARCHAR(20) NOT NULL DEFAULT 'live',  -- live, test
    
    -- 权限控制（JSONB存储权限列表）
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,  -- ["export:bank_statements", "read:transactions", etc.]
    
    -- 使用限制
    rate_limit INTEGER DEFAULT 100,  -- 每分钟请求限制
    expires_at TIMESTAMP WITH TIME ZONE,  -- 过期时间（NULL表示永不过期）
    
    -- 状态追踪
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_used_at TIMESTAMP WITH TIME ZONE,  -- 最后使用时间
    last_used_ip VARCHAR(45),  -- 最后使用的IP地址
    
    -- 审计时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),  -- 创建人
    revoked_at TIMESTAMP WITH TIME ZONE,  -- 撤销时间
    revoked_by INTEGER REFERENCES users(id),  -- 撤销人
    revoked_reason TEXT,  -- 撤销原因
    
    -- 约束
    CONSTRAINT chk_environment CHECK (environment IN ('live', 'test')),
    CONSTRAINT chk_rate_limit CHECK (rate_limit > 0 AND rate_limit <= 10000),
    CONSTRAINT chk_key_prefix_format CHECK (key_prefix ~ '^sk_(live|test)_[a-zA-Z0-9]{8,12}$')
);

-- 创建索引提升查询性能
CREATE INDEX IF NOT EXISTS idx_api_keys_company_id ON api_keys(company_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);  -- 认证时快速查找
CREATE INDEX IF NOT EXISTS idx_api_keys_key_prefix ON api_keys(key_prefix);  -- 前缀匹配
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active) WHERE is_active = TRUE;  -- 部分索引
CREATE INDEX IF NOT EXISTS idx_api_keys_expires_at ON api_keys(expires_at) WHERE expires_at IS NOT NULL;

-- 复合索引（常见查询模式）
CREATE INDEX IF NOT EXISTS idx_api_keys_company_active ON api_keys(company_id, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_api_keys_user_active ON api_keys(user_id, is_active) WHERE is_active = TRUE;

-- 自动更新updated_at时间戳
CREATE OR REPLACE FUNCTION update_api_keys_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_api_keys_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_api_keys_updated_at();

-- 验证迁移结果
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'api_keys'
    ) THEN
        RAISE EXCEPTION 'Migration failed: api_keys table not created';
    END IF;
END $$;

-- 迁移完成
COMMENT ON TABLE api_keys IS 'Phase 2-2 Task 5: API密钥表，支持程序化API访问';
COMMENT ON COLUMN api_keys.key_hash IS 'SHA-256哈希存储，绝不存储明文密钥';
COMMENT ON COLUMN api_keys.key_prefix IS '密钥前缀（如sk_live_abc123），用于快速查找和用户识别';
COMMENT ON COLUMN api_keys.permissions IS 'JSONB数组存储权限列表，如["export:bank_statements", "read:transactions"]';
COMMENT ON COLUMN api_keys.rate_limit IS '每分钟API请求限制，默认100次/分钟';
COMMENT ON COLUMN api_keys.environment IS 'live=生产环境密钥，test=测试环境密钥';
