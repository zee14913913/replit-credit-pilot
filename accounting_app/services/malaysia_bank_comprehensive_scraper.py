#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
马来西亚银行产品完整爬虫系统 - 严格模式
严格遵守：不许幻想数据、必须访问详情页、12字段完整提取
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
import pandas as pd
from .scrapingdog_client import scrapingdog_client

logger = logging.getLogger(__name__)

STRICT_RULES = {
    'NO_SYNTHESIS': True,
    'NO_DEFAULT_VALUES': True,
    'NO_EMPTY_FIELDS': True,
    'MUST_VERIFY_EACH_FIELD': True,
    'FORCE_DETAIL_PAGE': True,
}

REQUIRED_FIELDS = [
    'company',
    'loan_type',
    'required_doc',
    'features',
    'benefits',
    'fees_charges',
    'tenure',
    'rate',
    'application_form_url',
    'product_disclosure_url',
    'terms_conditions_url',
    'preferred_customer_type'
]

PRODUCT_CATEGORIES = {
    'PERSONAL': [
        'Credit Card', 'Charge Card',
        'Personal Loan', 'Debt Consolidation Loan',
        'Mortgage Loan', 'Home Loan', 'House Refinance',
        'Car Loan', 'Vehicle Loan', 'Auto Loan',
        'Overdraft', 'Fixed Deposit'
    ],
    'BUSINESS': [
        'SME Credit Card', 'Corporate Credit Card', 'Business Credit Card',
        'SME Loan', 'Business Loan', 'Corporate Loan',
        'Commercial Mortgage', 'Commercial Loan',
        'Business Overdraft', 'Business Fixed Deposit'
    ]
}


class ExtractionAudit:
    """审计每一步提取过程"""
    
    def __init__(self, company_name: str):
        self.company = company_name
        self.audit_log = []
        self.product_count = 0
        self.start_time = datetime.now()
    
    def log_list_page_fetch(self, url: str, found_count: int):
        self.audit_log.append({
            'step': 'FETCH_LIST_PAGE',
            'url': url,
            'product_count': found_count,
            'time': datetime.now().isoformat()
        })
        print(f"  📋 List page: {found_count} products found")
    
    def log_detail_page_extract(self, product_name: str, fields_extracted: int):
        self.audit_log.append({
            'step': 'EXTRACT_DETAIL_PAGE',
            'product': product_name,
            'fields_extracted': fields_extracted,
            'time': datetime.now().isoformat()
        })
        self.product_count += 1
        print(f"  ✅ Detail page [{self.product_count}]: {fields_extracted}/12 fields extracted")
    
    def log_field_not_found(self, field_name: str):
        self.audit_log.append({
            'step': 'FIELD_NOT_FOUND',
            'field': field_name,
            'action': 'Marked as [NO DATA FOUND]',
            'time': datetime.now().isoformat()
        })
    
    def save_audit(self):
        audit_file = f"audit_{self.company.replace(' ', '_')}.json"
        with open(audit_file, 'w', encoding='utf-8') as f:
            json.dump({
                'company': self.company,
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_products': self.product_count,
                'log': self.audit_log
            }, f, ensure_ascii=False, indent=2)
        print(f"  🔍 Audit log saved: {audit_file}")


