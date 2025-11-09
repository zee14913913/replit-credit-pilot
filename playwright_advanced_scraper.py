#!/usr/bin/env python3
"""
Playwright高级爬虫 - 处理JavaScript渲染的复杂网站
针对剩余43家机构，特别是Maybank、Public Bank等大型银行
"""
import csv, time, psycopg2, os, re, asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
from psycopg2.extras import execute_values
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL')
CSV_FILE = "/home/runner/workspace/attached_assets/New 马来西亚贷款机构与平台全官网_完整版.csv_1762667764316.csv"

print("=" * 80)
print("🚀 Playwright高级爬虫启动")
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
    if any(k in t for k in ['credit card', 'kad kredit', 'visa', 'mastercard', 'amex']): 
        return 'CREDIT_CARD'
    elif any(k in t for k in ['home loan', 'housing loan', 'mortgage', 'property loan', 'rumah']): 
        return 'HOME_LOAN'
    elif any(k in t for k in ['personal loan', 'cash loan', 'pinjaman peribadi']): 
        return 'PERSONAL_LOAN'
    elif any(k in t for k in ['car loan', 'auto loan', 'vehicle', 'hire purchase']): 
        return 'CAR_LOAN'
    elif any(k in t for k in ['business loan', 'sme loan', 'commercial']): 
        return 'SME_LOAN'
    elif any(k in t for k in ['fixed deposit', 'fd', 'time deposit', 'simpanan tetap']): 
        return 'FIXED_DEPOSIT'
    elif any(k in t for k in ['overdraft', 'od']): 
        return 'OVERDRAFT'
    elif any(k in t for k in ['refinanc']): 
        return 'REFINANCE'
    else: 
        return 'OTHER'

async def scrape_company_async(order, name, url):
    """使用Playwright异步爬取单个公司"""
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
                    '--disable-software-rasterizer'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            page.set_default_timeout(15000)  # 15秒超时
            
            # 定义要访问的路径
            paths = [
                '/',
                '/personal', '/business', '/sme', '/corporate',
                '/personal/cards', '/personal/loans', '/personal/deposits',
                '/business/loans', '/sme/loans',
                '/cards', '/credit-cards', '/loans', '/personal-loans',
                '/home-loans', '/mortgage', '/fixed-deposit', '/deposits'
            ]
            
            for path in paths[:12]:  # 限制12个URL
                try:
                    full_url = url.rstrip('/') + path if path != '/' else url
                    
                    await page.goto(full_url, wait_until='domcontentloaded', timeout=15000)
                    await asyncio.sleep(1)  # 等待动态内容加载
                    
                    # 尝试滚动加载更多内容
                    try:
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        await asyncio.sleep(0.5)
                    except:
                        pass
                    
                    # 获取页面内容
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # 提取产品信息
                    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b'])[:40]:
                        txt = tag.get_text(strip=True)
                        
                        if 6 < len(txt) < 120:
                            keywords = [
                                'card', 'loan', 'deposit', 'financing', 'mortgage',
                                'kredit', 'kad', 'pinjaman', 'simpanan', 'pembiayaan'
                            ]
                            if any(k in txt.lower() for k in keywords):
                                # 提取利率
                                rate = '请联系银行'
                                page_text = soup.get_text()[:8000]
                                rate_match = re.search(r'(\d+\.?\d*)\s*%', page_text)
                                if rate_match:
                                    rate = rate_match.group(0)
                                
                                products.append({
                                    'company': name,
                                    'name': txt,
                                    'type': classify(txt),
                                    'rate': rate,
                                    'url': full_url
                                })
                    
                except PlaywrightTimeout:
                    print(f"   ⏱️  超时: {path}")
                except Exception as e:
                    print(f"   ⚠️  {path}: {str(e)[:30]}")
                
                await asyncio.sleep(0.3)
            
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
        print(f"   ❌ 错误: {str(e)[:50]}")
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
            products = await scrape_company_async(inst['order'], inst['name'], inst['url'])
            
            if products:
                saved = save_to_db(products)
                total_new += len(products)
                success += 1
                print(f"   💾 已保存{saved}个")
            else:
                failed.append(inst['name'])
                print(f"   ⚠️  无数据")
            
            await asyncio.sleep(1)
            
        except Exception as e:
            failed.append(inst['name'])
            print(f"   ❌ 异常: {str(e)[:40]}")
    
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
        for f in failed[:20]:
            print(f"   - {f}")

if __name__ == '__main__':
    asyncio.run(main())
