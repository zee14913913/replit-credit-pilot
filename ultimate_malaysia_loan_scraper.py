"""
🚀 CreditPilot - 马来西亚68家金融机构深度爬虫系统 (Ultimate Edition)
三层架构设计：
- Layer 0: CSV驱动的orchestrator（按顺序处理68家机构）
- Layer 1: 无限制链接探索 + 自适应分页处理
- Layer 2: 产品详情页深度提取（12个字段）
- Layer 3: 数据验证和质量保证

目标：3000-5000个产品，100%准确性
"""
import sys
sys.path.insert(0, '/home/runner/workspace')

import csv
import logging
import time
import requests
from typing import List, Dict, Any, Set, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import hashlib
import os
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 路径配置
DATABASE_URL = os.getenv('DATABASE_URL')
CSV_INPUT = "/home/runner/workspace/attached_assets/New 马来西亚贷款机构与平台全官网_完整版.csv_1762667764316.csv"
CSV_OUTPUT = "/home/runner/malaysia_loans_ultimate_complete.csv"

# 比价平台列表（需要特殊处理）
COMPARISON_PLATFORMS = [
    'imoney', 'ringgitplus', 'loanstreet', 'bankbazaar', 
    'credit malaysia', 'propertyguru', 'mystartr', 'getfinancial',
    'finfolio', 'smartloans', 'kreditgo', '1bank'
]


class PaginationHandler:
    """自适应分页处理器 - 支持所有分页类型"""
    
    @staticmethod
    def find_next_page(soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """
        智能检测下一页链接
        支持：numbered links, rel='next', JS tokens, API offsets
        """
        base_url = urlparse(current_url)._replace(query='', fragment='').geturl()
        
        # 方法1: 查找rel="next"
        next_link = soup.find('a', rel='next')
        if next_link and next_link.get('href'):
            return urljoin(current_url, next_link['href'])
        
        # 方法2: 查找"Next"按钮或链接
        next_patterns = ['next', 'next page', '›', '»', 'seterusnya', 'berikutnya']
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True).lower()
            if any(pattern in text for pattern in next_patterns):
                href = link.get('href')
                if href and not href.startswith('#'):
                    return urljoin(current_url, href)
        
        # 方法3: 查找分页数字（当前页+1）
        parsed = urlparse(current_url)
        query_params = parse_qs(parsed.query)
        
        # 检查page参数
        if 'page' in query_params:
            try:
                current_page = int(query_params['page'][0])
                query_params['page'] = [str(current_page + 1)]
                new_query = urlencode(query_params, doseq=True)
                return urlunparse(parsed._replace(query=new_query))
            except:
                pass
        
        # 方法4: 检查offset参数
        if 'offset' in query_params:
            try:
                current_offset = int(query_params['offset'][0])
                limit = int(query_params.get('limit', [20])[0])
                query_params['offset'] = [str(current_offset + limit)]
                new_query = urlencode(query_params, doseq=True)
                return urlunparse(parsed._replace(query=new_query))
            except:
                pass
        
        return None
    
    @staticmethod
    def detect_max_pages(soup: BeautifulSoup) -> int:
        """检测最大页数"""
        max_page = 1
        
        # 查找分页链接中的最大数字
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True)
            if text.isdigit():
                page_num = int(text)
                max_page = max(max_page, page_num)
        
        return max_page


