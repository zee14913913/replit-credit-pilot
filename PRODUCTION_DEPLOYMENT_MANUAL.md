# 🚀 Smart Credit & Loan Manager - SFTP ERP 自动同步系统生产部署运维手册

**版本**: 1.0.0  
**更新日期**: 2025年11月11日  
**系统架构**: Replit Cloud → SFTP → Windows ERP → SQL ACC ERP Edition

---

## 📋 目录

1. [系统概述](#系统概述)
2. [部署前准备清单](#部署前准备清单)
3. [Replit 端配置](#replit-端配置)
4. [Windows ERP 端配置](#windows-erp-端配置)
5. [SQL ACC ERP Edition 自动导入配置](#sql-acc-erp-edition-自动导入配置)
6. [安全备份策略](#安全备份策略)
7. [监控与告警](#监控与告警)
8. [故障排查指南](#故障排查指南)
9. [日常运维操作](#日常运维操作)

---

## 🎯 系统概述

### 系统架构流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Replit Cloud Platform                    │
│                                                                   │
│  ┌────────────┐         ┌──────────────┐        ┌─────────────┐ │
│  │   Flask    │         │   FastAPI    │        │   SFTP      │ │
│  │  (Port     │◄────────│  (Port 8000) │◄───────│  Scheduler  │ │
│  │   5000)    │         │              │        │ (10 min)    │ │
│  └────────────┘         └──────┬───────┘        └─────────────┘ │
│                                 │                                 │
│                          ┌──────▼───────┐                        │
│                          │   PostgreSQL │                        │
│                          │ (Audit Logs) │                        │
│                          └──────────────┘                        │
└──────────────────────────────┬──────────────────────────────────┘
                               │ SFTP (SSH)
                               │ 161.142.139.122:22
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Windows ERP Server (On-Premise)               │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              C:\ERP_IMPORTS\                              │   │
│  │  ├── sales/                                               │   │
│  │  ├── suppliers/                                           │   │
│  │  ├── invoices/                                            │   │
│  │  ├── payments/                                            │   │
│  │  ├── bank_statements/                                     │   │
│  │  ├── payroll/                                             │   │
│  │  └── loan_charges/                                        │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                            │ Auto Import (Every 15 min)          │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │          SQL ACC ERP Edition Database                     │   │
│  │  - Sales Ledger                                           │   │
│  │  - Purchase Ledger                                        │   │
│  │  - General Ledger                                         │   │
│  │  - Bank Reconciliation                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 关键组件说明

| 组件 | 功能 | 技术栈 |
|------|------|--------|
| **FastAPI Backend** | SFTP 同步引擎、审计日志、REST API | FastAPI, Paramiko, SQLAlchemy |
| **SFTP Scheduler** | 自动化调度器（每 10 分钟执行一次） | Python Schedule, Background Thread |
| **SFTP Client** | 安全文件传输（SSH Host Key 验证） | Paramiko, SSH Protocol |
| **PostgreSQL** | 上传历史追踪、审计日志存储 | PostgreSQL (Neon) |
| **Windows ERP** | SFTP 服务器、文件接收点 | OpenSSH Server |
| **SQL ACC ERP** | 企业资源规划系统（会计核心） | SQL ACC ERP Edition |

---

## ✅ 部署前准备清单

### Replit 端检查项

- [ ] ✅ FastAPI 服务运行在 Port 8000
- [ ] ✅ Flask 服务运行在 Port 5000
- [ ] ✅ SFTP Scheduler 已启动（日志显示 "SFTP自动同步调度器已启动"）
- [ ] ✅ PostgreSQL 数据库连接正常
- [ ] ✅ `accounting_data/uploads/` 目录结构存在

### Windows ERP 端检查项

- [ ] 🔲 OpenSSH Server 已安装并运行
- [ ] 🔲 防火墙允许 SSH 端口 22 入站连接
- [ ] 🔲 SFTP 用户账户已创建（建议：`erp_sync`）
- [ ] 🔲 目标目录 `C:\ERP_IMPORTS\` 已创建，权限配置完成
- [ ] 🔲 已添加 Replit IP 到防火墙白名单（如适用）

### SQL ACC ERP Edition 端检查项

- [ ] 🔲 SQL ACC ERP Edition 已安装并激活
- [ ] 🔲 Auto Import 模块已启用（Tools → Preferences → Auto Import）
- [ ] 🔲 CSV 导入模板已配置（匹配 Replit 导出格式）
- [ ] 🔲 导入日志路径已设置：`C:\ERP_LOGS\import_logs\`
- [ ] 🔲 错误处理策略已配置：Skip errors and log

---

## 🛠️ Replit 端配置

### 步骤 1: 配置环境变量

在 Replit **Secrets** 中添加以下环境变量：

```bash
# SFTP 服务器配置
SFTP_HOST=161.142.139.122
SFTP_PORT=22
SFTP_USERNAME=erp_sync
SFTP_PASSWORD=<强密码，至少 16 位，包含大小写字母、数字、特殊字符>

# SFTP 安全配置
SFTP_VERIFY_HOST_KEY=true
SFTP_KNOWN_HOSTS_PATH=/home/runner/.ssh/known_hosts

# 上传目录配置
SFTP_REMOTE_BASE_DIR=C:/ERP_IMPORTS/
SFTP_LOCAL_BASE_DIR=accounting_data/uploads/

# 调度器配置（可选）
SFTP_SYNC_INTERVAL_MINUTES=10
SFTP_MAX_RETRY_ATTEMPTS=3
```

### 步骤 2: 添加 ERP 服务器 SSH Host Key

**在 Replit Shell 中执行：**

```bash
# 创建 .ssh 目录（如果不存在）
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 获取 ERP 服务器的 SSH Host Key
ssh-keyscan -p 22 161.142.139.122 >> ~/.ssh/known_hosts

# 验证 Host Key 已添加
cat ~/.ssh/known_hosts | grep 161.142.139.122
```

**预期输出示例：**
```
161.142.139.122 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC...
```

### 步骤 3: 测试 SFTP 连接

**手动触发同步测试：**

```bash
# 方法 1: 使用 API 端点
curl -X POST http://localhost:8000/api/sftp/sync/trigger

# 方法 2: 使用 Python 脚本
python3 -c "
from accounting_app.services.sftp.sync_service import SyncService
from accounting_app.database import get_db

db = next(get_db())
sync_service = SyncService(db)
result = sync_service.scan_and_upload()
print(result)
"
```

**预期成功响应：**
```json
{
  "success": true,
  "uploaded": 5,
  "failed": 0,
  "skipped": 2,
  "total_scanned": 7,
  "job_id": "SFTP-20251111-180530-001"
}
```

### 步骤 4: 验证调度器运行

**查看日志确认调度器状态：**

```bash
# 查看 FastAPI 日志
tail -f /tmp/logs/Accounting_API_*.log | grep "SFTP"
```

**预期日志输出：**
```
✅ SFTP自动同步调度器已启动（每10分钟同步一次）
📤 Starting scheduled SFTP sync...
✅ SFTP sync completed: 3 uploaded, 0 failed
```

---

## 🖥️ Windows ERP 端配置

### 步骤 1: 安装 OpenSSH Server

**在 Windows Server 上执行（以管理员身份）：**

```powershell
# 检查 OpenSSH Server 是否已安装
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*'

# 如果未安装，执行安装
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# 启动 SSH 服务并设置自动启动
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'

# 确认防火墙规则已创建
Get-NetFirewallRule -Name *ssh*
```

### 步骤 2: 创建 SFTP 用户账户

```powershell
# 创建专用 SFTP 用户
$Password = ConvertTo-SecureString "<强密码>" -AsPlainText -Force
New-LocalUser "erp_sync" -Password $Password -FullName "ERP Sync Account" -Description "SFTP automatic sync account"

# 将用户添加到 Remote Desktop Users 组（可选）
Add-LocalGroupMember -Group "Remote Desktop Users" -Member "erp_sync"
```

### 步骤 3: 配置 SFTP 目录权限

```powershell
# 创建导入目录结构
New-Item -Path "C:\ERP_IMPORTS" -ItemType Directory -Force
$folders = @("sales", "suppliers", "invoices", "payments", "bank_statements", "payroll", "loan_charges")
foreach ($folder in $folders) {
    New-Item -Path "C:\ERP_IMPORTS\$folder" -ItemType Directory -Force
}

# 设置权限（仅 erp_sync 用户可写入）
$acl = Get-Acl "C:\ERP_IMPORTS"
$AccessRule = New-Object System.Security.AccessControl.FileSystemAccessRule("erp_sync","Modify","ContainerInherit,ObjectInherit","None","Allow")
$acl.SetAccessRule($AccessRule)
Set-Acl "C:\ERP_IMPORTS" $acl

# 验证权限
Get-Acl "C:\ERP_IMPORTS" | Format-List
```

### 步骤 4: 配置 Windows 防火墙

```powershell
# 允许 SSH 端口 22 入站连接
New-NetFirewallRule -Name "SSH-SFTP" -DisplayName "SSH SFTP Service" -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22

# （可选）仅允许特定 IP 地址连接
New-NetFirewallRule -Name "SSH-SFTP-Restricted" -DisplayName "SSH SFTP (Replit Only)" -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 -RemoteAddress <Replit_IP_Address>
```

### 步骤 5: 测试 SFTP 连接（从本地）

```powershell
# 从本地测试 SFTP 登录
sftp erp_sync@localhost

# 成功登录后测试上传
sftp> cd /ERP_IMPORTS/sales
sftp> put test_file.csv
sftp> ls
sftp> quit
```

---

## 📊 SQL ACC ERP Edition 自动导入配置

### 步骤 1: 启用 Auto Import 模块

**在 SQL ACC ERP Edition 中：**

1. **打开主菜单** → Tools → Preferences → Auto Import Settings
2. **启用 Auto Import**:
   - ☑️ Enable Auto Import
   - **Scan Interval**: 15 minutes（建议与 SFTP 同步间隔匹配）
   - **Import Folder**: `C:\ERP_IMPORTS\`
   - **Backup Folder**: `C:\ERP_BACKUPS\imported\`
   - **Error Log Path**: `C:\ERP_LOGS\import_errors\`

3. **设置文件处理规则**:
   - **After successful import**: Move to backup folder
   - **After failed import**: Keep in place and log error
   - **Duplicate detection**: Skip and log warning

### 步骤 2: 配置 CSV 导入模板

**为每种数据类型创建导入模板：**

#### Sales (销售订单)

**导入路径**: `C:\ERP_IMPORTS\sales\`

**CSV 格式映射**:
```
Column 1: Date (日期) → ERP Field: Transaction Date
Column 2: Customer Code (客户代码) → ERP Field: Customer ID
Column 3: Amount (金额) → ERP Field: Total Amount
Column 4: Description (描述) → ERP Field: Remarks
Column 5: Reference No (参考编号) → ERP Field: Invoice No
```

**导入模板保存**: `Templates → Sales_Import_Template.xml`

#### Suppliers (供应商采购)

**导入路径**: `C:\ERP_IMPORTS\suppliers\`

**CSV 格式映射**:
```
Column 1: Date → ERP Field: Purchase Date
Column 2: Supplier Code → ERP Field: Supplier ID
Column 3: Amount → ERP Field: Purchase Amount
Column 4: Description → ERP Field: Item Description
Column 5: Invoice No → ERP Field: Supplier Invoice
```

#### Invoices (发票)

**导入路径**: `C:\ERP_IMPORTS\invoices\`

**CSV 格式映射**:
```
Column 1: Invoice Date → ERP Field: Invoice Date
Column 2: Invoice No → ERP Field: Invoice Number
Column 3: Customer Code → ERP Field: Customer ID
Column 4: Amount → ERP Field: Invoice Amount (Excl. Tax)
Column 5: Tax Amount → ERP Field: Tax Amount
Column 6: Total Amount → ERP Field: Total Amount (Incl. Tax)
```

#### Payments (客户付款)

**导入路径**: `C:\ERP_IMPORTS\payments\`

**CSV 格式映射**:
```
Column 1: Payment Date → ERP Field: Receipt Date
Column 2: Customer Code → ERP Field: Customer ID
Column 3: Payment Amount → ERP Field: Amount Received
Column 4: Payment Method → ERP Field: Payment Method (Cash/Cheque/Bank Transfer)
Column 5: Reference No → ERP Field: Receipt No
```

#### Bank Statements (银行对账单)

**导入路径**: `C:\ERP_IMPORTS\bank_statements\`

**CSV 格式映射**:
```
Column 1: Transaction Date → ERP Field: Statement Date
Column 2: Description → ERP Field: Transaction Description
Column 3: Debit Amount → ERP Field: Debit (Withdrawal)
Column 4: Credit Amount → ERP Field: Credit (Deposit)
Column 5: Balance → ERP Field: Running Balance
Column 6: Bank Code → ERP Field: Bank Account ID
```

#### Payroll (工资单)

**导入路径**: `C:\ERP_IMPORTS\payroll\`

**CSV 格式映射**:
```
Column 1: Pay Period → ERP Field: Payroll Month
Column 2: Employee ID → ERP Field: Employee Code
Column 3: Basic Salary → ERP Field: Basic Pay
Column 4: Allowances → ERP Field: Total Allowances
Column 5: Deductions → ERP Field: Total Deductions
Column 6: Net Pay → ERP Field: Net Salary
```

#### Loan Charges (贷款费用)

**导入路径**: `C:\ERP_IMPORTS\loan_charges\`

**CSV 格式映射**:
```
Column 1: Charge Date → ERP Field: Transaction Date
Column 2: Loan Account → ERP Field: Loan Account No
Column 3: Charge Type → ERP Field: Charge Category (Interest/Fee/Penalty)
Column 4: Amount → ERP Field: Charge Amount
Column 5: Description → ERP Field: Remarks
```

### 步骤 3: 设置自动导入任务计划

**在 Windows Task Scheduler 中：**

```powershell
# 创建每 15 分钟自动导入任务
$Action = New-ScheduledTaskAction -Execute "C:\Program Files\SQL ACC ERP\AutoImport.exe" -Argument "-source C:\ERP_IMPORTS -backup C:\ERP_BACKUPS"
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration ([TimeSpan]::MaxValue)
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName "SQL_ACC_Auto_Import" -Action $Action -Trigger $Trigger -Principal $Principal -Description "Auto import CSV files from ERP_IMPORTS to SQL ACC"
```

### 步骤 4: 验证自动导入功能

**手动测试导入流程：**

1. **上传测试文件**:
   - 在 Replit 中上传测试 CSV 到 `accounting_data/uploads/sales/test_sales.csv`
   - 等待 10 分钟（SFTP 同步周期）

2. **检查 Windows ERP 服务器**:
   - 确认文件出现在 `C:\ERP_IMPORTS\sales\test_sales.csv`

3. **检查 SQL ACC ERP**:
   - 等待 15 分钟（Auto Import 周期）
   - 打开 Sales → Sales Order List → 搜索测试订单
   - 确认数据已导入

4. **检查备份与日志**:
   - 成功导入后，文件应移至 `C:\ERP_BACKUPS\imported\sales\test_sales_20251111_1830.csv`
   - 日志文件：`C:\ERP_LOGS\import_logs\import_20251111.log`

---

## 🔐 安全备份策略

### 1. Replit 端数据库备份

**每日自动备份（使用 Replit Scheduled Tasks）：**

```python
# backup_script.py
import os
import subprocess
from datetime import datetime

def backup_postgresql():
    """每日备份 PostgreSQL 数据库"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"/tmp/backups/postgres_backup_{timestamp}.sql"
    
    os.makedirs("/tmp/backups", exist_ok=True)
    
    # 使用 pg_dump 备份
    subprocess.run([
        "pg_dump",
        os.environ["DATABASE_URL"],
        "-f", backup_file
    ])
    
    print(f"✅ Backup completed: {backup_file}")
    
    # 上传到云端存储（如 Replit Object Storage）
    # ... 实现云端上传逻辑

if __name__ == "__main__":
    backup_postgresql()
```

**在 Replit 中设置 Cron Job：**
```bash
# 每天凌晨 2:00 执行备份
0 2 * * * /usr/bin/python3 /home/runner/workspace/backup_script.py
```

### 2. Windows ERP 端文件备份

**PowerShell 备份脚本（`C:\Scripts\erp_backup.ps1`）：**

```powershell
# ERP 文件备份脚本
$SourcePath = "C:\ERP_IMPORTS"
$BackupPath = "D:\ERP_Backups\$(Get-Date -Format 'yyyyMMdd')"
$RetentionDays = 30

# 创建备份目录
New-Item -Path $BackupPath -ItemType Directory -Force

# 复制文件（保留时间戳）
Copy-Item -Path "$SourcePath\*" -Destination $BackupPath -Recurse -Force

# 压缩备份
Compress-Archive -Path $BackupPath -DestinationPath "$BackupPath.zip" -Force

# 删除超过 30 天的旧备份
Get-ChildItem "D:\ERP_Backups" | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-$RetentionDays)} | Remove-Item -Recurse -Force

Write-Host "✅ ERP backup completed: $BackupPath.zip"
```

**在 Windows Task Scheduler 中配置每日备份：**

```powershell
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\Scripts\erp_backup.ps1"
$Trigger = New-ScheduledTaskTrigger -Daily -At "01:00AM"
Register-ScheduledTask -TaskName "ERP_Daily_Backup" -Action $Action -Trigger $Trigger -Description "Daily backup of ERP import files"
```

### 3. SQL ACC ERP Edition 数据库备份

**每日数据库备份（SQL Server）：**

```sql
-- 创建维护计划（在 SQL Server Management Studio 中）
USE msdb;
GO

EXEC sp_add_jobstep
    @job_name = N'Daily_ACC_Backup',
    @step_name = N'Backup Database',
    @command = N'
        BACKUP DATABASE [SQL_ACC_ERP]
        TO DISK = N''D:\SQLBackups\SQL_ACC_ERP_'' + CONVERT(VARCHAR(8), GETDATE(), 112) + ''.bak''
        WITH COMPRESSION, STATS = 10;
    ';
```

### 4. 灾难恢复测试计划

**每季度执行一次恢复演练：**

1. **模拟数据丢失场景**（在测试环境）
2. **从备份恢复 PostgreSQL 数据库**
3. **从备份恢复 Windows 文件**
4. **从备份恢复 SQL ACC 数据库**
5. **验证数据完整性**（对比生产环境数据）
6. **记录恢复时间与遇到的问题**

---

## 📊 监控与告警

### 1. Replit 端监控指标

**关键监控指标：**

| 指标 | 监控方式 | 告警阈值 |
|------|----------|----------|
| **SFTP 上传成功率** | 查询 `sftp_upload_job` 表 | < 95% 发送告警 |
| **调度器运行状态** | 检查日志中的 "SFTP sync completed" | > 20 分钟无日志 |
| **磁盘空间使用率** | `df -h` 检查 `/tmp` 空间 | > 80% 发送告警 |
| **数据库连接数** | PostgreSQL `pg_stat_activity` | > 80% 连接池 |
| **API 响应时间** | FastAPI 中间件统计 | > 5 秒 发送告警 |

**监控脚本示例（`monitor_sftp.py`）：**

```python
import requests
from datetime import datetime, timedelta

def check_sftp_health():
    """检查 SFTP 系统健康状态"""
    
    # 检查最近 30 分钟的上传任务
    response = requests.get("http://localhost:8000/api/sftp/sync/statistics")
    stats = response.json()
    
    # 计算成功率
    total = stats["total_jobs"]
    success = stats["successful_jobs"]
    success_rate = (success / total * 100) if total > 0 else 0
    
    if success_rate < 95:
        send_alert(f"⚠️ SFTP success rate dropped to {success_rate:.2f}%")
    
    # 检查最后一次同步时间
    last_sync = datetime.fromisoformat(stats["last_sync_time"])
    if datetime.now() - last_sync > timedelta(minutes=20):
        send_alert(f"⚠️ SFTP scheduler may be down. Last sync: {last_sync}")
    
    print(f"✅ SFTP Health Check Passed: {success_rate:.2f}% success rate")

def send_alert(message):
    """发送告警（邮件 + SMS）"""
    # 使用 Twilio 发送 SMS
    # 使用 SendGrid 发送邮件
    print(f"🚨 ALERT: {message}")

if __name__ == "__main__":
    check_sftp_health()
```

### 2. Windows ERP 端监控

**PowerShell 监控脚本（`C:\Scripts\monitor_erp.ps1`）：**

```powershell
# 监控 ERP SFTP 服务状态
$sshService = Get-Service -Name "sshd"
if ($sshService.Status -ne "Running") {
    Send-MailMessage -To "admin@company.com" -From "erp@company.com" -Subject "⚠️ SSH Service Down" -Body "SSH service is not running on ERP server" -SmtpServer "smtp.company.com"
}

# 检查磁盘空间
$disk = Get-PSDrive C
$freeSpacePercent = ($disk.Free / $disk.Used) * 100
if ($freeSpacePercent -lt 20) {
    Write-Warning "⚠️ Disk space low: $freeSpacePercent% free"
}

# 检查最近是否有新文件上传
$latestFile = Get-ChildItem "C:\ERP_IMPORTS\*\*" -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$timeSinceLastUpload = (Get-Date) - $latestFile.LastWriteTime
if ($timeSinceLastUpload.TotalMinutes -gt 30) {
    Write-Warning "⚠️ No new files uploaded in the last 30 minutes"
}
```

### 3. 告警通知渠道

**多渠道告警配置：**

1. **邮件告警** (SendGrid):
   - 接收人：IT 管理员、系统管理员
   - 触发条件：严重错误、系统停机

2. **SMS 告警** (Twilio):
   - 接收人：On-call 值班人员
   - 触发条件：超过 30 分钟无同步、数据库连接失败

3. **Slack/Teams 通知**:
   - 频道：#erp-alerts
   - 触发条件：所有告警（包括警告级别）

---

## 🔧 故障排查指南

### 问题 1: SFTP 连接失败

**症状**:
```
❌ Host key verification failed: 161.142.139.122:22 not found in known_hosts
```

**解决方案**:
```bash
# 添加 Host Key
ssh-keyscan -p 22 161.142.139.122 >> ~/.ssh/known_hosts

# 验证
cat ~/.ssh/known_hosts | grep 161.142.139.122
```

---

### 问题 2: SFTP 上传失败（认证错误）

**症状**:
```
❌ Authentication failed for user: erp_sync
```

**排查步骤**:
1. **验证用户名和密码**:
   ```bash
   # 手动测试 SFTP 登录
   sftp erp_sync@161.142.139.122
   ```

2. **检查 Windows 用户状态**:
   ```powershell
   Get-LocalUser -Name "erp_sync"
   ```

3. **重置密码**（如果需要）:
   ```powershell
   $Password = ConvertTo-SecureString "<新密码>" -AsPlainText -Force
   Set-LocalUser -Name "erp_sync" -Password $Password
   ```

4. **更新 Replit Secrets**:
   - 在 Replit Secrets 中更新 `SFTP_PASSWORD`

---

### 问题 3: 文件未导入到 SQL ACC

**症状**:
- 文件已上传到 `C:\ERP_IMPORTS\sales\`，但 SQL ACC 中未出现数据

**排查步骤**:

1. **检查 Auto Import 服务状态**:
   - 打开 SQL ACC ERP → Tools → Auto Import Status
   - 确认服务状态为 "Running"

2. **查看导入日志**:
   ```powershell
   Get-Content "C:\ERP_LOGS\import_logs\import_$(Get-Date -Format 'yyyyMMdd').log" -Tail 50
   ```

3. **检查 CSV 格式**:
   - 确认 CSV 列顺序与导入模板匹配
   - 检查日期格式（应为 `YYYY-MM-DD`）
   - 验证数值格式（无货币符号）

4. **手动导入测试**:
   - 在 SQL ACC 中：File → Import → CSV
   - 选择问题文件，查看详细错误消息

---

### 问题 4: 调度器未运行

**症状**:
```
日志超过 20 分钟无 "SFTP sync completed" 消息
```

**解决方案**:

1. **检查 FastAPI 服务状态**:
   ```bash
   curl http://localhost:8000/
   ```

2. **重启 Accounting API workflow**:
   - 在 Replit 界面点击 "Restart Workflow"

3. **查看调度器日志**:
   ```bash
   tail -f /tmp/logs/Accounting_API_*.log | grep -i schedule
   ```

4. **手动触发同步**:
   ```bash
   curl -X POST http://localhost:8000/api/sftp/sync/trigger
   ```

---

### 问题 5: 磁盘空间不足

**症状**:
```
❌ No space left on device
```

**Windows 端解决方案**:

```powershell
# 清理旧备份文件（超过 30 天）
Get-ChildItem "D:\ERP_Backups" | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | Remove-Item -Recurse -Force

# 清理导入日志（超过 60 天）
Get-ChildItem "C:\ERP_LOGS" -Recurse | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-60)} | Remove-Item -Force
```

**Replit 端解决方案**:

```bash
# 清理临时文件
rm -rf /tmp/logs/*_old.log
rm -rf /tmp/backups/*_old.sql

# 清理旧的 SFTP 上传记录（保留最近 90 天）
python3 -c "
from accounting_app.database import get_db
from accounting_app.models import SFTPUploadJob
from datetime import datetime, timedelta

db = next(get_db())
cutoff_date = datetime.now() - timedelta(days=90)
db.query(SFTPUploadJob).filter(SFTPUploadJob.created_at < cutoff_date).delete()
db.commit()
print('✅ Old SFTP records cleaned')
"
```

---

## 🛠️ 日常运维操作

### 每日检查清单

- [ ] 检查 SFTP 上传成功率（目标 > 98%）
- [ ] 查看审计日志是否有异常操作
- [ ] 确认 SQL ACC 数据导入无错误
- [ ] 检查磁盘空间使用率（< 80%）
- [ ] 验证备份任务已执行

### 每周维护任务

- [ ] 审查 SFTP 上传历史记录
- [ ] 检查并清理旧备份文件
- [ ] 更新系统日志分析报告
- [ ] 验证告警通知渠道正常工作

### 每月维护任务

- [ ] 审查安全日志（登录失败、权限错误）
- [ ] 更新文档（如有配置变更）
- [ ] 执行灾难恢复演练
- [ ] 检查系统性能指标趋势

### 手动操作指南

#### 手动触发 SFTP 同步

**方法 1: 使用 API**
```bash
curl -X POST http://localhost:8000/api/sftp/sync/trigger
```

**方法 2: 使用 Replit Shell**
```bash
python3 -c "
from accounting_app.services.sftp.sync_service import SyncService
from accounting_app.database import get_db

db = next(get_db())
sync = SyncService(db)
result = sync.scan_and_upload()
print(result)
"
```

#### 查询上传历史

```bash
curl http://localhost:8000/api/sftp/sync/history?limit=10
```

#### 查询统计数据

```bash
curl http://localhost:8000/api/sftp/sync/statistics
```

---

## 📞 技术支持联系方式

| 角色 | 姓名 | 联系方式 | 负责范围 |
|------|------|----------|----------|
| **系统架构师** | ZEE | zee@company.com | 整体系统架构与集成 |
| **Replit 管理员** | [姓名] | [邮箱] | Replit 平台配置与维护 |
| **Windows ERP 管理员** | [姓名] | [邮箱] | Windows 服务器与 SFTP |
| **SQL ACC 管理员** | [姓名] | [邮箱] | ERP 系统与数据导入 |
| **On-call 值班** | [姓名] | [手机] | 24/7 紧急故障处理 |

---

## 📝 附录

### A. CSV 文件格式标准

**通用要求**:
- 编码：UTF-8
- 分隔符：逗号（`,`）
- 日期格式：`YYYY-MM-DD`
- 数值格式：无货币符号，小数点使用 `.`
- 文本引号：双引号 `"`
- 第一行：列标题（可选，取决于导入模板）

### B. 常用 SQL 查询

**查询最近 10 次 SFTP 上传任务**:
```sql
SELECT job_id, status, created_at, completed_at, job_metadata
FROM sftp_upload_job
ORDER BY created_at DESC
LIMIT 10;
```

**统计每日上传成功率**:
```sql
SELECT 
    DATE(created_at) as upload_date,
    COUNT(*) as total_jobs,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_jobs,
    ROUND(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate
FROM sftp_upload_job
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY upload_date DESC;
```

### C. 环境变量完整清单

```bash
# PostgreSQL Database
DATABASE_URL=postgresql://user:password@host:port/database
PGHOST=<host>
PGPORT=5432
PGUSER=<user>
PGPASSWORD=<password>
PGDATABASE=<database>

# SFTP Configuration
SFTP_HOST=161.142.139.122
SFTP_PORT=22
SFTP_USERNAME=erp_sync
SFTP_PASSWORD=<strong_password>
SFTP_VERIFY_HOST_KEY=true
SFTP_KNOWN_HOSTS_PATH=/home/runner/.ssh/known_hosts
SFTP_REMOTE_BASE_DIR=C:/ERP_IMPORTS/
SFTP_LOCAL_BASE_DIR=accounting_data/uploads/

# System Configuration
ADMIN_EMAIL=admin@company.com
ADMIN_PASSWORD=<admin_password>
```

---

## 🎯 部署检查表（最终确认）

### Replit 端

- [ ] ✅ 所有环境变量已配置
- [ ] ✅ SSH Host Key 已添加到 known_hosts
- [ ] ✅ SFTP 连接测试成功
- [ ] ✅ 调度器日志显示正常运行
- [ ] ✅ 备份脚本已配置并测试

### Windows ERP 端

- [ ] 🔲 OpenSSH Server 已安装并运行
- [ ] 🔲 SFTP 用户账户已创建
- [ ] 🔲 目标目录权限配置完成
- [ ] 🔲 防火墙规则已添加
- [ ] 🔲 备份脚本已配置并测试

### SQL ACC ERP Edition 端

- [ ] 🔲 Auto Import 模块已启用
- [ ] 🔲 CSV 导入模板已配置（7 种类型）
- [ ] 🔲 自动导入任务计划已设置
- [ ] 🔲 导入日志路径已配置
- [ ] 🔲 手动导入测试成功

### 监控与告警

- [ ] 🔲 监控脚本已部署
- [ ] 🔲 告警通知渠道已测试
- [ ] 🔲 值班人员联系方式已确认

### 文档与培训

- [ ] 🔲 运维手册已交付给 IT 团队
- [ ] 🔲 IT 团队已完成培训
- [ ] 🔲 故障排查流程已演练

---

**文档版本**: 1.0.0  
**最后更新**: 2025年11月11日  
**下次审查**: 2025年12月11日

---

*本运维手册由 Smart Credit & Loan Manager 开发团队编写，旨在确保 SFTP ERP 自动同步系统的稳定运行与高效维护。如有任何疑问或建议，请联系技术支持团队。*
