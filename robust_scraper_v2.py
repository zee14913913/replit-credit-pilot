#!/usr/bin/env python3
"""
强化版爬虫V2 - 处理大型银行网站，超时保护，自动跳过问题网站
"""
import csv, time, requests, psycopg2, os, re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from psycopg2.extras import execute_values
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from functools import partial

DATABASE_URL = os.getenv('DATABASE_URL')
CSV_FILE = "/home/runner/workspace/attached_assets/New 马来西亚贷款机构与平台全官网_完整版.csv_1762667764316.csv"

print("=" * 80)
print("🚀 强化版爬虫V2 启动")
print("=" * 80)

def get_completed():
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    cur.execute("SELECT DISTINCT company FROM loan_products_ultimate")
    completed = set(r[0] for r in cur.fetchall())
    cur.close()
    con.close()
    return completed

def load_institutions():
    inst = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for idx, row in enumerate(reader, 1):
            if len(row) >= 2:
                inst.append({'order': idx, 'name': row[0].strip(), 'url': row[1].strip()})
    return inst

def classify_product(text):
    t = text.lower()
    if any(k in t for k in ['credit card', 'kad kredit', 'visa', 'mastercard', 'amex']): 
        return 'CREDIT_CARD'
    elif any(k in t for k in ['home', 'housing', 'mortgage', 'property', 'rumah']): 
        return 'HOME_LOAN'
    elif any(k in t for k in ['personal loan', 'cash loan', 'pinjaman peribadi']): 
        return 'PERSONAL_LOAN'
    elif any(k in t for k in ['car', 'auto', 'vehicle', 'hire purchase']): 
        return 'CAR_LOAN'
    elif any(k in t for k in ['business', 'sme', 'commercial', 'enterprise']): 
        return 'SME_LOAN'
    elif any(k in t for k in ['fixed deposit', 'fd', 'time deposit', 'deposit']): 
        return 'FIXED_DEPOSIT'
    elif any(k in t for k in ['overdraft', 'od', 'working capital']): 
        return 'OVERDRAFT'
    elif any(k in t for k in ['refinance', 'refinancing', 'refi']): 
        return 'REFINANCE'
    else: 
        return 'OTHER'

def scrape_single_url(session, full_url, company_name, timeout=10):
    """爬取单个URL，带超时保护"""
    products = []
    try:
        r = session.get(full_url, timeout=timeout)
        if r.status_code != 200:
            return products
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 查找产品标题 (h1-h4, strong, bold text)
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'b'])[:50]:
            txt = tag.get_text(strip=True)
            
            # 过滤条件：长度合适 & 包含产品关键词
            if 5 < len(txt) < 150:
                keywords = ['card', 'loan', 'deposit', 'financing', 'kredit', 'pinjaman', 'simpanan', 'kad']
                if any(k in txt.lower() for k in keywords):
                    # 提取利率
                    rate = '请联系银行'
                    rate_match = re.search(r'(\d+\.?\d*)\s*%', soup.get_text()[:5000])
                    if rate_match:
                        rate = rate_match.group(0)
                    
                    products.append({
                        'company': company_name,
                        'name': txt,
                        'type': classify_product(txt),
                        'rate': rate,
                        'url': full_url
                    })
        
    except Exception:
        pass
    
    return products

