#!/usr/bin/env python3
"""
智能Playwright爬虫 - 快速跳过无法访问的网站，专注于有效目标
"""
import csv, time, psycopg2, os, re, asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
from psycopg2.extras import execute_values
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL')
CSV_FILE = "/home/runner/workspace/attached_assets/New 马来西亚贷款机构与平台全官网_完整版.csv_1762667764316.csv"

print("=" * 80)
print("🧠 智能Playwright爬虫 - 快速跳过问题网站")
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

def classify(text):
    t = text.lower()
    if any(k in t for k in ['credit card', 'kad kredit', 'visa', 'mastercard']): return 'CREDIT_CARD'
    elif any(k in t for k in ['home loan', 'housing', 'mortgage', 'property']): return 'HOME_LOAN'
    elif any(k in t for k in ['personal loan', 'cash loan']): return 'PERSONAL_LOAN'
    elif any(k in t for k in ['car loan', 'auto', 'vehicle']): return 'CAR_LOAN'
    elif any(k in t for k in ['business', 'sme', 'commercial']): return 'SME_LOAN'
    elif any(k in t for k in ['fixed deposit', 'fd', 'time deposit']): return 'FIXED_DEPOSIT'
    elif any(k in t for k in ['overdraft', 'od']): return 'OVERDRAFT'
    elif any(k in t for k in ['refinanc']): return 'REFINANCE'
    else: return 'OTHER'

async def scrape_company_smart(order, name, url):
    """智能爬取 - 快速失败，专注成功"""
    print(f"\n[{order}/67] {name}")
    print(f"   🌐 {url}")
    
    products = []
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                executable_path='/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium',
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--ignore-certificate-errors',
                    '--disable-software-rasterizer'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                ignore_https_errors=True  # 忽略SSL错误
            )
            
            page = await context.new_page()
            page.set_default_timeout(8000)  # 缩短到8秒
            
            # 简化路径列表 - 只访问最重要的8个
            paths = [
                '/', '/personal', '/business', '/cards', '/loans', 
                '/personal-loans', '/home-loans', '/fixed-deposit'
            ]
            
            success_count = 0
            fail_count = 0
            
            for path in paths:
                # 如果连续3次失败，放弃这个网站
                if fail_count >= 3:
                    print(f"   ⚠️  连续失败3次，跳过")
                    break
                
                try:
                    full_url = url.rstrip('/') + path if path != '/' else url
                    
                    await page.goto(full_url, wait_until='domcontentloaded', timeout=8000)
                    await asyncio.sleep(0.5)
                    
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    found_this_page = 0
                    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4'])[:30]:
                        txt = tag.get_text(strip=True)
                        
                        if 6 < len(txt) < 100:
                            keywords = ['card', 'loan', 'deposit', 'financing', 'kredit', 'pinjaman']
                            if any(k in txt.lower() for k in keywords):
                                rate = '请联系银行'
                                m = re.search(r'(\d+\.?\d*)\s*%', soup.get_text()[:5000])
                                if m: rate = m.group(0)
                                
                                products.append({
                                    'company': name,
                                    'name': txt,
                                    'type': classify(txt),
                                    'rate': rate,
                                    'url': full_url
                                })
                                found_this_page += 1
                    
                    if found_this_page > 0:
                        success_count += 1
                        fail_count = 0  # 重置失败计数
                    
                except PlaywrightTimeout:
                    fail_count += 1
                except Exception:
                    fail_count += 1
                
                await asyncio.sleep(0.2)
            
            await browser.close()
        
        # 去重
        seen = set()
        unique = []
        for p in products:
            key = f"{p['company']}|{p['name']}"
            if key not in seen:
                seen.add(key)
                unique.append(p)
        
        print(f"   ✅ {len(unique)} 个产品")
        return unique
        
    except Exception as e:
        print(f"   ❌ {str(e)[:50]}")
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
        p['company'], p['type'], p['name'], 
        '请访问银行官网了解详情', '请访问银行官网了解详情', '请访问银行官网了解详情',
        '请联系银行', '请联系银行', p['rate'], '', '', '', 
        '所有客户', p['url'], datetime.now()
    ) for p in products]
    
    execute_values(cur, sql, items)
    con.commit()
    inserted = cur.rowcount
    cur.close()
    con.close()
    return inserted

async def main():
    completed = get_completed()
    all_inst = load_institutions()
    remaining = [inst for inst in all_inst if inst['name'] not in completed]
    
    print(f"\n📊 已完成: {len(completed)} 家")
    print(f"📋 总机构: {len(all_inst)} 家")
    print(f"🎯 剩余: {len(remaining)} 家\n")
    
    total_new = 0
    success = 0
    failed = []
    
    for inst in remaining:
        try:
            products = await scrape_company_smart(inst['order'], inst['name'], inst['url'])
            
            if products:
                saved = save_to_db(products)
                total_new += len(products)
                success += 1
                print(f"   💾 已保存{saved}个")
            else:
                failed.append(inst['name'])
                print(f"   ⚠️  无数据")
            
            await asyncio.sleep(0.5)
            
        except Exception as e:
            failed.append(inst['name'])
            print(f"   ❌ {str(e)[:40]}")
    
    print("\n" + "=" * 80)
    print(f"🎉 爬取完成！")
    print(f"   成功: {success} 家")
    print(f"   新增: {total_new} 个产品")
    print(f"   失败: {len(failed)} 家")
    print("=" * 80)
    
    # 最终统计
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    cur.execute("SELECT COUNT(*), COUNT(DISTINCT company) FROM loan_products_ultimate")
    r = cur.fetchone()
    if r:
        print(f"\n📊 数据库总计: {r[0]} 个产品，{r[1]} 家公司")
    
    cur.execute("""
        SELECT loan_type, COUNT(*) 
        FROM loan_products_ultimate 
        GROUP BY loan_type 
        ORDER BY COUNT(*) DESC
    """)
    print("\n📈 产品分布:")
    for row in cur.fetchall():
        print(f"   {row[0]:15s}: {row[1]:4d}")
    
    cur.close()
    con.close()
    
    if failed:
        print(f"\n⚠️  无数据公司 ({len(failed)}):")
        for f in failed[:25]:
            print(f"   - {f}")
    
    print("\n✅ 完成！")

if __name__ == '__main__':
    asyncio.run(main())
