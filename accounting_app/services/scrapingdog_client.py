import os
import requests
import logging
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ScrapingDogClient:
    """ScrapingDog API客户端 - 用于爬取马来西亚银行贷款数据"""
    
    def __init__(self):
        self.api_key = os.getenv('SCRAPINGDOG_API_KEY')
        if not self.api_key:
            raise ValueError("SCRAPINGDOG_API_KEY not found in environment")
        
        self.base_url = "https://api.scrapingdog.com/scrape"
        logger.info("✅ ScrapingDog客户端已初始化")
    
    def scrape_url(self, url: str, dynamic: bool = False, premium: bool = False) -> Optional[str]:
        """
        使用ScrapingDog爬取URL
        
        Args:
            url: 目标URL
            dynamic: 是否使用JavaScript渲染（25x credits）
            premium: 是否使用高级代理
        
        Returns:
            HTML内容或None
        """
        params = {
            'api_key': self.api_key,
            'url': url,
            'dynamic': 'true' if dynamic else 'false',
            'premium': 'true' if premium else 'false'
        }
        
        try:
            logger.info(f"🕷️ 爬取URL: {url}")
            response = requests.get(self.base_url, params=params, timeout=120)
            
            if response.status_code == 200:
                logger.info(f"✅ 成功爬取: {url}")
                return response.text
            else:
                logger.error(f"❌ 爬取失败 {url}: HTTP {response.status_code}")
                logger.error(f"响应: {response.text[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 爬取异常 {url}: {str(e)}")
            return None
    
    def extract_loan_products(self, html: str, bank_name: str) -> Dict[str, Any]:
        """
        从HTML中提取贷款产品数据
        
        Args:
            html: 网页HTML内容
            bank_name: 银行名称
        
        Returns:
            提取的产品数据字典
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        products = {
            'bank': bank_name,
            'products': [],
            'raw_html_length': len(html)
        }
        
        loan_keywords = [
            'personal loan', 'home loan', 'housing loan', 'mortgage',
            'business loan', 'SME', 'car loan', 'auto loan',
            'debt consolidation', 'refinance', 'financing'
        ]
        
        text_content = soup.get_text().lower()
        
        for keyword in loan_keywords:
            if keyword in text_content:
                products['products'].append({
                    'type': keyword,
                    'found': True
                })
        
        return products

scrapingdog_client = ScrapingDogClient()
