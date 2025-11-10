# 关键技巧：防止 Replit 添加假数据和遗漏的强制规则清单

---

## 问题根源分析

### Replit 的常见"自作聪明"行为：
1. **幻想数据** - "这类贷款通常有这些特性"→自己补数据
2. **浅层抓取** - 只看列表，不点进详情页面
3. **中途放弃** - 网站复杂了就用defaults替代
4. **遗忘指示** - token消耗过程中逐渐忘记原始需求
5. **省略字段** - 某个字段难提取就不提取了
6. **跳过公司** - 认为小公司没必要抓就跳过

---

## 强制执行规则（必须加入代码中）

### 规则1：声明禁止幻想数据
```python
# 在脚本最顶部加入
STRICT_RULES = {
    'NO_SYNTHESIS': True,  # 禁止合成/推断任何数据
    'NO_DEFAULT_VALUES': True,  # 禁止使用默认值
    'NO_EMPTY_FIELDS': True,  # 禁止留空，必须标记[NO DATA FOUND]
    'MUST_VERIFY_EACH_FIELD': True,  # 每个字段都要有提取代码
    'FORCE_DETAIL_PAGE': True,  # 必须进详情页，不能只看列表
}

def validate_strict_rules():
    """启动时验证严格规则是否生效"""
    print("🔴 STRICT RULES ACTIVATED:")
    for rule, value in STRICT_RULES.items():
        print(f"   ✓ {rule} = {value}")
```

### 规则2：字段级别的强制检查
```python
# 每个产品必须检查所有12个字段
REQUIRED_FIELDS = [
    'COMPANY',
    'LOAN_TYPE',
    'REQUIRED_DOC',
    'FEATURES',
    'BENEFITS',
    'FEES_CHARGES',
    'TENURE',
    'RATE',
    'APPLICATION_FORM',
    'PRODUCT_DISCLOSURE',
    'TERMS_CONDITIONS',
    'BORROWER_PREFERENCE'
]

def enforce_field_check(product_data):
    """强制检查所有字段是否都被处理"""
    for field in REQUIRED_FIELDS:
        if field not in product_data:
            raise ValueError(f"❌ FATAL: Missing field {field}")
        
        # 如果字段是None，必须替换为[NO DATA FOUND]
        if product_data[field] is None:
            product_data[field] = '[NO DATA FOUND]'
        
        # 不许是空字符串
        if product_data[field] == '':
            product_data[field] = '[NO DATA FOUND]'
        
        # 不许是'N/A', 'NA', 'unknown'这类模糊值
        if product_data[field].lower() in ['n/a', 'na', 'unknown', 'not available', 'tbd', '待定']:
            product_data[field] = '[NO DATA FOUND]'
    
    print(f"✅ Field check passed for {product_data.get('LOAN_TYPE', 'unknown')}")
    return product_data
```

### 规则3：强制完整钻探日志
```python
class ExtractionAudit:
    """审计每一步是否真的完成"""
    
    def __init__(self, company_name):
        self.company = company_name
        self.audit_log = []
        self.product_count = 0
    
    def log_list_page_fetch(self, url, found_count):
        """记录列表页获取"""
        self.audit_log.append({
            'step': 'FETCH_LIST_PAGE',
            'url': url,
            'product_count': found_count,
            'time': datetime.now().isoformat()
        })
        print(f"  📋 List page: {found_count} products found")
    
    def log_detail_page_extract(self, product_name, fields_extracted):
        """记录详情页提取"""
        self.audit_log.append({
            'step': 'EXTRACT_DETAIL_PAGE',
            'product': product_name,
            'fields': fields_extracted,
            'time': datetime.now().isoformat()
        })
        self.product_count += 1
        print(f"  ✅ Detail page: {len(fields_extracted)} fields extracted")
    
    def log_field_not_found(self, field_name):
        """明确记录字段未找到"""
        self.audit_log.append({
            'step': 'FIELD_NOT_FOUND',
            'field': field_name,
            'action': 'Marked as [NO DATA FOUND]',
            'time': datetime.now().isoformat()
        })
    
    def save_audit(self):
        """保存审计日志"""
        audit_file = f"audit_{self.company}.json"
        with open(audit_file, 'w', encoding='utf-8') as f:
            json.dump(self.audit_log, f, ensure_ascii=False, indent=2, default=str)
        print(f"  🔍 Audit log saved: {audit_file}")
```

