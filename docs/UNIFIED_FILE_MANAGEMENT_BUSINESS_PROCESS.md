# 统一文件管理系统 - 业务流程规范文档

## 文档版本
- **版本**: v1.0
- **生效日期**: 2025年11月2日
- **适用范围**: Flask (Port 5000) + FastAPI (Port 8000) 双架构系统

---

## 1. 系统概述

### 1.1 业务目标
统一文件管理系统为Smart Credit & Loan Manager平台提供企业级文件索引、存储和生命周期管理服务，确保：
- **多租户隔离**：每个公司（company）的文件完全隔离
- **双引擎支持**：Flask和FastAPI共享统一文件索引
- **100%可追溯性**：所有文件操作可审计
- **状态驱动**：文件生命周期状态机管理

### 1.2 核心模块
| 模块 | 功能 | 引擎 |
|------|------|------|
| bank | 银行对账单管理 | Flask |
| receipt | 收据管理 | Flask |
| ctos | CTOS信用报告 | Flask |
| loan | 贷款文档管理 | Flask |
| accounting | 会计凭证和报表 | FastAPI |

---

## 2. 角色与权限

### 2.1 用户角色
| 角色 | 权限范围 | 典型用户 |
|------|---------|---------|
| **admin** | 全局管理：所有公司文件的CRUD | 系统管理员 |
| **customer** | 单租户：仅本公司文件的CRUD | 普通用户 |

### 2.2 权限矩阵
| 操作 | admin | customer | 说明 |
|------|-------|----------|------|
| 查看本公司文件 | ✅ | ✅ | 基于current_user.company_id |
| 查看其他公司文件 | ✅ | ❌ | admin可跨租户查看 |
| 上传文件 | ✅ | ✅ | 自动绑定current_user.company_id |
| 更新文件状态 | ✅ | ✅ | TOCTOU原子性验证 |
| 删除文件（软删除） | ✅ | ❌ | 仅admin可删除 |
| 恢复文件 | ✅ | ❌ | 从archived恢复到active |

---

## 3. 文件生命周期状态机

### 3.1 状态定义
```
┌─────────────┐
│  processing │ ──┐
└─────────────┘   │
                  │ 验证成功
                  ▼
┌─────────────┐  ┌─────────────┐
│   failed    │◄─┤   active    │
└─────────────┘  └─────────────┘
                  │
                  │ 归档
                  ▼
┌─────────────┐  ┌─────────────┐
│  deleted    │◄─┤  archived   │
└─────────────┘  └─────────────┘
```

| 状态 | 含义 | 允许操作 |
|------|------|---------|
| **processing** | 文件上传中或处理中 | 更新状态 |
| **active** | 文件验证通过，可正常使用 | 查看、归档 |
| **failed** | 文件验证失败 | 查看、重新上传 |
| **archived** | 文件已归档（历史数据） | 查看、恢复、删除 |
| **deleted** | 文件已软删除 | 恢复（仅admin） |

### 3.2 状态转换规则
| 起始状态 | 目标状态 | 触发条件 | 权限要求 |
|---------|---------|---------|---------|
| processing | active | 验证通过 | customer/admin |
| processing | failed | 验证失败 | 自动 |
| active | archived | 用户归档 | customer/admin |
| archived | active | 用户恢复 | customer/admin |
| archived | deleted | 管理员删除 | admin |
| failed | processing | 重新上传 | customer/admin |

---

## 4. 核心业务流程

### 4.1 文件上传流程

#### 4.1.1 Flask引擎上传（银行对账单）
```
┌──────────┐
│ 用户选择 │
│ PDF文件  │
└────┬─────┘
     │
     ▼
┌──────────────────┐
│ 客户端PDF.js转换 │ ← 100%数据保留
│ PDF → CSV        │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ POST /upload/bank│
│ - 上传CSV文件    │
│ - session认证    │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Flask保存文件到  │
│ /uploads/        │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ 调用FastAPI注册  │
│ POST /api/files/ │
│      register    │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ file_index记录   │
│ status=processing│
│ validation=pending│
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ 后台验证流程     │
│ - 提取交易数据   │
│ - 验证余额       │
└────┬─────────────┘
     │
     ├─── 验证通过 ──► status=active, validation=passed
     │
     └─── 验证失败 ──► status=failed, validation=failed
```

#### 4.1.2 FastAPI引擎上传（会计凭证）
```
┌──────────┐
│ 用户上传 │
│ Excel文件│
└────┬─────┘
     │
     ▼
┌──────────────────┐
│ POST /api/files/ │
│      register    │
│ - JWT认证        │
│ - company_id绑定 │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ 原子性INSERT     │
│ - 验证company_id │
│ - 验证file_path  │
│ - 唯一性约束     │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ 返回file_id      │
│ status=processing│
└──────────────────┘
```

### 4.2 文件查询流程