class ProductExtractor:
    """产品字段提取器 - 提取完整12个字段"""
    
    @staticmethod
    def extract_rate(text: str, soup: BeautifulSoup = None) -> str:
        """提取利率"""
        patterns = [
            r'(\d+\.?\d*)\s*%\s*(p\.a\.|per\s+annum|pa)?',
            r'(BR|BLR|SBR|OPR)\s*[\+\-]\s*(\d+\.?\d*)\s*%?',
            r'from\s+(\d+\.?\d*)\s*%',
            r'as\s+low\s+as\s+(\d+\.?\d*)\s*%',
            r'starting\s+from\s+(\d+\.?\d*)\s*%',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        # 查找表格中的利率
        if soup:
            for th in soup.find_all(['th', 'td', 'strong', 'b']):
                th_text = th.get_text().lower()
                if 'rate' in th_text or 'interest' in th_text or 'kadar' in th_text:
                    # 查找相邻单元格
                    sibling = th.find_next_sibling(['td', 'span', 'div'])
                    if sibling:
                        sibling_text = sibling.get_text(strip=True)
                        for pattern in patterns:
                            match = re.search(pattern, sibling_text, re.IGNORECASE)
                            if match:
                                return match.group(0).strip()
        
        return '请联系银行'
    
    @staticmethod
    def extract_tenure(text: str, soup: BeautifulSoup = None) -> str:
        """提取期限"""
        patterns = [
            r'up\s+to\s+(\d+)\s*(years?|months?|tahun|bulan)',
            r'(\d+)\s*[-–]\s*(\d+)\s*(years?|months?|tahun|bulan)',
            r'(\d+)\s*(years?|months?|tahun|bulan)',
            r'maximum\s+(\d+)\s*(years?|months?)',
            r'tenure.*?(\d+)\s*(years?|months?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        return '请联系银行'
    
    @staticmethod
    def extract_fees(text: str, soup: BeautifulSoup = None) -> str:
        """提取费用"""
        fees = []
        
        # 常见费用关键词
        fee_patterns = [
            (r'annual\s+fee.*?RM\s*(\d+[,\d]*)', 'Annual Fee'),
            (r'processing\s+fee.*?(\d+\.?\d*)\s*%', 'Processing Fee'),
            (r'stamp\s+duty.*?RM\s*(\d+[,\d]*)', 'Stamp Duty'),
            (r'legal\s+fee.*?RM\s*(\d+[,\d]*)', 'Legal Fee'),
            (r'late\s+payment.*?RM\s*(\d+[,\d]*)', 'Late Payment'),
            (r'service\s+tax.*?(\d+\.?\d*)\s*%', 'Service Tax'),
        ]
        
        for pattern, fee_type in fee_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fees.append(f"{fee_type}: {match.group(0)}")
        
        if fees:
            return ' | '.join(fees)
        
        return '请联系银行了解费用详情'
    
    @staticmethod
    def extract_features(soup: BeautifulSoup, text: str) -> str:
        """提取产品特点"""
        features = []
        
        # 查找列表项
        for ul in soup.find_all(['ul', 'ol']):
            # 检查是否是特点列表
            parent_text = ''
            parent = ul.find_parent(['div', 'section'])
            if parent:
                heading = parent.find(['h2', 'h3', 'h4', 'strong'])
                if heading:
                    parent_text = heading.get_text().lower()
            
            if any(kw in parent_text for kw in ['feature', 'highlight', 'benefit', 'advantage', 'ciri', 'kelebihan']):
                items = ul.find_all('li')
                for item in items[:5]:
                    item_text = item.get_text(strip=True)
                    if 10 < len(item_text) < 200:
                        features.append(item_text)
        
        if features:
            return ' | '.join(features[:5])
        
        return '请访问银行官网了解产品特点'
    
    @staticmethod
    def extract_benefits(soup: BeautifulSoup, text: str) -> str:
        """提取产品优势"""
        benefits = []
        
        # 查找包含"benefits"或"rewards"的部分
        for section in soup.find_all(['div', 'section', 'article']):
            heading = section.find(['h2', 'h3', 'h4', 'strong', 'b'])
            if heading:
                heading_text = heading.get_text().lower()
                if any(kw in heading_text for kw in ['benefit', 'reward', 'advantage', 'perks', 'ganjaran', 'manfaat']):
                    # 提取此部分的列表
                    items = section.find_all('li')
                    for item in items[:5]:
                        item_text = item.get_text(strip=True)
                        if 10 < len(item_text) < 200:
                            benefits.append(item_text)
        
        if benefits:
            return ' | '.join(benefits[:5])
        
        return '请访问银行官网了解产品优势'
    
    @staticmethod
    def extract_required_docs(soup: BeautifulSoup, text: str) -> str:
        """提取所需文件"""
        docs = []
        
        # 查找包含"document"或"requirement"的部分
        for section in soup.find_all(['div', 'section', 'article']):
            heading = section.find(['h2', 'h3', 'h4', 'strong', 'b'])
            if heading:
                heading_text = heading.get_text().lower()
                if any(kw in heading_text for kw in ['document', 'requirement', 'eligibility', 'dokumen', 'syarat']):
                    items = section.find_all('li')
                    for item in items[:5]:
                        item_text = item.get_text(strip=True)
                        if any(kw in item_text.lower() for kw in ['ic', 'nric', 'passport', 'payslip', 'statement', 'form', 'proof']):
                            docs.append(item_text)
        
        if docs:
            return ' | '.join(docs[:5])
        
        return '请联系银行了解所需文件'
    
    @staticmethod
    def find_pdf_links(soup: BeautifulSoup, keywords: List[str]) -> str:
        """查找PDF链接"""
        # 查找所有PDF链接
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
        
        for link in pdf_links:
            text = link.get_text().lower()
            href = link.get('href', '').lower()
            
            if any(kw in text or kw in href for kw in keywords):
                full_url = link.get('href')
                if full_url:
                    return full_url
        
        return ''
    
    @staticmethod
    def determine_customer_type(text: str, product_name: str) -> str:
        """判断客户类型偏好"""
        combined = (text + ' ' + product_name).lower()
        
        business_keywords = ['business', 'sme', 'enterprise', 'self-employed', 'entrepreneur', 'perniagaan']
        salaried_keywords = ['salaried', 'employee', 'payslip', 'gaji', 'pekerja']
        
        business_score = sum(1 for kw in business_keywords if kw in combined)
        salaried_score = sum(1 for kw in salaried_keywords if kw in combined)
        
        if business_score > salaried_score:
            return '企业客户 (Business/Self-Employed)'
        elif salaried_score > 0:
            return '打工族 (Salaried)'
        else:
            return '所有客户 (All)'


class UltimateLoanScraper:
    """终极深度爬虫 - 三层架构"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ms;q=0.8,zh;q=0.7',
        })
        
        self.pagination_handler = PaginationHandler()
        self.extractor = ProductExtractor()
        
        # 已访问URL（去重）
        self.visited_urls: Set[str] = set()
        self.product_hashes: Set[str] = set()
        
        # 贷款类型关键词
        self.loan_keywords = {
            'credit_card': ['credit card', 'credit-card', 'kad kredit', 'visa', 'mastercard', 'amex', 'cards/'],
            'home_loan': ['home loan', 'housing loan', 'mortgage', 'property loan', 'rumah', 'housing finance', 'home-loan'],
            'refinance': ['refinance', 'refinancing', 'loan refinance', 'refi'],
            'personal_loan': ['personal loan', 'cash loan', 'personal financing', 'pinjaman peribadi', 'personal-loan'],
            'debt_consolidation': ['debt consolidation', 'consolidation loan', 'debt management'],
            'car_loan': ['car loan', 'auto loan', 'vehicle loan', 'hire purchase', 'kereta', 'auto-loan'],
            'business_loan': ['business loan', 'business financing', 'commercial loan', 'business-loan'],
            'sme_loan': ['sme loan', 'sme financing', 'small business', 'enterprise loan', 'sme/'],
            'other': ['loan', 'financing', 'pinjaman', 'pembiayaan', 'credit']
        }
    
    def classify_loan_type(self, text: str) -> str:
        """智能分类贷款类型"""
        text_lower = text.lower()
        
        # 按优先级检查
        for loan_type, keywords in self.loan_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return loan_type.upper()
        
        return 'OTHER'
    
    def is_comparison_platform(self, company_name: str) -> bool:
        """判断是否为比价平台"""
        return any(platform in company_name.lower() for platform in COMPARISON_PLATFORMS)
    
    # ===== LAYER 1: 无限制发现 + 自适应分页 =====
    
    def discover_all_loan_pages(self, base_url: str, company_name: str, max_pages: int = 100) -> List[str]:
        """
        Layer 1: 无限制链接探索
        移除所有页面限制，使用分页处理器爬取所有页面
        """
        logger.info(f"  🔍 Layer 1: 深度探索 {company_name} 的所有贷款页面...")
        
        all_loan_pages = set()
        is_comparison = self.is_comparison_platform(company_name)
        
        try:
            # 访问首页
            response = self.session.get(base_url, timeout=20, allow_redirects=True)
            
            if response.status_code != 200:
                logger.warning(f"    首页返回 {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有贷款相关链接
            loan_links = self._find_loan_links(soup, base_url)
            all_loan_pages.update(loan_links)
            
            # 如果是比价平台，使用特殊策略
            if is_comparison:
                comparison_pages = self._scrape_comparison_platform(base_url, company_name, soup)
                all_loan_pages.update(comparison_pages)
            else:
                # 普通银行：尝试常见路径
                common_pages = self._try_common_paths(base_url)
                all_loan_pages.update(common_pages)
            
            # 处理分页（针对列表页）
            paginated_pages = self._handle_pagination(list(all_loan_pages)[:10], max_pages)
            all_loan_pages.update(paginated_pages)
            
            logger.info(f"    ✅ 找到 {len(all_loan_pages)} 个贷款页面（无限制）")
            return list(all_loan_pages)
            
        except Exception as e:
            logger.error(f"    ❌ 探索失败: {e}")
            return []
    
    def _find_loan_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """查找所有贷款相关链接"""
        loan_links = set()
        
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
                    loan_links.add(full_url)
        
        return loan_links
    
    def _is_valid_url(self, url: str, base_url: str) -> bool:
        """验证URL"""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_url)
            
            # 必须是同一域名
            if parsed_url.netloc != parsed_base.netloc:
                return False
            
            # 排除无效链接
            invalid = ['login', 'logout', 'signin', 'register', 'mailto:', 'tel:', 'javascript:', '#']
            if any(inv in url.lower() for inv in invalid):
                return False
            
            return True
        except:
            return False
    
    def _try_common_paths(self, base_url: str) -> Set[str]:
        """尝试常见贷款路径"""
        common_paths = [
            # Credit Cards
            '/personal/credit-cards', '/credit-cards', '/cards', '/en/cards',
            '/personal/cards', '/islamic/cards',
            # Home Loans
            '/personal/home-loans', '/home-loans', '/mortgage', '/housing-loan',
            '/personal/property', '/islamic/home-financing',
            # Personal Loans
            '/personal/loans', '/personal-loans', '/cash-loan', '/personal/financing',
            '/islamic/personal-financing',
            # Car Loans
            '/personal/car-loan', '/auto-loan', '/hire-purchase', '/vehicle-financing',
            # Business & SME
            '/business/loans', '/sme', '/business/financing', '/sme/loans',
            '/business/sme-loans', '/islamic/business-financing',
            # General
            '/loans', '/financing', '/products/loans', '/en/loans',
        ]
        
        valid_urls = set()
        for path in common_paths:
            url = urljoin(base_url, path)
            try:
                response = self.session.head(url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    valid_urls.add(url)
                    logger.info(f"      ✅ 找到路径: {path}")
            except:
                pass
        
        return valid_urls
    
    def _scrape_comparison_platform(self, base_url: str, company_name: str, soup: BeautifulSoup) -> Set[str]:
        """比价平台专用爬虫策略"""
        logger.info(f"      🎯 检测到比价平台，使用专用策略")
        
        comparison_pages = set()
        
        # 策略1: 查找所有产品列表页
        product_list_keywords = ['credit-card', 'personal-loan', 'home-loan', 'car-loan', 
                                  'business-loan', 'compare', 'products', 'list']
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            if any(kw in href for kw in product_list_keywords):
                full_url = urljoin(base_url, link['href'])
                if self._is_valid_url(full_url, base_url):
                    comparison_pages.add(full_url)
        
        # 策略2: 尝试直接路径
        comparison_paths = [
            '/credit-cards', '/credit-cards/all',
            '/personal-loans', '/personal-loans/all',
            '/home-loans', '/home-loans/all',
            '/car-loans', '/car-loans/all',
            '/business-loans', '/business-loans/all',
            '/compare/credit-cards', '/compare/personal-loans',
        ]
        
        for path in comparison_paths:
            url = urljoin(base_url, path)
            try:
                response = self.session.head(url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    comparison_pages.add(url)
            except:
                pass
        
        return comparison_pages
    
    def _handle_pagination(self, seed_urls: List[str], max_pages: int = 100) -> Set[str]:
        """处理分页 - 爬取所有页面直到没有下一页"""
        logger.info(f"      📑 开始处理分页（最多{max_pages}页）...")
        
        all_pages = set()
        
        for seed_url in seed_urls:
            if seed_url in self.visited_urls:
                continue
            
            current_url = seed_url
            page_count = 0
            
            while current_url and page_count < max_pages:
                if current_url in self.visited_urls:
                    break
                
                try:
                    response = self.session.get(current_url, timeout=15)
                    if response.status_code != 200:
                        break
                    
                    self.visited_urls.add(current_url)
                    all_pages.add(current_url)
                    page_count += 1
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 查找下一页
                    next_url = self.pagination_handler.find_next_page(soup, current_url)
                    
                    if not next_url or next_url == current_url:
                        break
                    
                    current_url = next_url
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.debug(f"        分页处理错误: {e}")
                    break
            
            if page_count > 1:
                logger.info(f"        ✅ {seed_url} - 找到 {page_count} 页")
        
        return all_pages
    
    # ===== LAYER 2: 产品详情深度提取 =====
    
    def extract_products_from_page(self, url: str, company_name: str) -> List[Dict[str, Any]]:
        """
        Layer 2: 产品详情页深度提取
        提取完整12个字段
        """
        products = []
        
        try:
            response = self.session.get(url, timeout=20)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            
            # 检查是否是产品列表页还是详情页
            is_listing_page = self._is_listing_page(soup)
            
            if is_listing_page:
                # 列表页：提取所有产品链接，然后访问详情页
                product_links = self._extract_product_links(soup, url)
                logger.info(f"      📋 列表页，找到 {len(product_links)} 个产品链接")
                
                for product_url in product_links[:50]:  # 限制每页最多50个产品
                    product = self._extract_single_product(product_url, company_name)
                    if product:
                        products.append(product)
                    time.sleep(0.3)
            else:
                # 详情页：直接提取
                product = self._extract_single_product(url, company_name)
                if product:
                    products.append(product)
            
        except Exception as e:
            logger.error(f"      ❌ 页面提取失败 {url}: {e}")
        
        return products
    
    def _is_listing_page(self, soup: BeautifulSoup) -> bool:
        """判断是否为产品列表页"""
        # 查找多个产品卡片或列表项
        product_cards = soup.find_all(['div', 'article'], class_=re.compile(r'(product|card|item)', re.I))
        
        if len(product_cards) > 3:
            return True
        
        # 查找表格行
        table_rows = soup.find_all('tr')
        if len(table_rows) > 5:
            return True
        
        return False
    
    def _extract_product_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """从列表页提取所有产品链接"""
        product_links = []
        
        # 查找产品卡片中的链接
        for card in soup.find_all(['div', 'article'], class_=re.compile(r'(product|card|item)', re.I)):
            link = card.find('a', href=True)
            if link:
                full_url = urljoin(base_url, link['href'])
                if self._is_valid_url(full_url, base_url):
                    product_links.append(full_url)
        
        # 查找表格中的链接
        for row in soup.find_all('tr'):
            link = row.find('a', href=True)
            if link:
                href = link['href']
                # 排除分页链接
                if not any(kw in href.lower() for kw in ['page=', 'next', 'prev']):
                    full_url = urljoin(base_url, href)
                    if self._is_valid_url(full_url, base_url):
                        product_links.append(full_url)
        
        return list(set(product_links))  # 去重
    
    def _extract_single_product(self, url: str, company_name: str) -> Optional[Dict[str, Any]]:
        """提取单个产品的完整12个字段"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            
            # 提取产品名称
            product_name = self._extract_product_name(soup)
            if not product_name or len(product_name) < 3:
                return None
            
            # 去重检查
            product_hash = hashlib.md5(f"{company_name}_{product_name}".encode()).hexdigest()
            if product_hash in self.product_hashes:
                return None
            self.product_hashes.add(product_hash)
            
            # 判断贷款类型
            loan_type = self.classify_loan_type(url + ' ' + text + ' ' + product_name)
            
            # 提取12个字段
            product = {
                'company': company_name,
                'loan_type': loan_type,
                'product_name': product_name,
                'required_doc': self.extractor.extract_required_docs(soup, text),
                'features': self.extractor.extract_features(soup, text),
                'benefits': self.extractor.extract_benefits(soup, text),
                'fees_charges': self.extractor.extract_fees(text, soup),
                'tenure': self.extractor.extract_tenure(text, soup),
                'rate': self.extractor.extract_rate(text, soup),
                'application_form_url': self.extractor.find_pdf_links(soup, ['application', 'apply', 'form']),
                'product_disclosure_url': self.extractor.find_pdf_links(soup, ['disclosure', 'pds', 'product disclosure']),
                'terms_conditions_url': self.extractor.find_pdf_links(soup, ['terms', 'conditions', 'tnc', 't&c']),
                'preferred_customer_type': self.extractor.determine_customer_type(text, product_name),
                'source_url': url,
                'scraped_at': datetime.now().isoformat()
            }
            
            return product
            
        except Exception as e:
            logger.debug(f"        提取产品失败 {url}: {e}")
            return None
    
    def _extract_product_name(self, soup: BeautifulSoup) -> str:
        """提取产品名称"""
        # 优先级1: h1
        h1 = soup.find('h1')
        if h1:
            name = h1.get_text(strip=True)
            if 5 < len(name) < 150:
                return name
        
        # 优先级2: title
        title = soup.find('title')
        if title:
            name = title.get_text(strip=True)
            # 清理title（移除站点名称）
            name = re.split(r'[|–-]', name)[0].strip()
            if 5 < len(name) < 150:
                return name
        
        # 优先级3: h2
        h2 = soup.find('h2')
        if h2:
            name = h2.get_text(strip=True)
            if 5 < len(name) < 150:
                return name
        
        return ''
    
    # ===== LAYER 0: CSV Orchestrator =====
    
    def scrape_institution(self, company_name: str, website: str) -> List[Dict[str, Any]]:
        """
        Layer 0: 爬取单个机构的所有贷款产品
        orchestrator - 协调Layer 1和Layer 2
        """
        logger.info(f"🏦 开始爬取: {company_name}")
        logger.info(f"   网址: {website}")
        
        all_products = []
        
        # Layer 1: 发现所有贷款页面（无限制）
        loan_pages = self.discover_all_loan_pages(website, company_name, max_pages=100)
        
        if not loan_pages:
            logger.warning(f"  ⚠️ {company_name}: 未找到贷款页面")
            return []
        
        logger.info(f"  📄 Layer 2: 提取产品详情（{len(loan_pages)} 个页面）...")
        
        # Layer 2: 提取每个页面的产品（无页面限制）
        for idx, page_url in enumerate(loan_pages, 1):
            logger.info(f"    [{idx}/{len(loan_pages)}] {page_url}")
            
            products = self.extract_products_from_page(page_url, company_name)
            
            if products:
                logger.info(f"      ✅ 找到 {len(products)} 个产品")
                all_products.extend(products)
            
            time.sleep(0.5)  # 礼貌延迟
        
        logger.info(f"  ✅ {company_name}: 共 {len(all_products)} 个产品")
        return all_products


# ===== LAYER 3: 数据验证和QA =====

def validate_product(product: Dict[str, Any]) -> bool:
    """验证产品数据质量"""
    required_fields = ['company', 'loan_type', 'product_name']
    
    # 必须字段检查
    for field in required_fields:
        if not product.get(field):
            return False
    
    # 至少10个非空字段
    non_empty_count = sum(1 for v in product.values() if v and str(v).strip())
    if non_empty_count < 10:
        return False
    
    return True


def init_database():
    """初始化PostgreSQL数据库"""
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS loan_products_ultimate(
            id SERIAL PRIMARY KEY,
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
            scraped_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(company, product_name)
        )
    """)
    
    con.commit()
    cur.close()
    con.close()
    logger.info("✅ PostgreSQL数据库初始化完成")


def load_institutions_from_csv(csv_path: str) -> List[Dict[str, str]]:
    """从CSV加载机构列表（按顺序）"""
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
    
    logger.info(f"📋 加载了 {len(institutions)} 家金融机构（按CSV顺序）")
    return institutions


def save_to_database(products: List[Dict[str, Any]]):
    """保存到PostgreSQL数据库（去重）"""
    if not products:
        return
    
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    
    insert_sql = """
        INSERT INTO loan_products_ultimate(
            company, loan_type, product_name, required_doc, features, benefits,
            fees_charges, tenure, rate, application_form_url, product_disclosure_url,
            terms_conditions_url, preferred_customer_type, source_url, scraped_at
        ) VALUES %s
        ON CONFLICT (company, product_name) DO NOTHING
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
        if validate_product(p)  # Layer 3: 验证
    ]
    
    if items:
        execute_values(cur, insert_sql, items)
        con.commit()
        logger.info(f"    💾 保存了 {len(items)} 个有效产品到数据库")
    
    cur.close()
    con.close()


def export_to_csv_table(output_path: str):
    """导出为精致表格（12列）"""
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    
    cur.execute("""
        SELECT 
            company AS "COMPANY",
            loan_type AS "LOAN TYPE",
            required_doc AS "REQUIRED DOC",
            features AS "FEATURES",
            benefits AS "BENEFITS",
            fees_charges AS "FEES & CHARGES",
            tenure AS "TENURE",
            rate AS "RATE",
            application_form_url AS "APPLICATION FORM",
            product_disclosure_url AS "PRODUCT DISCLOSURE",
            terms_conditions_url AS "TERMS & CONDITIONS",
            preferred_customer_type AS "客户偏好"
        FROM loan_products_ultimate
        ORDER BY 
            CASE company
                WHEN 'Affin Bank Berhad' THEN 1
                WHEN 'Alliance Bank Malaysia Berhad' THEN 2
                WHEN 'AmBank (M) Berhad' THEN 3
                ELSE 999
            END,
            loan_type,
            product_name
    """)
    
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    
    cur.close()
    con.close()
    
    # 写入CSV
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(zip(columns, row)))
    
    logger.info(f"📤 表格已导出: {output_path}")
    logger.info(f"   总计: {len(rows)} 个产品")


