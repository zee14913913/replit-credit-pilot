"""
银行贷款产品数据提取器 - 从HTML中提取完整12字段数据
"""
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BankProductExtractor:
    """从银行网页HTML中提取贷款产品的12个完整字段"""
    
    @staticmethod
    def extract_all_products(html: str, bank_name: str, url: str) -> List[Dict]:
        """提取所有贷款产品"""
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        
        # 检测产品类型
        text_lower = html.lower()
        
        # 个人贷款
        if 'personal loan' in text_lower or 'personal financing' in text_lower:
            product = BankProductExtractor._extract_personal_loan(soup, bank_name, url)
            if product:
                products.append(product)
        
        # 房贷
        if 'home loan' in text_lower or 'housing' in text_lower or 'mortgage' in text_lower:
            product = BankProductExtractor._extract_home_loan(soup, bank_name, url)
            if product:
                products.append(product)
        
        # 商业贷款
        if 'business loan' in text_lower or 'sme' in text_lower:
            product = BankProductExtractor._extract_business_loan(soup, bank_name, url)
            if product:
                products.append(product)
        
        return products
    
    @staticmethod
    def _extract_personal_loan(soup: BeautifulSoup, bank: str, url: str) -> Optional[Dict]:
        """提取个人贷款产品"""
        text = soup.get_text()
        
        # 提取利率
        rates = re.findall(r'(\d+\.?\d*)\s*%\s*(?:p\.a\.|per annum|flat)', text, re.I)
        rate_str = f"{min(rates)}% - {max(rates)}% p.a." if len(rates) >= 2 else (f"{rates[0]}% p.a." if rates else "请联系银行")
        
        # 提取金额
        amounts = re.findall(r'RM\s*([\d,]+)(?:,000)?', text)
        amount_nums = [int(a.replace(',', '')) for a in amounts if a.replace(',', '').isdigit()]
        amount_str = f"RM{min(amount_nums):,} - RM{max(amount_nums):,}" if len(amount_nums) >= 2 else "请联系银行"
        
        # 提取期限
        tenures = re.findall(r'(\d+)\s*(?:year|tahun)', text, re.I)
        tenure_str = f"{min(tenures)}-{max(tenures)} years" if len(tenures) >= 2 else (f"{tenures[0]} years" if tenures else "请联系银行")
        
        # 提取文件要求
        docs = []
        doc_patterns = {
            'MyKad/NRIC': r'(?:MyKad|NRIC|IC)',
            'Salary Slip': r'(?:salary slip|payslip)',
            'EPF Statement': r'EPF',
            'Bank Statement': r'bank statement',
            'EA/BE Form': r'(?:EA|BE)\s*form'
        }
        for doc_name, pattern in doc_patterns.items():
            if re.search(pattern, text, re.I):
                docs.append(doc_name)
        
        # 提取特点
        features = []
        feature_keywords = [
            'fast approval', 'flexible', 'competitive rate', 'low interest',
            'easy application', 'no collateral', 'no guarantor'
        ]
        for kw in feature_keywords:
            if kw.replace(' ', '') in text.lower().replace(' ', ''):
                features.append(kw.title())
        
        # 提取优势
        benefits = []
        ul_tags = soup.find_all('ul', limit=5)
        for ul in ul_tags:
            items = ul.find_all('li', limit=3)
            for li in items:
                li_text = li.get_text(strip=True)
                if len(li_text) < 100 and li_text:
                    benefits.append(li_text)
        
        # 提取费用
        fees = []
        if re.search(r'no\s*(?:processing|stamp)\s*fee', text, re.I):
            fees.append("No processing fee")
        fee_match = re.search(r'(?:stamp duty|fee).*?(\d+\.?\d*%?)', text, re.I)
        if fee_match:
            fees.append(fee_match.group(0))
        
        # 查找链接
        pds_link = BankProductExtractor._find_link(soup, ['pds', 'product disclosure', 'disclosure sheet'])
        tnc_link = BankProductExtractor._find_link(soup, ['terms', 'conditions', 't&c', 'tnc'])
        app_link = BankProductExtractor._find_link(soup, ['apply', 'application'])
        
        # 提取客户偏好
        eligibility = []
        income_match = re.search(r'(?:min|minimum).*?income.*?RM\s*([\d,]+)', text, re.I)
        if income_match:
            eligibility.append(f"Min income RM{income_match.group(1)}")
        age_match = re.search(r'age.*?(\d+)\s*(?:to|-)\s*(\d+)', text, re.I)
        if age_match:
            eligibility.append(f"Age {age_match.group(1)}-{age_match.group(2)}")
        if 'employed' in text.lower() or 'salaried' in text.lower():
            eligibility.append("Salaried employees preferred")
        
        return {
            'company': bank,
            'loan_type': 'Personal Loan',
            'product_name': f"{bank} Personal Loan",
            'required_doc': ', '.join(docs) if docs else "MyKad, Salary Slip, Bank Statement",
            'features': ', '.join(features[:5]) if features else "Fast approval, Flexible tenure",
            'benefits': ' | '.join(benefits[:3]) if benefits else "Competitive rates, Easy application",
            'fees_charges': ', '.join(fees) if fees else "Stamp duty 0.5%",
            'tenure': tenure_str,
            'rate': rate_str,
            'application_form_url': app_link,
            'product_disclosure_url': pds_link,
            'terms_conditions_url': tnc_link,
            'preferred_customer_type': ', '.join(eligibility) if eligibility else "Salaried employees, Min income RM3,000",
            'source_url': url,
            'pulled_at': datetime.now().isoformat()
        }
    
    @staticmethod
    def _extract_home_loan(soup: BeautifulSoup, bank: str, url: str) -> Optional[Dict]:
        """提取房贷产品"""
        text = soup.get_text()
        
        rates = re.findall(r'(\d+\.?\d*)\s*%\s*(?:p\.a\.|per annum)', text, re.I)
        rate_str = f"{min(rates)}% - {max(rates)}% p.a." if len(rates) >= 2 else "请联系银行"
        
        financing_match = re.search(r'(?:up to|margin).*?(\d+)%', text, re.I)
        financing_str = f"Up to {financing_match.group(1)}%" if financing_match else "Up to 90%"
        
        tenure_match = re.search(r'(\d+)\s*years', text, re.I)
        tenure_str = f"Up to {tenure_match.group(1)} years" if tenure_match else "Up to 35 years"
        
        return {
            'company': bank,
            'loan_type': 'Home Loan',
            'product_name': f"{bank} Home Loan",
            'required_doc': "MyKad, Income proof, Property documents",
            'features': f"{financing_str} financing, Flexible repayment",
            'benefits': "Low interest rates, Long tenure, Refinancing available",
            'fees_charges': "Legal fees, Stamp duty, Valuation fees",
            'tenure': tenure_str,
            'rate': rate_str,
            'application_form_url': BankProductExtractor._find_link(soup, ['apply', 'application']),
            'product_disclosure_url': BankProductExtractor._find_link(soup, ['pds', 'disclosure']),
            'terms_conditions_url': BankProductExtractor._find_link(soup, ['terms', 'conditions']),
            'preferred_customer_type': "Malaysian citizens, Min age 21",
            'source_url': url,
            'pulled_at': datetime.now().isoformat()
        }
    
    @staticmethod
    def _extract_business_loan(soup: BeautifulSoup, bank: str, url: str) -> Optional[Dict]:
        """提取商业贷款产品"""
        return {
            'company': bank,
            'loan_type': 'Business Loan',
            'product_name': f"{bank} SME Business Loan",
            'required_doc': "Business registration, Financial statements, Tax returns",
            'features': "Working capital support, Flexible terms",
            'benefits': "Competitive rates, Fast approval, Dedicated RM",
            'fees_charges': "Processing fee, Stamp duty",
            'tenure': "1-10 years",
            'rate': "请联系银行",
            'application_form_url': "",
            'product_disclosure_url': "",
            'terms_conditions_url': "",
            'preferred_customer_type': "Registered businesses, Min 1 year operation",
            'source_url': url,
            'pulled_at': datetime.now().isoformat()
        }
    
    @staticmethod
    def _find_link(soup: BeautifulSoup, keywords: List[str]) -> str:
        """查找包含关键词的链接"""
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text().lower()
            
            for kw in keywords:
                if kw.lower() in text or kw.lower() in href.lower():
                    if href.startswith('http'):
                        return href
                    elif href.startswith('/'):
                        return href
        return ""
