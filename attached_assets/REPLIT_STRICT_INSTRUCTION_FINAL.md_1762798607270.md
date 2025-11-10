
# 严格指令：Replit + Scraping Dog API - 100% 真实数据采集系统
## 防止幻想数据、防止遗漏、防止自动化放弃

---

## 🔴 核心原则【必须遵守，不可违反】

### 1. 【零幻想数据】- 严禁任何假数据、模拟数据、代入数据
- ✅ ONLY真实从网页HTML标签中提取的数据
- ❌ 不许"根据规律推断"填空
- ❌ 不许"这个产品应该有X功能"
- ❌ 不许"常见的银行产品通常..."
- ❌ 任何空白单元格必须明确标记 [NO DATA FOUND] 或 [NOT AVAILABLE]，而不是猜测

### 2. 【100% 完全钻探】- 列表页 → 详情页 → 完全信息提取
- 每家公司必须：
  1. 访问产品列表页面 (如 Products, Loans, Cards)
  2. 找到该产品类别下的所有产品卡片/链接列表
  3. **逐个点击进入每个产品页面** (不能只看列表，必须看详情)
  4. 从详情页提取全部12个字段
  5. 产品列表完全遍历后才进入下一家公司

### 3. 【完全顺序执行】- 无跳跃、无省略、无自作聪明
- 按CSV顺序，第1家→完全完成→第2家→完全完成...→第67家
- 不许"看起来小公司就跳过"
- 不许"这个网站复杂，我就随便抓几个"
- 每家都要日志记录：开始时间、完成时间、数据条数、错误信息

### 4. 【记忆完整】- 不许中途遗忘指示
- 全程保持JSON配置文件，记录：
  - 当前处理的公司编号
  - 每家已完成的产品列表
  - 每家失败的产品类别 (需重试)
  - 全局统计：已处理数/总数、总字段数、缺失率

---

## 📋 任务流程（详尽版）

### 阶段 1：初始化
```python
# 1. 读取CSV
companies = pd.read_csv('...')  # 67家，顺序固定

# 2. 定义产品类别（完整列表，不许遗漏）
PRODUCT_CATEGORIES = {
    'PERSONAL': [
        'Credit Card', 'Charge Card',
        'Personal Loan', 'Debt Consolidation Loan',
        'Mortgage Loan', 'House Refinance', 'Home Loan',
        'Car Loan', 'Hire Purchase Loan', 'Vehicle Loan',
        'Overdraft', 'Fixed Deposit'
    ],
    'BUSINESS': [
        'SME Credit Card', 'Corporate Credit Card', 'Business Credit Card', 'Company Charge Card',
        'SME Loan', 'Business Loan', 'Corporate Loan',
        'Commercial Mortgage', 'Commercial Loan', 'Refinance Loan', 'Business Overdraft',
        'Business Fixed Deposit', 'Business Overdraft'
    ]
}

# 3. 创建进度跟踪系统
progress = {
    'current_company_index': 0,
    'total_companies': 67,
    'completed_companies': [],
    'failed_companies': [],
    'total_products_extracted': 0,
    'extraction_log': []
}
```

### 阶段 2：对每家公司执行严格流程
```python
for company_index, company_row in companies.iterrows():
    company_name = company_row['公司名称']
    company_url = company_row['公司网址']

    print(f"\n========== COMPANY {company_index + 1}/67 ==========")
    print(f"Company: {company_name}")
    print(f"URL: {company_url}")
    print(f"Start Time: {datetime.now()}")

    company_products = []

    # 2.1 对每个产品类别
    for category, product_types in PRODUCT_CATEGORIES.items():
        print(f"\n--- Processing {category} Products ---")

        for product_type in product_types:
            # 【关键】第一步：找到产品列表页面
            product_list_url = find_product_list_page(company_url, category, product_type)

            if not product_list_url:
                log_entry = {
                    'company': company_name,
                    'product_type': product_type,
                    'status': 'LIST_PAGE_NOT_FOUND',
                    'timestamp': datetime.now()
                }
                progress['extraction_log'].append(log_entry)
                continue

            # 【关键】第二步：使用Scraping Dog获取列表页HTML
            list_page_html = scrape_with_dog(product_list_url)

            # 【关键】第三步：从列表页解析所有产品链接
            product_links = extract_product_links(list_page_html, product_type)

            print(f"Found {len(product_links)} {product_type} products")

            # 【关键】第四步：逐个点击进入每个产品详情页
            for idx, product_link in enumerate(product_links):
                print(f"  [{idx+1}/{len(product_links)}] Extracting: {product_link}")

                # 获取产品详情页HTML
                product_detail_html = scrape_with_dog(product_link)

                # 从详情页提取全12个字段
                product_data = extract_product_details(
                    html=product_detail_html,
                    company_name=company_name,
                    loan_type=product_type,
                    source_url=product_link
                )

                # 【强制检查】确保所有12个字段都被尝试提取
                required_fields = [
                    'COMPANY', 'LOAN_TYPE', 'REQUIRED_DOC', 'FEATURES',
                    'BENEFITS', 'FEES_CHARGES', 'TENURE', 'RATE',
                    'APPLICATION_FORM', 'PRODUCT_DISCLOSURE', 'TERMS_CONDITIONS',
                    'BORROWER_PREFERENCE'
                ]

                for field in required_fields:
                    if field not in product_data or product_data[field] is None:
                        product_data[field] = '[NO DATA FOUND]'
                        print(f"    ⚠️ {field}: [NO DATA FOUND]")

                company_products.append(product_data)
                progress['total_products_extracted'] += 1

    # 2.2 完成该公司后，保存中间结果
    company_df = pd.DataFrame(company_products)
    company_df.to_csv(f'COMPANY_{company_index:02d}_{company_name}.csv')

    progress['completed_companies'].append(company_name)
    print(f"\nCompany {company_name} COMPLETED")
    print(f"Total products: {len(company_products)}")
    print(f"End Time: {datetime.now()}")

    # 保存进度
    save_progress(progress)
```