### 规则4：强制顺序+防遗忘
```python
class CompanyProcessor:
    """严格顺序处理，防止遗漏"""
    
    def __init__(self, companies_df):
        self.companies = companies_df
        self.processed = []
        self.skipped = []
        self.checkpoint_file = 'checkpoint.json'
    
    def process_sequentially(self):
        """必须按顺序处理，不能跳过"""
        for idx, row in self.companies.iterrows():
            company_name = row['公司名称']
            
            # 【强制】检查是否已处理过
            if self._is_already_processed(company_name):
                print(f"⏭️  Skipping {company_name} (already processed)")
                continue
            
            # 【强制】按顺序处理，完全完成才进下一个
            print(f"\n{'='*80}")
            print(f"🔴 MUST COMPLETE: Company {idx+1}/67 - {company_name}")
            print(f"{'='*80}")
            
            # 处理逻辑...
            # products = self._extract_all_products(row)
            
            # 【强制】确认完成才标记
            self._mark_as_processed(company_name)
            self._save_checkpoint()
    
    def _is_already_processed(self, company_name):
        return company_name in self.processed
    
    def _mark_as_processed(self, company_name):
        self.processed.append(company_name)
    
    def _save_checkpoint(self):
        """定期保存检查点，防止中途遗忘"""
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump({
                'processed': self.processed,
                'skipped': self.skipped,
                'total': len(self.companies),
                'progress_percent': len(self.processed) / len(self.companies) * 100,
                'timestamp': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Checkpoint saved: {len(self.processed)}/{len(self.companies)}")
```

### 规则5：多选择器尝试 + 详细日志
```python
def extract_with_fallback(soup, field_name, extraction_methods):
    """
    尝试多个提取方法，记录每次尝试
    
    Args:
        soup: BeautifulSoup对象
        field_name: 字段名称
        extraction_methods: 提取方法列表 [(方法名, 函数), ...]
    
    Returns:
        (提取结果, 使用的方法)
    """
    print(f"\n  🔍 Extracting {field_name}...")
    
    for method_name, extraction_func in extraction_methods:
        try:
            result = extraction_func(soup)
            if result and result != '[NO DATA FOUND]':
                print(f"     ✅ Found using method: {method_name}")
                return result, method_name
            else:
                print(f"     ⚠️  Method {method_name}: no data")
        except Exception as e:
            print(f"     ❌ Method {method_name} failed: {str(e)}")
    
    # 所有方法都失败了
    print(f"     🔴 ALL METHODS FAILED for {field_name}")
    return '[NO DATA FOUND]', 'NONE'

# 使用示例
def extract_rate_field(soup):
    methods = [
        ('keyword_search', lambda s: extract_by_keywords(s, ['interest rate', 'rate', '利率'])),
        ('table_extraction', lambda s: extract_from_table(s, 'rate')),
        ('spec_box', lambda s: extract_from_spec_section(s, 'rate')),
        ('json_ld_schema', lambda s: extract_from_json_ld(s, 'rate')),
    ]
    result, method_used = extract_with_fallback(soup, 'RATE', methods)
    return result
```

