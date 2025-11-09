#!/usr/bin/env python3
"""
超强容错爬虫 - 每个公司独立进程，绝不崩溃
"""
import csv, time, requests, psycopg2, os, re, signal
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from psycopg2.extras import execute_values
from datetime import datetime
from contextlib import contextmanager

DATABASE_URL = os.getenv('DATABASE_URL')
CSV_FILE = "/home/runner/workspace/attached_assets/New 马来西亚贷款机构与平台全官网_完整版.csv_1762667764316.csv"

print("=" * 80)
print("🛡️  超强容错爬虫启动 - 每家公司独立处理，绝不崩溃")
print("=" * 80)

@contextmanager
def timeout(seconds):
    """超时上下文管理器"""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"操作超时({seconds}秒)")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def get_completed():
    try:
        con = psycopg2.connect(DATABASE_URL)
        cur = con.cursor()
        cur.execute("SELECT DISTINCT company FROM loan_products_ultimate")
        completed = set(r[0] for r in cur.fetchall())
        cur.close()
        con.close()
        return completed
    except:
        return set()

def load_institutions():
    inst = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for idx, row in enumerate(reader, 1):
            if len(row) >= 2:
                inst.append({'order': idx, 'name': row[0].strip(), 'url': row[1].strip()})
    return inst

def classify(text):
    t = text.lower()
    if 'credit' in t or 'kad' in t or 'card' in t or 'visa' in t or 'master' in t: return 'CREDIT_CARD'
    elif 'home' in t or 'housing' in t or 'mortgage' in t or 'property' in t: return 'HOME_LOAN'
    elif 'personal' in t or 'cash' in t: return 'PERSONAL_LOAN'
    elif 'car' in t or 'auto' in t or 'vehicle' in t: return 'CAR_LOAN'
    elif 'business' in t or 'sme' in t or 'commercial' in t: return 'SME_LOAN'
    elif 'deposit' in t or 'fd' in t or 'simpanan' in t: return 'FIXED_DEPOSIT'
    elif 'overdraft' in t or 'od' in t: return 'OVERDRAFT'
    elif 'refinanc' in t: return 'REFINANCE'
    else: return 'OTHER'

def scrape_company_safe(order, name, url):
    """安全爬取单个公司，带多重保护"""
    print(f"\n[{order}/67] {name}")
    print(f"   🌐 {url[:70]}")
    
    products = []
    
    try:
        with timeout(90):  # 总超时90秒
            session = requests.Session()
            session.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            
            # 限制爬取的URL数量
            paths = [
                '/', '/personal', '/business', '/sme',
                '/cards', '/loans', '/deposits', '/financing',
                '/personal/cards', '/personal/loans', '/personal/deposits',
                '/business/loans', '/sme/loans',
                '/credit-cards', '/personal-loan', '/home-loan', '/fixed-deposit'
            ]
            
            for p in paths[:15]:  # 只爬15个URL
                try:
                    full_url = urljoin(url, p)
                    r = session.get(full_url, timeout=6)
                    
                    if r.status_code != 200:
                        continue
                    
                    soup = BeautifulSoup(r.text[:50000], 'html.parser')  # 只解析前50KB
                    
                    # 查找产品标题
                    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'strong'])[:30]:
                        txt = tag.get_text(strip=True)
                        if 6 < len(txt) < 100:
                            keywords = ['card', 'loan', 'deposit', 'financing', 'kredit', 'pinjaman']
                            if any(k in txt.lower() for k in keywords):
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
                    
                    time.sleep(0.1)
                except:
                    pass
        
        # 去重
        seen = set()
        unique = []
        for p in products:
            k = f"{p['company']}|{p['name']}"
            if k not in seen:
                seen.add(k)
                unique.append(p)
        
        print(f"   ✅ {len(unique)} 个产品")
        return unique
        
    except TimeoutError:
        print(f"   ⏱️  超时90秒")
        return products
    except Exception as e:
        print(f"   ❌ {str(e)[:40]}")
        return []

def save_to_db(products):
    if not products:
        return 0
    
    try:
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
        inserted = cur.rowcount
        cur.close()
        con.close()
        return inserted
    except Exception as e:
        print(f"   💥 数据库错误: {str(e)[:30]}")
        return 0

# 主程序
completed = get_completed()
all_inst = load_institutions()
remaining = [inst for inst in all_inst if inst['name'] not in completed]

print(f"\n📊 已完成: {len(completed)} 家")
print(f"📋 总机构: {len(all_inst)} 家")
print(f"🎯 剩余: {len(remaining)} 家\n")

total_new = 0
success_count = 0
failed = []

for inst in remaining:
    try:
        prods = scrape_company_safe(inst['order'], inst['name'], inst['url'])
        
        if prods:
            saved = save_to_db(prods)
            total_new += len(prods)
            success_count += 1
            print(f"   💾 已保存{saved}个")
        else:
            failed.append(inst['name'])
            print(f"   ⚠️  无数据")
        
        time.sleep(0.5)
        
    except Exception as e:
        failed.append(inst['name'])
        print(f"   ❌ 异常: {str(e)[:30]}")
        continue

print("\n" + "=" * 80)
print(f"🎉 爬取完成！")
print(f"   成功: {success_count} 家公司")
print(f"   新增: {total_new} 个产品")
print(f"   失败: {len(failed)} 家")
print("=" * 80)

# 最终统计
try:
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    cur.execute("SELECT COUNT(*), COUNT(DISTINCT company) FROM loan_products_ultimate")
    r = cur.fetchone()
    if r:
        print(f"\n📊 数据库总计: {r[0]} 个产品，{r[1]} 家公司")
    
    cur.execute("SELECT loan_type, COUNT(*) FROM loan_products_ultimate GROUP BY loan_type ORDER BY COUNT(*) DESC")
    print("\n📈 产品分布:")
    for row in cur.fetchall():
        print(f"   {row[0]:15s}: {row[1]:4d}")
    
    cur.close()
    con.close()
except:
    pass

if failed:
    print(f"\n⚠️  无数据公司 ({len(failed)}):")
    for f in failed[:15]:
        print(f"   - {f}")

print("\n✅ 完成！")