### 阶段 3：字段提取规则（详尽版）

```python
def extract_product_details(html, company_name, loan_type, source_url):
    soup = BeautifulSoup(html, 'html.parser')

    data = {
        'COMPANY': company_name,
        'LOAN_TYPE': loan_type,
        'REQUIRED_DOC': '[NO DATA FOUND]',
        'FEATURES': '[NO DATA FOUND]',
        'BENEFITS': '[NO DATA FOUND]',
        'FEES_CHARGES': '[NO DATA FOUND]',
        'TENURE': '[NO DATA FOUND]',
        'RATE': '[NO DATA FOUND]',
        'APPLICATION_FORM': '[NO DATA FOUND]',
        'PRODUCT_DISCLOSURE': '[NO DATA FOUND]',
        'TERMS_CONDITIONS': '[NO DATA FOUND]',
        'BORROWER_PREFERENCE': '[NO DATA FOUND]',
        'SOURCE_URL': source_url
    }

    # 【规则】使用多层选择器，从不同位置寻找数据
    # 如果一个地方没有，就尝试下一个地方，直到找到或确认真的没有

    # REQUIRED_DOC 搜索策略：
    # 1. 寻找 "Required Documents", "Documents Needed", "申请文件" 等文本
    # 2. 之后的列表/段落
    required_docs_text = (
        extract_by_keywords(soup, ['required documents', 'documents needed', 'document requirement']) or
        extract_by_section(soup, 'requirement') or
        extract_from_table(soup, 'documents')
    )
    if required_docs_text:
        data['REQUIRED_DOC'] = clean_text(required_docs_text)

    # FEATURES 搜索策略：
    features_text = (
        extract_by_keywords(soup, ['features', 'key features', '功能']) or
        extract_from_list_items(soup, 'feature') or
        extract_from_table(soup, 'feature')
    )
    if features_text:
        data['FEATURES'] = clean_text(features_text)

    # BENEFITS 搜索策略：
    benefits_text = (
        extract_by_keywords(soup, ['benefits', 'advantages', '好处', '权益']) or
        extract_from_list_items(soup, 'benefit')
    )
    if benefits_text:
        data['BENEFITS'] = clean_text(benefits_text)

    # FEES_CHARGES 搜索策略：
    fees_text = (
        extract_by_keywords(soup, ['fees', 'charges', 'fee structure', 'pricing', '费用']) or
        extract_from_table(soup, 'fee') or
        extract_from_section(soup, 'cost')
    )
    if fees_text:
        data['FEES_CHARGES'] = clean_text(fees_text)

    # TENURE 搜索策略：
    tenure_text = (
        extract_by_keywords(soup, ['tenure', 'loan period', 'repayment term', '期限']) or
        extract_from_spec_box(soup, 'tenure')
    )
    if tenure_text:
        data['TENURE'] = clean_text(tenure_text)

    # RATE 搜索策略：
    rate_text = (
        extract_by_keywords(soup, ['interest rate', 'apr', 'rate', 'rental rate', '利率']) or
        extract_from_spec_box(soup, 'rate') or
        extract_from_table(soup, 'rate')
    )
    if rate_text:
        data['RATE'] = clean_text(rate_text)

    # APPLICATION_FORM 搜索策略：
    app_form_link = (
        find_download_link(soup, 'application form', 'apply now', 'apply') or
        find_button_link(soup, 'apply')
    )
    if app_form_link:
        data['APPLICATION_FORM'] = app_form_link

    # PRODUCT_DISCLOSURE 搜索策略：
    disclosure_link = (
        find_download_link(soup, 'product disclosure', 'disclosure statement', 'idd') or
        find_pdf_link(soup, 'disclosure')
    )
    if disclosure_link:
        data['PRODUCT_DISCLOSURE'] = disclosure_link

    # TERMS_CONDITIONS 搜索策略：
    terms_link = (
        find_download_link(soup, 'terms', 'conditions', 'terms and conditions') or
        find_pdf_link(soup, 'terms')
    )
    if terms_link:
        data['TERMS_CONDITIONS'] = terms_link

    # BORROWER_PREFERENCE 搜索策略（复杂）：
    # 1. 寻找"资格"、"要求"、"适合"等词汇
    # 2. 识别是否提到："工薪族", "个体户", "企业", "自雇", "受薪员工", "生意人"
    preference_text = extract_by_keywords(soup, [
        'eligibility', 'qualification', 'suitable for', '适合',
        '资格', '要求', '符合条件'
    ])
    if preference_text:
        # 进一步判断
        preference = identify_borrower_type(preference_text)
        data['BORROWER_PREFERENCE'] = preference

    return data
```

