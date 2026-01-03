# 马来西亚金融产品匹配系统

## 📊 数据库概览

### 数据统计
- **总产品数**: 759个（已验证）
  - 信用卡: 129张
  - 贷款和金融产品: 630个
- **覆盖机构**: 40+ 家银行和金融机构
- **产品类别**: 
  - Personal（个人）
  - Business（企业）
  - Personal/Business（个人/企业通用）

### 数据来源
1. **ALL CC CHOICES.xlsx** - 129张信用卡
2. **Malaysia Financial Products.xlsx** - 630个金融产品

---

## 🎯 产品匹配系统设计

### 核心匹配参数

#### 1. Monthly Income (月收入)
- 用于评估客户的还款能力
- 决定客户可申请的产品等级
- 影响贷款额度和信用卡额度

#### 2. Monthly Commitment (月供承诺)
- 包括所有现有贷款的月供
- 包括信用卡最低还款
- 用于计算Debt Service Ratio (DSR)

#### 3. Debt Service Ratio (DSR)计算
```
DSR = (Total Monthly Commitments / Monthly Income) × 100%
```

**马来西亚银行标准**:
- **个人贷款**: DSR应≤60%
- **房贷**: DSR应≤70%
- **信用卡**: 一般要求DSR≤60%

---

## 🔍 产品匹配逻辑

### 阶段1: 基础资格筛选

```python
def check_basic_eligibility(monthly_income, monthly_commitment):
    """
    基础资格检查
    """
    # 计算DSR
    dsr = (monthly_commitment / monthly_income) * 100
    
    # 计算可用收入
    available_income = monthly_income - monthly_commitment
    
    return {
        'dsr': dsr,
        'available_income': available_income,
        'eligible_for_personal_loan': dsr <= 60,
        'eligible_for_mortgage': dsr <= 70,
        'eligible_for_credit_card': dsr <= 60
    }
```

### 阶段2: 产品类型筛选

#### 信用卡匹配
```python
def match_credit_cards(monthly_income, dsr):
    """
    信用卡匹配规则
    """
    if monthly_income < 24000:  # 年收入 < RM24,000
        return "不符合大多数信用卡申请条件"
    
    if dsr > 60:
        return "DSR过高，建议先降低月供"
    
    # 根据收入等级推荐卡片
    if monthly_income >= 100000:  # RM100k+/年
        return "Infinite/World/Platinum cards"
    elif monthly_income >= 50000:  # RM50k+/年
        return "Platinum/Gold cards"
    elif monthly_income >= 24000:  # RM24k+/年
        return "Classic/Basic cards"
```

#### 个人贷款匹配
```python
def match_personal_loans(monthly_income, monthly_commitment, loan_amount_needed):
    """
    个人贷款匹配规则
    """
    # 计算最大可贷额
    max_monthly_payment = (monthly_income * 0.6) - monthly_commitment
    
    # 假设5年期，利率8%
    max_loan_amount = calculate_loan_amount(max_monthly_payment, 60, 0.08/12)
    
    if loan_amount_needed > max_loan_amount:
        return {
            'status': 'rejected',
            'reason': f'申请额度超过最大可贷额 RM{max_loan_amount:.2f}',
            'suggested_amount': max_loan_amount
        }
    
    return {
        'status': 'eligible',
        'max_amount': max_loan_amount,
        'recommended_tenure': '36-60 months',
        'estimated_monthly_payment': loan_amount_needed / 60  # 简化计算
    }
```

#### 房贷匹配
```python
def match_mortgages(monthly_income, monthly_commitment, property_price):
    """
    房贷匹配规则
    """
    # 计算最大月供（70% DSR）
    max_monthly_payment = (monthly_income * 0.7) - monthly_commitment
    
    # 假设30年期，利率4.5%
    max_loan_amount = calculate_loan_amount(max_monthly_payment, 360, 0.045/12)
    
    # 马来西亚房贷一般最高90%（首次购房者）
    required_loan = property_price * 0.9
    
    if required_loan > max_loan_amount:
        return {
            'status': 'rejected',
            'reason': f'最大可贷额不足',
            'max_loan_amount': max_loan_amount,
            'max_property_price': max_loan_amount / 0.9,
            'required_downpayment_percentage': ((property_price - max_loan_amount) / property_price) * 100
        }
    
    return {
        'status': 'eligible',
        'loan_amount': required_loan,
        'monthly_payment': calculate_monthly_payment(required_loan, 360, 0.045/12),
        'downpayment': property_price * 0.1
    }
```

---

## 📋 产品分类体系

### 1. 信用卡 (Credit Cards)
**子类别**:
- Corporate cards (企业卡)
- Infinite/World cards (顶级卡)
- Platinum cards (白金卡)
- Gold cards (金卡)
- Classic cards (经典卡)
- Islamic cards (伊斯兰卡)

