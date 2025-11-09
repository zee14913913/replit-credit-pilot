#!/usr/bin/env python
"""
超级快速爬虫 - 68家金融机构全面产品提取
策略：直接从产品列表页提取，无需访问每个详情页
目标：100%完整性 - 信用卡、贷款、OD、FD等所有产品
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

# 产品路径 - 针对每家银行尝试
PRODUCT_PATHS = {
    'credit_card': ['/personal/cards', '/Cards/Credit-Cards', '/credit-cards', '/cards', '/en/cards', '/my/en/personal/cards'],
    'personal_loan': ['/personal/loans', '/personal-loans', '/personal-financing', '/cash-loan', '/my/en/personal/loans'],
    'home_loan': ['/personal/home-loans', '/home-loans', '/housing-loan', '/mortgage', '/property-financing'],
    'car_loan': ['/personal/car-loan', '/auto-loan', '/hire-purchase', '/vehicle-financing'],
    'business_loan': ['/business/loans', '/business/financing', '/sme', '/sme-loans', '/business-financing'],
    'overdraft': ['/personal/overdraft', '/overdraft', '/od'],
    'fixed_deposit': ['/personal/fixed-deposit', '/fixed-deposit', '/fd', '/deposits', '/time-deposit'],
}

def load_institutions():
    """加载68家机构"""
    institutions = []
    with open(CSV_INPUT, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 2:
                institutions.append({'name': row[0], 'website': row[1]})
    return institutions

def extract_rate(text):
    """提取利率"""
    # 匹配 "X.XX%" or "X%" 格式
    rate_match = re.search(r'(\d+\.?\d*)\s*%', text)
    if rate_match:
        return rate_match.group(0)
    return '请联系银行'

def classify_loan_type(product_name, url_path=''):
    """分类产品类型"""
    text = (product_name + ' ' + url_path).lower()
    
    if 'credit card' in text or 'kad kredit' in text or '/card' in text:
        return 'CREDIT_CARD'
    elif 'home' in text or 'housing' in text or 'mortgage' in text or 'property' in text:
        return 'HOME_LOAN'
    elif 'personal' in text or 'cash loan' in text:
        return 'PERSONAL_LOAN'
    elif 'car' in text or 'auto' in text or 'vehicle' in text or 'hire purchase' in text:
        return 'CAR_LOAN'
    elif 'business' in text or 'sme' in text or 'commercial' in text:
        return 'SME_LOAN'
    elif 'deposit' in text or 'fd' in text or 'time deposit' in text:
        return 'FIXED_DEPOSIT'
    elif 'overdraft' in text or 'od' in text:
        return 'OVERDRAFT'
    elif 'refinance' in text or 'refinancing' in text:
        return 'REFINANCE'
    elif 'debt consolidation' in text:
        return 'DEBT_CONSOLIDATION'
    else:
        return 'OTHER'

def extract_products_from_page(url, company_name):
    """从单个页面提取所有产品"""
    products = []
    
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
        })
        
        if response.status_code != 200:
            return products
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        
        # 策略1: 提取所有heading标签（产品名称通常在heading中）
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5']):
            heading_text = heading.get_text(strip=True)
            
            # 过滤：长度合理且包含产品关键词
            if 5 < len(heading_text) < 150:
                if any(kw in heading_text.lower() for kw in [
                    'card', 'loan', 'financing', 'deposit', 'overdraft', 'mortgage',
                    'cash', 'personal', 'business', 'sme', 'home', 'auto', 'car'
                ]):
                    # 提取周围的利率信息
                    rate = '请联系银行'
                    parent = heading.find_parent(['div', 'section', 'article'])
                    if parent:
                        parent_text = parent.get_text()
                        rate = extract_rate(parent_text)
                    
                    # 提取产品链接
                    product_url = url
                    link = heading.find('a', href=True)
                    if link:
                        product_url = urljoin(url, link.get('href'))
                    
                    products.append({
                        'company': company_name,
                        'product_name': heading_text,
                        'loan_type': classify_loan_type(heading_text, url),
                        'rate': rate,
                        'source_url': product_url,
                        'required_doc': '请访问银行官网',
                        'features': '请访问银行官网',
                        'benefits': '请访问银行官网',
                        'fees_charges': '请联系银行',
                        'tenure': '请联系银行',
                        'application_form_url': '',
                        'product_disclosure_url': '',
                        'terms_conditions_url': '',
                        'preferred_customer_type': '所有客户',
                        'scraped_at': datetime.now()
                    })
        
        # 策略2: 提取产品卡片（通常包含class="card"或class="product"）
        for card in soup.find_all(['div', 'article'], class_=lambda x: x and (
            'card' in str(x).lower() or 'product' in str(x).lower()
        )):
            # 提取产品名称
            name_tag = card.find(['h1', 'h2', 'h3', 'h4', 'h5'])
            if name_tag:
                name = name_tag.get_text(strip=True)
                if 5 < len(name) < 150:
                    card_text = card.get_text()
                    rate = extract_rate(card_text)
                    
                    link = card.find('a', href=True)
                    product_url = urljoin(url, link.get('href')) if link else url
                    
                    products.append({
                        'company': company_name,
                        'product_name': name,
                        'loan_type': classify_loan_type(name, url),
                        'rate': rate,
                        'source_url': product_url,
                        'required_doc': '请访问银行官网',
                        'features': '请访问银行官网',
                        'benefits': '请访问银行官网',
                        'fees_charges': '请联系银行',
                        'tenure': '请联系银行',
                        'application_form_url': '',
                        'product_disclosure_url': '',
                        'terms_conditions_url': '',
                        'preferred_customer_type': '所有客户',
                        'scraped_at': datetime.now()
                    })
    
    except Exception as e:
        pass
    
    return products

def scrape_institution(company_name, base_url):
    """爬取单个机构的所有产品"""
    print(f"\n🏦 {company_name}")
    print(f"   {base_url}")
    
    all_products = []
    
    # 遍历所有产品类型的路径
    for category, paths in PRODUCT_PATHS.items():
        for path in paths:
            url = urljoin(base_url, path)
            products = extract_products_from_page(url, company_name)
            if products:
                all_products.extend(products)
                print(f"   ✅ {path} → {len(products)} products")
            time.sleep(0.2)  # 礼貌延迟
    
    # 去重
    seen = set()
    unique_products = []
    for p in all_products:
        key = f"{p['company']}_{p['product_name']}"
        if key not in seen:
            seen.add(key)
            unique_products.append(p)
    
    print(f"   📦 总计: {len(unique_products)} 个产品")
    return unique_products

def save_to_db(products):
    """批量保存到数据库"""
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
        ON CONFLICT (company, product_name) DO UPDATE SET
            loan_type = EXCLUDED.loan_type,
            rate = EXCLUDED.rate,
            source_url = EXCLUDED.source_url,
            scraped_at = EXCLUDED.scraped_at
    """
    
    items = [(
        p['company'], p['loan_type'], p['product_name'], p['required_doc'],
        p['features'], p['benefits'], p['fees_charges'], p['tenure'], p['rate'],
        p['application_form_url'], p['product_disclosure_url'], p['terms_conditions_url'],
        p['preferred_customer_type'], p['source_url'], p['scraped_at']
    ) for p in products]
    
    execute_values(cur, sql, items)
    con.commit()
    cur.close()
    con.close()
    print(f"   💾 已保存到数据库")

