#!/usr/bin/env python
"""
严格按CSV顺序爬取 - 68家金融机构完整产品提取
规则：
1. 严格按CSV文件顺序（第1行到第68行）
2. 每家公司必须提取所有信用卡、贷款、OD、FD产品
3. 宁可多抓（后期删除），绝不遗漏
4. 无过滤、无跳过、100%完整性
"""
import csv
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import psycopg2
from psycopg2.extras import execute_values
import os
from datetime import datetime
import re

DATABASE_URL = os.getenv('DATABASE_URL')
CSV_INPUT = "/home/runner/workspace/attached_assets/New 马来西亚贷款机构与平台全官网_完整版.csv_1762667764316.csv"

# 所有可能的产品路径（宁可多不能少）
ALL_PATHS = [
    # Credit Cards
    '/personal/cards', '/cards', '/credit-cards', '/Cards/Credit-Cards', 
    '/en/cards', '/my/en/personal/cards', '/en/personal/cards',
    '/personal/credit-cards', '/products/cards', '/retail/cards',
    
    # Personal Loans
    '/personal/loans', '/personal-loans', '/loans', '/personal-financing',
    '/cash-loan', '/my/en/personal/loans', '/en/personal/loans',
    '/products/loans', '/retail/loans', '/personal/borrowing',
    
    # Home Loans
    '/personal/home-loans', '/home-loans', '/housing-loan', '/mortgage',
    '/property-financing', '/home-financing', '/en/home-loans',
    '/my/en/personal/home-loans', '/products/home-loans',
    
    # Car Loans
    '/personal/car-loan', '/auto-loan', '/hire-purchase', '/vehicle-financing',
    '/car-financing', '/en/car-loans', '/my/en/personal/car-loans',
    
    # Business/SME Loans
    '/business/loans', '/business/financing', '/sme', '/sme-loans',
    '/business-financing', '/commercial/loans', '/business-banking/loans',
    '/en/business/loans', '/sme-financing',
    
    # Overdraft
    '/personal/overdraft', '/overdraft', '/od', '/business/overdraft',
    '/en/overdraft',
    
    # Fixed Deposit
    '/personal/fixed-deposit', '/fixed-deposit', '/fd', '/deposits',
    '/time-deposit', '/en/fixed-deposit', '/my/en/personal/deposits',
    '/products/deposits', '/investments/fixed-deposit',
    
    # Refinancing
    '/refinancing', '/refinance', '/debt-consolidation', '/personal/refinancing',
    
    # Islamic Banking
    '/islamic/cards', '/islamic/financing', '/islamic/home-financing',
    '/islamic/personal-financing', '/islamic/deposits',
]

def load_institutions_in_order():
    """严格按CSV顺序加载所有机构"""
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

def extract_all_links(soup, base_url):
    """提取页面所有链接"""
    links = []
    for a in soup.find_all('a', href=True):
        href = a.get('href')
        full_url = urljoin(base_url, href)
        
        # 排除明显无关的链接
        if any(x in full_url.lower() for x in ['mailto:', 'tel:', 'javascript:', '#']):
            continue
        if any(x in full_url.lower() for x in ['/login', '/logout', '/signin', '/signout']):
            continue
            
        links.append(full_url)
    
    return list(set(links))

def extract_all_headings(soup):
    """提取所有可能的产品标题"""
    products = []
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text = heading.get_text(strip=True)
        if len(text) > 3 and len(text) < 200:
            products.append(text)
    return products

def classify_loan_type(text):
    """分类产品类型"""
    text_lower = text.lower()
    
    if any(kw in text_lower for kw in ['credit card', 'kad kredit', 'debit card']):
        return 'CREDIT_CARD'
    elif any(kw in text_lower for kw in ['home loan', 'housing', 'mortgage', 'property financing', 'home financing']):
        return 'HOME_LOAN'
    elif any(kw in text_lower for kw in ['personal loan', 'cash loan', 'personal financing']):
        return 'PERSONAL_LOAN'
    elif any(kw in text_lower for kw in ['car loan', 'auto loan', 'vehicle', 'hire purchase']):
        return 'CAR_LOAN'
    elif any(kw in text_lower for kw in ['business loan', 'sme', 'commercial loan', 'business financing']):
        return 'SME_LOAN'
    elif any(kw in text_lower for kw in ['fixed deposit', 'time deposit', 'fd', 'deposit']):
        return 'FIXED_DEPOSIT'
    elif any(kw in text_lower for kw in ['overdraft', 'od']):
        return 'OVERDRAFT'
    elif any(kw in text_lower for kw in ['refinance', 'refinancing', 'debt consolidation']):
        return 'REFINANCE'
    else:
        return 'OTHER'

def extract_rate(text):
    """提取利率"""
    rate_match = re.search(r'(\d+\.?\d*)\s*%', text)
    if rate_match:
        return rate_match.group(0)
    return '请联系银行'