def scrape_company_with_timeout(order, name, url, max_timeout=120):
    """爬取单个公司，总超时限制"""
    print(f"\n[{order}/67] {name}")
    print(f"   🌐 {url}")
    
    start_time = time.time()
    products = []
    
    try:
        session = requests.Session()
        session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        # 动态生成URL路径
        paths = [
            '/', '/personal', '/business', '/sme', '/corporate',
            '/personal/cards', '/personal/loans', '/personal/deposits', '/personal/financing',
            '/business/loans', '/business/financing', '/sme/loans', '/sme/financing',
            '/cards', '/credit-cards', '/debit-cards',
            '/loans', '/financing', '/personal-loan', '/home-loan', '/mortgage',
            '/fixed-deposit', '/time-deposit', '/deposits',
            '/overdraft', '/working-capital',
            '/products', '/products/cards', '/products/loans', '/products/deposits',
            '/banking/personal', '/banking/business',
        ]
        
        # 遍历路径，但限制总时间
        for p in paths[:40]:
            if time.time() - start_time > max_timeout:
                print(f"   ⏱️  超时({max_timeout}秒)，停止爬取")
                break
            
            full_url = urljoin(url, p)
            prods = scrape_single_url(session, full_url, name, timeout=8)
            products.extend(prods)
            time.sleep(0.15)
        
        # 去重
        seen = set()
        unique = []
        for p in products:
            key = f"{p['company']}|{p['name']}"
            if key not in seen and len(p['name']) > 5:
                seen.add(key)
                unique.append(p)
        
        elapsed = time.time() - start_time
        print(f"   ✅ {len(unique)} 个产品 (用时{elapsed:.1f}秒)")
        return unique
        
    except Exception as e:
        print(f"   ❌ 错误: {str(e)[:60]}")
        return []

def save_to_db(products):
    if not products:
        return 0
    
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
        p['company'], p['type'], p['name'], '请访问银行官网了解详情', 
        '请访问银行官网了解详情', '请访问银行官网了解详情',
        '请联系银行', '请联系银行', p['rate'], '', '', '', 
        '所有客户', p['url'], datetime.now()
    ) for p in products]
    
    execute_values(cur, sql, items)
    con.commit()
    inserted = cur.rowcount
    cur.close()
    con.close()
    return inserted

# 主程序
completed = get_completed()
all_inst = load_institutions()
remaining = [inst for inst in all_inst if inst['name'] not in completed]

print(f"\n📊 已完成: {len(completed)} 家")
print(f"📋 总机构: {len(all_inst)} 家")
print(f"🎯 剩余: {len(remaining)} 家\n")

total_new_products = 0
total_new_companies = 0
failed_companies = []

for inst in remaining:
    try:
        products = scrape_company_with_timeout(inst['order'], inst['name'], inst['url'], max_timeout=120)
        
        if products:
            inserted = save_to_db(products)
            total_new_products += len(products)
            total_new_companies += 1
            print(f"   💾 已保存{inserted}个产品")
        else:
            failed_companies.append(inst['name'])
            print(f"   ⚠️  无产品数据")
        
        time.sleep(1)
        
    except Exception as e:
        failed_companies.append(inst['name'])
        print(f"   ❌ 异常: {str(e)[:50]}")

print("\n" + "=" * 80)
print(f"🎉 爬取完成！")
print(f"   新增产品: {total_new_products} 个")
print(f"   新增公司: {total_new_companies} 家")
print("=" * 80)

# 最终统计
con = psycopg2.connect(DATABASE_URL)
cur = con.cursor()
cur.execute("SELECT COUNT(*), COUNT(DISTINCT company) FROM loan_products_ultimate")
result = cur.fetchone()
if result:
    total, companies = result
    print(f"\n📊 数据库总计: {total} 个产品，{companies} 家公司")

cur.execute("""
    SELECT loan_type, COUNT(*) as cnt 
    FROM loan_products_ultimate 
    GROUP BY loan_type 
    ORDER BY cnt DESC
""")
print("\n📈 产品类型分布:")
for row in cur.fetchall():
    print(f"   {row[0]:20s}: {row[1]:4d}")

cur.close()
con.close()

if failed_companies:
    print(f"\n⚠️  无数据的公司 ({len(failed_companies)}):")
    for name in failed_companies[:10]:
        print(f"   - {name}")
    if len(failed_companies) > 10:
        print(f"   ... 还有{len(failed_companies)-10}家")

print("\n✅ 所有任务完成！")
print("=" * 80)