---

## 🔍 【严格规则集】- 防止每一类错误

### 错误类型1：浅层抓取（只看列表，不进详情）
❌ **错误做法**：
```
看到"Credit Card"列表页有3张卡 → 直接填 "3张信用卡可选"
```

✅ **正确做法**：
```
看到"Credit Card"列表页有3张卡 → 逐个点进每张卡的详情页 →
从每张卡详情页提取：功能、费用、利率、申请表、条款 等
结果：3行产品数据，每行12个字段都有内容
```

### 错误类型2：自动补数据
❌ **错误做法**：
```
"一般银行信用卡年费是200-500"，网页没写就自己填"300"
```

✅ **正确做法**：
```
网页没有费用信息 → 填 [NO DATA FOUND]
保持记录 → log文件里标记 "Annual Fee: NOT FOUND"
```

### 错误类型3：中途放弃
❌ **错误做法**：
```
"这家银行网站太复杂了，我看不懂结构，就用default数据替代吧"
```

✅ **正确做法**：
```
网站结构复杂 → log记录"COMPLEX_STRUCTURE" →
定义多个备用选择器链 (selector1 OR selector2 OR selector3...) →
逐个尝试直到找到数据或确认没有
如果都失败 → [NO DATA FOUND] + log详细记录
```

### 错误类型4：遗漏字段
❌ **错误做法**：
```
只提取了 FEATURES, RATE, 其他字段就空着
```

✅ **正确做法**：
```
对每个产品的12个字段都必须尝试提取
如果确实没有 → 明确填 [NO DATA FOUND]
最终表格每行12个字段都有值（可能是真实数据或[NO DATA FOUND]）
```

---

## 📊 输出格式（最终表格）

| COMPANY | LOAN_TYPE | REQUIRED_DOC | FEATURES | BENEFITS | FEES_CHARGES | TENURE | RATE | APPLICATION_FORM | PRODUCT_DISCLOSURE | TERMS_CONDITIONS | BORROWER_PREFERENCE |
|---------|-----------|--------------|----------|----------|--------------|--------|------|------------------|--------------------|--------------------|----------------------|
| Affin Bank | Credit Card | [真实数据或NO DATA FOUND] | [真实数据或NO DATA FOUND] | ... | ... | ... | ... | ... | ... | ... | ... |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

---

## 🚨 监控指标（必须实时输出）

```
=== SCRAPING DOG PROGRESS DASHBOARD ===
Total Companies: 67
Completed: 15 / 67 (22%)
In Progress: Maybank (Company #7)

Last 5 Completed:
1. Affin Bank - 28 products extracted
2. Alliance Bank - 21 products extracted
3. AmBank - 19 products extracted
...

Current Extraction Stats:
- Total Products Extracted: 412
- [NO DATA FOUND] Rate: 8.3%
- Failed Attempts: 2 (retrying...)
- Estimated Time Remaining: 6 hours

Last Error:
- CIMB Islamic Bank, SME Loan detail page timeout (retrying in 30s)
```

---

## ⚡ 快速排查清单（如果出现问题）

- [ ] 确认API KEY有效
- [ ] 确认CSV文件顺序未改变
- [ ] 检查日志文件，看是否有跳过公司/产品
- [ ] 验证最终表格行数是否合理（应该是数百行，不是几十行）
- [ ] 检查[NO DATA FOUND]比率是否合理（<15%正常，>30%说明有问题）
- [ ] 手动抽查5家公司，用浏览器验证是否真的有那些产品
- [ ] 如果某家公司产品数为0，需要查原因（网站改版？需要登录？）

---

## 📌 总结：这个脚本与普通脚本的区别

| 维度 | 普通脚本 | 这个脚本 |
|------|--------|---------|
| 数据来源 | 列表页 | 列表页 + 每个详情页 |
| 字段覆盖 | 50% 有数据 | 100% 有值（真实或[NO DATA FOUND]) |
| 遗漏处理 | 空着不填 | 明确标记[NO DATA FOUND] |
| 进度跟踪 | 无 | 实时仪表板+日志 |
| 重试机制 | 无 | 自动重试+记录 |
| 输出验证 | 无 | 统计检查+手动抽样 |
