"""
Credit Card Validation System - 信用卡账单验证系统
==================================================
多层验证系统，确保数据准确性和完整性

验证层级：
1. DR/CR平衡验证 - total_dr 必须等于 total_cr（允许±0.01误差）
2. 基础数据完整性验证 - Previous Balance、交易记录完整性
3. 交易分类完整性验证 - 所有交易必须有分类
4. 异常检测与二次验证 - 检测异常金额、异常交易
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from db.database import get_db
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationResult:
    """验证结果"""
    
    def __init__(self, passed: bool, message: str, details: Optional[Dict] = None):
        self.passed = passed
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        return f"{status}: {self.message}"
    
    def __repr__(self):
        return f"ValidationResult(passed={self.passed}, message='{self.message}')"


class CreditCardValidation:
    """信用卡账单验证系统"""
    
    # 允许的DR/CR误差范围
    BALANCE_TOLERANCE = Decimal('0.01')
    
    # 异常金额阈值（单笔交易超过此金额需要二次验证）
    ANOMALY_THRESHOLD = Decimal('10000.00')
    
    def __init__(self, db_path: str = 'db/smart_loan_manager.db'):
        self.db_path = db_path
    
    def validate_statement(self, statement_id: int) -> Dict[str, ValidationResult]:
        """
        完整验证单个账单
        
        Args:
            statement_id: 账单ID
            
        Returns:
            包含所有验证结果的字典
        """
        results = {}
        
        # 1. DR/CR平衡验证
        results['balance'] = self._validate_dr_cr_balance(statement_id)
        
        # 2. 基础数据完整性验证
        results['data_integrity'] = self._validate_data_integrity(statement_id)
        
        # 3. 交易分类完整性验证
        results['classification'] = self._validate_classification_completeness(statement_id)
        
        # 4. 异常检测
        results['anomaly'] = self._detect_anomalies(statement_id)
        
        # 总体验证结果
        all_passed = all(r.passed for r in results.values())
        results['overall'] = ValidationResult(
            passed=all_passed,
            message="所有验证通过" if all_passed else "存在验证失败项",
            details={
                'total_checks': len(results) - 1,
                'passed_checks': sum(1 for r in results.values() if r.passed),
                'failed_checks': sum(1 for r in results.values() if not r.passed)
            }
        )
        
        return results
    
    def _validate_dr_cr_balance(self, statement_id: int) -> ValidationResult:
        """
        验证DR/CR平衡
        
        规则：total_dr 必须等于 total_cr（允许±0.01误差）
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN transaction_type = 'DR' THEN amount ELSE 0 END) as total_dr,
                    SUM(CASE WHEN transaction_type = 'CR' THEN amount ELSE 0 END) as total_cr,
                    COUNT(*) as total_transactions
                FROM transactions
                WHERE statement_id = ?
            """, (statement_id,))
            
            row = cursor.fetchone()
            
            if not row or row[2] == 0:
                return ValidationResult(
                    passed=False,
                    message="账单无交易记录",
                    details={'total_transactions': 0}
                )
            
            total_dr = Decimal(str(row[0] or 0))
            total_cr = Decimal(str(row[1] or 0))
            difference = abs(total_dr - total_cr)
            
            passed = difference <= self.BALANCE_TOLERANCE
            
            return ValidationResult(
                passed=passed,
                message=f"DR/CR {'平衡' if passed else '不平衡'}",
                details={
                    'total_dr': float(total_dr),
                    'total_cr': float(total_cr),
                    'difference': float(difference),
                    'tolerance': float(self.BALANCE_TOLERANCE),
                    'total_transactions': row[2]
                }
            )
    
    def _validate_data_integrity(self, statement_id: int) -> ValidationResult:
        """
        验证基础数据完整性
        
        检查项：
        - Previous Balance是否存在
        - 账单基本信息是否完整
        - 交易记录是否有缺失字段
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 检查账单基本信息
            cursor.execute("""
                SELECT s.previous_balance_total, s.statement_month,
                       cc.bank_name, cc.card_holder_name
                FROM statements s
                JOIN credit_cards cc ON s.card_id = cc.id
                WHERE s.id = ?
            """, (statement_id,))
            
            stmt_row = cursor.fetchone()
            
            if not stmt_row:
                return ValidationResult(
                    passed=False,
                    message="账单不存在",
                    details={'statement_id': statement_id}
                )
            
            issues = []
            
            # 检查Previous Balance
            if stmt_row[0] is None:
                issues.append("Previous Balance缺失")
            
            # 检查账单月份
            if not stmt_row[1]:
                issues.append("账单月份缺失")
            
            # 检查银行名称
            if not stmt_row[2]:
                issues.append("银行名称缺失")
            
            # 检查持卡人
            if not stmt_row[3]:
                issues.append("持卡人缺失")
            
            # 检查交易记录完整性
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN description IS NULL OR description = '' THEN 1 ELSE 0 END) as missing_desc,
                       SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END) as missing_amount,
                       SUM(CASE WHEN transaction_type IS NULL OR transaction_type = '' THEN 1 ELSE 0 END) as missing_type
                FROM transactions
                WHERE statement_id = ?
            """, (statement_id,))
            
            txn_row = cursor.fetchone()
            
            if txn_row[1] > 0:
                issues.append(f"{txn_row[1]}笔交易缺少描述")
            if txn_row[2] > 0:
                issues.append(f"{txn_row[2]}笔交易缺少金额")
            if txn_row[3] > 0:
                issues.append(f"{txn_row[3]}笔交易缺少类型")
            
            passed = len(issues) == 0
            
            return ValidationResult(
                passed=passed,
                message="数据完整" if passed else f"发现{len(issues)}个问题",
                details={
                    'issues': issues,
                    'total_transactions': txn_row[0] if txn_row else 0
                }
            )
    
    def _validate_classification_completeness(self, statement_id: int) -> ValidationResult:
        """
        验证交易分类完整性
        
        检查：所有DR交易是否都已分类
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) as total_dr,
                       SUM(CASE WHEN category IS NULL OR category = '' THEN 1 ELSE 0 END) as unclassified
                FROM transactions
                WHERE statement_id = ? AND transaction_type = 'DR'
            """, (statement_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return ValidationResult(
                    passed=False,
                    message="无法查询交易分类",
                    details={}
                )
            
            total_dr = row[0] or 0
            unclassified = row[1] or 0
            classified = total_dr - unclassified
            
            passed = unclassified == 0
            
            return ValidationResult(
                passed=passed,
                message="所有交易已分类" if passed else f"{unclassified}笔交易未分类",
                details={
                    'total_dr_transactions': total_dr,
                    'classified': classified,
                    'unclassified': unclassified,
                    'classification_rate': f"{(classified/total_dr*100):.1f}%" if total_dr > 0 else "N/A"
                }
            )
    
    def _detect_anomalies(self, statement_id: int) -> ValidationResult:
        """
        异常检测
        
        检测项：
        - 异常大额交易（超过阈值）
        - 重复交易
        - 异常日期
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            anomalies = []
            
            # 1. 检测大额交易
            cursor.execute("""
                SELECT id, description, amount, transaction_date
                FROM transactions
                WHERE statement_id = ? AND amount > ?
                ORDER BY amount DESC
            """, (statement_id, float(self.ANOMALY_THRESHOLD)))
            
            large_txns = cursor.fetchall()
            if large_txns:
                anomalies.append({
                    'type': 'large_transaction',
                    'count': len(large_txns),
                    'message': f"发现{len(large_txns)}笔大额交易（>RM{self.ANOMALY_THRESHOLD:,.2f}）",
                    'transactions': [
                        {
                            'id': row[0],
                            'description': row[1],
                            'amount': float(row[2]),
                            'date': row[3]
                        } for row in large_txns
                    ]
                })
            
            # 2. 检测可能的重复交易（相同日期、相同金额、相似描述）
            cursor.execute("""
                SELECT t1.id, t1.description, t1.amount, t1.transaction_date, COUNT(*) as duplicates
                FROM transactions t1
                JOIN transactions t2 ON 
                    t1.statement_id = t2.statement_id AND
                    t1.transaction_date = t2.transaction_date AND
                    t1.amount = t2.amount AND
                    t1.id < t2.id
                WHERE t1.statement_id = ?
                GROUP BY t1.id, t1.description, t1.amount, t1.transaction_date
                HAVING COUNT(*) > 0
            """, (statement_id,))
            
            duplicates = cursor.fetchall()
            if duplicates:
                anomalies.append({
                    'type': 'duplicate_transaction',
                    'count': len(duplicates),
                    'message': f"发现{len(duplicates)}组可能的重复交易",
                    'transactions': [
                        {
                            'id': row[0],
                            'description': row[1],
                            'amount': float(row[2]),
                            'date': row[3],
                            'duplicate_count': row[4]
                        } for row in duplicates
                    ]
                })
            
            # 3. 检测异常日期（未来日期）
            cursor.execute("""
                SELECT id, description, amount, transaction_date
                FROM transactions
                WHERE statement_id = ? AND transaction_date > date('now')
            """, (statement_id,))
            
            future_txns = cursor.fetchall()
            if future_txns:
                anomalies.append({
                    'type': 'future_date',
                    'count': len(future_txns),
                    'message': f"发现{len(future_txns)}笔未来日期交易",
                    'transactions': [
                        {
                            'id': row[0],
                            'description': row[1],
                            'amount': float(row[2]),
                            'date': row[3]
                        } for row in future_txns
                    ]
                })
            
            # 异常检测不算失败，只是警告
            has_critical = any(a['type'] == 'future_date' for a in anomalies)
            
            return ValidationResult(
                passed=not has_critical,
                message=f"发现{len(anomalies)}类异常" if anomalies else "未发现异常",
                details={
                    'anomaly_count': len(anomalies),
                    'anomalies': anomalies
                }
            )
    
    def validate_batch(self, statement_ids: List[int]) -> Dict[int, Dict[str, ValidationResult]]:
        """
        批量验证多个账单
        
        Args:
            statement_ids: 账单ID列表
            
        Returns:
            每个账单的验证结果字典
        """
        results = {}
        for stmt_id in statement_ids:
            try:
                results[stmt_id] = self.validate_statement(stmt_id)
            except Exception as e:
                logger.error(f"验证账单 {stmt_id} 时出错: {e}")
                results[stmt_id] = {
                    'overall': ValidationResult(
                        passed=False,
                        message=f"验证失败: {str(e)}",
                        details={'error': str(e)}
                    )
                }
        
        return results
    
    def generate_validation_report(self, statement_id: int) -> str:
        """
        生成验证报告（文本格式）
        
        Args:
            statement_id: 账单ID
            
        Returns:
            验证报告文本
        """
        results = self.validate_statement(statement_id)
        
        report_lines = [
            "=" * 60,
            f"账单验证报告 - Statement ID: {statement_id}",
            "=" * 60,
            ""
        ]
        
        for check_name, result in results.items():
            if check_name == 'overall':
                continue
            
            report_lines.append(f"【{check_name.upper()}】")
            report_lines.append(str(result))
            
            if result.details:
                report_lines.append("  详情:")
                for key, value in result.details.items():
                    if key != 'anomalies' and key != 'transactions':
                        report_lines.append(f"    - {key}: {value}")
            
            report_lines.append("")
        
        # 总结
        overall = results['overall']
        report_lines.append("=" * 60)
        report_lines.append(f"【总体结果】 {str(overall)}")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
