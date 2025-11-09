#!/usr/bin/env python
"""
从剩余机构继续爬取 - 使用3种智能方法
已完成: 8家 (750个产品)
剩余: 59家机构
"""
import csv
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import psycopg2
from psycopg2.extras import execute_values
import os
from datetime import datetime
import re

DATABASE_URL = os.getenv('DATABASE_URL')
CSV_INPUT = "/home/runner/workspace/attached_assets/New 马来西亚贷款机构与平台全官网_完整版.csv_1762667764316.csv"

# 产品分类关键词
BUSINESS_CATS = ['personal', 'business', 'sme', 'corporate']
PRODUCT_TYPES = ['credit-card', 'cards', 'loan', 'loans', 'financing', 'mortgage', 
                 'home-loan', 'housing-loan', 'fixed-deposit', 'fd', 'deposit', 'overdraft', 'od']

def get_completed_companies():
    """获取已完成的公司"""
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    cur.execute("SELECT DISTINCT company FROM loan_products_ultimate")
    completed = set(row[0] for row in cur.fetchall())
    cur.close()
    con.close()
    return completed

def load_all_institutions():
    """加载所有机构"""
    institutions = []
    with open(CSV_INPUT, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for idx, row in enumerate(reader, 1):
            if len(row) >= 2:
                institutions.append({
                    'order': idx,
                    'name': row[0].strip(),
                    'website': row[1].strip()
                })
    return institutions

def classify_product(text):
    """分类产品"""
    text_lower = text.lower()
    if any(kw in text_lower for kw in ['credit card', 'kad kredit', 'visa', 'mastercard']):
        return 'CREDIT_CARD'
    elif any(kw in text_lower for kw in ['home', 'housing', 'mortgage', 'property']):
        return 'HOME_LOAN'
    elif any(kw in text_lower for kw in ['personal loan', 'cash loan']):
        return 'PERSONAL_LOAN'
    elif any(kw in text_lower for kw in ['car', 'auto', 'vehicle']):
        return 'CAR_LOAN'
    elif any(kw in text_lower for kw in ['business', 'sme', 'commercial']):
        return 'SME_LOAN'
    elif any(kw in text_lower for kw in ['fixed deposit', 'fd', 'time deposit']):
        return 'FIXED_DEPOSIT'
    elif any(kw in text_lower for kw in ['overdraft', 'od']):
        return 'OVERDRAFT'
    else:
        return 'OTHER'

def extract_rate(text):
    """提取利率"""
    match = re.search(r'(\d+\.?\d*)\s*%', text)
    return match.group(0) if match else '请联系银行'

def scrape_single_company(order, name, website):
    """爬取单个公司 - 简化版"""
    print(f"\n[{order}/67] 🏦 {name}")
    print(f"   {website}")
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    products = []
    visited = set()
    
    # 生成所有可能的URL (方法3: URL拼接)
    urls_to_try = []
    
    # 根URL
    urls_to_try.append(website)
    
    # /personal, /business, /sme, /corporate
    for cat in BUSINESS_CATS:
        urls_to_try.append(urljoin(website, f'/{cat}'))
        urls_to_try.append(urljoin(website, f'/en/{cat}'))
        
        # /personal/cards, /personal/loans, etc.
        for prod in PRODUCT_TYPES:
            urls_to_try.append(urljoin(website, f'/{cat}/{prod}'))
            urls_to_try.append(urljoin(website, f'/en/{cat}/{prod}'))
    
    # 直接产品URL
    for prod in PRODUCT_TYPES:
        urls_to_try.append(urljoin(website, f'/{prod}'))
        urls_to_try.append(urljoin(website, f'/en/{prod}'))
    
    # 去重
    urls_to_try = list(set(urls_to_try))
    print(f"   尝试 {len(urls_to_try)} 个URL")
    
    # 访问每个URL
    for idx, url in enumerate(urls_to_try[:80], 1):  # 限制80个
        if url in visited:
            continue
        visited.add(url)
        
        try:
            response = session.get(url, timeout=8)
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            
            # 提取所有标题
            for tag in ['h1', 'h2', 'h3', 'h4']:
                for heading in soup.find_all(tag):
                    h_text = heading.get_text(strip=True)
                    
                    # 必须包含产品关键词
                    if 5 < len(h_text) < 150 and any(kw in h_text.lower() for kw in [
                        'card', 'loan', 'financing', 'deposit', 'overdraft', 'mortgage'
                    ]):
                        products.append({
                            'company': name,
                            'product_name': h_text,
                            'loan_type': classify_product(h_text),
                            'rate': extract_rate(text[:3000]),
                            'source_url': url
                        })
            
            if idx % 20 == 0:
                print(f"   进度: {idx}/{min(len(urls_to_try), 80)}, 找到: {len(products)}")
            
            time.sleep(0.2)
            
        except:
            pass
    
    # 去重
    seen = set()
    unique = []
    for p in products:
        key = f"{p['company']}_{p['product_name']}"
        if key not in seen:
            seen.add(key)
            unique.append(p)
    
    print(f"   ✅ 找到 {len(unique)} 个产品")
    return unique

def save_products(products):
    """保存产品"""
    if not products:
        return
    
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
        p['company'], p['loan_type'], p['product_name'], '请访问银行官网',
        '请访问银行官网', '请访问银行官网', '请联系银行', '请联系银行',
        p['rate'], '', '', '', '所有客户', p['source_url'], datetime.now()
    ) for p in products]
    
    execute_values(cur, sql, items)
    con.commit()
    cur.close()
    con.close()

def main():
    print("=" * 80)
    print("继续爬取 - 从剩余机构开始")
    print("=" * 80)
    
    # 获取已完成和所有机构
    completed = get_completed_companies()
    all_inst = load_all_institutions()
    
    print(f"\n✅ 已完成: {len(completed)} 家")
    print(f"📋 总机构: {len(all_inst)} 家")
    
    # 过滤剩余
    remaining = [inst for inst in all_inst if inst['name'] not in completed]
    print(f"📌 剩余: {len(remaining)} 家\n")
    
    total_new = 0
    
    # 逐个爬取
    for inst in remaining:
        try:
            products = scrape_single_company(inst['order'], inst['name'], inst['website'])
            if products:
                save_products(products)
                total_new += len(products)
                print(f"   💾 已保存")
            else:
                print(f"   ⚠️  无产品")
        except Exception as e:
            print(f"   ❌ 错误: {str(e)[:50]}")
        
        time.sleep(1)
    
    print("\n" + "=" * 80)
    print(f"🎉 完成！新增 {total_new} 个产品")
    
    # 最终统计
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    cur.execute("SELECT COUNT(*), COUNT(DISTINCT company) FROM loan_products_ultimate")
    result = cur.fetchone()
    if result:
        total, companies = result
        print(f"📊 数据库: {total} 个产品，{companies} 家公司")
    cur.close()
    con.close()

if __name__ == '__main__':
    main()
