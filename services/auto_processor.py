"""
Credit Card Auto Processor - 信用卡账单自动处理系统
=======================================================
100%自动化处理流程：
1. PDF解析 → 2. 交易分类 → 3. 计算引擎 → 4. 验证系统 → 5. 手续费Invoice
"""

from typing import Dict, Optional
import logging
from pathlib import Path

# 导入所有需要的模块
from services.credit_card_core import CreditCardCore
from services.miscellaneous_fee import MiscellaneousFeeSystem
from services.credit_card_validation import CreditCardValidation
from services.transaction_classifier import TransactionClassifier
from db.database import get_db

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CreditCardAutoProcessor:
    """信用卡账单自动处理器 - 100%自动化"""
    
    def __init__(self):
        self.core_engine = CreditCardCore()
        self.fee_system = MiscellaneousFeeSystem()
        self.validator = CreditCardValidation()
        self.classifier = TransactionClassifier()
    
    def process_uploaded_statement(self, statement_id: int) -> Dict:
        """
        自动处理上传的账单
        
        Args:
            statement_id: 账单ID
            
        Returns:
            处理结果字典 {
                'success': bool,
                'step': str,  # 当前步骤
                'calculation': dict,  # 计算结果
                'validation': dict,  # 验证结果
                'fee_invoice_path': str,  # 手续费Invoice路径
                'errors': list  # 错误列表
            }
        """
        result = {
            'success': False,
            'step': 'initialization',
            'calculation': None,
            'validation': None,
            'fee_invoice_path': None,
            'errors': []
        }
        
        try:
            # 步骤1: 自动分类交易
            logger.info(f"📝 步骤1: 自动分类交易 (Statement ID: {statement_id})")
            result['step'] = 'classification'
            classification_result = self._classify_transactions(statement_id)
            
            if not classification_result['success']:
                result['errors'].append(f"分类失败: {classification_result['message']}")
                return result
            
            # 步骤2: 执行计算引擎
            logger.info(f"🔢 步骤2: 执行计算引擎")
            result['step'] = 'calculation'
            calculation_result = self.core_engine.calculate_statement(statement_id)
            result['calculation'] = calculation_result
            
            # 步骤3: 验证系统
            logger.info(f"✅ 步骤3: 执行验证系统")
            result['step'] = 'validation'
            validation_result = self.validator.validate_statement(statement_id)
            result['validation'] = {
                'overall_passed': validation_result['overall'].passed,
                'balance_check': validation_result['balance'].passed,
                'data_integrity': validation_result['data_integrity'].passed,
                'classification': validation_result['classification'].passed,
                'anomaly': validation_result['anomaly'].passed,
                'details': {
                    k: v.details for k, v in validation_result.items()
                }
            }
            
            # 如果DR/CR不平衡，标记为严重错误
            if not validation_result['balance'].passed:
                result['errors'].append(
                    f"DR/CR不平衡! DR={validation_result['balance'].details['total_dr']}, "
                    f"CR={validation_result['balance'].details['total_cr']}, "
                    f"差异={validation_result['balance'].details['difference']}"
                )
            
            # 步骤4: 生成手续费Invoice
            logger.info(f"💰 步骤4: 生成手续费Invoice")
            result['step'] = 'fee_generation'
            
            # 获取customer_id和year_month
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.id as customer_id, s.statement_month
                    FROM statements s
                    JOIN credit_cards cc ON s.card_id = cc.id
                    JOIN customers c ON cc.customer_id = c.id
                    WHERE s.id = ?
                """, (statement_id,))
                row = cursor.fetchone()
                
                if row:
                    customer_id = row['customer_id']
                    year_month = row['statement_month']
                    
                    # 生成手续费Invoice
                    gz_expenses = calculation_result.get('gz_expenses', 0)
                    if gz_expenses > 0:
                        try:
                            invoice_path = self.fee_system.generate_invoice(
                                customer_id=customer_id,
                                year_month=year_month,
                                gz_expenses=gz_expenses,
                                statement_ids=[statement_id]
                            )
                            result['fee_invoice_path'] = invoice_path
                            logger.info(f"✅ 手续费Invoice已生成: {invoice_path}")
                        except Exception as e:
                            logger.error(f"❌ 手续费Invoice生成失败: {e}")
                            result['errors'].append(f"手续费Invoice生成失败: {str(e)}")
            
            # 步骤5: 保存计算结果到数据库
            logger.info(f"💾 步骤5: 保存计算结果")
            result['step'] = 'saving_results'
            self._save_calculation_results(statement_id, calculation_result)
            
            # 完成
            result['step'] = 'completed'
            result['success'] = validation_result['overall'].passed
            
            logger.info(f"{'✅' if result['success'] else '⚠️'} 处理完成 (Statement ID: {statement_id})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 自动处理失败: {e}", exc_info=True)
            result['errors'].append(f"系统错误: {str(e)}")
            return result
    
    def _classify_transactions(self, statement_id: int) -> Dict:
        """分类账单的所有交易"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # 获取所有未分类的交易
                cursor.execute("""
                    SELECT t.id, t.description, t.amount, t.transaction_type,
                           cc.bank_name, cc.card_holder_name
                    FROM transactions t
                    JOIN statements s ON t.statement_id = s.id
                    JOIN credit_cards cc ON s.card_id = cc.id
                    WHERE t.statement_id = ?
                      AND (t.category IS NULL OR t.category = '' OR t.category = 'Uncategorized')
                """, (statement_id,))
                
                unclassified = cursor.fetchall()
                
                if not unclassified:
                    return {
                        'success': True,
                        'message': '所有交易已分类',
                        'classified_count': 0
                    }
                
                classified_count = 0
                for txn in unclassified:
                    category = self.classifier.classify_single_transaction(
                        description=txn['description'] or '',
                        amount=txn['amount'] or 0,
                        cardholder=txn['card_holder_name'] or '',
                        bank_name=txn['bank_name'] or ''
                    )
                    
                    cursor.execute("""
                        UPDATE transactions
                        SET category = ?
                        WHERE id = ?
                    """, (category, txn['id']))
                    
                    classified_count += 1
                
                conn.commit()
                
                return {
                    'success': True,
                    'message': f'成功分类{classified_count}笔交易',
                    'classified_count': classified_count
                }
                
        except Exception as e:
            logger.error(f"分类失败: {e}")
            return {
                'success': False,
                'message': str(e),
                'classified_count': 0
            }
    
    def _save_calculation_results(self, statement_id: int, calc_result: Dict):
        """保存计算结果到数据库"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # 创建或更新计算结果表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS statement_calculations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        statement_id INTEGER UNIQUE NOT NULL,
                        owner_expenses DECIMAL(10, 2),
                        gz_expenses DECIMAL(10, 2),
                        owner_payment DECIMAL(10, 2),
                        gz_payment1 DECIMAL(10, 2),
                        gz_payment2 DECIMAL(10, 2),
                        owner_os_bal_round1 DECIMAL(10, 2),
                        gz_os_bal_round1 DECIMAL(10, 2),
                        final_owner_os_bal DECIMAL(10, 2),
                        final_gz_os_bal DECIMAL(10, 2),
                        total_dr DECIMAL(10, 2),
                        total_cr DECIMAL(10, 2),
                        calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (statement_id) REFERENCES statements(id)
                    )
                """)
                
                # 插入或更新计算结果
                cursor.execute("""
                    INSERT OR REPLACE INTO statement_calculations
                    (statement_id, owner_expenses, gz_expenses, owner_payment, gz_payment1, gz_payment2,
                     owner_os_bal_round1, gz_os_bal_round1, final_owner_os_bal, final_gz_os_bal,
                     total_dr, total_cr)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    statement_id,
                    float(calc_result.get('owner_expenses', 0)),
                    float(calc_result.get('gz_expenses', 0)),
                    float(calc_result.get('owner_payment', 0)),
                    float(calc_result.get('gz_payment1', 0)),
                    float(calc_result.get('gz_payment2', 0)),
                    float(calc_result.get('owner_os_bal_round1', 0)),
                    float(calc_result.get('gz_os_bal_round1', 0)),
                    float(calc_result.get('final_owner_os_bal', 0)),
                    float(calc_result.get('final_gz_os_bal', 0)),
                    float(calc_result.get('total_dr', 0)),
                    float(calc_result.get('total_cr', 0))
                ))
                
                conn.commit()
                logger.info(f"✅ 计算结果已保存 (Statement ID: {statement_id})")
                
        except Exception as e:
            logger.error(f"保存计算结果失败: {e}")
            raise
    
    def batch_process_month(self, customer_id: int, year_month: str) -> Dict:
        """
        批量处理某客户某月的所有账单
        
        Args:
            customer_id: 客户ID
            year_month: 年月 (YYYY-MM)
            
        Returns:
            处理结果汇总
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.id
                FROM statements s
                JOIN credit_cards cc ON s.card_id = cc.id
                WHERE cc.customer_id = ? AND s.statement_month = ?
            """, (customer_id, year_month))
            
            statement_ids = [row[0] for row in cursor.fetchall()]
        
        results = {
            'total': len(statement_ids),
            'succeeded': 0,
            'failed': 0,
            'details': []
        }
        
        for stmt_id in statement_ids:
            result = self.process_uploaded_statement(stmt_id)
            
            if result['success']:
                results['succeeded'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append({
                'statement_id': stmt_id,
                'success': result['success'],
                'errors': result['errors']
            })
        
        return results


# 全局实例
auto_processor = CreditCardAutoProcessor()