def main():
    print("=" * 80)
    print("🚀 超级快速爬虫 - 68家金融机构全面产品提取")
    print("   目标: 100%完整性 - 信用卡、贷款、OD、FD等所有产品")
    print("=" * 80)
    
    # 清空数据库
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    cur.execute("TRUNCATE TABLE loan_products_ultimate RESTART IDENTITY;")
    con.commit()
    cur.close()
    con.close()
    print("✅ 数据库已清空\n")
    
    institutions = load_institutions()
    print(f"📋 共 {len(institutions)} 家机构\n")
    
    total_products = 0
    for idx, inst in enumerate(institutions, 1):
        print(f"\n[{idx}/{len(institutions)}]", end=" ")
        try:
            products = scrape_institution(inst['name'], inst['website'])
            if products:
                total_products += len(products)
                save_to_db(products)
        except Exception as e:
            print(f"   ❌ 错误: {str(e)[:50]}")
        
        time.sleep(0.5)  # 礼貌延迟
    
    print("\n" + "=" * 80)
    print(f"🎉 完成！总计: {total_products} 个产品")
    print("=" * 80)
    
    # 最终统计
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    
    cur.execute("SELECT COUNT(*) FROM loan_products_ultimate")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT loan_type, COUNT(*) FROM loan_products_ultimate GROUP BY loan_type ORDER BY COUNT(*) DESC")
    breakdown = cur.fetchall()
    
    print(f"\n📊 数据库统计:")
    print(f"   总产品数: {total}")
    print(f"\n   分类统计:")
    for loan_type, count in breakdown:
        print(f"   - {loan_type}: {count}")
    
    cur.close()
    con.close()

if __name__ == '__main__':
    main()
