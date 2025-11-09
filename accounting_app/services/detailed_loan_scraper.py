"""
增强版贷款爬虫 - 采集12个详细字段
专门设计用于提取完整的贷款产品信息
"""
import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time

logger = logging.getLogger(__name__)


class DetailedLoanScraper:
    """
    增强版爬虫：采集12个详细字段
    
    字段清单：
    1. COMPANY (公司/金融机构)
    2. LOAN TYPE (贷款类型)
    3. REQUIRED DOC (所需文件)
    4. FEATURES (特点)
    5. BENEFITS (优势)
    6. FEES & CHARGES (费用与收费)
    7. TENURE (期限)
    8. RATE (利率)
    9. APPLICATION FORM (申请表链接)
    10. PRODUCT DISCLOSURE (产品披露文件链接)
    11. TERMS & CONDITIONS (条款与条件链接)
    12. 放贷方对于借贷人的喜好
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_rate(self, text: str) -> Optional[str]:
        """提取利率信息"""
        if not text:
            return None
        
        # 匹配各种利率格式
        patterns = [
            r'(\d+\.?\d*)%\s*(p\.a\.|per\s+annum)?',  # 6.88% p.a.
            r'(BR|BLR|SBR)\s*[\+\-]\s*(\d+\.?\d*)%?',  # BR + 2.5%
            r'from\s+(\d+\.?\d*)%',                     # from 3.5%
            r'starting\s+(\d+\.?\d*)%',                 # starting 4.0%
        ]
        
        for pattern in patterns:
            match = re.search(pattern, str(text), re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "Contact Bank"
    
    def extract_tenure(self, text: str) -> Optional[str]:
        """提取贷款期限"""
        if not text:
            return None
        
        patterns = [
            r'(\d+)\s*(years?|tahun)',              # 35 years
            r'up\s+to\s+(\d+)\s*(years?|months?)',  # up to 35 years
            r'(\d+)\s*-\s*(\d+)\s*(years?)',        # 5-35 years
        ]
        
        for pattern in patterns:
            match = re.search(pattern, str(text), re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "Contact Bank"
    
    def extract_documents(self, soup: BeautifulSoup) -> str:
        """
        提取所需文件列表
        常见关键词：documents required, documentation, supporting documents
        """
        doc_keywords = [
            'documents? required',
            'documentation',
            'supporting documents?',
            'required documents?',
            'dokumen diperlukan'
        ]
        
        documents = []
        
        # 查找文件相关章节
        for keyword in doc_keywords:
            sections = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            
            for section in sections:
                parent = section.find_parent(['div', 'section', 'ul', 'ol'])
                if parent:
                    # 提取列表项
                    items = parent.find_all('li')
                    for item in items[:10]:  # 限制最多10项
                        doc_text = item.get_text(strip=True)
                        if len(doc_text) > 5 and len(doc_text) < 200:
                            documents.append(doc_text)
        
        if documents:
            return " | ".join(documents[:5])  # 返回前5个最重要的文件
        
        return "请联系银行了解详情"
    
    def extract_features(self, soup: BeautifulSoup) -> str:
        """
        提取产品特点
        常见关键词：features, key features, highlights, what's included
        """
        feature_keywords = [
            'key features',
            'features',
            'highlights',
            'product features',
            'ciri-ciri utama'
        ]
        
        features = []
        
        for keyword in feature_keywords:
            sections = soup.find_all(['h2', 'h3', 'h4'], text=re.compile(keyword, re.IGNORECASE))
            
            for section in sections:
                parent = section.find_parent(['div', 'section'])
                if parent:
                    items = parent.find_all('li')
                    for item in items[:5]:
                        feature_text = item.get_text(strip=True)
                        if len(feature_text) > 10 and len(feature_text) < 200:
                            features.append(feature_text)
        
        if features:
            return " | ".join(features)
        
        return "请访问银行官网了解产品特点"
    
    def extract_benefits(self, soup: BeautifulSoup) -> str:
        """
        提取产品优势
        常见关键词：benefits, advantages, why choose
        """
        benefit_keywords = [
            'benefits',
            'advantages',
            'why choose',
            'kelebihan'
        ]
        
        benefits = []
        
        for keyword in benefit_keywords:
            sections = soup.find_all(['h2', 'h3', 'h4'], text=re.compile(keyword, re.IGNORECASE))
            
            for section in sections:
                parent = section.find_parent(['div', 'section'])
                if parent:
                    items = parent.find_all('li')
                    for item in items[:5]:
                        benefit_text = item.get_text(strip=True)
                        if len(benefit_text) > 10 and len(benefit_text) < 200:
                            benefits.append(benefit_text)
        
        if benefits:
            return " | ".join(benefits)
        
        return "请访问银行官网了解产品优势"
    
    def extract_fees(self, soup: BeautifulSoup) -> str:
        """
        提取费用与收费
        常见关键词：fees, charges, costs, fees and charges
        """
        fee_keywords = [
            'fees? and charges?',
            'fees?',
            'charges?',
            'costs?',
            'yuran'
        ]
        
        fees = []
        
        for keyword in fee_keywords:
            sections = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            
            for section in sections[:3]:
                parent = section.find_parent(['div', 'section', 'table', 'ul'])
                if parent:
                    # 提取表格或列表中的费用项
                    rows = parent.find_all(['tr', 'li'])
                    for row in rows[:8]:
                        fee_text = row.get_text(strip=True)
                        if any(kw in fee_text.lower() for kw in ['rm', 'fee', 'charge', '%']):
                            if len(fee_text) > 5 and len(fee_text) < 150:
                                fees.append(fee_text)
        
        if fees:
            return " | ".join(fees[:5])
        
        return "请联系银行了解费用详情"
    
    def find_pdf_links(self, soup: BeautifulSoup, keywords: List[str]) -> Optional[str]:
        """
        查找PDF文档链接
        用于：申请表、产品披露、条款与条件
        """
        for keyword in keywords:
            links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
            
            for link in links:
                link_text = link.get_text(strip=True).lower()
                href = link.get('href', '')
                
                if keyword.lower() in link_text or keyword.lower() in href.lower():
                    # 处理相对路径
                    if href.startswith('/'):
                        # 需要base_url，暂时返回相对路径
                        return href
                    return href
        
        return None
    
    def determine_preferred_customer(self, soup: BeautifulSoup, product_name: str) -> str:
        """
        判断放贷方对借贷人的喜好
        基于产品描述和特点分析
        """
        text = soup.get_text().lower()
        product_lower = product_name.lower()
        
        # 关键词匹配
        salaried_keywords = [
            'salaried', 'salary', 'employee', 'employed', 
            'fixed income', 'payslip', 'gaji', 'pekerja'
        ]
        
        business_keywords = [
            'business', 'self-employed', 'sme', 'entrepreneur',
            'self employed', 'perniagaan', 'usahawan'
        ]
        
        salaried_score = sum(1 for kw in salaried_keywords if kw in text)
        business_score = sum(1 for kw in business_keywords if kw in text or kw in product_lower)
        
        if business_score > salaried_score:
            return "企业客户 (Business/Self-Employed)"
        elif salaried_score > 0:
            return "打工族/固定收入客户 (Salaried/Fixed Income)"
        else:
            return "所有客户类型 (All Customer Types)"
    
    def scrape_product_details(
        self, 
        bank_name: str, 
        product_url: str, 
        loan_type: str,
        institution_type: str = "commercial"
    ) -> Dict[str, Any]:
        """
        爬取单个产品的完整12个字段
        
        Args:
            bank_name: 银行名称
            product_url: 产品页面URL
            loan_type: 贷款类型
            institution_type: 机构类型
        
        Returns:
            包含12个字段的字典
        """
        try:
            response = self.session.get(product_url, timeout=15)
            
            if response.status_code != 200:
                logger.warning(f"⚠️ {bank_name} 产品页面返回 {response.status_code}")
                return self._create_placeholder_product(bank_name, loan_type, product_url, institution_type)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取产品名称
            product_name = soup.find('h1')
            if product_name:
                product_name = product_name.get_text(strip=True)
            else:
                product_name = f"{bank_name} {loan_type} Loan"
            
            # 构建完整产品信息（12个字段）
            product = {
                'company': bank_name,                                          # 1
                'loan_type': loan_type,                                        # 2
                'product_name': product_name,
                'required_doc': self.extract_documents(soup),                  # 3
                'features': self.extract_features(soup),                       # 4
                'benefits': self.extract_benefits(soup),                       # 5
                'fees_charges': self.extract_fees(soup),                       # 6
                'tenure': self.extract_tenure(soup.get_text()),                # 7
                'rate': self.extract_rate(soup.get_text()),                    # 8
                'application_form_url': self.find_pdf_links(soup, ['application', 'apply']),      # 9
                'product_disclosure_url': self.find_pdf_links(soup, ['disclosure', 'pds']),       # 10
                'terms_conditions_url': self.find_pdf_links(soup, ['terms', 'conditions', 'tnc']), # 11
                'preferred_customer_type': self.determine_preferred_customer(soup, product_name),  # 12
                'institution_type': institution_type,
                'source_url': product_url,
                'pulled_at': datetime.now().isoformat()
            }
            
            logger.info(f"✅ {bank_name} - {product_name}: 详细信息已提取")
            return product
            
        except Exception as e:
            logger.error(f"❌ {bank_name} 产品详情提取失败: {e}")
            return self._create_placeholder_product(bank_name, loan_type, product_url, institution_type)
    
    def _create_placeholder_product(
        self, 
        bank_name: str, 
        loan_type: str, 
        url: str,
        institution_type: str
    ) -> Dict[str, Any]:
        """创建占位符产品（当爬取失败时）"""
        return {
            'company': bank_name,
            'loan_type': loan_type,
            'product_name': f"{bank_name} {loan_type} Loan",
            'required_doc': "请联系银行了解所需文件",
            'features': "请访问银行官网了解产品特点",
            'benefits': "请访问银行官网了解产品优势",
            'fees_charges': "请联系银行了解费用详情",
            'tenure': "Contact Bank",
            'rate': "Contact Bank",
            'application_form_url': None,
            'product_disclosure_url': None,
            'terms_conditions_url': None,
            'preferred_customer_type': "所有客户类型 (All Customer Types)",
            'institution_type': institution_type,
            'source_url': url,
            'pulled_at': datetime.now().isoformat()
        }


# 全局单例
detailed_scraper = DetailedLoanScraper()
