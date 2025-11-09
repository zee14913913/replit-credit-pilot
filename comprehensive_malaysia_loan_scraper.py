"""
马来西亚68家金融机构全面贷款产品爬虫
按CSV文件顺序爬取所有贷款产品（信用卡、房贷、个人贷款、refinance、债务整合、车贷、企业贷款、SME贷款等）
生成12列精致表格
"""
import sys
sys.path.insert(0, '/home/runner/workspace')

import csv
import logging
import sqlite3
import time
import requests
from typing import List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = "/home/runner/loans_comprehensive.db"
CSV_INPUT = "/home/runner/workspace/attached_assets/New 马来西亚贷款机构与平台全官网_完整版.csv_1762664297188.csv"
CSV_OUTPUT = "/home/runner/malaysia_loans_complete_table.csv"


class ComprehensiveLoanScraper:
    """全面贷款产品爬虫"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ms;q=0.8,zh;q=0.7',
        })
        
        # 所有贷款产品类型关键词
        self.loan_keywords = {
            'credit_card': ['credit card', 'credit-card', 'kad kredit', 'visa', 'mastercard', 'amex'],
            'home_loan': ['home loan', 'housing loan', 'mortgage', 'property loan', 'rumah', 'housing finance'],
            'refinance': ['refinance', 'refinancing', 'loan refinance'],
            'personal_loan': ['personal loan', 'cash loan', 'personal financing', 'pinjaman peribadi'],
            'debt_consolidation': ['debt consolidation', 'consolidation loan', 'debt management'],
            'car_loan': ['car loan', 'auto loan', 'vehicle loan', 'hire purchase', 'kereta'],
            'business_loan': ['business loan', 'business financing', 'commercial loan'],
            'sme_loan': ['sme loan', 'sme financing', 'small business', 'enterprise loan'],
            'other': ['loan', 'financing', 'pinjaman', 'pembiayaan', 'credit']
        }
    
    def classify_loan_type(self, text: str) -> str:
        """智能分类贷款类型"""
        text_lower = text.lower()
        
        # 按优先级检查
        if any(kw in text_lower for kw in self.loan_keywords['credit_card']):
            return 'CREDIT_CARD'
        elif any(kw in text_lower for kw in self.loan_keywords['home_loan']):
            return 'HOME_LOAN'
        elif any(kw in text_lower for kw in self.loan_keywords['refinance']):
            return 'REFINANCE'
        elif any(kw in text_lower for kw in self.loan_keywords['debt_consolidation']):
            return 'DEBT_CONSOLIDATION'
        elif any(kw in text_lower for kw in self.loan_keywords['car_loan']):
            return 'CAR_LOAN'
        elif any(kw in text_lower for kw in self.loan_keywords['sme_loan']):
            return 'SME_LOAN'
        elif any(kw in text_lower for kw in self.loan_keywords['business_loan']):
            return 'BUSINESS_LOAN'
        elif any(kw in text_lower for kw in self.loan_keywords['personal_loan']):
            return 'PERSONAL_LOAN'
        else:
            return 'OTHER'
    
    def find_all_loan_pages(self, base_url: str, company_name: str) -> List[str]:
        """
        查找所有贷款相关页面
        包括信用卡、房贷、个人贷款等所有类型
        """
        logger.info(f"  🔍 探索 {company_name} 的所有贷款页面...")
        
        loan_pages = set()
        
        try:
            # 访问首页
            response = self.session.get(base_url, timeout=20, allow_redirects=True)
            
            if response.status_code != 200:
                logger.warning(f"    首页返回 {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有链接
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                
                # 检查是否包含贷款关键词
                is_loan_link = False
                for category, keywords in self.loan_keywords.items():
                    if any(kw in text or kw in href.lower() for kw in keywords):
                        is_loan_link = True
                        break
                
                if is_loan_link:
                    full_url = urljoin(base_url, href)
                    if self._is_valid_url(full_url, base_url):
                        loan_pages.add(full_url)
            
            # 如果没找到，尝试常见路径
            if not loan_pages:
                loan_pages = self._try_common_loan_paths(base_url)
            
            logger.info(f"    找到 {len(loan_pages)} 个贷款页面")
            return list(loan_pages)
            
        except Exception as e:
            logger.error(f"    ❌ 探索失败: {e}")
            return []
    
    def _is_valid_url(self, url: str, base_url: str) -> bool:
        """验证URL"""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_url)
            
            if parsed_url.netloc != parsed_base.netloc:
                return False
            
            invalid = ['login', 'logout', 'signin', 'register', 'mailto:', 'tel:', 'javascript:', '#']
            if any(inv in url.lower() for inv in invalid):
                return False
            
            return True
        except:
            return False
    
    def _try_common_loan_paths(self, base_url: str) -> set:
        """尝试常见路径"""
        common_paths = [
            '/personal/loans', '/personal/financing', '/loans', '/financing',
            '/personal/credit-cards', '/cards', '/credit-cards',
            '/home-loans', '/mortgage', '/personal-loans',
            '/business-loans', '/sme', '/business/financing',
            '/products/loans', '/en/loans', '/en/personal/loans'
        ]
        
        valid_urls = set()
        for path in common_paths:
            url = urljoin(base_url, path)
            try:
                response = self.session.head(url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    valid_urls.add(url)
            except:
                pass
        
        return valid_urls
    
    def extract_products_from_page(self, url: str, company_name: str) -> List[Dict[str, Any]]:
        """从页面提取产品（12个字段）"""
        products = []
        
        try:
            response = self.session.get(url, timeout=20)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            
            # 判断贷款类型
            loan_type = self.classify_loan_type(url + ' ' + text)
            
            # 提取产品名称
            product_name = None
            for tag in ['h1', 'h2', 'title']:
                heading = soup.find(tag)
                if heading:
                    product_name = heading.get_text(strip=True)
                    if len(product_name) > 5:
                        break
            
            if not product_name:
                return []
            
            # 提取利率
            rate = self._extract_rate(text)
            
            # 提取期限
            tenure = self._extract_tenure(text)
            
            # 提取特点（从列表项）
            features = []
            feature_sections = soup.find_all(['ul', 'ol'])
            for section in feature_sections[:3]:
                items = section.find_all('li')
                for item in items[:5]:
                    item_text = item.get_text(strip=True)
                    if 10 < len(item_text) < 150:
                        features.append(item_text)
            
            # 查找PDF链接
            app_form = self._find_pdf(soup, ['application', 'apply', 'form'])
            disclosure = self._find_pdf(soup, ['disclosure', 'pds', 'product disclosure'])
            terms = self._find_pdf(soup, ['terms', 'conditions', 'tnc', 't&c'])
            
            # 判断客户偏好
            customer_pref = self._determine_customer_type(text, product_name)
            
            product = {
                'company': company_name,
                'loan_type': loan_type,
                'product_name': product_name,
                'required_doc': '请联系银行了解所需文件',
                'features': ' | '.join(features[:5]) if features else '请访问银行官网了解产品特点',
                'benefits': '请访问银行官网了解产品优势',
                'fees_charges': '请联系银行了解费用详情',
                'tenure': tenure,
                'rate': rate,
                'application_form_url': app_form or '',
                'product_disclosure_url': disclosure or '',
                'terms_conditions_url': terms or '',
                'preferred_customer_type': customer_pref,
                'source_url': url,
                'scraped_at': datetime.now().isoformat()
            }
            
            products.append(product)
            
        except Exception as e:
            logger.error(f"    ❌ 页面提取失败 {url}: {e}")
        
        return products
    
    def _extract_rate(self, text: str) -> str:
        """提取利率"""
        patterns = [
            r'(\d+\.?\d*)\s*%\s*(p\.a\.|per\s+annum)?',
            r'(BR|BLR|SBR)\s*[\+\-]\s*(\d+\.?\d*)\s*%?',
            r'from\s+(\d+\.?\d*)\s*%',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return '请联系银行'
    
    def _extract_tenure(self, text: str) -> str:
        """提取期限"""
        patterns = [
            r'up\s+to\s+(\d+)\s*(years?|months?)',
            r'(\d+)\s*(years?|tahun)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return '请联系银行'
    
    def _find_pdf(self, soup: BeautifulSoup, keywords: List[str]) -> str:
        """查找PDF链接"""
        links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
        
        for link in links:
            text = link.get_text().lower()
            href = link.get('href', '').lower()
            if any(kw in text or kw in href for kw in keywords):
                return link.get('href')
        
        return ''
    
    def _determine_customer_type(self, text: str, product_name: str) -> str:
        """判断客户类型"""
        combined = (text + ' ' + product_name).lower()
        
        business_score = sum(1 for kw in ['business', 'sme', 'enterprise', 'self-employed'] if kw in combined)
        salaried_score = sum(1 for kw in ['salaried', 'employee', 'payslip'] if kw in combined)
        
        if business_score > salaried_score:
            return '企业客户 (Business/Self-Employed)'
        elif salaried_score > 0:
            return '打工族 (Salaried)'
        else:
            return '所有客户 (All)'
    
    def scrape_institution(self, company_name: str, website: str) -> List[Dict[str, Any]]:
        """爬取单个机构的所有贷款产品"""
        logger.info(f"🏦 开始爬取: {company_name}")
        
        all_products = []
        
        # 查找所有贷款页面
        loan_pages = self.find_all_loan_pages(website, company_name)
        
        if not loan_pages:
            logger.warning(f"  ⚠️ {company_name}: 未找到贷款页面")
            return []
        
        # 提取每个页面的产品
        for page_url in loan_pages[:10]:  # 限制最多10个页面
            logger.info(f"    📄 访问: {page_url}")
            products = self.extract_products_from_page(page_url, company_name)
            
            if products:
                logger.info(f"      ✅ 找到 {len(products)} 个产品")
                all_products.extend(products)
            
            time.sleep(0.5)  # 礼貌延迟
        
        logger.info(f"  ✅ {company_name}: 共 {len(all_products)} 个产品")
        return all_products


def init_database():
    """初始化数据库"""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS loan_products_complete(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            loan_type TEXT,
            product_name TEXT,
            required_doc TEXT,
            features TEXT,
            benefits TEXT,
            fees_charges TEXT,
            tenure TEXT,
            rate TEXT,
            application_form_url TEXT,
            product_disclosure_url TEXT,
            terms_conditions_url TEXT,
            preferred_customer_type TEXT,
            source_url TEXT,
            scraped_at TEXT
        )
    """)
    
    con.commit()
    con.close()
    logger.info("✅ 数据库初始化完成")