#### 4.2.1 最近文件列表
```
GET /api/files/recent?limit=10&module=bank

┌──────────────────┐
│ 用户请求         │
│ + JWT token      │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ require_auth验证 │ ← 401 if未认证
│ 提取company_id   │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ 查询file_index   │
│ WHERE company_id │
│ ORDER BY created │
│       DESC       │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ 返回文件列表     │
│ {                │
│   success: true, │
│   company_id: 1, │
│   total: 10,     │
│   files: [...]   │
│ }                │
└──────────────────┘
```

#### 4.2.2 文件详情查询
```
GET /api/files/detail/{file_id}

┌──────────────────┐
│ 用户请求         │
│ + JWT token      │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ require_auth验证 │
│ 提取company_id   │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ 查询file_index   │
│ WHERE id AND     │
│ company_id       │ ← 租户隔离
└────┬─────────────┘
     │
     ├─── 找到 ──► 返回文件详情
     │
     └─── 未找到 ──► 404 Not Found
```

### 4.3 文件状态更新流程（TOCTOU防护）

```
PATCH /api/files/status/{file_id}?status=active&validation_status=passed

┌──────────────────┐
│ 用户请求         │
│ + JWT token      │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ require_auth验证 │
│ company_id=1     │
└────┬─────────────┘
     │
     ▼
┌──────────────────────────┐
│ 原子性UPDATE             │
│ UPDATE file_index        │
│ SET status='active'      │
│ WHERE id={file_id}       │
│ AND company_id=1         │ ← TOCTOU防护
└────┬─────────────────────┘
     │
     ├─── 更新成功(1行) ──► 200 OK
     │
     └─── 更新失败(0行) ──► 404/403 (文件不存在或无权限)
```

**TOCTOU防护机制**：
- ❌ **不安全方式**：先SELECT验证company_id，再UPDATE状态
- ✅ **安全方式**：UPDATE WHERE file_id AND company_id（原子性验证）

### 4.4 文件归档流程

```
┌──────────────────┐
│ 用户点击"归档"   │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ PATCH /status    │
│ status=archived  │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ 文件移至归档区   │
│ - 仍可查看       │
│ - 不出现在主列表 │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ 可恢复到active   │
│ 或删除(admin)    │
└──────────────────┘
```

---

## 5. 数据验证规范

### 5.1 文件路径验证
**规则**：
- 必须以`/files/company_{company_id}/`开头
- 路径唯一性约束（UNIQUE constraint）
- 禁止路径遍历攻击（`..`检测）

**示例**：
```
✅ 合法: /files/company_1/bank/statement_202511.csv
✅ 合法: /files/company_2/receipt/receipt_001.jpg
❌ 非法: /files/company_1/../company_2/data.csv
❌ 非法: /uploads/statement.csv (缺少company_id)
```

### 5.2 文件大小限制
| 文件类型 | 最大大小 | 说明 |
|---------|---------|------|
| CSV | 50 MB | 银行对账单 |
| PDF | 20 MB | CTOS报告 |
| Excel | 30 MB | 会计凭证 |
| 图片(JPG/PNG) | 10 MB | 收据 |

### 5.3 文件类型白名单
```python
ALLOWED_EXTENSIONS = {
    'bank': ['.csv', '.pdf'],
    'receipt': ['.jpg', '.jpeg', '.png'],
    'ctos': ['.pdf'],
    'loan': ['.pdf', '.docx'],
    'accounting': ['.xlsx', '.csv', '.pdf']
}
```

---

## 6. 异常处理流程

### 6.1 上传失败场景
| 错误代码 | 原因 | 用户提示 | 系统操作 |
|---------|------|---------|---------|
| 400 | 文件类型不允许 | "不支持该文件格式" | 拒绝上传 |
| 413 | 文件过大 | "文件超过XX MB限制" | 拒绝上传 |
| 409 | file_path重复 | "文件已存在" | 提示覆盖或重命名 |
| 500 | 存储失败 | "上传失败，请重试" | 记录错误日志 |

### 6.2 验证失败场景
| 验证类型 | 失败原因 | 状态 | 用户操作 |
|---------|---------|------|---------|
| 余额验证 | 期初+交易≠期末 | failed | 重新上传 |
| 格式验证 | CSV格式错误 | failed | 检查文件 |
| OCR验证 | 收据无法识别 | failed | 手动输入 |

### 6.3 权限拒绝场景
```
场景1: 跨租户访问
请求: GET /api/files/detail/999 (属于company_id=2)
用户: company_id=1
结果: 404 Not Found (不暴露文件存在性)

场景2: 未认证访问
请求: GET /api/files/recent
用户: 无JWT token
结果: 401 Unauthorized

场景3: customer删除文件
请求: DELETE /api/files/123
用户: role=customer
结果: 403 Forbidden
```

---

## 7. 审计日志规范

### 7.1 记录内容
所有文件操作记录到`audit_logs`表：

| 字段 | 说明 | 示例 |
|------|------|------|
| user_id | 操作用户 | 123 |
| action | 操作类型 | file_upload |
| entity_type | 实体类型 | file_index |
| entity_id | 文件ID | 456 |
| changes | 变更内容 | {"status": "processing→active"} |
| ip_address | 来源IP | 192.168.1.100 |
| created_at | 时间戳 | 2025-11-02 11:30:00 |

