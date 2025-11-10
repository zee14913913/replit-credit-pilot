"""
马来西亚银行贷款数据采集器 - 使用ScrapingDog API
"""
import os
import json
import logging
import time
import csv
from typing import List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class MalaysiaBankScraper:
    """使用ScrapingDog采集马来西亚64家银行的贷款产品数据"""
    
    def __init__(self):
        from accounting_app.services.scrapingdog_client import scrapingdog_client
        self.client = scrapingdog_client
        
        config_path = os.path.join(
            os.path.dirname(__file__),
            '../data/malaysia_financial_institutions.json'
        )
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.institutions = []
        for category in ['commercial_banks', 'islamic_banks', 'development_banks', 
                        'digital_banks', 'p2p_platforms', 'non_bank_credit']:
            self.institutions.extend(self.config.get(category, []))
        
        logger.info(f"✅ 已加载 {len(self.institutions)} 家金融机构")
    
    def scrape_bank(self, bank: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        爬取单个银行的所有贷款产品
        
        Returns:
            产品列表，每个产品包含12个字段
        """
        products = []
        bank_name = bank['name']
        website = bank['website']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🏦 开始爬取: {bank_name}")
        logger.info(f"🌐 网站: {website}")
        
        loan_paths = [
            '/personal/loans',
            '/loans',
            '/financing',
            '/products/loans',
            '/en/personal/loans',
            '/personal-loan',
            '/home-loan',
            '/business-loan',
        ]
        
        for path in loan_paths:
            url = f"{website}{path}"
            
            html = self.client.scrape_url(url, dynamic=False)
            
            if html and len(html) > 1000:
                logger.info(f"  ✅ 获取到内容: {len(html)} 字符")
                
                extracted = self._extract_products_from_html(html, bank, url)
                products.extend(extracted)
                
                if len(products) > 0:
                    logger.info(f"  📊 找到 {len(extracted)} 个产品")
                    break
            else:
                logger.info(f"  ⏭️  跳过: {url}")
            
            time.sleep(2)
        
        if len(products) == 0:
            logger.warning(f"  ⚠️  {bank_name}: 未找到贷款产品")
        else:
            logger.info(f"  ✅ {bank_name}: 共找到 {len(products)} 个产品")
        
        return products
    
    def _extract_products_from_html(self, html: str, bank: Dict, source_url: str) -> List[Dict[str, Any]]:
        """从HTML中提取产品数据"""
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        
        title_tags = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        
        loan_keywords = {
            'personal': ['personal loan', 'personal financing', 'cash'],
            'home': ['home loan', 'housing', 'mortgage', 'property'],
            'business': ['business loan', 'SME', 'corporate', 'commercial'],
            'auto': ['car loan', 'auto', 'vehicle'],
            'other': ['debt consolidation', 'refinance', 'education']
        }
        
        text_blocks = soup.find_all(['div', 'section', 'article'], class_=re.compile(r'product|loan|financing', re.I))
        
        for block in text_blocks[:10]:
            text = block.get_text().lower()
            
            for loan_type, keywords in loan_keywords.items():
                if any(kw in text for kw in keywords):
                    
                    rate_match = re.search(r'(\d+\.?\d*)\s*%', text)
                    amount_match = re.search(r'RM\s*([\d,]+)', text)
                    tenure_match = re.search(r'(\d+)\s*(?:year|tahun)', text)
                    
                    product = {
                        'company': bank['name'],
                        'loan_type': loan_type.upper(),
                        'product_name': self._clean_text(block.find(['h1', 'h2', 'h3', 'h4']).get_text() if block.find(['h1', 'h2', 'h3', 'h4']) else f"{loan_type} Loan"),
                        'required_doc': self._extract_documents(text),
                        'features': self._extract_features(block),
                        'benefits': self._extract_benefits(block),
                        'fees_charges': self._extract_fees(text),
                        'tenure': f"{tenure_match.group(1)} years" if tenure_match else "查询银行",
                        'rate': f"{rate_match.group(1)}% p.a." if rate_match else "查询银行",
                        'application_form_url': self._find_link(block, ['apply', 'application']),
                        'product_disclosure_url': self._find_link(block, ['pds', 'disclosure', 'product disclosure']),
                        'terms_conditions_url': self._find_link(block, ['terms', 'conditions', 't&c', 'tnc']),
                        'preferred_customer_type': self._extract_eligibility(text),
                        'institution_type': bank['type'],
                        'source_url': source_url,
                        'pulled_at': datetime.now().isoformat()
                    }
                    
                    products.append(product)
                    break
        
        return products[:5]
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        return ' '.join(text.split()).strip()
    
    def _extract_documents(self, text: str) -> str:
        """提取所需文件"""
        docs = []
        doc_keywords = ['MyKad', 'NRIC', 'IC', 'payslip', 'salary', 'EPF', 'bank statement', 'income']
        for keyword in doc_keywords:
            if keyword.lower() in text:
                docs.append(keyword)
        return ', '.join(docs) if docs else "请联系银行"
    
    def _extract_features(self, block) -> str:
        """提取特点"""
        features = []
        feature_keywords = ['flexible', 'fast', 'easy', 'competitive', 'low rate', 'no fee']
        text = block.get_text().lower()
        for kw in feature_keywords:
            if kw in text:
                features.append(kw.title())
        return ', '.join(features[:3]) if features else "查询银行"
    
    def _extract_benefits(self, block) -> str:
        """提取优势"""
        benefits = []
        ul_tags = block.find_all('ul')
        for ul in ul_tags:
            items = ul.find_all('li')
            benefits.extend([self._clean_text(li.get_text()) for li in items[:3]])
        return ' | '.join(benefits[:3]) if benefits else "查询银行"
    
    def _extract_fees(self, text: str) -> str:
        """提取费用"""
        fee_match = re.search(r'(?:fee|charge|stamp duty).*?(\d+\.?\d*%?)', text, re.I)
        return fee_match.group(0) if fee_match else "查询银行"
    
    def _extract_eligibility(self, text: str) -> str:
        """提取借贷人喜好"""
        conditions = []
        if 'monthly income' in text or 'rm' in text:
            income_match = re.search(r'RM\s*([\d,]+)', text)
            if income_match:
                conditions.append(f"Min income RM{income_match.group(1)}")
        if 'age' in text:
            conditions.append("Age requirements apply")
        if 'employed' in text or 'salary' in text:
            conditions.append("Salaried employees")
        return ', '.join(conditions) if conditions else "查询银行"
    
    def _find_link(self, block, keywords: List[str]) -> str:
        """查找相关链接"""
        links = block.find_all('a', href=True)
        for link in links:
            link_text = link.get_text().lower()
            href = link['href']
            if any(kw in link_text or kw in href.lower() for kw in keywords):
                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    return f"{block.find_parent().get('data-url', '')}{href}"
        return ""
    
    def scrape_top_banks(self, limit: int = 5) -> List[Dict[str, Any]]:
        """爬取前N家银行"""
        all_products = []
        
        for i, bank in enumerate(self.institutions[:limit], 1):
            logger.info(f"\n📍 进度: {i}/{limit}")
            products = self.scrape_bank(bank)
            all_products.extend(products)
            
            time.sleep(3)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎉 采集完成！共获取 {len(all_products)} 个产品")
        
        return all_products
    
    def export_to_csv(self, products: List[Dict[str, Any]], filename: str):
        """导出为CSV"""
        if not products:
            logger.warning("没有产品数据可导出")
            return
        
        fieldnames = [
            'company', 'loan_type', 'product_name', 'required_doc',
            'features', 'benefits', 'fees_charges', 'tenure', 'rate',
            'application_form_url', 'product_disclosure_url', 
            'terms_conditions_url', 'preferred_customer_type',
            'institution_type', 'source_url', 'pulled_at'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(products)
        
        logger.info(f"✅ 数据已导出到: {filename}")

malaysia_scraper = MalaysiaBankScraper()