def load_institutions_from_csv(csv_path: str) -> List[Dict[str, str]]:
    """从CSV加载机构列表"""
    institutions = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # 跳过标题行
        
        for row in reader:
            if len(row) >= 2:
                institutions.append({
                    'name': row[0],
                    'website': row[1]
                })
    
    logger.info(f"📋 加载了 {len(institutions)} 家金融机构")
    return institutions


def save_to_database(products: List[Dict[str, Any]]):
    """保存到数据库"""
    if not products:
        return
    
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    insert_sql = """
        INSERT INTO loan_products_complete(
            company, loan_type, product_name, required_doc, features, benefits,
            fees_charges, tenure, rate, application_form_url, product_disclosure_url,
            terms_conditions_url, preferred_customer_type, source_url, scraped_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    items = [
        (
            p['company'], p['loan_type'], p['product_name'], p['required_doc'],
            p['features'], p['benefits'], p['fees_charges'], p['tenure'],
            p['rate'], p.get('application_form_url', ''), p.get('product_disclosure_url', ''),
            p.get('terms_conditions_url', ''), p['preferred_customer_type'],
            p.get('source_url', ''), p.get('scraped_at', '')
        )
        for p in products
    ]
    
    cur.executemany(insert_sql, items)
    con.commit()
    con.close()


def export_to_csv_table(output_path: str):
    """导出为精致表格（12列）"""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    cur.execute("""
        SELECT 
            company AS 'COMPANY',
            loan_type AS 'LOAN TYPE',
            required_doc AS 'REQUIRED DOC',
            features AS 'FEATURES',
            benefits AS 'BENEFITS',
            fees_charges AS 'FEES & CHARGES',
            tenure AS 'TENURE',
            rate AS 'RATE',
            application_form_url AS 'APPLICATION FORM',
            product_disclosure_url AS 'PRODUCT DISCLOSURE',
            terms_conditions_url AS 'TERMS & CONDITIONS',
            preferred_customer_type AS '客户偏好'
        FROM loan_products_complete
        ORDER BY company, loan_type
    """)
    
    rows = cur.fetchall()
    con.close()
    
    # 写入CSV
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))
    
    logger.info(f"📤 表格已导出: {output_path}")
    logger.info(f"   总计: {len(rows)} 个产品")


def main():
    """主流程"""
    logger.info("")
    logger.info("=" * 100)
    logger.info("🚀 马来西亚68家金融机构全面贷款产品爬虫")
    logger.info("=" * 100)
    logger.info("")
    
    start_time = datetime.now()
    
    # 初始化
    init_database()
    
    # 加载机构列表
    institutions = load_institutions_from_csv(CSV_INPUT)
    
    # 创建爬虫
    scraper = ComprehensiveLoanScraper()
    
    # 逐个爬取（按CSV顺序）
    all_products = []
    
    for idx, inst in enumerate(institutions, 1):
        logger.info(f"\n进度: {idx}/{len(institutions)}")
        logger.info("-" * 100)
        
        try:
            products = scraper.scrape_institution(inst['name'], inst['website'])
            if products:
                all_products.extend(products)
                # 即时保存
                save_to_database(products)
        except Exception as e:
            logger.error(f"❌ {inst['name']} 爬取失败: {e}")
        
        time.sleep(1)  # 机构间延迟
    
    # 导出表格
    logger.info("")
    logger.info("=" * 100)
    logger.info("📊 导出精致表格（12列）")
    logger.info("=" * 100)
    export_to_csv_table(CSV_OUTPUT)
    
    # 统计
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("")
    logger.info("=" * 100)
    logger.info("🎉 爬取完成！")
    logger.info("=" * 100)
    logger.info(f"总耗时: {duration:.1f} 秒 ({duration/60:.1f} 分钟)")
    logger.info(f"处理机构: {len(institutions)} 家")
    logger.info(f"产品总数: {len(all_products)}")
    logger.info(f"数据库: {DB_PATH}")
    logger.info(f"表格文件: {CSV_OUTPUT}")
    logger.info("")


if __name__ == '__main__':
    main()