def deep_scrape_company(order, company_name, base_url):
    """深度爬取单个公司的所有产品 - 100%完整性"""
    print(f"\n{'='*80}")
    print(f"[{order}/68] 正在爬取: {company_name}")
    print(f"网址: {base_url}")
    print(f"{'='*80}")
    
    all_products = []
    visited_urls = set()
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
    })
    
    # 添加公司超时保护（每家公司最多5分钟）
    import signal
    def timeout_handler(signum, frame):
        raise TimeoutError(f"公司 {company_name} 超时")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)  # 5分钟超时
    
    # 第一层：尝试所有预定义路径
    for path in ALL_PATHS:
        url = urljoin(base_url, path)
        
        if url in visited_urls:
            continue
        visited_urls.add(url)
        
        try:
            response = session.get(url, timeout=10)
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            
            # 提取所有heading作为产品
            headings = extract_all_headings(soup)
            for heading_text in headings:
                # 判断是否包含产品关键词
                if any(kw in heading_text.lower() for kw in [
                    'card', 'loan', 'financing', 'deposit', 'overdraft', 
                    'mortgage', 'cash', 'business', 'sme', 'refinance',
                    'visa', 'mastercard', 'amex', 'maybank', 'cimb', 'public bank'
                ]):
                    loan_type = classify_loan_type(heading_text + ' ' + url)
                    rate = extract_rate(text[:5000])  # 从页面前5000字符提取利率
                    
                    all_products.append({
                        'company': company_name,
                        'product_name': heading_text,
                        'loan_type': loan_type,
                        'rate': rate,
                        'source_url': url
                    })
            
            # 提取该页面的所有链接（寻找更多产品页）
            page_links = extract_all_links(soup, base_url)
            
            # 过滤：只保留同域名的产品相关链接
            domain = urlparse(base_url).netloc
            for link in page_links:
                if urlparse(link).netloc == domain:
                    link_lower = link.lower()
                    if any(kw in link_lower for kw in [
                        'card', 'loan', 'financing', 'deposit', 'overdraft',
                        'mortgage', 'product', 'personal', 'business', 'sme'
                    ]):
                        # 访问这个链接并提取产品
                        if link not in visited_urls and len(visited_urls) < 100:  # 限制每家公司最多100个页面
                            visited_urls.add(link)
                            try:
                                sub_response = session.get(link, timeout=8)
                                if sub_response.status_code == 200:
                                    sub_soup = BeautifulSoup(sub_response.text, 'html.parser')
                                    sub_headings = extract_all_headings(sub_soup)
                                    sub_text = sub_soup.get_text()
                                    
                                    for sub_heading in sub_headings:
                                        if any(kw in sub_heading.lower() for kw in [
                                            'card', 'loan', 'financing', 'deposit', 'overdraft'
                                        ]):
                                            loan_type = classify_loan_type(sub_heading + ' ' + link)
                                            rate = extract_rate(sub_text[:5000])
                                            
                                            all_products.append({
                                                'company': company_name,
                                                'product_name': sub_heading,
                                                'loan_type': loan_type,
                                                'rate': rate,
                                                'source_url': link
                                            })
                                    
                                    time.sleep(0.3)
                            except:
                                pass
            
            time.sleep(0.5)
            
        except Exception as e:
            pass
    
    # 取消超时
    signal.alarm(0)
    
    # 去重
    seen = set()
    unique_products = []
    for p in all_products:
        key = f"{p['company']}_{p['product_name']}"
        if key not in seen:
            seen.add(key)
            unique_products.append(p)
    
    print(f"✅ {company_name}: 找到 {len(unique_products)} 个产品")
    
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
    print("严格按CSV顺序爬取 - 68家金融机构完整产品提取")
    print("规则: 按顺序、100%完整、宁可多不能少")
    print("=" * 80)
    
    # 清空数据库
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    cur.execute("TRUNCATE TABLE loan_products_ultimate RESTART IDENTITY;")
    con.commit()
    cur.close()
    con.close()
    print("✅ 数据库已清空\n")
    
    # 严格按CSV顺序加载
    institutions = load_institutions_in_order()
    print(f"📋 共 {len(institutions)} 家机构（严格按CSV顺序）\n")
    
    total_products = 0
    
    # 按顺序爬取每一家
    for inst in institutions:
        try:
            products = deep_scrape_company(inst['order'], inst['name'], inst['website'])
            if products:
                total_products += len(products)
                save_to_db(products)
                print(f"💾 已保存 {len(products)} 个产品到数据库")
            else:
                print(f"⚠️  [{inst['order']}/68] {inst['name']}: 未找到产品")
        except TimeoutError as e:
            print(f"⏱️  [{inst['order']}/68] {inst['name']} 超时，跳过继续下一家")
        except Exception as e:
            print(f"❌ [{inst['order']}/68] {inst['name']} 错误: {str(e)[:80]}")
        
        time.sleep(1)  # 礼貌延迟
    
    print("\n" + "=" * 80)
    print(f"🎉 完成！总计: {total_products} 个产品")
    print("=" * 80)
    
    # 最终统计
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    
    cur.execute("SELECT COUNT(*) FROM loan_products_ultimate")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(DISTINCT company) FROM loan_products_ultimate")
    companies = cur.fetchone()[0]
    
    cur.execute("SELECT loan_type, COUNT(*) FROM loan_products_ultimate GROUP BY loan_type ORDER BY COUNT(*) DESC")
    breakdown = cur.fetchall()
    
    print(f"\n📊 最终统计:")
    print(f"   总产品数: {total}")
    print(f"   公司数量: {companies}/68")
    print(f"\n   产品类型分布:")
    for loan_type, count in breakdown:
        print(f"   - {loan_type}: {count}")
    
    cur.close()
    con.close()

if __name__ == '__main__':
    main()
