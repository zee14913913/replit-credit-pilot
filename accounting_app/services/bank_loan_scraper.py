"""
马来西亚主要银行贷款产品爬虫
抓取真实的贷款产品信息
"""
import requests
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class BankLoanScraper:
    """银行贷款产品爬虫基类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def extract_rate(self, text: str) -> Optional[str]:
        """从文本中提取利率数字"""
        match = re.search(r'(\d+\.?\d*)%', text)
        return match.group(0) if match else None
    
    def scrape(self) -> List[Dict[str, Any]]:
        """爬取贷款产品（子类实现）"""
        raise NotImplementedError


class MaybankScraper(BankLoanScraper):
    """Maybank 贷款产品爬虫"""
    
    LOAN_PAGES = {
        'personal': 'https://www.maybank2u.com.my/en/personal/loans/personal-financing.page',
        'home': 'https://www.maybank2u.com.my/en/personal/loans/home-financing.page',
        'auto': 'https://www.maybank2u.com.my/en/personal/loans/hire-purchase.page',
    }
    
    def scrape(self) -> List[Dict[str, Any]]:
        """爬取Maybank贷款产品"""
        products = []
        
        for loan_type, url in self.LOAN_PAGES.items():
            try:
                logger.info(f"正在爬取 Maybank {loan_type} loan...")
                response = self.session.get(url, timeout=15)
                
                if response.status_code != 200:
                    logger.warning(f"⚠️ Maybank {loan_type} 页面返回 {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 示例解析逻辑（需根据实际网页结构调整）
                # 这里提供一个通用框架
                product_cards = soup.find_all('div', class_=re.compile('product|loan|card'))
                
                for card in product_cards[:5]:  # 限制每类最多5个产品
                    title = card.find(['h2', 'h3', 'h4'])
                    rate_elem = card.find(text=re.compile(r'\d+\.?\d*%'))
                    
                    if title:
                        product = {
                            'source': 'maybank',
                            'bank': 'Maybank',
                            'product': title.get_text(strip=True),
                            'type': loan_type.upper(),
                            'rate': self.extract_rate(rate_elem) if rate_elem else 'Contact Bank',
                            'summary': '请访问 Maybank 官网了解详情',
                            'url': url,
                            'pulled_at': datetime.now().isoformat()
                        }
                        products.append(product)
                
                logger.info(f"✅ Maybank {loan_type}: 找到 {len(products)} 个产品")
                
            except Exception as e:
                logger.error(f"❌ Maybank {loan_type} 爬取失败: {e}")
        
        return products


class CIMBScraper(BankLoanScraper):
    """CIMB 贷款产品爬虫"""
    
    LOAN_PAGES = {
        'personal': 'https://www.cimb.com.my/en/personal/products/loans/personal-loans.html',
        'home': 'https://www.cimb.com.my/en/personal/products/loans/home-loans.html',
    }
    
    def scrape(self) -> List[Dict[str, Any]]:
        """爬取CIMB贷款产品"""
        products = []
        
        for loan_type, url in self.LOAN_PAGES.items():
            try:
                logger.info(f"正在爬取 CIMB {loan_type} loan...")
                response = self.session.get(url, timeout=15)
                
                if response.status_code != 200:
                    logger.warning(f"⚠️ CIMB {loan_type} 页面返回 {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 解析CIMB网页结构
                product_sections = soup.find_all(['div', 'section'], class_=re.compile('product|loan'))
                
                for section in product_sections[:5]:
                    title = section.find(['h2', 'h3', 'h4'])
                    
                    if title:
                        product = {
                            'source': 'cimb',
                            'bank': 'CIMB Bank',
                            'product': title.get_text(strip=True),
                            'type': loan_type.upper(),
                            'rate': 'Contact Bank',
                            'summary': '请访问 CIMB 官网了解详情',
                            'url': url,
                            'pulled_at': datetime.now().isoformat()
                        }
                        products.append(product)
                
                logger.info(f"✅ CIMB {loan_type}: 找到 {len(products)} 个产品")
                
            except Exception as e:
                logger.error(f"❌ CIMB {loan_type} 爬取失败: {e}")
        
        return products


class PublicBankScraper(BankLoanScraper):
    """Public Bank 贷款产品爬虫"""
    
    LOAN_PAGES = {
        'personal': 'https://www.pbebank.com/personal/loans/personal-loans.html',
        'home': 'https://www.pbebank.com/personal/loans/home-loans.html',
    }
    
    def scrape(self) -> List[Dict[str, Any]]:
        """爬取Public Bank贷款产品"""
        products = []
        
        for loan_type, url in self.LOAN_PAGES.items():
            try:
                logger.info(f"正在爬取 Public Bank {loan_type} loan...")
                response = self.session.get(url, timeout=15)
                
                if response.status_code != 200:
                    logger.warning(f"⚠️ Public Bank {loan_type} 页面返回 {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 解析Public Bank网页结构
                titles = soup.find_all(['h2', 'h3'], class_=re.compile('product|title|loan'))
                
                for title in titles[:5]:
                    product = {
                        'source': 'public-bank',
                        'bank': 'Public Bank',
                        'product': title.get_text(strip=True),
                        'type': loan_type.upper(),
                        'rate': 'Contact Bank',
                        'summary': '请访问 Public Bank 官网了解详情',
                        'url': url,
                        'pulled_at': datetime.now().isoformat()
                    }
                    products.append(product)
                
                logger.info(f"✅ Public Bank {loan_type}: 找到 {len(products)} 个产品")
                
            except Exception as e:
                logger.error(f"❌ Public Bank {loan_type} 爬取失败: {e}")
        
        return products


class BankLoanAggregator:
    """银行贷款数据聚合器"""
    
    def __init__(self):
        self.scrapers = [
            MaybankScraper(),
            CIMBScraper(),
            PublicBankScraper(),
        ]
    
    def scrape_all_banks(self) -> List[Dict[str, Any]]:
        """
        爬取所有银行的贷款产品
        
        Returns:
            [
                {
                    'source': 'maybank',
                    'bank': 'Maybank',
                    'product': 'Personal Loan-i',
                    'type': 'PERSONAL',
                    'rate': '6.88%',
                    'summary': '...',
                    'url': 'https://...',
                    'pulled_at': '2025-11-09T04:00:00'
                },
                ...
            ]
        """
        all_products = []
        
        for scraper in self.scrapers:
            try:
                products = scraper.scrape()
                all_products.extend(products)
                logger.info(f"✅ {scraper.__class__.__name__}: 成功获取 {len(products)} 个产品")
            except Exception as e:
                logger.error(f"❌ {scraper.__class__.__name__} 失败: {e}")
        
        logger.info(f"🎉 总计爬取 {len(all_products)} 个银行贷款产品")
        return all_products
    
    def validate_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        验证产品数据完整性
        
        Args:
            products: 原始产品列表
        
        Returns:
            验证通过的产品列表
        """
        valid_products = []
        required_fields = ['source', 'bank', 'product', 'type']
        
        for product in products:
            # 检查必需字段
            if all(product.get(field) for field in required_fields):
                # 标准化利率格式
                if product.get('rate') and '%' not in product['rate']:
                    product['rate'] = f"{product['rate']}%"
                
                # 确保有summary
                if not product.get('summary'):
                    product['summary'] = f"请访问 {product['bank']} 官网了解详情"
                
                valid_products.append(product)
            else:
                logger.warning(f"⚠️ 产品数据不完整，跳过: {product.get('product', 'Unknown')}")
        
        logger.info(f"✅ 验证通过 {len(valid_products)}/{len(products)} 个产品")
        return valid_products


# 全局单例
bank_aggregator = BankLoanAggregator()
