"""
启动真实贷款数据采集
从68家马来西亚金融机构获取真实数据
包含12个详细字段
"""
import sys
import os
sys.path.insert(0, '/home/runner/workspace')

import sqlite3
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入采集模块
from accounting_app.services.bnm_api_client import bnm_client
from accounting_app.services.comprehensive_loan_scraper import comprehensive_scraper
from accounting_app.services.detailed_loan_scraper import detailed_scraper

DB_PATH = os.getenv("LOANS_DB_PATH", "/home/runner/loans.db")


def init_database():
    """初始化数据库（12个字段）"""
    logger.info("📊 初始化数据库...")
    
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    # 创建详细产品表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS loan_products_detailed(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            institution_type TEXT,
            source_url TEXT,
            pulled_at TEXT
        )
    """)
    
    con.commit()
    con.close()
    logger.info("✅ 数据库初始化完成")


def collect_bnm_rates():
    """采集BNM官方利率"""
    logger.info("=" * 80)
    logger.info("📊 第1步：采集BNM官方利率数据")
    logger.info("=" * 80)
    
    try:
        rates = bnm_client.get_all_rates()
        logger.info(f"✅ BNM数据采集成功")
        logger.info(f"   数据来源: {', '.join(rates.get('data_sources', []))}")
        
        if rates.get('opr'):
            logger.info(f"   OPR: {rates['opr'].get('opr', 'N/A')}%")
        
        return rates
    except Exception as e:
        logger.error(f"❌ BNM数据采集失败: {e}")
        return None


def collect_basic_products():
    """
    采集基础产品信息（7个字段）
    快速获取所有68家机构的产品列表
    """
    logger.info("=" * 80)
    logger.info("🕷️ 第2步：采集基础产品信息（68家机构）")
    logger.info("=" * 80)
    
    try:
        # 并发爬取所有机构
        products = comprehensive_scraper.scrape_all_institutions(max_workers=10)
        
        # 验证数据
        valid_products = comprehensive_scraper.validate_products(products)
        
        logger.info(f"✅ 基础产品信息采集完成")
        logger.info(f"   总计: {len(valid_products)} 个产品")
        
        # 按机构类型统计
        stats = {}
        for p in valid_products:
            inst_type = p.get('institution_type', 'unknown')
            stats[inst_type] = stats.get(inst_type, 0) + 1
        
        logger.info("   按机构类型分布:")
        for inst_type, count in sorted(stats.items(), key=lambda x: -x[1]):
            logger.info(f"     - {inst_type}: {count} 个产品")
        
        return valid_products
    except Exception as e:
        logger.error(f"❌ 基础产品采集失败: {e}")
        return []


def enrich_product_details(basic_products):
    """
    增强产品详细信息（12个字段）
    为每个产品补充完整的详细字段
    """
    logger.info("=" * 80)
    logger.info("🔍 第3步：增强产品详细信息（12个字段）")
    logger.info("=" * 80)
    
    detailed_products = []
    total = len(basic_products)
    
    logger.info(f"⚙️ 开始深度爬取 {total} 个产品的详细信息...")
    logger.info("⏱️ 预计时间: 15-30分钟")
    logger.info("")
    
    # 使用线程池并发处理
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        
        for product in basic_products:
            # 提交任务：爬取每个产品的详细页面
            future = executor.submit(
                detailed_scraper.scrape_product_details,
                bank_name=product['bank'],
                product_url=product.get('url', product.get('source_url', '')),
                loan_type=product['type'],
                institution_type=product.get('institution_type', 'commercial')
            )
            futures.append(future)
        
        # 收集结果
        completed = 0
        for future in as_completed(futures):
            try:
                detailed_product = future.result()
                detailed_products.append(detailed_product)
                
                completed += 1
                if completed % 10 == 0:
                    logger.info(f"📊 进度: {completed}/{total} ({completed*100//total}%)")
                    
            except Exception as e:
                logger.error(f"❌ 产品详情提取失败: {e}")
                completed += 1
    
    logger.info(f"✅ 详细信息采集完成: {len(detailed_products)}/{total}")
    return detailed_products


def save_to_database(products):
    """保存到数据库"""
    logger.info("=" * 80)
    logger.info("💾 第4步：保存数据到数据库")
    logger.info("=" * 80)
    
    if not products:
        logger.warning("⚠️ 没有产品数据可保存")
        return
    
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    # 清空旧数据
    cur.execute("DELETE FROM loan_products_detailed")
    logger.info("   清空旧数据...")
    
    # 插入新数据
    timestamp = datetime.now().isoformat()
    
    insert_sql = """
        INSERT INTO loan_products_detailed(
            company, loan_type, product_name, required_doc, features, benefits,
            fees_charges, tenure, rate, application_form_url, product_disclosure_url,
            terms_conditions_url, preferred_customer_type, institution_type,
            source_url, pulled_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    items = [
        (
            p['company'],
            p['loan_type'],
            p['product_name'],
            p['required_doc'],
            p['features'],
            p['benefits'],
            p['fees_charges'],
            p['tenure'],
            p['rate'],
            p.get('application_form_url'),
            p.get('product_disclosure_url'),
            p.get('terms_conditions_url'),
            p['preferred_customer_type'],
            p['institution_type'],
            p.get('source_url'),
            timestamp
        )
        for p in products
    ]
    
    cur.executemany(insert_sql, items)
    con.commit()
    con.close()
    
    logger.info(f"✅ 成功保存 {len(products)} 个产品到数据库")


def export_to_csv(products):
    """导出为CSV文件"""
    logger.info("=" * 80)
    logger.info("📤 第5步：导出CSV备份")
    logger.info("=" * 80)
    
    import csv
    
    if not products:
        logger.warning("⚠️ 没有产品数据可导出")
        return
    
    filename = f"/home/runner/malaysia_loans_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    fieldnames = [
        'company', 'loan_type', 'product_name', 'required_doc', 'features',
        'benefits', 'fees_charges', 'tenure', 'rate', 'application_form_url',
        'product_disclosure_url', 'terms_conditions_url', 'preferred_customer_type',
        'institution_type', 'source_url', 'pulled_at'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)
    
    logger.info(f"✅ CSV文件已导出: {filename}")