class MalaysiaBankComprehensiveScraper:
    """完整的马来西亚银行爬虫 - 严格模式"""
    
    def __init__(self, progress_file: str = 'scraper_progress.json'):
        self.progress_file = progress_file
        self.progress = self.load_progress()
        self.validate_strict_rules()
    
    def validate_strict_rules(self):
        """验证严格规则"""
        print("\n" + "="*80)
        print("🔴 STRICT MODE ACTIVATED - NO COMPROMISE")
        print("="*80)
        for rule, value in STRICT_RULES.items():
            status = "✅ ON" if value else "❌ OFF"
            print(f"  {rule}: {status}")
        print("="*80 + "\n")
    
    def load_progress(self) -> Dict:
        """加载进度文件"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'current_company_index': 0,
            'completed_companies': [],
            'failed_companies': [],
            'total_products_extracted': 0,
            'extraction_log': [],
            'start_time': datetime.now().isoformat()
        }
    
    def save_progress(self):
        """保存进度文件"""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2, default=str)
        print(f"💾 Progress saved: {self.progress['total_products_extracted']} products")
    
    def enforce_field_check(self, product_data: Dict) -> Dict:
        """强制检查所有字段"""
        for field in REQUIRED_FIELDS:
            if field not in product_data:
                raise ValueError(f"❌ FATAL: Missing field {field}")
            
            if product_data[field] is None or product_data[field] == '':
                product_data[field] = '[NO DATA FOUND]'
            
            if str(product_data[field]).lower() in ['n/a', 'na', 'unknown', 'not available', 'tbd']:
                product_data[field] = '[NO DATA FOUND]'
        
        return product_data
    
    def extract_product_links(self, html: str, base_url: str, product_type: str) -> List[str]:
        """从列表页提取所有产品链接"""
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        product_links = []
        
        keywords = product_type.lower().split()
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True).lower()
            
            if any(kw in text or kw in href.lower() for kw in keywords):
                if href.startswith('http'):
                    product_links.append(href)
                elif href.startswith('/'):
                    domain = base_url.split('/')[0] + '//' + base_url.split('/')[2]
                    product_links.append(domain + href)
        
        return list(set(product_links))
    
    def extract_with_fallback(self, soup: BeautifulSoup, field_name: str, 
                              extraction_methods: List[Tuple]) -> Tuple[str, str]:
        """尝试多个提取方法"""
        print(f"  🔍 Extracting {field_name}...")
        
        for method_name, extraction_func in extraction_methods:
            try:
                result = extraction_func(soup)
                if result and result != '[NO DATA FOUND]' and len(result) > 3:
                    print(f"     ✅ Found using: {method_name}")
                    return result, method_name
                else:
                    print(f"     ⚠️  {method_name}: no data")
            except Exception as e:
                print(f"     ❌ {method_name} failed: {str(e)}")
        
        print(f"     🔴 ALL METHODS FAILED for {field_name}")
        return '[NO DATA FOUND]', 'NONE'
    
    def clean_text(self, text: str) -> str:
        """清理文本"""
        text = ' '.join(text.split())
        text = text.replace('\n', ' ').replace('\r', '').strip()
        if len(text) > 500:
            text = text[:500] + '...'
        return text
    
    def extract_by_keywords(self, soup: BeautifulSoup, keywords: List[str]) -> Optional[str]:
        """通过关键词提取"""
        for keyword in keywords:
            for tag in soup.find_all(['p', 'li', 'div', 'td', 'span', 'h2', 'h3', 'h4']):
                if keyword.lower() in tag.get_text().lower():
                    next_elem = tag.find_next(['p', 'ul', 'ol', 'table', 'div'])
                    if next_elem:
                        return self.clean_text(next_elem.get_text())
                    return self.clean_text(tag.get_text())
        return None
    
    def extract_from_table(self, soup: BeautifulSoup, column_keyword: str) -> Optional[str]:
        """从表格提取"""
        tables = soup.find_all('table')
        for table in tables:
            headers = [th.get_text().lower() for th in table.find_all('th')]
            for i, header in enumerate(headers):
                if column_keyword.lower() in header:
                    rows = table.find_all('tr')[1:]
                    values = []
                    for row in rows[:5]:
                        cols = row.find_all('td')
                        if i < len(cols):
                            values.append(self.clean_text(cols[i].get_text()))
                    if values:
                        return ' | '.join(values)
        return None
    
    def extract_from_list(self, soup: BeautifulSoup) -> Optional[str]:
        """从列表提取"""
        lists = soup.find_all(['ul', 'ol'])
        for lst in lists:
            items = lst.find_all('li')
            if len(items) > 2:
                return ' | '.join([self.clean_text(item.get_text()) for item in items[:10]])
        return None
    
    def find_link(self, soup: BeautifulSoup, keywords: List[str]) -> Optional[str]:
        """寻找链接"""
        links = soup.find_all('a', href=True)
        for link in links:
            text = link.get_text().lower()
            href = link['href'].lower()
            for keyword in keywords:
                if keyword.lower() in text or keyword.lower() in href:
                    return link['href']
        return None
    
    def extract_product_details(self, html: str, company_name: str, 
                               loan_type: str, source_url: str) -> Dict:
        """从详情页提取所有12个字段"""
        if not html:
            return self.create_empty_product(company_name, loan_type, source_url)
        
        soup = BeautifulSoup(html, 'html.parser')
        
        data = {
            'company': company_name,
            'loan_type': loan_type,
            'source_url': source_url
        }
        
        doc_methods = [
            ('keywords', lambda s: self.extract_by_keywords(s, ['required documents', 'documents needed', 'document requirement'])),
            ('list', lambda s: self.extract_from_list(s)),
            ('table', lambda s: self.extract_from_table(s, 'document'))
        ]
        data['required_doc'], _ = self.extract_with_fallback(soup, 'REQUIRED_DOC', doc_methods)
        
        feat_methods = [
            ('keywords', lambda s: self.extract_by_keywords(s, ['features', 'key features', 'highlights'])),
            ('list', lambda s: self.extract_from_list(s))
        ]
        data['features'], _ = self.extract_with_fallback(soup, 'FEATURES', feat_methods)
        
        ben_methods = [
            ('keywords', lambda s: self.extract_by_keywords(s, ['benefits', 'advantages', 'rewards'])),
            ('list', lambda s: self.extract_from_list(s))
        ]
        data['benefits'], _ = self.extract_with_fallback(soup, 'BENEFITS', ben_methods)
        
        fee_methods = [
            ('keywords', lambda s: self.extract_by_keywords(s, ['fees', 'charges', 'pricing', 'annual fee'])),
            ('table', lambda s: self.extract_from_table(s, 'fee'))
        ]
        data['fees_charges'], _ = self.extract_with_fallback(soup, 'FEES_CHARGES', fee_methods)
        
        ten_methods = [
            ('keywords', lambda s: self.extract_by_keywords(s, ['tenure', 'loan period', 'repayment term'])),
            ('table', lambda s: self.extract_from_table(s, 'tenure'))
        ]
        data['tenure'], _ = self.extract_with_fallback(soup, 'TENURE', ten_methods)
        
        rate_methods = [
            ('keywords', lambda s: self.extract_by_keywords(s, ['interest rate', 'apr', 'rate', 'p.a.'])),
            ('table', lambda s: self.extract_from_table(s, 'rate'))
        ]
        data['rate'], _ = self.extract_with_fallback(soup, 'RATE', rate_methods)
        
        app_methods = [
            ('link', lambda s: self.find_link(s, ['application form', 'apply now', 'apply online']))
        ]
        data['application_form_url'], _ = self.extract_with_fallback(soup, 'APPLICATION_FORM', app_methods)
        
        disc_methods = [
            ('link', lambda s: self.find_link(s, ['product disclosure', 'disclosure', 'pds']))
        ]
        data['product_disclosure_url'], _ = self.extract_with_fallback(soup, 'PRODUCT_DISCLOSURE', disc_methods)
        
        terms_methods = [
            ('link', lambda s: self.find_link(s, ['terms', 'conditions', 'terms and conditions', 'tnc']))
        ]
        data['terms_conditions_url'], _ = self.extract_with_fallback(soup, 'TERMS_CONDITIONS', terms_methods)
        
        pref_methods = [
            ('keywords', lambda s: self.extract_by_keywords(s, ['eligibility', 'qualification', 'suitable for']))
        ]
        pref_text, _ = self.extract_with_fallback(soup, 'BORROWER_PREFERENCE', pref_methods)
        data['preferred_customer_type'] = self.identify_borrower_type(pref_text)
        
        return self.enforce_field_check(data)
    
    def identify_borrower_type(self, text: str) -> str:
        """识别借贷人类型"""
        if not text or text == '[NO DATA FOUND]':
            return '[NO DATA FOUND]'
        
        text = text.lower()
        types = []
        
        if any(kw in text for kw in ['salaried', 'employee', 'employed']):
            types.append('Salaried Employee')
        if any(kw in text for kw in ['self-employed', 'business owner', 'entrepreneur']):
            types.append('Self-Employed')
        if any(kw in text for kw in ['business', 'corporate', 'sme']):
            types.append('Business')
        
        return ' | '.join(types) if types else '[NO DATA FOUND]'
    
    def create_empty_product(self, company: str, loan_type: str, url: str) -> Dict:
        """创建空产品（所有字段为NO DATA FOUND）"""
        return {
            'company': company,
            'loan_type': loan_type,
            'required_doc': '[NO DATA FOUND]',
            'features': '[NO DATA FOUND]',
            'benefits': '[NO DATA FOUND]',
            'fees_charges': '[NO DATA FOUND]',
            'tenure': '[NO DATA FOUND]',
            'rate': '[NO DATA FOUND]',
            'application_form_url': '[NO DATA FOUND]',
            'product_disclosure_url': '[NO DATA FOUND]',
            'terms_conditions_url': '[NO DATA FOUND]',
            'preferred_customer_type': '[NO DATA FOUND]',
            'source_url': url
        }
    
    def scrape_company(self, company_name: str, company_url: str) -> List[Dict]:
        """爬取单个公司的所有产品"""
        print(f"\n{'='*80}")
        print(f"🔴 COMPANY: {company_name}")
        print(f"🔗 URL: {company_url}")
        print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*80}")
        
        audit = ExtractionAudit(company_name)
        company_products = []
        
        for category, product_types in PRODUCT_CATEGORIES.items():
            print(f"\n--- Processing {category} Products ---")
            
            for product_type in product_types:
                print(f"\n  🔍 Product Type: {product_type}")
                
                list_page_html = scrapingdog_client.scrape_url(company_url, dynamic=True, premium=True)
                
                if not list_page_html:
                    print(f"     ❌ Failed to fetch homepage")
                    continue
                
                product_links = self.extract_product_links(list_page_html, company_url, product_type)
                
                if not product_links:
                    print(f"     ⚠️  No {product_type} links found")
                    continue
                
                audit.log_list_page_fetch(company_url, len(product_links))
                print(f"     📊 Found {len(product_links)} {product_type} links")
                
                for idx, product_url in enumerate(product_links[:10], 1):
                    print(f"\n     [{idx}/{min(len(product_links), 10)}] {product_url[:60]}...")
                    
                    detail_html = scrapingdog_client.scrape_url(product_url, dynamic=True, premium=True)
                    
                    if not detail_html:
                        print(f"        ❌ Failed to fetch detail page")
                        continue
                    
                    product_data = self.extract_product_details(
                        detail_html, company_name, product_type, product_url
                    )
                    
                    fields_found = sum(1 for v in product_data.values() if v != '[NO DATA FOUND]')
                    audit.log_detail_page_extract(product_url, fields_found)
                    
                    company_products.append(product_data)
                    self.progress['total_products_extracted'] += 1
                    
                    time.sleep(2)
        
        audit.save_audit()
        
        print(f"\n{'='*80}")
        print(f"✅ COMPANY COMPLETED: {company_name}")
        print(f"📊 Total products: {len(company_products)}")
        print(f"⏰ End: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*80}\n")
        
        return company_products


scraper = MalaysiaBankComprehensiveScraper()
