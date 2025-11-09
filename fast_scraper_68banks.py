"""
快速爬虫 - 68家金融机构全面产品提取
策略：直接访问主要产品页面，提取所有信息
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

DATABASE_URL = os.getenv('DATABASE_URL')
CSV_INPUT = "/home/runner/workspace/attached_assets/New 马来西亚贷款机构与平台全官网_完整版.csv_1762667764316.csv"

# 主要产品路径（针对每家银行尝试）
PRODUCT_PATHS = [
    # 信用卡
    '/personal/cards', '/personal/Cards/Credit-Cards', '/credit-cards', '/cards', '/en/cards',
    # 个人贷款
    '/personal/loans', '/personal-loans', '/personal/financing', '/cash-loan',
    # 房贷
    '/personal/home-loans', '/home-loans', '/housing-loan', '/mortgage',
    # 车贷
    '/personal/car-loan', '/auto-loan', '/hire-purchase', '/vehicle-financing',
    # 企业贷款
    '/business/loans', '/business/financing', '/sme', '/sme-loans',
    # OD & FD
    '/personal/overdraft', '/overdraft', '/od',
    '/personal/fixed-deposit', '/fixed-deposit', '/fd', '/deposits',
]

def load_institutions():
    """加载68家机构"""
    institutions = []
    with open(CSV_INPUT, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) >= 2:
                institutions.append({'name': row[0], 'website': row[1]})
    return institutions

def quick_scrape(company_name, base_url):
    """快速爬取单个机构的所有产品"""
    print(f"\n🏦 {company_name}")
    print(f"   {base_url}")
    
    products = []
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
    })
    
    # 尝试所有产品路径
    for path in PRODUCT_PATHS:
        url = urljoin(base_url, path)
        try:
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()
                
                # 简单提取：所有包含产品关键词的标题
                for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5']):
                    heading_text = heading.get_text(strip=True)
                    if len(heading_text) > 5 and len(heading_text) < 150:
                        # 判断是否包含产品关键词
                        if any(kw in heading_text.lower() for kw in ['card', 'loan', 'financing', 'deposit', 'overdraft']):
                            # 提取利率
                            rate = '请联系银行'
                            parent = heading.find_parent(['div', 'section', 'article'])
                            if parent:
                                parent_text = parent.get_text()
                                import re
                                rate_match = re.search(r'(\d+\.?\d*)\s*%', parent_text)
                                if rate_match:
                                    rate = rate_match.group(0)
                            
                            # 分类
                            loan_type = 'OTHER'
                            ht_lower = heading_text.lower()
                            if 'credit card' in ht_lower or 'kad kredit' in ht_lower:
                                loan_type = 'CREDIT_CARD'
                            elif 'home' in ht_lower or 'housing' in ht_lower or 'mortgage' in ht_lower:
                                loan_type = 'HOME_LOAN'
                            elif 'personal' in ht_lower or 'cash' in ht_lower:
                                loan_type = 'PERSONAL_LOAN'
                            elif 'car' in ht_lower or 'auto' in ht_lower or 'vehicle' in ht_lower:
                                loan_type = 'CAR_LOAN'
                            elif 'business' in ht_lower or 'sme' in ht_lower:
                                loan_type = 'SME_LOAN'
                            elif 'deposit' in ht_lower or 'fd' in ht_lower:
                                loan_type = 'FIXED_DEPOSIT'
                            elif 'overdraft' in ht_lower or 'od' in ht_lower:
                                loan_type = 'OVERDRAFT'
                            
                            products.append({
                                'company': company_name,
                                'loan_type': loan_type,
                                'product_name': heading_text,
                                'rate': rate,
                                'source_url': url
                            })
                
                print(f"   ✅ {path} → {len(products)} products")
                time.sleep(0.3)
        except:
            pass
    
    # 去重
    seen = set()
    unique_products = []
    for p in products:
        key = f"{p['company']}_{p['product_name']}"
        if key not in seen:
            seen.add(key)
            unique_products.append(p)
    
    print(f"   📦 总计: {len(unique_products)} 个产品")
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
    print(f"   💾 已保存到数据库")

def main():
    print("=" * 80)
    print("🚀 快速爬虫 - 68家金融机构全面产品提取")
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
    
    all_products = []
    for idx, inst in enumerate(institutions, 1):
        print(f"\n[{idx}/{len(institutions)}]", end=" ")
        try:
            products = quick_scrape(inst['name'], inst['website'])
            if products:
                all_products.extend(products)
                save_to_db(products)
        except Exception as e:
            print(f"   ❌ 错误: {e}")
        
        time.sleep(1)
    
    print("\n" + "=" * 80)
    print(f"🎉 完成！总计: {len(all_products)} 个产品")
    print("=" * 80)

if __name__ == '__main__':
    main()