### 规则6：数据质量验证
```python
class DataQualityChecker:
    """验证数据质量，防止垃圾数据"""
    
    @staticmethod
    def validate_product(product_data):
        """检查产品数据是否符合质量标准"""
        issues = []
        
        # 检查1：不能所有字段都是[NO DATA FOUND]
        no_data_count = sum(1 for v in product_data.values() 
                           if v == '[NO DATA FOUND]')
        if no_data_count > 8:  # 超过8个字段没数据
            issues.append(f"⚠️  Too many [NO DATA FOUND] fields ({no_data_count}/12)")
        
        # 检查2：COMPANY和LOAN_TYPE必须有值
        if product_data['COMPANY'] == '[NO DATA FOUND]':
            issues.append(f"❌ FATAL: COMPANY field is empty")
            return False
        
        if product_data['LOAN_TYPE'] == '[NO DATA FOUND]':
            issues.append(f"❌ FATAL: LOAN_TYPE field is empty")
            return False
        
        # 检查3：检查是否是合成数据（例如所有字段都一样）
        values = [str(v).lower() for v in product_data.values() if v]
        if len(set(values)) < 3:
            issues.append(f"❌ Suspicious: too many duplicate values")
            return False
        
        # 检查4：长度合理性
        for field, value in product_data.items():
            if isinstance(value, str):
                if len(value) > 1000:
                    issues.append(f"⚠️  {field} too long ({len(value)} chars)")
        
        if issues:
            print("\n".join(issues))
            return len([i for i in issues if i.startswith('❌')]) == 0
        
        return True

    @staticmethod
    def generate_quality_report(all_products):
        """生成质量报告"""
        print(f"\n{'='*80}")
        print("📊 DATA QUALITY REPORT")
        print(f"{'='*80}")
        
        total = len(all_products)
        complete = sum(1 for p in all_products if DataQualityChecker.validate_product(p))
        no_data_rate = sum(1 for p in all_products 
                          for v in p.values() if v == '[NO DATA FOUND]') / (total * 12) * 100
        
        print(f"Total products: {total}")
        print(f"Valid products: {complete} ({complete/total*100:.1f}%)")
        print(f"[NO DATA FOUND] rate: {no_data_rate:.1f}%")
        
        # 按公司分类统计
        companies = {}
        for product in all_products:
            company = product['COMPANY']
            if company not in companies:
                companies[company] = {'count': 0, 'no_data_rate': 0}
            companies[company]['count'] += 1
        
        print(f"\nProducts per company (top 5):")
        for company, stats in sorted(companies.items(), 
                                    key=lambda x: x[1]['count'], 
                                    reverse=True)[:5]:
            print(f"  - {company}: {stats['count']} products")
```

---

## 最终集成检查清单

### ✅ 前期检查（运行前）
- [ ] 代码中明确定义STRICT_RULES = {所有规则都是True}
- [ ] 强制字段检查函数已集成
- [ ] 审计日志类已实例化
- [ ] 进度检查点文件已配置

### ✅ 运行中监控
- [ ] 每家公司打印"="*80分隔符
- [ ] 每个产品显示从列表页→详情页→字段提取过程
- [ ] 每个字段提取失败都有log
- [ ] 进度定时保存（每公司后）

### ✅ 完成后验证
- [ ] 总表行数 > 100（如果<100，说明抓得太少）
- [ ] [NO DATA FOUND]比率 < 15%（太多说明方法不对）
- [ ] 每家公司至少1-2条产品记录（如果=0，检查网站结构）
- [ ] 随机抽取5家公司，手动浏览网站验证数据
- [ ] 没有两行完全相同的产品记录

---

## 命令行运行时强制参数

```bash
# 启用严格模式
python solution.py --strict-mode=true

# 启用详细日志
python solution.py --verbose=true

# 启用数据验证
python solution.py --validate=true

# 完整命令
python solution.py --strict-mode=true --verbose=true --validate=true --output-dir=./output
```

---

## 最后的话

这些规则不是建议，而是**强制措施**。Replit倾向于：
- 🚫 留空字段而不是标记NO DATA FOUND
- 🚫 只看列表页而不进详情页  
- 🚫 网页复杂了就用默认数据
- 🚫 中途放弃某个字段

你的代码必须在每一步都**显式验证**和**审计**这些行为，确保Replit不能偷懒。