### 7.2 审计事件类型
| 事件 | action值 | 触发时机 |
|------|---------|---------|
| 文件上传 | file_upload | POST /register |
| 状态更新 | file_status_update | PATCH /status |
| 文件归档 | file_archive | status→archived |
| 文件删除 | file_delete | status→deleted |
| 文件恢复 | file_restore | archived→active |

---

## 8. 性能指标与SLA

### 8.1 响应时间要求
| 接口 | 目标响应时间 | 说明 |
|------|-------------|------|
| GET /recent | < 200ms | 缓存优化 |
| POST /register | < 500ms | 不含验证 |
| PATCH /status | < 100ms | 原子性操作 |
| GET /detail | < 150ms | 单条查询 |

### 8.2 吞吐量要求
- **并发上传**: 50 files/min per company
- **批量查询**: 1000 files per request (max)
- **数据库连接池**: 20 connections

### 8.3 可用性要求
- **系统可用性**: 99.5% (月度)
- **数据持久性**: 99.99%
- **备份频率**: 每日全量 + 实时增量

---

## 9. 集成规范

### 9.1 Flask → FastAPI 同步机制
```python
# Flask上传文件后，立即调用FastAPI注册
def upload_bank_statement(file, user):
    # 1. Flask保存文件
    file_path = save_to_uploads(file)
    
    # 2. 调用FastAPI注册
    response = requests.post(
        'http://localhost:8000/api/files/register',
        json={
            'company_id': user.company_id,
            'filename': file.filename,
            'file_path': file_path,
            'module': 'bank',
            'from_engine': 'flask',
            'uploaded_by': user.username
        },
        headers={'Authorization': f'Bearer {session_token}'}
    )
    
    # 3. 返回file_id
    return response.json()['file_id']
```

### 9.2 双引擎查询协议
- **Flask**: 通过HTTP调用FastAPI GET /api/files/recent
- **FastAPI**: 直接查询PostgreSQL file_index表
- **一致性**: 共享同一数据库，强一致性

---

## 10. 安全规范

### 10.1 认证机制
| 引擎 | 认证方式 | Token存储 |
|------|---------|----------|
| Flask | Session Cookie | Redis |
| FastAPI | JWT Token | HTTP-only Cookie |

### 10.2 租户隔离机制
```python
# ✅ 正确：强制使用current_user.company_id
@router.get("/recent")
def get_recent_files(current_user: User = Depends(require_auth)):
    company_id = current_user.company_id
    files = query_files(company_id)
    
# ❌ 错误：允许指定company_id
@router.get("/recent")
def get_recent_files(company_id: int):  # 不安全！
    files = query_files(company_id)
```

### 10.3 SQL注入防护
- ✅ 使用ORM参数化查询（SQLAlchemy）
- ❌ 禁止字符串拼接SQL
- ✅ 文件路径白名单验证

---

## 11. 故障恢复流程

### 11.1 文件丢失场景
```
检测 → 查询audit_logs → 定位原file_path → 从备份恢复 → 更新file_index
```

### 11.2 数据库约束冲突
```
场景: status值不在允许列表
解决: 
1. 检查migration 009已执行
2. 验证CHECK约束包含{active, processing, failed, archived, deleted}
3. 必要时手动执行: ALTER TABLE DROP/ADD CONSTRAINT
```

### 11.3 跨租户数据泄露检测
```
检测机制:
1. 定期审计audit_logs，查找异常访问模式
2. 监控404/403比率（高比率=可能的攻击）
3. 告警：同一用户短时间内尝试访问>100个不同file_id
```

---

## 12. 未来扩展规划

### 12.1 Phase 2 功能
- [ ] 文件版本控制（同一文档多版本）
- [ ] 文件分享链接（临时访问令牌）
- [ ] 文件标签系统（tags字段增强）
- [ ] 全文搜索（ElasticSearch集成）

### 12.2 Phase 3 功能
- [ ] 对象存储迁移（S3兼容）
- [ ] CDN加速（静态文件分发）
- [ ] 智能归档策略（基于访问频率）
- [ ] 数据生命周期管理（自动删除过期文件）

---

## 附录A：API端点快速参考

| 方法 | 端点 | 认证 | 租户隔离 | 说明 |
|------|------|------|---------|------|
| GET | /api/files/recent | ✅ | ✅ | 最近文件列表 |
| GET | /api/files/detail/{id} | ✅ | ✅ | 文件详情 |
| POST | /api/files/register | ✅ | ✅ | 注册新文件 |
| PATCH | /api/files/status/{id} | ✅ | ✅ | 更新文件状态 |

## 附录B：数据库Schema核心字段

```sql
CREATE TABLE file_index (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    module VARCHAR(50) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) UNIQUE NOT NULL,
    status VARCHAR(20) CHECK (status IN ('active', 'processing', 'failed', 'archived', 'deleted')),
    validation_status VARCHAR(20),
    uploaded_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);
```

---

**文档所有者**: Smart Credit & Loan Manager 技术团队  
**审批人**: Architect Agent  
**最后修订**: 2025年11月2日
