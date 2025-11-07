# CreditPilot 生产环境部署指南

---

## 📋 目录

1. [选项B：生产服务接入](#选项b生产服务接入)
   - [B1. OCR服务真接入](#b1-ocr服务真接入)
   - [B2. Email提醒配置](#b2-email提醒配置)
   - [B3. SMS提醒配置](#b3-sms提醒配置)

2. [选项C：功能测试](#选项c功能测试)
   - [C1. PDF账单解析测试](#c1-pdf账单解析测试)
   - [C2. OCR收据识别测试](#c2-ocr收据识别测试)
   - [C3. 发票PDF导出测试](#c3-发票pdf导出测试)

3. [选项D：继续开发](#选项d继续开发)
   - [D1. PostgreSQL数据库集成](#d1-postgresql数据库集成)
   - [D2. 用户认证系统](#d2-用户认证系统)
   - [D3. 月度报告自动生成](#d3-月度报告自动生成)
   - [D4. Dashboard数据可视化](#d4-dashboard数据可视化)

---

## 选项B：生产服务接入

### B1. OCR服务真接入

#### 方案1：Google Vision API（推荐 - 准确率最高）

**步骤1：获取Google Cloud凭证**
```bash
1. 访问 https://console.cloud.google.com
2. 创建新项目或选择现有项目
3. 启用 Cloud Vision API
4. 创建服务账号：
   - IAM & Admin → Service Accounts → Create Service Account
   - 赋予角色：Cloud Vision API User
   - 创建密钥（JSON格式）下载到本地
```

**步骤2：添加到Replit Secrets**
```bash
1. 打开Replit左侧工具栏 → Secrets（锁图标）
2. 添加新Secret：
   Key: GOOGLE_VISION_CREDENTIALS
   Value: 粘贴整个JSON文件内容（从 { 到 }）
3. 添加另一个Secret：
   Key: OCR_PROVIDER
   Value: google
```

**步骤3：安装依赖**
```bash
# Replit Shell中执行：
pip install google-cloud-vision
```

**步骤4：测试配置**
```bash
# 访问页面：
http://your-repl-url/credit-cards/receipts

# 上传任意JPG/PNG收据图片
# 应该看到OCR Results表格显示识别结果
```

---

#### 方案2：Azure Computer Vision（企业级备选）

**步骤1：创建Azure资源**
```bash
1. 访问 https://portal.azure.com
2. 创建资源 → AI + Machine Learning → Computer Vision
3. 选择定价层：Free F0（每月5000次免费）
4. 创建后获取：
   - Endpoint URL (例如: https://xxx.cognitiveservices.azure.com/)
   - API Key（在Keys and Endpoint页面）
```

**步骤2：添加到Replit Secrets**
```bash
Secret 1:
  Key: AZURE_VISION_ENDPOINT
  Value: 你的Endpoint URL

Secret 2:
  Key: AZURE_VISION_KEY
  Value: 你的API Key

Secret 3:
  Key: OCR_PROVIDER
  Value: azure
```

**步骤3：安装依赖**
```bash
pip install azure-ai-vision-imageanalysis
```

---

#### 方案3：Tesseract OCR（离线免费方案）

**步骤1：系统依赖已安装**
```bash
# Tesseract已在系统中（pytesseract已安装）
# 无需额外配置
```

**步骤2：设置提供商**
```bash
在Replit Secrets中添加：
  Key: OCR_PROVIDER
  Value: tesseract
```

**步骤3：限制说明**
```
优点：完全免费，无API限制
缺点：准确率较低（约70-80%），中文识别较弱
适用场景：开发测试、非关键业务
```

---

### B2. Email提醒配置

**步骤1：获取SendGrid API密钥**
```bash
1. 访问 https://sendgrid.com （已有账号直接登录）
2. Settings → API Keys → Create API Key
3. 选择权限：Full Access 或 Mail Send（推荐）
4. 复制生成的密钥（格式：SG.xxxxxxxxxxxx）
```

**步骤2：添加到Replit Secrets**
```bash
# 在Replit Secrets中添加：
Key: SENDGRID_API_KEY
Value: SG.你的密钥

# 添加发件人邮箱（必须在SendGrid中验证）：
Key: SENDER_EMAIL
Value: noreply@yourdomain.com

# （可选）添加收件人邮箱：
Key: ADMIN_EMAIL
Value: admin@yourdomain.com
```

**步骤3：验证发件人域名**
```bash
1. SendGrid → Settings → Sender Authentication
2. Domain Authentication → Authenticate Your Domain
3. 选择DNS提供商（如Cloudflare/GoDaddy）
4. 添加提供的CNAME记录到您的DNS
5. 验证完成后邮件送达率提升至98%+
```

**步骤4：测试邮件发送**
```bash
# 系统会在每天8:00 AM (Malaysia时区) 自动发送提醒
# 立即测试：访问 /test/send-email 端点（需添加测试路由）
```

---

### B3. SMS提醒配置

**步骤1：Twilio账号配置（Replit已集成）**
```bash
1. 访问 https://www.twilio.com/console
2. 获取凭证：
   - Account SID（格式：ACxxxxxxxxxxxxxxxx）
   - Auth Token（格式：xxxxxxxxxxxxxxxx）
   - Twilio Phone Number（格式：+1234567890）
```

**步骤2：添加到Replit Secrets**
```bash
# Twilio凭证：
Key: TWILIO_ACCOUNT_SID
Value: 你的Account SID

Key: TWILIO_AUTH_TOKEN
Value: 你的Auth Token

Key: TWILIO_PHONE_NUMBER
Value: 你的Twilio号码（+开头）

# 接收号码（用于测试）：
Key: ADMIN_PHONE
Value: +60123456789（马来西亚手机格式）
```

**步骤3：验证手机号码（免费账号必需）**
```bash
1. Twilio Console → Phone Numbers → Verified Caller IDs
2. 点击 "+" 添加新号码
3. 输入+60开头的马来西亚手机号
4. 输入收到的验证码
```

**步骤4：测试SMS发送**
```bash
# 重启应用后，每天8:00 AM会自动发送
# 立即测试：
curl -X POST http://your-repl-url/test/send-sms
```

---

## 选项C：功能测试

### C1. PDF账单解析测试

**测试场景1：标准Maybank账单**

```bash
步骤1：准备测试文件
- 下载真实Maybank信用卡账单PDF
- 确保包含：Previous Balance, New Charges, Total Amount Due

步骤2：访问上传页面
http://your-repl-url/credit-cards/statements/page

步骤3：上传文件
- 点击"Choose File"
- 选择PDF文件
- 点击"Upload & Parse"

步骤4：验证结果
✅ 应显示解析成功消息
✅ 检查提取的字段：
   - Statement Date（账单日期）
   - Due Date（到期日期）
   - Previous Balance（上期余额）
   - New Charges（本期消费）
   - Minimum Payment（最低还款）
   - Total Amount Due（应付总额）

步骤5：验证交易列表
- 访问 /credit-cards/transactions
- 确认新交易已导入
- 检查分类标签（OWNER/INFINITE）
```

**测试场景2：CIMB/Hong Leong账单**

```bash
重复上述步骤，测试其他银行格式
- CIMB：Balance Change格式
- Hong Leong：Standard格式
- Public Bank：Universal格式

预期行为：
- Universal Parser自动识别格式
- 容错处理异常字段
- 日志输出调试信息
```

---

### C2. OCR收据识别测试

**测试场景1：清晰收据（理想情况）**

```bash
步骤1：准备测试图片
- 拍摄或下载清晰的餐厅收据
- 格式：JPG/PNG
- 分辨率：至少1080p
- 确保包含：商户名、金额、日期

步骤2：访问收据匹配页面
http://your-repl-url/credit-cards/receipts

步骤3：上传收据
- 点击"Choose Files"（支持多选）
- 选择1-5张收据图片
- 点击"Upload & OCR"

步骤4：验证OCR结果
在"Latest OCR Results"表格中检查：
✅ Merchant（商户名准确）
✅ Amount（金额精确到分）
✅ Date（日期格式YYYY-MM-DD）
✅ Confidence（置信度 >0.85为优秀）
✅ Raw（原始文本前80字符）

步骤5：检查自动匹配
- 查看"Pending Matching"表格
- 系统应自动匹配相似金额/日期的交易
- Similarity显示"Good"/"Excellent"
- 点击"Confirm"完成匹配
```

**测试场景2：模糊/手写收据（挑战场景）**

```bash
测试文件：
- 模糊照片（低光照/抖动）
- 手写收据
- 倾斜角度拍摄

预期行为：
- Google Vision：仍有80%+识别率
- Azure：类似表现
- Tesseract：识别率下降至50-60%

验证点：
- Confidence分数下降
- 部分字段可能为null
- 需手动修正
```

---

### C3. 发票PDF导出测试

**测试场景1：单供应商发票**

```bash
步骤1：访问供应商发票页面
http://your-repl-url/credit-cards/supplier-invoices

步骤2：选择参数
- Supplier下拉框：选择"Dinas"
- Month输入框：输入"2025-11"

步骤3：生成PDF
- 点击粉色"Generate PDF"按钮
- 浏览器应自动下载PDF文件

步骤4：验证PDF内容
打开下载的PDF，检查：
✅ 公司Logo（INFINITE GZ SDN. BHD.）
✅ 粉色标题（#FF007F）
✅ 发票编号（INV-20251107-DINAS）
✅ 供应商信息（Dinas Restaurant）
✅ 交易明细表格
✅ 服务费计算（1%）
✅ 总计金额正确
```

**测试场景2：月度汇总发票**

```bash
步骤1：修改URL参数
http://your-repl-url/invoices/supplier.pdf?supplier=ALL&month=2025-11

步骤2：验证内容
✅ 包含所有7家供应商
✅ 分页处理（超过50条交易）
✅ 总服务费汇总
✅ 页脚页码显示

步骤3：性能测试
- 生成包含200+交易的大文件
- 应在5秒内完成
- PDF大小 <2MB
```

---

## 选项D：继续开发

### D1. PostgreSQL数据库集成

**阶段1：数据库设计（已有DATABASE_URL）**

```sql
-- 核心表结构设计

-- 1. 客户表
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    customer_code VARCHAR(20) UNIQUE NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. 信用卡表
CREATE TABLE credit_cards (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    card_number_last4 VARCHAR(4) NOT NULL,
    bank_name VARCHAR(50) NOT NULL,
    card_type VARCHAR(20), -- OWNER / INFINITE
    credit_limit DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. 账单表
CREATE TABLE statements (
    id SERIAL PRIMARY KEY,
    card_id INT REFERENCES credit_cards(id),
    statement_date DATE NOT NULL,
    due_date DATE NOT NULL,
    previous_balance DECIMAL(12,2),
    new_charges DECIMAL(12,2),
    total_amount_due DECIMAL(12,2),
    minimum_payment DECIMAL(12,2),
    pdf_file_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. 交易表
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    statement_id INT REFERENCES statements(id),
    transaction_date DATE NOT NULL,
    description VARCHAR(200) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    category VARCHAR(50), -- owner_expenses, gz_expenses, etc.
    receipt_id INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. 收据表
CREATE TABLE receipts (
    id SERIAL PRIMARY KEY,
    transaction_id INT REFERENCES transactions(id),
    file_path VARCHAR(500) NOT NULL,
    ocr_merchant VARCHAR(200),
    ocr_amount DECIMAL(12,2),
    ocr_date DATE,
    ocr_confidence DECIMAL(3,2),
    ocr_raw_text TEXT,
    matched_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. 供应商表
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    service_fee_rate DECIMAL(5,4) DEFAULT 0.0100, -- 1%
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 7. 提醒日志表
CREATE TABLE reminder_logs (
    id SERIAL PRIMARY KEY,
    statement_id INT REFERENCES statements(id),
    reminder_type VARCHAR(20), -- email / sms / whatsapp
    recipient VARCHAR(200),
    status VARCHAR(20), -- sent / failed / pending
    sent_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**阶段2：ORM集成（使用SQLAlchemy）**

```bash
步骤1：安装依赖
pip install sqlalchemy psycopg2-binary alembic

步骤2：创建模型文件
# 文件：accounting_app/models/database.py
```

```python
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Date, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    customer_code = Column(String(20), unique=True, nullable=False)
    company_name = Column(String(200), nullable=False)
    contact_person = Column(String(100))
    email = Column(String(100))
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.now)
    
    credit_cards = relationship("CreditCard", back_populates="customer")

class CreditCard(Base):
    __tablename__ = "credit_cards"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    card_number_last4 = Column(String(4), nullable=False)
    bank_name = Column(String(50), nullable=False)
    card_type = Column(String(20))
    credit_limit = Column(Numeric(12,2))
    created_at = Column(DateTime, default=datetime.now)
    
    customer = relationship("Customer", back_populates="credit_cards")
    statements = relationship("Statement", back_populates="card")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    statement_id = Column(Integer, ForeignKey("statements.id"))
    transaction_date = Column(Date, nullable=False)
    description = Column(String(200), nullable=False)
    amount = Column(Numeric(12,2), nullable=False)
    category = Column(String(50))
    receipt_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    
    statement = relationship("Statement", back_populates="transactions")

# 初始化数据库
Base.metadata.create_all(engine)
```

**阶段3：数据迁移脚本**

```bash
步骤1：创建迁移工具
# 文件：scripts/migrate_demo_to_db.py
```

```python
from accounting_app.models.database import SessionLocal, Customer, CreditCard, Transaction
from accounting_app.routers.credit_cards import DEMO_TX

def migrate_demo_data():
    db = SessionLocal()
    
    # 创建测试客户
    customer = Customer(
        customer_code="DEMO001",
        company_name="Demo Company Sdn Bhd",
        email="demo@example.com"
    )
    db.add(customer)
    db.commit()
    
    # 创建测试信用卡
    card = CreditCard(
        customer_id=customer.id,
        card_number_last4="1234",
        bank_name="Maybank",
        card_type="INFINITE"
    )
    db.add(card)
    db.commit()
    
    # 迁移交易数据
    for tx in DEMO_TX:
        transaction = Transaction(
            statement_id=1,  # 待创建Statement后更新
            transaction_date=tx["date"],
            description=tx["desc"],
            amount=tx["amount"],
            category=tx["tag"]
        )
        db.add(transaction)
    
    db.commit()
    print("✅ Demo data migrated successfully!")

if __name__ == "__main__":
    migrate_demo_data()
```

**阶段4：更新路由使用数据库**

```python
# 文件：accounting_app/routers/credit_cards.py（修改）

from accounting_app.models.database import SessionLocal, Transaction

@router.get("/transactions", response_class=HTMLResponse)
async def page_transactions(request: Request):
    db = SessionLocal()
    transactions = db.query(Transaction).order_by(Transaction.transaction_date.desc()).all()
    
    # 转换为模板需要的格式
    items = [
        {
            "date": str(t.transaction_date),
            "desc": t.description,
            "amount": float(t.amount),
            "category": t.category,
            "receipt_status": "matched" if t.receipt_id else "pending"
        }
        for t in transactions
    ]
    
    db.close()
    return templates.TemplateResponse("credit_cards_transactions.html",
        {"request": request, "transactions": items, "matched_count": 45, "total_count": 60})
```

---

### D2. 用户认证系统

**阶段1：选择认证方案**

推荐使用**Replit Auth Integration**（最简单）

```bash
步骤1：搜索Replit Auth
# 在Replit中执行（或通过Agent）
```

**阶段2：JWT认证实现（自建方案）**

```bash
步骤1：安装依赖
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

```python
# 文件：accounting_app/core/auth.py

from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24小时

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception
```

**阶段3：创建用户管理路由**

```python
# 文件：accounting_app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from accounting_app.core.auth import verify_password, create_access_token, get_password_hash
from accounting_app.models.database import SessionLocal, User  # 需添加User模型

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
async def register(username: str, password: str, email: str):
    db = SessionLocal()
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password)
    )
    db.add(user)
    db.commit()
    return {"message": "User created successfully"}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
```

**阶段4：保护路由**

```python
# 在需要认证的路由中添加依赖：

from accounting_app.core.auth import get_current_user

@router.get("/credit-cards/transactions")
async def page_transactions(
    request: Request,
    current_user: str = Depends(get_current_user)  # ← 添加此依赖
):
    # 只有登录用户才能访问
    pass
```

---

### D3. 月度报告自动生成

**阶段1：报告模板设计**

```python
# 文件：accounting_app/services/report_generator.py

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from datetime import datetime
import calendar

def generate_monthly_report(year: int, month: int, transactions: list) -> BytesIO:
    """
    生成月度财务报告PDF
    
    内容包含：
    - 收入/支出汇总
    - OWNER vs INFINITE分类统计
    - 供应商服务费明细
    - 同比/环比分析
    - 收据匹配率
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # 标题
    title = Paragraph(
        f"<font size=18 color='#FF007F'><b>月度财务报告 - {year}年{month}月</b></font>",
        styles['Title']
    )
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # 汇总统计
    total_expenses = sum(t['amount'] for t in transactions if t['category'].endswith('_expenses'))
    total_payments = sum(t['amount'] for t in transactions if t['category'].endswith('_payments'))
    
    summary_data = [
        ['类别', '金额 (RM)', '占比'],
        ['总支出', f"{total_expenses:,.2f}", '100%'],
        ['- OWNER支出', f"{sum(t['amount'] for t in transactions if t['category']=='owner_expenses'):,.2f}", f"{(sum(t['amount'] for t in transactions if t['category']=='owner_expenses')/total_expenses*100):.1f}%"],
        ['- INFINITE支出', f"{sum(t['amount'] for t in transactions if t['category']=='gz_expenses'):,.2f}", f"{(sum(t['amount'] for t in transactions if t['category']=='gz_expenses')/total_expenses*100):.1f}%"],
        ['总还款', f"{total_payments:,.2f}", '-'],
    ]
    
    table = Table(summary_data, colWidths=[200, 150, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#322446')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#3b2b4e')),
    ]))
    elements.append(table)
    
    # 生成PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
```

**阶段2：自动化调度（月末生成）**

```python
# 在 accounting_app/services/reminders.py 中添加：

from accounting_app.services.report_generator import generate_monthly_report
from datetime import datetime
import calendar

def schedule_monthly_reports():
    """每月最后一天23:00生成报告"""
    @scheduler.scheduled_job('cron', day='last', hour=23, minute=0, timezone='Asia/Kuala_Lumpur')
    def generate_report_job():
        now = datetime.now()
        year, month = now.year, now.month
        
        # 查询本月交易
        db = SessionLocal()
        transactions = db.query(Transaction).filter(
            Transaction.transaction_date >= f"{year}-{month:02d}-01",
            Transaction.transaction_date <= f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
        ).all()
        
        # 生成PDF
        pdf_buffer = generate_monthly_report(year, month, transactions)
        
        # 保存到文件
        file_path = f"reports/monthly_report_{year}_{month:02d}.pdf"
        with open(file_path, 'wb') as f:
            f.write(pdf_buffer.read())
        
        # 发送邮件附件
        send_email_with_attachment(
            to=os.getenv("ADMIN_EMAIL"),
            subject=f"月度财务报告 - {year}年{month}月",
            body="请查收附件中的月度报告。",
            attachment=pdf_buffer
        )
        
        db.close()
```

---

### D4. Dashboard数据可视化

**阶段1：前端图表库选择**

推荐使用**Plotly.js**（已在项目中）

```html
<!-- 文件：accounting_app/templates/dashboard.html -->

{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}

{% block head_extra %}
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
  .chart-container { background: #322446; border-radius: 16px; padding: 20px; margin-bottom: 20px; }
  .chart-title { color: #FF007F; font-size: 18px; font-weight: 700; margin-bottom: 10px; }
</style>
{% endblock %}

{% block content %}
<div class="page">
  <div class="main">
    <h1 class="title">Dashboard</h1>
    
    <!-- 月度趋势图 -->
    <div class="chart-container">
      <div class="chart-title">月度支出趋势</div>
      <div id="monthlyTrendChart"></div>
    </div>
    
    <!-- 分类饼图 -->
    <div class="grid-auto">
      <div class="chart-container">
        <div class="chart-title">OWNER vs INFINITE</div>
        <div id="categoryPieChart"></div>
      </div>
      
      <div class="chart-container">
        <div class="chart-title">供应商支出分布</div>
        <div id="supplierBarChart"></div>
      </div>
    </div>
  </div>
</div>

<script>
// 月度趋势线图
const monthlyData = {
  x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
  y: [4500, 5200, 4800, 5600, 6100, 5800],
  type: 'scatter',
  mode: 'lines+markers',
  marker: { color: '#FF007F', size: 10 },
  line: { color: '#FF007F', width: 3 }
};

Plotly.newPlot('monthlyTrendChart', [monthlyData], {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: '#fff' },
  xaxis: { gridcolor: '#3b2b4e' },
  yaxis: { gridcolor: '#3b2b4e' }
});

// 分类饼图
const categoryData = [{
  values: [3200, 2800],
  labels: ['INFINITE', 'OWNER'],
  type: 'pie',
  marker: {
    colors: ['#FF007F', '#322446']
  }
}];

Plotly.newPlot('categoryPieChart', categoryData, {
  paper_bgcolor: 'transparent',
  font: { color: '#fff' }
});

// 供应商条形图
const supplierData = [{
  x: ['Dinas', 'Huawei', '7SL', 'Pasar Raya'],
  y: [850, 1200, 650, 500],
  type: 'bar',
  marker: { color: '#FF007F' }
}];

Plotly.newPlot('supplierBarChart', supplierData, {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: '#fff' },
  xaxis: { gridcolor: '#3b2b4e' },
  yaxis: { gridcolor: '#3b2b4e' }
});
</script>
{% endblock %}
```

**阶段2：后端数据API**

```python
# 文件：accounting_app/routers/dashboard.py

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from accounting_app.models.database import SessionLocal, Transaction
from sqlalchemy import func
from datetime import datetime, timedelta

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/api/monthly-trend")
async def get_monthly_trend():
    """获取最近6个月的支出趋势"""
    db = SessionLocal()
    
    # 查询最近6个月数据
    results = db.query(
        func.date_trunc('month', Transaction.transaction_date).label('month'),
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.transaction_date >= datetime.now() - timedelta(days=180)
    ).group_by('month').order_by('month').all()
    
    return {
        "months": [r.month.strftime('%b') for r in results],
        "amounts": [float(r.total) for r in results]
    }

@router.get("/api/category-breakdown")
async def get_category_breakdown():
    """获取OWNER vs INFINITE分类统计"""
    db = SessionLocal()
    
    owner_total = db.query(func.sum(Transaction.amount)).filter(
        Transaction.category.in_(['owner_expenses', 'owner_payments'])
    ).scalar() or 0
    
    infinite_total = db.query(func.sum(Transaction.amount)).filter(
        Transaction.category.in_(['gz_expenses', 'gz_payments'])
    ).scalar() or 0
    
    return {
        "labels": ["OWNER", "INFINITE"],
        "values": [float(owner_total), float(infinite_total)]
    }
```

**阶段3：实时数据刷新（WebSocket可选）**

```python
# 高级功能：使用WebSocket实时推送数据更新

from fastapi import WebSocket

@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    await websocket.accept()
    while True:
        # 每10秒推送最新数据
        data = await get_monthly_trend()
        await websocket.send_json(data)
        await asyncio.sleep(10)
```

---

## 📝 任务执行顺序建议

### 快速启动路径（1-2小时）

```
1. B3：配置Twilio SMS（15分钟）
   → 最简单，立即可测试

2. C1：测试PDF解析（30分钟）
   → 验证核心功能

3. B1：配置Tesseract OCR（10分钟）
   → 免费方案，快速验证

4. C2：测试收据OCR（20分钟）
   → 端到端流程验证

5. C3：测试发票导出（15分钟）
   → 完整业务闭环
```

### 生产就绪路径（1天）

```
1. B1：配置Google Vision（1小时）
   → 高准确率OCR

2. B2：配置SendGrid（30分钟）
   → 域名验证+测试

3. D1：数据库集成（3小时）
   → 核心架构升级

4. D2：用户认证（2小时）
   → 安全保障

5. 功能测试（2小时）
   → 全面回归测试
```

### 企业级路径（1周）

```
Day 1-2: 数据库+认证系统
Day 3-4: 月度报告+自动化
Day 5-6: Dashboard可视化
Day 7: 性能优化+压力测试
```

---

## 🆘 常见问题排查

### Q1：OCR识别率低怎么办？

```
解决方案：
1. 提高图片质量（分辨率≥1080p）
2. 调整光照（避免反光/阴影）
3. 切换OCR提供商（Tesseract→Google Vision）
4. 添加图像预处理（锐化/去噪）
```

### Q2：邮件进垃圾箱？

```
解决方案：
1. 完成SendGrid域名验证（DKIM/SPF）
2. 避免垃圾词汇（Free/Winner/Click）
3. 添加退订链接
4. 预热发件人IP（逐步增加发送量）
```

### Q3：数据库迁移失败？

```
解决方案：
1. 备份现有数据（pg_dump）
2. 检查外键约束
3. 分批迁移（小表→大表）
4. 使用事务回滚（出错自动撤销）
```

---

## ✅ 完成检查清单

每完成一个任务，勾选对应项：

**选项B：生产服务**
- [ ] B1.1：Google Vision配置完成
- [ ] B1.2：OCR测试通过（识别率>85%）
- [ ] B2.1：SendGrid域名验证完成
- [ ] B2.2：测试邮件送达成功
- [ ] B3.1：Twilio凭证配置完成
- [ ] B3.2：测试SMS发送成功

**选项C：功能测试**
- [ ] C1.1：Maybank PDF解析成功
- [ ] C1.2：CIMB/Hong Leong解析成功
- [ ] C2.1：清晰收据OCR识别准确
- [ ] C2.2：自动匹配交易成功
- [ ] C3.1：单供应商PDF导出正确
- [ ] C3.2：月度汇总PDF生成成功

**选项D：继续开发**
- [ ] D1.1：数据库表结构创建完成
- [ ] D1.2：ORM模型定义完成
- [ ] D1.3：Demo数据迁移成功
- [ ] D1.4：路由更新使用数据库
- [ ] D2.1：JWT认证实现完成
- [ ] D2.2：用户注册/登录测试通过
- [ ] D2.3：路由保护生效
- [ ] D3.1：报告模板开发完成
- [ ] D3.2：月度自动生成调度设置
- [ ] D3.3：邮件附件发送测试通过
- [ ] D4.1：Dashboard页面创建完成
- [ ] D4.2：3种图表渲染成功
- [ ] D4.3：数据API响应正常

---

**如需帮助执行任何步骤，请告诉我具体哪一步！** 🚀
