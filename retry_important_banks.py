"""
重新爬取重要银行 - 使用增强版智能爬虫
专门针对Maybank、CIMB、Public Bank等大型银行
"""
import sys
sys.path.insert(0, '/home/runner/workspace')

import logging
import sqlite3
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from accounting_app.services.enhanced_bank_scraper import enhanced_scraper

# 重要银行列表（之前失败的）
IMPORTANT_BANKS = [
    # 商业银行 (Top 10)
    {"name": "Malayan Banking Berhad (Maybank)", "website": "https://www.maybank2u.com.my", "type": "commercial"},
    {"name": "CIMB Bank Berhad", "website": "https://www.cimb.com.my", "type": "commercial"},
    {"name": "Public Bank Berhad", "website": "https://www.pbebank.com", "type": "commercial"},
    {"name": "RHB Bank Berhad", "website": "https://www.rhbgroup.com", "type": "commercial"},
    {"name": "Hong Leong Bank Berhad", "website": "https://www.hlb.com.my", "type": "commercial"},
    {"name": "AmBank (M) Berhad", "website": "https://www.ambank.com.my", "type": "commercial"},
    {"name": "Alliance Bank Malaysia Berhad", "website": "https://www.alliancebank.com.my", "type": "commercial"},
    {"name": "Affin Bank Berhad", "website": "https://www.affinbank.com.my", "type": "commercial"},
    {"name": "United Overseas Bank (Malaysia) Bhd", "website": "https://www.uob.com.my", "type": "commercial"},
    
    # 伊斯兰银行 (Top 5)
    {"name": "Maybank Islamic Berhad", "website": "https://www.maybank2u.com.my/islamic", "type": "islamic"},
    {"name": "CIMB Islamic Bank Berhad", "website": "https://www.cimbislamic.com", "type": "islamic"},
    {"name": "Bank Islam Malaysia Berhad", "website": "https://www.bankislam.com", "type": "islamic"},
    {"name": "Public Islamic Bank Berhad", "website": "https://www.pbebank.com/islamic", "type": "islamic"},
    {"name": "RHB Islamic Bank Berhad", "website": "https://www.rhbgroup.com/islamic", "type": "islamic"},
    
    # 数字银行
    {"name": "GX Bank Berhad", "website": "https://www.gxbank.my", "type": "digital"},
    {"name": "Boost Bank Berhad", "website": "https://www.boostbank.com", "type": "digital"},
]

DB_PATH = "/home/runner/loans.db"


def scrape_single_bank(bank: dict) -> list:
    """爬取单个银行"""
    try:
        products = enhanced_scraper.scrape_bank_comprehensive(
            bank_name=bank['name'],
            website=bank['website'],
            institution_type=bank['type']
        )
        return products
    except Exception as e:
        logger.error(f"❌ {bank['name']} 爬取失败: {e}")
        return []


def main():
    """主流程"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("🚀 重新爬取重要银行 - 使用增强版智能爬虫")
    logger.info("=" * 80)
    logger.info(f"目标银行: {len(IMPORTANT_BANKS)} 家")
    logger.info("")
    
    all_products = []
    
    # 并发爬取
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(scrape_single_bank, bank): bank
            for bank in IMPORTANT_BANKS
        }
        
        completed = 0
        for future in as_completed(futures):
            bank = futures[future]
            try:
                products = future.result()
                if products:
                    all_products.extend(products)
                    logger.info(f"✅ {bank['name']}: {len(products)} 个产品")
                else:
                    logger.warning(f"⚠️ {bank['name']}: 未找到产品")
                
                completed += 1
                logger.info(f"📊 进度: {completed}/{len(IMPORTANT_BANKS)}")
                logger.info("")
                
            except Exception as e:
                logger.error(f"❌ {bank['name']} 处理失败: {e}")
    
    # 保存到数据库
    if all_products:
        logger.info("=" * 80)
        logger.info("💾 保存到数据库...")
        logger.info("=" * 80)
        
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        
        # 追加到现有数据（不删除）
        insert_sql = """
            INSERT INTO loan_products_detailed(
                company, loan_type, product_name, required_doc, features, benefits,
                fees_charges, tenure, rate, application_form_url, product_disclosure_url,
                terms_conditions_url, preferred_customer_type, institution_type,
                source_url, pulled_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        timestamp = datetime.now().isoformat()
        items = [
            (
                p['company'], p['loan_type'], p['product_name'], p['required_doc'],
                p['features'], p['benefits'], p['fees_charges'], p['tenure'],
                p['rate'], p.get('application_form_url'), p.get('product_disclosure_url'),
                p.get('terms_conditions_url'), p['preferred_customer_type'],
                p['institution_type'], p.get('source_url'), timestamp
            )
            for p in all_products
        ]
        
        cur.executemany(insert_sql, items)
        con.commit()
        con.close()
        
        logger.info(f"✅ 成功追加 {len(all_products)} 个新产品")
        
        # 统计
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM loan_products_detailed")
        total = cur.fetchone()[0]
        con.close()
        
        logger.info(f"📊 数据库总计: {total} 个产品")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("🎉 重新爬取完成！")
    logger.info("=" * 80)
    logger.info("")


if __name__ == '__main__':
    main()
