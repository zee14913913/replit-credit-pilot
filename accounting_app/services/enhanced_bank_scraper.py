"""
增强版银行爬虫 - 智能探索导航菜单
不需要登录也能找到完整的贷款产品信息
"""
import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional, Set
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class EnhancedBankScraper:
    """
    增强版爬虫：智能探索网站导航
    
    策略：
    1. 首页 → 探索所有导航菜单链接
    2. 查找侧边栏、页脚的贷款相关链接
    3. 尝试多种URL模式
    4. 递归探索子页面
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ms;q=0.8,zh;q=0.7',
        })
        
        # 贷款相关关键词（英文/马来文/中文）
        self.loan_keywords = [
            # 英文
            'loan', 'loans', 'financing', 'finance', 'credit', 'mortgage',
            'borrow', 'lending', 'personal loan', 'home loan', 'business loan',
            'sme loan', 'car loan', 'education loan', 'refinance',
            
            # 马来文
            'pinjaman', 'pembiayaan', 'kredit',
            
            # 常见产品名
            'flexi', 'cash', 'easy loan', 'quick loan',
        ]
    
    def find_loan_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """
        智能查找所有可能的贷款相关链接
        
        查找位置：
        1. 顶部导航栏（nav, header）
        2. 侧边栏（sidebar, aside）
        3. 页脚（footer）
        4. 下拉菜单（dropdown, mega-menu）
        5. 主内容区域的链接
        """
        loan_links = set()
        
        # 1. 查找所有链接
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True).lower()
            
            # 检查链接文本或URL是否包含贷款关键词
            if any(keyword in text or keyword in href.lower() for keyword in self.loan_keywords):
                full_url = urljoin(base_url, href)
                
                # 过滤外部链接和无效链接
                if self._is_valid_url(full_url, base_url):
                    loan_links.add(full_url)
        
        logger.info(f"   找到 {len(loan_links)} 个贷款相关链接")
        return loan_links
    
    def _is_valid_url(self, url: str, base_url: str) -> bool:
        """验证URL是否有效"""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_url)
            
            # 必须是同一个域名
            if parsed_url.netloc != parsed_base.netloc:
                return False
            
            # 排除登录、下载、外部链接
            invalid_patterns = [
                'login', 'logout', 'signin', 'signup', 'register',
                'download', 'pdf', 'doc', 'xls',
                'mailto:', 'tel:', 'javascript:',
                '#', 'void(0)'
            ]
            
            if any(pattern in url.lower() for pattern in invalid_patterns):
                return False
            
            return True
        except:
            return False
    
    def explore_navigation_menu(self, bank_name: str, website: str) -> List[str]:
        """
        探索网站导航菜单，找到所有贷款产品页面
        
        Args:
            bank_name: 银行名称
            website: 银行网站URL
        
        Returns:
            所有贷款产品页面的URL列表
        """
        logger.info(f"🔍 探索 {bank_name} 的导航菜单...")
        
        try:
            # 访问首页
            response = self.session.get(website, timeout=15, allow_redirects=True)
            
            if response.status_code != 200:
                logger.warning(f"   首页返回 {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有贷款相关链接
            loan_links = self.find_loan_links(soup, website)
            
            if not loan_links:
                logger.warning(f"   ⚠️ 未找到贷款链接，尝试常见URL模式...")
                loan_links = self._try_common_patterns(website)
            
            return list(loan_links)
            
        except Exception as e:
            logger.error(f"   ❌ 探索失败: {e}")
            return []
    
    def _try_common_patterns(self, base_url: str) -> Set[str]:
        """尝试常见的贷款页面URL模式"""
        common_paths = [
            # 英文路径
            '/personal/loans',
            '/personal/financing',
            '/loans',
            '/financing',
            '/products/loans',
            '/products/financing',
            '/personal/products/loans',
            '/personal-loans',
            '/home-loans',
            '/business-loans',
            '/sme-financing',
            
            # 马来文路径
            '/pinjaman',
            '/pembiayaan',
            
            # 常见子路径
            '/en/personal/loans',
            '/en/loans',
            '/my/personal/loans',
        ]
        
        valid_urls = set()
        
        for path in common_paths:
            url = urljoin(base_url, path)
            try:
                response = self.session.head(url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    valid_urls.add(url)
                    logger.info(f"   ✅ 找到: {path}")
            except:
                pass
        
        return valid_urls
    
    def extract_product_details_from_page(
        self,
        url: str,
        bank_name: str,
        institution_type: str
    ) -> List[Dict[str, Any]]:
        """
        从单个页面提取所有贷款产品详情
        
        返回12个字段的产品列表
        """
        products = []
        
        try:
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 策略1: 查找产品卡片或列表项
            product_containers = self._find_product_containers(soup)
            
            if not product_containers:
                # 策略2: 整个页面作为一个产品
                product = self._extract_single_product(soup, url, bank_name, institution_type)
                if product:
                    products.append(product)
            else:
                # 提取每个产品
                for container in product_containers[:10]:  # 限制最多10个
                    product = self._extract_product_from_container(
                        container, url, bank_name, institution_type, soup
                    )
                    if product:
                        products.append(product)
            
        except Exception as e:
            logger.error(f"   ❌ 页面解析失败 {url}: {e}")
        
        return products
    
    def _find_product_containers(self, soup: BeautifulSoup) -> List:
        """查找产品容器（卡片、列表项等）"""
        containers = []
        
        # 常见产品容器的CSS类名和标签
        selectors = [
            {'class': re.compile(r'product.*card', re.I)},
            {'class': re.compile(r'loan.*card', re.I)},
            {'class': re.compile(r'product.*item', re.I)},
            {'class': re.compile(r'financing.*card', re.I)},
        ]
        
        for selector in selectors:
            found = soup.find_all('div', selector)
            if found:
                containers.extend(found)
        
        # 如果没找到，尝试查找列表项
        if not containers:
            # 查找包含贷款关键词的section
            sections = soup.find_all('section')
            for section in sections:
                text = section.get_text().lower()
                if any(kw in text for kw in ['loan', 'financing', 'pinjaman']):
                    items = section.find_all('li')
                    if items:
                        containers.extend(items)
        
        return containers
    
    def _extract_product_from_container(
        self,
        container,
        page_url: str,
        bank_name: str,
        institution_type: str,
        full_soup: BeautifulSoup
    ) -> Optional[Dict[str, Any]]:
        """从产品容器中提取12个字段"""
        
        # 产品名称
        product_name = None
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5']:
            heading = container.find(tag)
            if heading:
                product_name = heading.get_text(strip=True)
                break
        
        if not product_name or len(product_name) < 3:
            return None
        
        # 提取利率
        text = container.get_text()
        rate = self._extract_rate(text)
        
        # 提取期限
        tenure = self._extract_tenure(text)
        
        # 判断贷款类型
        loan_type = self._classify_loan_type(product_name + ' ' + text)
        
        # 提取特点和优势（从列表项）
        features = []
        benefits = []
        
        lists = container.find_all('li')
        for li in lists[:5]:
            item_text = li.get_text(strip=True)
            if len(item_text) > 10 and len(item_text) < 150:
                # 简单判断是特点还是优势
                if any(kw in item_text.lower() for kw in ['benefit', 'advantage', 'why']):
                    benefits.append(item_text)
                else:
                    features.append(item_text)
        
        # 查找PDF链接
        application_form = self._find_pdf_link(container, ['apply', 'application'])
        disclosure = self._find_pdf_link(container, ['disclosure', 'pds'])
        terms = self._find_pdf_link(container, ['terms', 'conditions', 'tnc'])
        
        # 判断客户偏好
        preferred_customer = self._determine_customer_preference(text, product_name)
        
        return {
            'company': bank_name,
            'loan_type': loan_type,
            'product_name': product_name,
            'required_doc': "请联系银行了解所需文件",
            'features': ' | '.join(features) if features else "请访问银行官网了解产品特点",
            'benefits': ' | '.join(benefits) if benefits else "请访问银行官网了解产品优势",
            'fees_charges': "请联系银行了解费用详情",
            'tenure': tenure,
            'rate': rate,
            'application_form_url': application_form,
            'product_disclosure_url': disclosure,
            'terms_conditions_url': terms,
            'preferred_customer_type': preferred_customer,
            'institution_type': institution_type,
            'source_url': page_url,
            'pulled_at': datetime.now().isoformat()
        }
    
    def _extract_single_product(
        self,
        soup: BeautifulSoup,
        url: str,
        bank_name: str,
        institution_type: str
    ) -> Optional[Dict[str, Any]]:
        """将整个页面作为一个产品提取"""
        
        # 产品名称（页面标题）
        product_name = None
        h1 = soup.find('h1')
        if h1:
            product_name = h1.get_text(strip=True)
        else:
            title = soup.find('title')
            if title:
                product_name = title.get_text(strip=True)
        
        if not product_name:
            return None
        
        text = soup.get_text()
        
        return {
            'company': bank_name,
            'loan_type': self._classify_loan_type(product_name + ' ' + text),
            'product_name': product_name,
            'required_doc': "请联系银行了解所需文件",
            'features': "请访问银行官网了解产品特点",
            'benefits': "请访问银行官网了解产品优势",
            'fees_charges': "请联系银行了解费用详情",
            'tenure': self._extract_tenure(text),
            'rate': self._extract_rate(text),
            'application_form_url': None,
            'product_disclosure_url': None,
            'terms_conditions_url': None,
            'preferred_customer_type': self._determine_customer_preference(text, product_name),
            'institution_type': institution_type,
            'source_url': url,
            'pulled_at': datetime.now().isoformat()
        }
    
    def _extract_rate(self, text: str) -> str:
        """提取利率"""
        patterns = [
            r'(\d+\.?\d*)\s*%\s*(p\.a\.|per\s+annum)?',
            r'(BR|BLR|SBR)\s*[\+\-]\s*(\d+\.?\d*)\s*%?',
            r'from\s+(\d+\.?\d*)\s*%',
            r'as\s+low\s+as\s+(\d+\.?\d*)\s*%',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "Contact Bank"
    
    def _extract_tenure(self, text: str) -> str:
        """提取期限"""
        patterns = [
            r'up\s+to\s+(\d+)\s*(years?|months?)',
            r'(\d+)\s*(years?|tahun)',
            r'(\d+)\s*-\s*(\d+)\s*(years?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "Contact Bank"
    
    def _classify_loan_type(self, text: str) -> str:
        """分类贷款类型"""
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in ['home', 'housing', 'mortgage', 'property', 'rumah']):
            return 'HOME'
        elif any(kw in text_lower for kw in ['refinance', 'refinancing']):
            return 'REFINANCE'
        elif any(kw in text_lower for kw in ['debt consolidation', 'consolidation']):
            return 'DEBT_CONSOLIDATION'
        elif any(kw in text_lower for kw in ['business', 'sme', 'commercial', 'enterprise']):
            return 'BUSINESS'
        elif any(kw in text_lower for kw in ['personal', 'cash', 'peribadi']):
            return 'PERSONAL'
        else:
            return 'OTHER'
    
    def _find_pdf_link(self, container, keywords: List[str]) -> Optional[str]:
        """查找PDF链接"""
        links = container.find_all('a', href=re.compile(r'\.pdf$', re.I))
        
        for link in links:
            text = link.get_text().lower()
            href = link.get('href', '').lower()
            
            if any(kw in text or kw in href for kw in keywords):
                return link.get('href')
        
        return None
    
    def _determine_customer_preference(self, text: str, product_name: str) -> str:
        """判断客户偏好"""
        text_lower = (text + ' ' + product_name).lower()
        
        business_score = sum(1 for kw in ['business', 'sme', 'entrepreneur', 'self-employed'] if kw in text_lower)
        salaried_score = sum(1 for kw in ['salaried', 'employee', 'fixed income', 'payslip'] if kw in text_lower)
        
        if business_score > salaried_score:
            return "企业客户 (Business/Self-Employed)"
        elif salaried_score > 0:
            return "打工族/固定收入客户 (Salaried/Fixed Income)"
        else:
            return "所有客户类型 (All Customer Types)"
    
    def scrape_bank_comprehensive(
        self,
        bank_name: str,
        website: str,
        institution_type: str
    ) -> List[Dict[str, Any]]:
        """
        完整爬取单个银行的所有贷款产品
        
        流程：
        1. 探索导航菜单，找到所有贷款页面
        2. 访问每个页面，提取产品详情
        3. 返回所有产品
        """
        logger.info(f"🏦 开始爬取: {bank_name}")
        
        all_products = []
        
        # 步骤1: 探索导航，找到所有贷款页面
        loan_pages = self.explore_navigation_menu(bank_name, website)
        
        if not loan_pages:
            logger.warning(f"   ⚠️ {bank_name}: 未找到贷款页面")
            return []
        
        logger.info(f"   找到 {len(loan_pages)} 个贷款页面")
        
        # 步骤2: 访问每个页面，提取产品
        for page_url in loan_pages[:5]:  # 限制最多5个页面
            logger.info(f"   📄 访问: {page_url}")
            
            products = self.extract_product_details_from_page(
                page_url, bank_name, institution_type
            )
            
            if products:
                logger.info(f"      ✅ 找到 {len(products)} 个产品")
                all_products.extend(products)
            
            time.sleep(1)  # 礼貌性延迟
        
        logger.info(f"✅ {bank_name}: 共获取 {len(all_products)} 个产品")
        return all_products


# 全局单例
enhanced_scraper = EnhancedBankScraper()