**匹配字段**:
- `MIN_INCOME`: 最低年收入要求
- `ANNUAL_FEE`: 年费
- `BENEFITS`: 福利（返现、里程、积分等）
- `CATEGORY`: Personal/Business

### 2. 个人贷款 (Personal Loans)
**子类别**:
- Personal financing
- Cash loans
- Debt consolidation
- Islamic personal financing

**匹配字段**:
- `RATE`: 利率
- `TENURE`: 期限
- `REQUIRED_DOC`: 所需文件
- `FEES_CHARGES`: 费用

### 3. 房屋贷款 (Mortgages)
**子类别**:
- Home financing
- Property loans
- Islamic home financing
- Refinancing

**匹配字段**:
- `RATE`: 利率
- `TENURE`: 最长期限（通常30-35年）
- `REQUIRED_DOC`: 所需文件
- `FEATURES`: 特点（fixed rate, variable rate等）

### 4. 商业贷款 (Business Loans)
**子类别**:
- SME financing
- Working capital
- Equipment financing
- Trade financing
- Overdraft facilities

**匹配字段**:
- `PRODUCT_TYPE`: 产品类型
- `RATE`: 利率
- `TENURE`: 期限
- `REQUIRED_DOC`: 所需文件（公司注册、财务报表等）

### 5. P2P和Fintech产品
**子类别**:
- P2P lending
- Invoice financing
- Supply chain financing
- Digital loans

**匹配字段**:
- `RATE`: 利率
- `TENURE`: 期限
- `FEATURES`: 特点（快速审批、线上申请等）

---

## 🚀 实施步骤

### 步骤1: 数据库增强
```sql
-- 添加关键匹配字段
ALTER TABLE products ADD COLUMN min_income_annual DECIMAL(10,2);
ALTER TABLE products ADD COLUMN min_dsr_requirement DECIMAL(5,2);
ALTER TABLE products ADD COLUMN max_dsr_allowed DECIMAL(5,2);
ALTER TABLE products ADD COLUMN min_loan_amount DECIMAL(10,2);
ALTER TABLE products ADD COLUMN max_loan_amount DECIMAL(10,2);
ALTER TABLE products ADD COLUMN interest_rate_min DECIMAL(5,2);
ALTER TABLE products ADD COLUMN interest_rate_max DECIMAL(5,2);
```

### 步骤2: 创建匹配API

```python
# app/api/match_products.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd

router = APIRouter()

class CustomerProfile(BaseModel):
    monthly_income: float
    monthly_commitment: float
    product_type: str  # 'credit_card', 'personal_loan', 'mortgage', 'business_loan'
    loan_amount: float = None  # 仅用于贷款类产品
    property_price: float = None  # 仅用于房贷

@router.post("/match-products")
async def match_products(profile: CustomerProfile):
    """
    根据客户信息匹配合适的金融产品
    """
    # 1. 计算DSR
    dsr = (profile.monthly_commitment / profile.monthly_income) * 100
    
    # 2. 加载产品数据库
    df_products = pd.read_excel('Malaysia_Financial_Products_Database_Complete.xlsx')
    
    # 3. 根据产品类型筛选
    if profile.product_type == 'credit_card':
        matched_products = match_credit_cards_logic(df_products, profile, dsr)
    elif profile.product_type == 'personal_loan':
        matched_products = match_personal_loans_logic(df_products, profile, dsr)
    elif profile.product_type == 'mortgage':
        matched_products = match_mortgages_logic(df_products, profile, dsr)
    elif profile.product_type == 'business_loan':
        matched_products = match_business_loans_logic(df_products, profile, dsr)
    else:
        raise HTTPException(status_code=400, detail="Invalid product type")
    
    # 4. 返回匹配结果
    return {
        'customer_profile': {
            'monthly_income': profile.monthly_income,
            'monthly_commitment': profile.monthly_commitment,
            'dsr': round(dsr, 2),
            'available_income': profile.monthly_income - profile.monthly_commitment
        },
        'eligibility': {
            'credit_card': dsr <= 60,
            'personal_loan': dsr <= 60,
            'mortgage': dsr <= 70,
            'status': 'eligible' if dsr <= 60 else 'high_dsr'
        },
        'matched_products': matched_products,
        'recommendations': generate_recommendations(profile, dsr)
    }
```

### 步骤3: 前端集成

