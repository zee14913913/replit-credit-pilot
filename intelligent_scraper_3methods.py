#!/usr/bin/env python
"""
智能爬虫 - 结合3种方法100%提取完整产品详情
方法1: Footer导航 → Personal/Business/SME/Corporate → 产品类别 → Learn More/Apply
方法2: Search功能 → 搜索关键词 → 产品类别 → Learn More/Apply
方法3: URL拼接 → 直接访问 → 产品类别 → Learn More/Apply
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

# 业务分类
BUSINESS_CATEGORIES = ['personal', 'business', 'sme', 'corporate']

# 产品类型路径
PRODUCT_PATHS = {
    'credit_card': ['credit-card', 'cards', 'credit-cards', 'card'],
    'loan': ['loan', 'loans', 'lending', 'borrowing'],
    'financing': ['financing', 'finance'],
    'mortgage': ['mortgage', 'home-loan', 'housing-loan', 'property-loan', 'home-financing'],
    'fixed_deposit': ['fixed-deposit', 'fd', 'deposit', 'deposits', 'time-deposit'],
    'overdraft': ['overdraft', 'od'],
    'banking': ['banking', 'products']
}

def load_institutions_in_order():
    """加载所有机构（严格CSV顺序）"""
    institutions = []
    with open(CSV_INPUT, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for idx, row in enumerate(reader, 1):
            if len(row) >= 2:
                institutions.append({
                    'order': idx,
                    'name': row[0].strip(),
                    'website': row[1].strip()
                })
    return institutions

def get_completed_companies():
    """获取已完成的公司列表"""
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    cur.execute("SELECT DISTINCT company FROM loan_products_ultimate")
    completed = set(row[0] for row in cur.fetchall())
    cur.close()
    con.close()
    return completed

def classify_loan_type(text):
    """智能分类产品类型"""
    text_lower = text.lower()
    
    if any(kw in text_lower for kw in ['credit card', 'debit card', 'kad kredit', 'visa', 'mastercard', 'amex']):
        return 'CREDIT_CARD'
    elif any(kw in text_lower for kw in ['home loan', 'housing', 'mortgage', 'property']):
        return 'HOME_LOAN'
    elif any(kw in text_lower for kw in ['personal loan', 'cash loan', 'personal financing']):
        return 'PERSONAL_LOAN'
    elif any(kw in text_lower for kw in ['car loan', 'auto', 'vehicle', 'hire purchase']):
        return 'CAR_LOAN'
    elif any(kw in text_lower for kw in ['business', 'sme', 'commercial']):
        return 'SME_LOAN'
    elif any(kw in text_lower for kw in ['fixed deposit', 'fd', 'time deposit']):
        return 'FIXED_DEPOSIT'
    elif any(kw in text_lower for kw in ['overdraft', 'od']):
        return 'OVERDRAFT'
    elif any(kw in text_lower for kw in ['refinanc', 'debt consolidation']):
        return 'REFINANCE'
    else:
        return 'OTHER'

def extract_detailed_fields(soup, url):
    """提取详细的12字段信息"""
    text = soup.get_text()
    
    # 提取利率
    rate = '请联系银行'
    rate_patterns = [
        r'(\d+\.?\d*)\s*%\s*p\.?a\.?',
        r'rate[:\s]+(\d+\.?\d*)\s*%',
        r'interest[:\s]+(\d+\.?\d*)\s*%',
        r'(\d+\.?\d*)\s*%'
    ]
    for pattern in rate_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            rate = match.group(0)
            break
    
    # 提取期限
    tenure = '请联系银行'
    tenure_patterns = [
        r'(\d+)\s*(?:year|tahun|month|bulan)',
        r'tenure[:\s]+(\d+)',
        r'term[:\s]+(\d+)'
    ]
    for pattern in tenure_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            tenure = match.group(0)
            break
    
    # 提取特点（Features）
    features = '请访问银行官网'
    features_section = soup.find(['div', 'section'], text=re.compile(r'feature|benefit|highlight', re.I))
    if features_section:
        features_list = features_section.find_all(['li', 'p'])
        if features_list:
            features = ' | '.join([li.get_text(strip=True)[:100] for li in features_list[:3]])
    
    # 提取费用
    fees = '请联系银行'
    if re.search(r'annual fee|fee|charge', text, re.I):
        fee_match = re.search(r'RM\s*\d+', text)
        if fee_match:
            fees = fee_match.group(0)
    
    # 查找申请表链接
    application_url = ''
    apply_link = soup.find('a', text=re.compile(r'apply|application', re.I))
    if apply_link and apply_link.get('href'):
        application_url = urljoin(url, apply_link.get('href'))
    
    # 查找产品披露链接
    disclosure_url = ''
    disclosure_link = soup.find('a', text=re.compile(r'disclosure|product.*sheet|brochure', re.I))
    if disclosure_link and disclosure_link.get('href'):
        disclosure_url = urljoin(url, disclosure_link.get('href'))
    
    # 查找条款链接
    terms_url = ''
    terms_link = soup.find('a', text=re.compile(r'term|condition|t&c|tnc', re.I))
    if terms_link and terms_link.get('href'):
        terms_url = urljoin(url, terms_link.get('href'))
    
    return {
        'rate': rate,
        'tenure': tenure,
        'features': features,
        'fees_charges': fees,
        'application_form_url': application_url,
        'product_disclosure_url': disclosure_url,
        'terms_conditions_url': terms_url
    }

def method1_footer_navigation(session, base_url):
    """方法1: 从Footer导航查找产品"""
    print("   📍 方法1: Footer导航")
    products = []
    
    try:
        response = session.get(base_url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找Footer
        footer = soup.find(['footer', 'div'], class_=lambda x: x and 'footer' in str(x).lower())
        if not footer:
            footer = soup.find_all(['footer', 'div'])[-1] if soup.find_all(['footer', 'div']) else soup
        
        # 在Footer中查找业务分类链接
        for category in BUSINESS_CATEGORIES:
            links = footer.find_all('a', text=re.compile(category, re.I))
            for link in links[:2]:  # 每个分类最多2个链接
                if link.get('href'):
                    category_url = urljoin(base_url, link.get('href'))
                    print(f"      → {category.upper()}: {category_url}")
                    
                    # 访问分类页面
                    try:
                        cat_response = session.get(category_url, timeout=10)
                        cat_soup = BeautifulSoup(cat_response.text, 'html.parser')
                        
                        # 查找产品类型链接
                        for product_type, keywords in PRODUCT_PATHS.items():
                            for keyword in keywords:
                                product_links = cat_soup.find_all('a', href=re.compile(keyword, re.I))
                                for prod_link in product_links[:5]:  # 每种产品类型最多5个
                                    if prod_link.get('href'):
                                        product_url = urljoin(category_url, prod_link.get('href'))
                                        products.append(product_url)
                        
                        time.sleep(0.3)
                    except:
                        pass
    except:
        pass
    
    return list(set(products))

def method2_search_function(session, base_url):
    """方法2: 使用Search功能"""
    print("   🔍 方法2: Search功能")
    products = []
    
    try:
        response = session.get(base_url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找搜索框
        search_input = soup.find(['input'], {'type': 'search'}) or soup.find(['input'], {'name': re.compile('search', re.I)})
        
        # 查找搜索链接
        search_links = soup.find_all('a', text=re.compile(r'search', re.I)) + soup.find_all('a', href=re.compile(r'search', re.I))
        
        for search_link in search_links[:1]:
            if search_link.get('href'):
                search_url = urljoin(base_url, search_link.get('href'))
                print(f"      → Search URL: {search_url}")
                products.append(search_url)
    except:
        pass
    
    return products

def method3_url_append(base_url):
    """方法3: URL直接拼接"""
    print("   🔗 方法3: URL拼接")
    products = []
    
    # 组合: /category/product
    for category in BUSINESS_CATEGORIES:
        for product_type, keywords in PRODUCT_PATHS.items():
            for keyword in keywords[:2]:  # 每种产品最多2个关键词
                # /personal/credit-cards
                url1 = urljoin(base_url, f"/{category}/{keyword}")
                products.append(url1)
                
                # /personal/cards
                url2 = urljoin(base_url, f"/{category}/{keyword}s" if not keyword.endswith('s') else keyword)
                products.append(url2)
    
    return list(set(products))

def extract_product_from_detail_page(session, url, company_name):
    """从产品详情页提取完整信息"""
    try:
        response = session.get(url, timeout=10)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        
        # 查找产品名称
        product_name = None
        for tag in ['h1', 'h2', 'h3']:
            heading = soup.find(tag)
            if heading:
                product_name = heading.get_text(strip=True)
                if len(product_name) > 3 and len(product_name) < 150:
                    break
        
        if not product_name:
            return None
        
        # 判断是否为产品页（必须包含产品关键词）
        if not any(kw in text.lower() for kw in ['card', 'loan', 'financing', 'deposit', 'overdraft']):
            return None
        
        # 提取详细字段
        details = extract_detailed_fields(soup, url)
        loan_type = classify_loan_type(product_name + ' ' + url)
        
        return {
            'company': company_name,
            'product_name': product_name,
            'loan_type': loan_type,
            'rate': details['rate'],
            'tenure': details['tenure'],
            'features': details['features'],
            'fees_charges': details['fees_charges'],
            'application_form_url': details['application_form_url'],
            'product_disclosure_url': details['product_disclosure_url'],
            'terms_conditions_url': details['terms_conditions_url'],
            'required_doc': '请访问银行官网',
            'benefits': '请访问银行官网',
            'preferred_customer_type': '所有客户',
            'source_url': url
        }
    except:
        return None

def scrape_company_with_3methods(order, company_name, base_url):
    """使用3种方法综合爬取单个公司"""
    print(f"\n{'='*80}")
    print(f"[{order}/68] 🏦 {company_name}")
    print(f"{'='*80}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
    })
    
    all_product_urls = []
    
    # 方法1: Footer导航
    try:
        urls1 = method1_footer_navigation(session, base_url)
        all_product_urls.extend(urls1)
        print(f"      方法1找到: {len(urls1)} 个链接")
    except Exception as e:
        print(f"      方法1失败: {str(e)[:50]}")
    
    # 方法2: Search功能
    try:
        urls2 = method2_search_function(session, base_url)
        all_product_urls.extend(urls2)
        print(f"      方法2找到: {len(urls2)} 个链接")
    except Exception as e:
        print(f"      方法2失败: {str(e)[:50]}")
    
    # 方法3: URL拼接
    try:
        urls3 = method3_url_append(base_url)
        all_product_urls.extend(urls3)
        print(f"      方法3找到: {len(urls3)} 个链接")
    except Exception as e:
        print(f"      方法3失败: {str(e)[:50]}")
    
    # 去重
    all_product_urls = list(set(all_product_urls))
    print(f"   📦 总链接数: {len(all_product_urls)}")
    
    # 访问每个链接并提取产品详情
    products = []
    for idx, url in enumerate(all_product_urls[:100], 1):  # 限制每家公司100个链接
        product = extract_product_from_detail_page(session, url, company_name)
        if product:
            products.append(product)
            if idx % 10 == 0:
                print(f"      已处理: {idx}/{min(len(all_product_urls), 100)}, 找到: {len(products)} 个产品")
        time.sleep(0.2)
    
    # 去重
    seen = set()
    unique_products = []
    for p in products:
        key = f"{p['company']}_{p['product_name']}"
        if key not in seen:
            seen.add(key)
            unique_products.append(p)
    
    print(f"   ✅ 最终产品数: {len(unique_products)}")
    return unique_products

def save_to_db(products):
    """保存到数据库"""
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
            tenure = EXCLUDED.tenure,
            features = EXCLUDED.features,
            fees_charges = EXCLUDED.fees_charges,
            application_form_url = EXCLUDED.application_form_url,
            product_disclosure_url = EXCLUDED.product_disclosure_url,
            terms_conditions_url = EXCLUDED.terms_conditions_url,
            source_url = EXCLUDED.source_url,
            scraped_at = EXCLUDED.scraped_at
    """
    
    items = [(
        p['company'], p['loan_type'], p['product_name'], p['required_doc'],
        p['features'], p['benefits'], p['fees_charges'], p['tenure'], p['rate'],
        p['application_form_url'], p['product_disclosure_url'], p['terms_conditions_url'],
        p['preferred_customer_type'], p['source_url'], datetime.now()
    ) for p in products]
    
    execute_values(cur, sql, items)
    con.commit()
    cur.close()
    con.close()