def main():
    """主流程"""
    logger.info("")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 15 + "马来西亚68家金融机构真实贷款数据采集" + " " * 22 + "║")
    logger.info("║" + " " * 25 + "12个详细字段完整版" + " " * 27 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("")
    
    start_time = datetime.now()
    
    # 步骤1：初始化数据库
    init_database()
    logger.info("")
    
    # 步骤2：采集BNM官方利率
    bnm_rates = collect_bnm_rates()
    logger.info("")
    
    # 步骤3：采集基础产品信息
    basic_products = collect_basic_products()
    logger.info("")
    
    if not basic_products:
        logger.error("❌ 基础产品采集失败，流程中止")
        return
    
    # 步骤4：增强详细信息
    detailed_products = enrich_product_details(basic_products)
    logger.info("")
    
    # 步骤5：保存到数据库
    save_to_database(detailed_products)
    logger.info("")
    
    # 步骤6：导出CSV
    export_to_csv(detailed_products)
    logger.info("")
    
    # 完成
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("=" * 80)
    logger.info("🎉 数据采集完成！")
    logger.info("=" * 80)
    logger.info(f"   总耗时: {duration:.1f} 秒 ({duration/60:.1f} 分钟)")
    logger.info(f"   产品总数: {len(detailed_products)}")
    logger.info(f"   数据库: {DB_PATH}")
    logger.info("")
    logger.info("📊 现在可以通过以下API访问数据:")
    logger.info("   GET /loans/detailed/")
    logger.info("   GET /loans/detailed/export.csv")
    logger.info("   GET /loans/detailed/stats/summary")
    logger.info("")


if __name__ == '__main__':
    main()