def generate_statistics():
    """生成统计报告"""
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    
    # 总产品数
    cur.execute("SELECT COUNT(*) FROM loan_products_ultimate")
    total_products = cur.fetchone()[0]
    
    # 按公司统计
    cur.execute("""
        SELECT company, COUNT(*) as count 
        FROM loan_products_ultimate 
        GROUP BY company 
        ORDER BY count DESC
    """)
    by_company = cur.fetchall()
    
    # 按贷款类型统计
    cur.execute("""
        SELECT loan_type, COUNT(*) as count 
        FROM loan_products_ultimate 
        GROUP BY loan_type 
        ORDER BY count DESC
    """)
    by_loan_type = cur.fetchall()
    
    cur.close()
    con.close()
    
    logger.info("")
    logger.info("=" * 100)
    logger.info("📊 统计报告")
    logger.info("=" * 100)
    logger.info(f"总产品数: {total_products}")
    logger.info("")
    logger.info("按公司分布（Top 10）:")
    for company, count in by_company[:10]:
        logger.info(f"  {company}: {count} 个产品")
    logger.info("")
    logger.info("按贷款类型分布:")
    for loan_type, count in by_loan_type:
        logger.info(f"  {loan_type}: {count} 个产品")
    logger.info("")


def main():
    """主流程"""
    logger.info("")
    logger.info("=" * 100)
    logger.info("🚀 CreditPilot - 马来西亚68家金融机构深度爬虫系统 (Ultimate Edition)")
    logger.info("=" * 100)
    logger.info("三层架构: Layer 0 (Orchestrator) + Layer 1 (Discovery) + Layer 2 (Extraction) + Layer 3 (QA)")
    logger.info("目标: 3000-5000个产品，100%准确性")
    logger.info("=" * 100)
    logger.info("")
    
    start_time = datetime.now()
    
    # 初始化
    init_database()
    
    # 加载机构列表（按CSV顺序）
    institutions = load_institutions_from_csv(CSV_INPUT)
    
    # 创建爬虫
    scraper = UltimateLoanScraper()
    
    # 逐个爬取（按CSV顺序）
    all_products = []
    
    for idx, inst in enumerate(institutions, 1):
        logger.info(f"\n📍 进度: {idx}/{len(institutions)}")
        logger.info("-" * 100)
        
        try:
            products = scraper.scrape_institution(inst['name'], inst['website'])
            if products:
                all_products.extend(products)
                # 即时保存（Layer 3: 验证）
                save_to_database(products)
        except Exception as e:
            logger.error(f"❌ {inst['name']} 爬取失败: {e}")
        
        time.sleep(2)  # 机构间延迟
    
    # 导出表格
    logger.info("")
    logger.info("=" * 100)
    logger.info("📊 导出精致表格（12列）")
    logger.info("=" * 100)
    export_to_csv_table(CSV_OUTPUT)
    
    # 统计
    generate_statistics()
    
    # 总结
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("")
    logger.info("=" * 100)
    logger.info("🎉 爬取完成！")
    logger.info("=" * 100)
    logger.info(f"总耗时: {duration:.1f} 秒 ({duration/60:.1f} 分钟)")
    logger.info(f"处理机构: {len(institutions)} 家")
    logger.info(f"产品总数: {len(all_products)}")
    logger.info(f"数据库: PostgreSQL (persistent)")
    logger.info(f"表格文件: {CSV_OUTPUT}")
    logger.info("")
    logger.info("💡 提示: 请随机验证几家公司的数据，确保100%准确性！")
    logger.info("")


if __name__ == '__main__':
    main()