def main():
    print("=" * 80)
    print("智能爬虫 - 3种方法综合策略")
    print("从第9家公司继续 - 保留已有750个产品")
    print("=" * 80)
    
    # 获取已完成的公司
    completed = get_completed_companies()
    print(f"\n✅ 已完成: {len(completed)} 家公司")
    for c in sorted(completed):
        print(f"   - {c}")
    
    # 加载所有机构
    institutions = load_institutions_in_order()
    print(f"\n📋 总机构数: {len(institutions)}")
    
    # 过滤出未完成的
    remaining = [inst for inst in institutions if inst['name'] not in completed]
    print(f"📌 剩余: {len(remaining)} 家机构\n")
    
    total_new_products = 0
    
    # 按顺序爬取剩余的
    for inst in remaining:
        try:
            products = scrape_company_with_3methods(inst['order'], inst['name'], inst['website'])
            if products:
                total_new_products += len(products)
                save_to_db(products)
                print(f"   💾 已保存 {len(products)} 个新产品")
            else:
                print(f"   ⚠️  未找到产品")
        except Exception as e:
            print(f"   ❌ 错误: {str(e)[:80]}")
        
        time.sleep(2)
    
    print("\n" + "=" * 80)
    print(f"🎉 完成！新增: {total_new_products} 个产品")
    print("=" * 80)
    
    # 最终统计
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    
    cur.execute("SELECT COUNT(*) FROM loan_products_ultimate")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(DISTINCT company) FROM loan_products_ultimate")
    companies = cur.fetchone()[0]
    
    print(f"\n📊 数据库总统计:")
    print(f"   总产品数: {total}")
    print(f"   公司数量: {companies}/68")
    
    cur.close()
    con.close()

if __name__ == '__main__':
    main()
