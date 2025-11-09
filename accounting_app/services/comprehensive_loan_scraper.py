"""
马来西亚68家金融机构完整贷款数据采集系统
支持7种贷款产品类型的自动化爬取
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
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class ComprehensiveLoanScraper:
    """68家金融机构完整爬虫系统"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # 加载金融机构配置
        config_path = os.path.join(
            os.path.dirname(__file__),
            '../data/malaysia_financial_institutions.json'
        )
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 汇总所有金融机构
        self.institutions = []
        for category in ['commercial_banks', 'islamic_banks', 'development_banks', 
                        'digital_banks', 'p2p_platforms', 'non_bank_credit']:
            self.institutions.extend(self.config.get(category, []))
        
        self.loan_products = self.config['loan_products']
        
        logger.info(f"✅ 加载了 {len(self.institutions)} 家金融机构")
        logger.info(f"✅ 支持 {len(self.loan_products)} 种贷款产品类型")
    
    def extract_rate(self, text: str) -> Optional[str]:
        """从文本中提取利率"""
        if not text:
            return None
        # 匹配百分比格式：6.88%, 3.5%, etc.
        match = re.search(r'(\d+\.?\d*)%', str(text))
        if match:
            return match.group(0)
        # 匹配基准利率格式：BR + 2.5%, BLR - 1.0%, etc.
        match = re.search(r'(BR|BLR|SBR)\s*[\+\-]\s*(\d+\.?\d*)%?', str(text), re.IGNORECASE)
        if match:
            return f"{match.group(1)} {match.group(2)}%"
        return None
    
    def scrape_institution(self, institution: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        爬取单个金融机构的所有贷款产品
        
        Args:
            institution: {
                'code': 'maybank',
                'name': 'Malayan Banking Berhad',
                'website': 'https://www.maybank.com.my',
                'type': 'commercial'
            }
        
        Returns:
            [
                {
                    'source': 'maybank',
                    'bank': 'Maybank',
                    'product': 'Home Loan Flexi',
                    'type': 'HOME',
                    'rate': '3.75%',
                    'summary': '...',
                    'url': 'https://...',
                    'institution_type': 'commercial',
                    'pulled_at': '2025-11-09T...'
                },
                ...
            ]
        """
        products = []
        
        try:
            base_url = institution['website']
            
            # 常见贷款产品页面路径模式
            loan_paths = [
                '/personal/loans',
                '/loans',
                '/financing',
                '/products/loans',
                '/en/personal/loans',
                '/loan-products',
                '/personal-loan',
                '/home-loan',
                '/business-loan',
            ]
            
            for path in loan_paths:
                try:
                    url = f"{base_url}{path}"
                    response = self.session.get(url, timeout=10, allow_redirects=True)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # 查找贷款产品标题
                        titles = soup.find_all(['h1', 'h2', 'h3', 'h4'], 
                                               string=re.compile(r'loan|financing|kredit', re.IGNORECASE))
                        
                        for title in titles[:10]:  # 限制每个页面最多10个产品
                            product_name = title.get_text(strip=True)
                            
                            # 判断贷款类型
                            product_type = self.classify_loan_type(product_name)
                            
                            # 查找利率信息
                            parent = title.find_parent(['div', 'section', 'article'])
                            rate_text = None
                            if parent:
                                rate_elem = parent.find(text=re.compile(r'\d+\.?\d*%'))
                                rate_text = self.extract_rate(rate_elem) if rate_elem else None
                            
                            product = {
                                'source': institution['code'],
                                'bank': institution['name'],
                                'product': product_name,
                                'type': product_type,
                                'rate': rate_text or 'Contact Bank',
                                'summary': f"请访问 {institution['name']} 官网了解详情",
                                'url': url,
                                'institution_type': institution['type'],
                                'pulled_at': datetime.now().isoformat()
                            }
                            products.append(product)
                        
                        if len(products) > 0:
                            logger.info(f"✅ {institution['name']}: 找到 {len(products)} 个产品")
                            break  # 找到产品后跳出路径循环
                    
                    time.sleep(0.5)  # 避免请求过快
                    
                except Exception as e:
                    logger.debug(f"⚠️ {institution['name']} 路径 {path} 失败: {e}")
                    continue
            
            if len(products) == 0:
                logger.warning(f"⚠️ {institution['name']}: 未找到贷款产品")
            
        except Exception as e:
            logger.error(f"❌ {institution['name']} 整体爬取失败: {e}")
        
        return products
    
    def classify_loan_type(self, product_name: str) -> str:
        """根据产品名称分类贷款类型"""
        product_lower = product_name.lower()
        
        # 房贷
        if any(kw in product_lower for kw in ['home', 'housing', 'mortgage', 'property', 'rumah']):
            return 'HOME'
        
        # 再融资
        if any(kw in product_lower for kw in ['refinance', 'refin', 'refinancing']):
            return 'REFINANCE'
        
        # 债务整合
        if any(kw in product_lower for kw in ['debt consolidation', 'consolidation', 'debt']):
            return 'DEBT_CONSOLIDATION'
        
        # 企业/SME贷款
        if any(kw in product_lower for kw in ['business', 'sme', 'commercial', 'enterprise', 'perniagaan']):
            return 'BUSINESS'
        
        # 个人贷款（默认）
        if any(kw in product_lower for kw in ['personal', 'peribadi', 'cash']):
            return 'PERSONAL'
        
        # 其他
        return 'OTHER'
    
    def scrape_all_institutions(self, max_workers: int = 10) -> List[Dict[str, Any]]:
        """
        并发爬取所有68家金融机构
        
        Args:
            max_workers: 并发线程数（默认10）
        
        Returns:
            所有爬取到的贷款产品列表
        """
        all_products = []
        
        logger.info(f"🚀 开始并发爬取 {len(self.institutions)} 家金融机构...")
        logger.info(f"⚙️ 使用 {max_workers} 个并发线程")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_inst = {
                executor.submit(self.scrape_institution, inst): inst 
                for inst in self.institutions
            }
            
            # 收集结果
            completed = 0
            for future in as_completed(future_to_inst):
                inst = future_to_inst[future]
                try:
                    products = future.result()
                    all_products.extend(products)
                    completed += 1
                    
                    if completed % 10 == 0:
                        logger.info(f"📊 进度: {completed}/{len(self.institutions)} 家机构已完成")
                    
                except Exception as e:
                    logger.error(f"❌ {inst['name']} 处理失败: {e}")
        
        logger.info(f"🎉 爬取完成！共获取 {len(all_products)} 个贷款产品")
        
        # 按银行类型分组统计
        stats = {}
        for product in all_products:
            inst_type = product['institution_type']
            stats[inst_type] = stats.get(inst_type, 0) + 1
        
        logger.info("📈 按机构类型统计:")
        for inst_type, count in stats.items():
            logger.info(f"  - {inst_type}: {count} 个产品")
        
        return all_products
    
    def scrape_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        按机构类别爬取（用于分批测试）
        
        Args:
            category: 'commercial_banks', 'islamic_banks', 'digital_banks', etc.
        """
        institutions = self.config.get(category, [])
        logger.info(f"🎯 爬取类别: {category} ({len(institutions)} 家机构)")
        
        products = []
        for inst in institutions:
            inst_products = self.scrape_institution(inst)
            products.extend(inst_products)
            time.sleep(1)  # 避免请求过快
        
        return products
    
    def validate_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证和清洗产品数据"""
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
                
                # 确保有URL
                if not product.get('url'):
                    product['url'] = 'N/A'
                
                valid_products.append(product)
            else:
                missing = [f for f in required_fields if not product.get(f)]
                logger.warning(f"⚠️ 产品数据不完整（缺少 {missing}），跳过: {product.get('product', 'Unknown')}")
        
        logger.info(f"✅ 验证通过 {len(valid_products)}/{len(products)} 个产品")
        return valid_products
    
    def export_to_csv(self, products: List[Dict[str, Any]], filename: str = 'malaysia_loans.csv'):
        """导出为CSV文件"""
        import csv
        
        if not products:
            logger.warning("⚠️ 没有产品可导出")
            return
        
        fieldnames = list(products[0].keys())
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(products)
        
        logger.info(f"✅ 已导出 {len(products)} 个产品到 {filename}")


# 全局单例
comprehensive_scraper = ComprehensiveLoanScraper()