```javascript
// components/ProductMatcher.tsx

import { useState } from 'react';

export default function ProductMatcher() {
  const [income, setIncome] = useState('');
  const [commitment, setCommitment] = useState('');
  const [productType, setProductType] = useState('credit_card');
  const [results, setResults] = useState(null);
  
  const handleMatch = async () => {
    const response = await fetch('/api/match-products', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        monthly_income: parseFloat(income),
        monthly_commitment: parseFloat(commitment),
        product_type: productType
      })
    });
    
    const data = await response.json();
    setResults(data);
  };
  
  return (
    <div className="product-matcher">
      <h2>Find Your Best Financial Products</h2>
      
      <div className="input-group">
        <label>Monthly Income (RM)</label>
        <input 
          type="number" 
          value={income}
          onChange={(e) => setIncome(e.target.value)}
          placeholder="e.g. 5000"
        />
      </div>
      
      <div className="input-group">
        <label>Monthly Commitments (RM)</label>
        <input 
          type="number"
          value={commitment}
          onChange={(e) => setCommitment(e.target.value)}
          placeholder="e.g. 1500"
        />
      </div>
      
      <div className="input-group">
        <label>Product Type</label>
        <select value={productType} onChange={(e) => setProductType(e.target.value)}>
          <option value="credit_card">Credit Card</option>
          <option value="personal_loan">Personal Loan</option>
          <option value="mortgage">Home Loan</option>
          <option value="business_loan">Business Loan</option>
        </select>
      </div>
      
      <button onClick={handleMatch}>Find Matching Products</button>
      
      {results && (
        <div className="results">
          <div className="eligibility">
            <h3>Your Profile</h3>
            <p>DSR: {results.customer_profile.dsr}%</p>
            <p>Available Income: RM {results.customer_profile.available_income}</p>
            <p>Status: {results.eligibility.status}</p>
          </div>
          
          <div className="matched-products">
            <h3>Recommended Products ({results.matched_products.length})</h3>
            {results.matched_products.map((product, index) => (
              <div key={index} className="product-card">
                <h4>{product.PRODUCT_NAME}</h4>
                <p>{product.COMPANY}</p>
                <p>{product.PRODUCT_TYPE}</p>
                <p>Rate: {product.RATE}</p>
                <button>Apply Now</button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 📊 匹配算法详细说明

### 算法1: 基于DSR的筛选

```python
def filter_by_dsr(products_df, dsr, product_category):
    """
    根据DSR筛选产品
    """
    if product_category == 'credit_card':
        max_dsr = 60
    elif product_category == 'mortgage':
        max_dsr = 70
    else:  # personal/business loans
        max_dsr = 60
    
    if dsr > max_dsr:
        return pd.DataFrame()  # 返回空DataFrame
    
    # 进一步筛选产品
    return products_df[products_df['CATEGORY'].str.contains(product_category, case=False, na=False)]
```

### 算法2: 基于收入等级的匹配

```python
def match_by_income_tier(products_df, annual_income):
    """
    根据收入等级匹配产品
    """
    if annual_income >= 100000:
        tier = 'premium'  # Infinite, World, Platinum
    elif annual_income >= 50000:
        tier = 'mid'  # Platinum, Gold
    elif annual_income >= 24000:
        tier = 'basic'  # Classic, Gold
    else:
        tier = 'none'
    
    # 根据tier筛选产品
    # 这需要产品数据库中有income_tier字段
    return products_df[products_df['income_tier'] == tier]
```

### 算法3: 基于特征的相似度匹配

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def match_by_features(products_df, user_preferences):
    """
    基于产品特征的相似度匹配
    
    user_preferences: 用户偏好关键词，如 ['cashback', 'travel', 'rewards']
    """
    # 合并产品的FEATURES和BENEFITS字段
    products_df['combined_text'] = products_df['FEATURES'] + ' ' + products_df['BENEFITS']
    
    # TF-IDF向量化
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(products_df['combined_text'])
    
    # 用户偏好向量化
    user_vector = vectorizer.transform([' '.join(user_preferences)])
    
    # 计算相似度
    similarities = cosine_similarity(user_vector, tfidf_matrix)[0]
    
    # 添加相似度分数
    products_df['similarity_score'] = similarities
    
    # 按相似度排序
    return products_df.sort_values('similarity_score', ascending=False)
```

---

## 🎯 下一步开发计划

### Phase 1: 数据清理和增强 ✅
- [x] 整合两个Excel文件
- [x] 统一数据格式
- [x] 创建完整产品数据库

### Phase 2: 数据库设计
- [ ] 设计关系型数据库schema
- [ ] 添加匹配所需的计算字段
- [ ] 从Excel导入到数据库

### Phase 3: API开发
- [ ] 创建产品匹配API
- [ ] 实现DSR计算逻辑
- [ ] 实现多维度筛选

### Phase 4: 前端开发
- [ ] 创建产品匹配界面
- [ ] 实现实时DSR计算
- [ ] 显示匹配结果和推荐

### Phase 5: 优化和测试
- [ ] 性能优化
- [ ] 匹配算法调优
- [ ] 用户测试和反馈

---

## 📝 注意事项

1. **DSR计算准确性**: 确保所有月供都被计入
2. **收入验证**: 需要客户提供收入证明
3. **产品更新**: 定期更新产品数据库（利率、条款等）
4. **合规性**: 确保遵守马来西亚金融监管要求
5. **数据安全**: 客户财务数据需加密存储

---

## 📞 联系信息

如有问题或建议，请联系开发团队。

**最后更新**: 2025-12-27
**版本**: 1.0.0
