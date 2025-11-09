#!/usr/bin/env python3
"""
简化工作爬虫 - 从剩余59家机构继续
"""
print("=" * 80)
print("开始爬取...")
print("=" * 80)

import csv, time, requests, psycopg2, os, re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from psycopg2.extras import execute_values
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL')
CSV_FILE = "/home/runner/workspace/attached_assets/New 马来西亚贷款机构与平台全官网_完整版.csv_1762667764316.csv"

# 获取已完成的公司
print("\n获取已完成公司...")
con = psycopg2.connect(DATABASE_URL)
cur = con.cursor()
cur.execute("SELECT DISTINCT company FROM loan_products_ultimate")
completed = set(r[0] for r in cur.fetchall())
cur.close()
con.close()
print(f"✅ 已完成: {len(completed)} 家")

# 读取所有机构
print("读取机构列表...")
institutions = []
with open(CSV_FILE, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    for idx, row in enumerate(reader, 1):
        if len(row) >= 2:
            institutions.append({'order': idx, 'name': row[0].strip(), 'url': row[1].strip()})

print(f"✅ 总机构: {len(institutions)} 家")

# 过滤剩余
remaining = [inst for inst in institutions if inst['name'] not in completed]
print(f"📌 剩余: {len(remaining)} 家\n")

# 产品分类
def classify(text):
    t = text.lower()
    if any(k in t for k in ['credit card', 'kad kredit', 'visa', 'mastercard']): return 'CREDIT_CARD'
    elif any(k in t for k in ['home', 'housing', 'mortgage', 'property']): return 'HOME_LOAN'
    elif any(k in t for k in ['personal loan', 'cash']): return 'PERSONAL_LOAN'
    elif any(k in t for k in ['car', 'auto', 'vehicle']): return 'CAR_LOAN'
    elif any(k in t for k in ['business', 'sme', 'commercial']): return 'SME_LOAN'
    elif any(k in t for k in ['fixed deposit', 'fd', 'time deposit']): return 'FIXED_DEPOSIT'
    elif any(k in t for k in ['overdraft', 'od']): return 'OVERDRAFT'
    else: return 'OTHER'

# 爬取单个公司
def scrape(order, name, url):
    print(f"\n[{order}/67] {name}")
    print(f"   {url}")
    
    products = []
    session = requests.Session()
    session.headers = {'User-Agent': 'Mozilla/5.0'}
    
    # URL列表
    paths = [
        '/', '/personal', '/business', '/sme', '/corporate',
        '/personal/cards', '/personal/loans', '/personal/financing', '/personal/fixed-deposit',
        '/business/loans', '/business/financing', '/sme/loans',
        '/cards', '/credit-cards', '/loans', '/financing', '/fixed-deposit', '/deposits', '/overdraft'
    ]
    
    for p in paths[:30]:  # 限制30个URL
        full_url = urljoin(url, p)
        try:
            r = session.get(full_url, timeout=8)
            if r.status_code != 200: continue
            
            soup = BeautifulSoup(r.text, 'html.parser')
            
            for h in soup.find_all(['h1', 'h2', 'h3', 'h4'])[:20]:
                txt = h.get_text(strip=True)
                if 5 < len(txt) < 120 and any(k in txt.lower() for k in ['card', 'loan', 'deposit', 'financing']):
                    rate = '请联系银行'
                    m = re.search(r'(\d+\.?\d*)\s*%', soup.get_text()[:3000])
                    if m: rate = m.group(0)
                    
                    products.append({
                        'company': name,
                        'name': txt,
                        'type': classify(txt),
                        'rate': rate,
                        'url': full_url
                    })
            
            time.sleep(0.2)
        except: pass
    
    # 去重
    seen = set()
    unique = []
    for p in products:
        k = f"{p['company']}_{p['name']}"
        if k not in seen:
            seen.add(k)
            unique.append(p)
    
    print(f"   ✅ {len(unique)} 个产品")
    return unique

# 保存到数据库
def save(products):
    if not products: return
    
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    
    sql = """
        INSERT INTO loan_products_ultimate(
            company, loan_type, product_name, required_doc, features, benefits,
            fees_charges, tenure, rate, application_form_url, product_disclosure_url,
            terms_conditions_url, preferred_customer_type, source_url, scraped_at
        ) VALUES %s
        ON CONFLICT (company, product_name) DO NOTHING
    """
    
    items = [(
        p['company'], p['type'], p['name'], '请访问银行官网', '请访问银行官网', '请访问银行官网',
        '请联系银行', '请联系银行', p['rate'], '', '', '', '所有客户', p['url'], datetime.now()
    ) for p in products]
    
    execute_values(cur, sql, items)
    con.commit()
    cur.close()
    con.close()

# 主循环
total = 0
for inst in remaining:
    try:
        prods = scrape(inst['order'], inst['name'], inst['url'])
        if prods:
            save(prods)
            total += len(prods)
            print(f"   💾 已保存")
    except Exception as e:
        print(f"   ❌ 错误: {str(e)[:40]}")
    
    time.sleep(1)

print("\n" + "=" * 80)
print(f"🎉 完成！新增 {total} 个产品")
print("=" * 80)

# 最终统计
con = psycopg2.connect(DATABASE_URL)
cur = con.cursor()
cur.execute("SELECT COUNT(*), COUNT(DISTINCT company) FROM loan_products_ultimate")
r = cur.fetchone()
if r:
    print(f"📊 数据库: {r[0]} 个产品，{r[1]} 家公司")
cur.close()
con.close()
