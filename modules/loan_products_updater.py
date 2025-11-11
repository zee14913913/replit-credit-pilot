"""
贷款产品自动更新模块
用于每月自动验证和更新贷款产品信息
"""

import json
import os
import sqlite3
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/loan_products_updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LoanProductsUpdater:
    """贷款产品更新器"""
    
    def __init__(self, db_path='db/smart_loan_manager.db', banks_dir='data/banks'):
        self.db_path = db_path
        self.banks_dir = banks_dir
    
    def verify_product_data(self):
        """验证产品数据完整性"""
        logger.info("开始验证贷款产品数据...")
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 检查产品总数
        cursor.execute("SELECT COUNT(*) as total FROM loan_products")
        total = cursor.fetchone()['total']
        
        # 检查最后验证日期
        cursor.execute("SELECT last_verified, COUNT(*) as count FROM loan_products GROUP BY last_verified ORDER BY last_verified DESC")
        verification_stats = cursor.fetchall()
        
        logger.info(f"数据库中有 {total} 个产品")
        logger.info("验证日期分布：")
        for stat in verification_stats:
            logger.info(f"  {stat['last_verified']}: {stat['count']} 个产品")
        
        # 检查缺失必要字段的产品
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM loan_products 
            WHERE product_id IS NULL 
               OR bank IS NULL 
               OR name IS NULL 
               OR category IS NULL
        """)
        missing_fields = cursor.fetchone()['count']
        
        if missing_fields > 0:
            logger.warning(f"发现 {missing_fields} 个产品缺少必要字段！")
        
        conn.close()
        
        return {
            'total_products': total,
            'missing_fields': missing_fields,
            'verification_stats': dict(verification_stats)
        }
    
    def update_from_source_files(self):
        """从源JSON文件重新导入数据"""
        logger.info(f"从 {self.banks_dir} 重新导入产品数据...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 清空现有数据
        cursor.execute("DELETE FROM loan_products")
        conn.commit()
        logger.info("已清空现有数据")
        
        # 读取所有银行文件
        bank_files = sorted([f for f in os.listdir(self.banks_dir) if f.endswith('.json')])
        total_imported = 0
        total_errors = 0
        
        for bank_file in bank_files:
            file_path = os.path.join(self.banks_dir, bank_file)
            logger.info(f"处理 {bank_file}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                products = json.load(f)
                
                for product in products:
                    try:
                        # 准备数据并插入（使用与主程序相同的逻辑）
                        self._insert_product(cursor, product)
                        total_imported += 1
                    except Exception as e:
                        logger.error(f"导入 {product.get('product_id')} 失败: {str(e)}")
                        total_errors += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"导入完成：成功 {total_imported} 个，失败 {total_errors} 个")
        
        return {
            'imported': total_imported,
            'errors': total_errors
        }
    
    def _insert_product(self, cursor, product):
        """插入单个产品（辅助方法）"""
        # 处理JSON字段
        def safe_json_dumps(value):
            if isinstance(value, list):
                return json.dumps(value)
            elif value is None:
                return None
            else:
                return str(value)
        
        channel_json = safe_json_dumps(product.get('channel'))
        docs_json = safe_json_dumps(product.get('docs_required'))
        features_json = safe_json_dumps(product.get('special_features'))
        conditions_json = safe_json_dumps(product.get('special_conditions'))
        
        link_value = product.get('link')
        if isinstance(link_value, list):
            link_value = link_value[0] if link_value else None
        
        links_json = safe_json_dumps(product.get('links'))
        
        insert_sql = '''
        INSERT OR REPLACE INTO loan_products (
            product_id, bank, name, category, shariah, citizenship,
            amount_min, amount_max, rate_display, rate_details,
            tenure_min_months, tenure_max_months, income_min, age_min, age_max,
            dsr_max, dsr_policy, collateral_required, channel, speed_rank,
            docs_required, approval_days, approval_days_note, description,
            special_features, special_conditions, link, links, last_verified,
            company_age_min_months, financing_ratio, lock_in_period, rate_type,
            base_rate, cash_out_tenure_max, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        values = (
            product.get('product_id'),
            product.get('bank'),
            product.get('name'),
            product.get('category'),
            product.get('shariah'),
            product.get('citizenship'),
            product.get('amount_min'),
            product.get('amount_max'),
            product.get('rate_display'),
            product.get('rate_details'),
            product.get('tenure_min_months'),
            product.get('tenure_max_months'),
            product.get('income_min'),
            product.get('age_min'),
            product.get('age_max'),
            product.get('dsr_max'),
            product.get('dsr_policy'),
            1 if product.get('collateral_required') else 0,
            channel_json,
            product.get('speed_rank'),
            docs_json,
            str(product.get('approval_days')) if product.get('approval_days') else None,
            product.get('approval_days_note'),
            product.get('description'),
            features_json,
            conditions_json,
            link_value,
            links_json,
            product.get('last_verified'),
            product.get('company_age_min_months'),
            product.get('financing_ratio'),
            product.get('lock_in_period'),
            product.get('rate_type'),
            product.get('base_rate'),
            product.get('cash_out_tenure_max'),
            datetime.now().isoformat()
        )
        
        cursor.execute(insert_sql, values)
    
    def run_monthly_update(self):
        """执行每月更新任务"""
        logger.info("=" * 60)
        logger.info("开始每月贷款产品更新任务")
        logger.info("=" * 60)
        
        # 1. 验证当前数据
        verification_result = self.verify_product_data()
        
        # 2. 从源文件重新导入
        import_result = self.update_from_source_files()
        
        # 3. 再次验证
        new_verification = self.verify_product_data()
        
        logger.info("=" * 60)
        logger.info(f"更新任务完成！总计 {new_verification['total_products']} 个产品")
        logger.info("=" * 60)
        
        return {
            'before': verification_result,
            'import': import_result,
            'after': new_verification,
            'timestamp': datetime.now().isoformat()
        }


if __name__ == "__main__":
    # 直接运行此脚本进行手动更新
    updater = LoanProductsUpdater()
    result = updater.run_monthly_update()
    print(json.dumps(result, indent=2, ensure_ascii=False))
