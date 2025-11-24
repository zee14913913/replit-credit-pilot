"""
自动验证引擎 - 储蓄账户月结单自动验证系统
Automatic Verification Engine for Savings Account Statements

功能：
1. 余额连续性验证：检查每笔交易的余额计算是否正确
2. Opening/Closing Balance验证：检查期初期末余额
3. 交易完整性验证：检查交易数量和数据完整性
4. 自动标记验证状态

使用场景：实现100%自动化验证流程
"""

from db.database import get_db
from typing import Dict, List, Tuple
from decimal import Decimal


class AutoVerifier:
    """自动验证引擎"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def verify_statement(self, statement_id: int) -> Dict:
        """
        自动验证单个月结单
        
        Args:
            statement_id: 月结单ID
            
        Returns:
            验证结果字典，包含状态、错误信息、警告信息
        """
        self.errors = []
        self.warnings = []
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取月结单信息
            cursor.execute('''
                SELECT 
                    ss.id,
                    ss.statement_date,
                    ss.total_transactions,
                    sa.bank_name,
                    c.name as customer_name
                FROM savings_statements ss
                JOIN savings_accounts sa ON ss.savings_account_id = sa.id
                JOIN customers c ON sa.customer_id = c.id
                WHERE ss.id = ?
            ''', (statement_id,))
            
            statement = cursor.fetchone()
            if not statement:
                return {
                    'status': 'error',
                    'message': f'找不到月结单 ID: {statement_id}'
                }
            
            statement = dict(statement)
            
            # 获取所有交易记录
            cursor.execute('''
                SELECT 
                    id,
                    transaction_date,
                    description,
                    amount,
                    transaction_type,
                    balance
                FROM savings_transactions
                WHERE savings_statement_id = ?
                ORDER BY id
            ''', (statement_id,))
            
            transactions = [dict(row) for row in cursor.fetchall()]
            
            if not transactions:
                self.errors.append('没有找到任何交易记录')
                return self._generate_result(statement, transactions, False)
            
            # 执行验证检查
            self._check_transaction_count(statement, transactions)
            self._check_balance_continuity(transactions)
            self._check_data_integrity(transactions)
            self._check_opening_closing_balance(transactions, statement_id, cursor)
            
            # 判断验证是否通过
            verification_passed = len(self.errors) == 0
            
            # 如果验证通过，自动标记为已验证
            if verification_passed:
                cursor.execute('''
                    UPDATE savings_statements
                    SET verification_status = 'verified',
                        verified_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (statement_id,))
                conn.commit()
            
            return self._generate_result(statement, transactions, verification_passed)
    
    def _check_transaction_count(self, statement: Dict, transactions: List[Dict]):
        """检查交易数量"""
        expected = statement['total_transactions']
        actual = len(transactions)
        
        if expected != actual:
            self.errors.append(
                f'交易数量不匹配：记录为{expected}笔，实际为{actual}笔'
            )
    
    def _check_balance_continuity(self, transactions: List[Dict]):
        """检查余额连续性 - 要求精确匹配（分为单位）"""
        for i, txn in enumerate(transactions):
            if txn['balance'] is None:
                self.errors.append(
                    f'第{i+1}笔交易缺少余额信息：{txn["transaction_date"]} {txn["description"][:30]}'
                )
                continue
            
            if i == 0:
                continue
            
            prev_txn = transactions[i-1]
            if prev_txn['balance'] is None:
                continue
            
            # 使用Decimal精确计算，四舍五入到分（2位小数）
            prev_balance = Decimal(str(prev_txn['balance'])).quantize(Decimal('0.01'))
            amount = Decimal(str(txn['amount'])).quantize(Decimal('0.01'))
            
            if txn['transaction_type'] == 'credit':
                expected_balance = (prev_balance + amount).quantize(Decimal('0.01'))
            else:
                expected_balance = (prev_balance - amount).quantize(Decimal('0.01'))
            
            actual_balance = Decimal(str(txn['balance'])).quantize(Decimal('0.01'))
            
            # 要求完全精确匹配（分为单位）
            if expected_balance != actual_balance:
                diff = abs(expected_balance - actual_balance)
                self.errors.append(
                    f'第{i+1}笔交易余额计算错误：'
                    f'{txn["transaction_date"]} {txn["description"][:30]} '
                    f'预期余额 RM{expected_balance:.2f}，实际余额 RM{actual_balance:.2f}，'
                    f'差异 RM{diff:.2f}'
                )
    
    def _check_data_integrity(self, transactions: List[Dict]):
        """检查数据完整性"""
        for i, txn in enumerate(transactions):
            # 检查必填字段
            if not txn['transaction_date']:
                self.errors.append(f'第{i+1}笔交易缺少日期')
            
            if not txn['description']:
                self.warnings.append(f'第{i+1}笔交易缺少描述')
            
            # 金额可以为0（例如0.00的利息），但不能为None或负数
            if txn['amount'] is None:
                self.errors.append(f'第{i+1}笔交易缺少金额')
            elif txn['amount'] < 0:
                self.errors.append(f'第{i+1}笔交易金额为负数：{txn["amount"]}')
            
            if txn['transaction_type'] not in ['credit', 'debit']:
                self.errors.append(f'第{i+1}笔交易类型无效：{txn["transaction_type"]}')
    
    def _check_opening_closing_balance(self, transactions: List[Dict], statement_id: int, cursor):
        """检查期初期末余额 - 验证Opening Balance与前一个月的Closing Balance一致"""
        if not transactions:
            return
        
        # 计算Opening Balance（从第一笔交易推导）
        first_txn = transactions[0]
        derived_opening_balance = None
        
        if first_txn['balance'] is not None and first_txn['amount'] is not None:
            balance = Decimal(str(first_txn['balance'])).quantize(Decimal('0.01'))
            amount = Decimal(str(first_txn['amount'])).quantize(Decimal('0.01'))
            
            if first_txn['transaction_type'] == 'credit':
                derived_opening_balance = (balance - amount).quantize(Decimal('0.01'))
            else:
                derived_opening_balance = (balance + amount).quantize(Decimal('0.01'))
        
        # 检查Closing Balance（最后一笔交易的余额）
        last_txn = transactions[-1]
        if last_txn['balance'] is None:
            self.errors.append('最后一笔交易缺少Closing Balance')
            return
        
        closing_balance = Decimal(str(last_txn['balance'])).quantize(Decimal('0.01'))
        
        # 使用Decimal计算总Credit和总Debit
        total_credit = sum(
            Decimal(str(t['amount'])).quantize(Decimal('0.01'))
            for t in transactions if t['transaction_type'] == 'credit'
        )
        total_debit = sum(
            Decimal(str(t['amount'])).quantize(Decimal('0.01'))
            for t in transactions if t['transaction_type'] == 'debit'
        )
        
        # 验证1：Opening Balance + Total Credit - Total Debit = Closing Balance
        if derived_opening_balance is not None:
            expected_closing = (derived_opening_balance + total_credit - total_debit).quantize(Decimal('0.01'))
            
            if expected_closing != closing_balance:
                diff = abs(expected_closing - closing_balance)
                self.errors.append(
                    f'Closing Balance计算错误：'
                    f'Opening RM{derived_opening_balance:.2f} + Credit RM{total_credit:.2f} - Debit RM{total_debit:.2f} '
                    f'= RM{expected_closing:.2f}，但实际Closing Balance为 RM{closing_balance:.2f}，'
                    f'差异 RM{diff:.2f}'
                )
        
        # 验证2：跨月连续性 - 当前Opening Balance必须等于前一个月的Closing Balance
        cursor.execute('''
            SELECT 
                ss_prev.id as prev_id,
                ss_prev.statement_date as prev_date,
                st_prev.balance as prev_closing_balance
            FROM savings_statements ss_current
            JOIN savings_statements ss_prev 
                ON ss_current.savings_account_id = ss_prev.savings_account_id
                AND ss_prev.statement_date < ss_current.statement_date
            LEFT JOIN savings_transactions st_prev 
                ON ss_prev.id = st_prev.savings_statement_id
            WHERE ss_current.id = ?
            ORDER BY ss_prev.statement_date DESC, st_prev.id DESC
            LIMIT 1
        ''', (statement_id,))
        
        prev_result = cursor.fetchone()
        
        if prev_result and prev_result['prev_closing_balance'] is not None:
            # 有前一个月的记录且有Closing Balance
            prev_closing = Decimal(str(prev_result['prev_closing_balance'])).quantize(Decimal('0.01'))
            
            if derived_opening_balance is not None:
                if derived_opening_balance != prev_closing:
                    diff = abs(derived_opening_balance - prev_closing)
                    self.errors.append(
                        f'跨月Opening Balance不连续：'
                        f'当前月Opening Balance为 RM{derived_opening_balance:.2f}，'
                        f'但前一个月({prev_result["prev_date"][:7]})的Closing Balance为 RM{prev_closing:.2f}，'
                        f'差异 RM{diff:.2f}'
                    )
        elif prev_result:
            # 找到前一个月的记录，但没有Closing Balance - 这是硬错误
            self.errors.append(
                f'跨月连续性验证失败：'
                f'前一个月({prev_result["prev_date"][:7]})的月结单缺少Closing Balance，'
                f'无法验证跨月连续性。必须先验证前一个月的月结单。'
            )
    
    def _generate_result(self, statement: Dict, transactions: List[Dict], 
                        verification_passed: bool) -> Dict:
        """生成验证结果"""
        # 使用Decimal计算所有金额
        total_credit = float(sum(
            Decimal(str(t['amount'])).quantize(Decimal('0.01'))
            for t in transactions if t['transaction_type'] == 'credit'
        ))
        total_debit = float(sum(
            Decimal(str(t['amount'])).quantize(Decimal('0.01'))
            for t in transactions if t['transaction_type'] == 'debit'
        ))
        
        # 计算Opening Balance
        opening_balance = 0
        if transactions and transactions[0]['balance'] is not None and transactions[0]['amount'] is not None:
            first_balance = Decimal(str(transactions[0]['balance'])).quantize(Decimal('0.01'))
            first_amount = Decimal(str(transactions[0]['amount'])).quantize(Decimal('0.01'))
            if transactions[0]['transaction_type'] == 'credit':
                opening_balance = float((first_balance - first_amount).quantize(Decimal('0.01')))
            else:
                opening_balance = float((first_balance + first_amount).quantize(Decimal('0.01')))
        
        return {
            'status': 'success' if verification_passed else 'failed',
            'statement_id': statement['id'],
            'customer_name': statement['customer_name'],
            'bank_name': statement['bank_name'],
            'statement_date': statement['statement_date'],
            'total_transactions': len(transactions),
            'verification_passed': verification_passed,
            'errors': self.errors,
            'warnings': self.warnings,
            'summary': {
                'total_credit': total_credit,
                'total_debit': total_debit,
                'opening_balance': opening_balance,
                'closing_balance': float(transactions[-1]['balance']) if transactions and transactions[-1]['balance'] is not None else 0
            }
        }
    
    def batch_verify(self, statement_ids: List[int]) -> List[Dict]:
        """
        批量自动验证多个月结单
        
        Args:
            statement_ids: 月结单ID列表
            
        Returns:
            验证结果列表
        """
        results = []
        for statement_id in statement_ids:
            result = self.verify_statement(statement_id)
            results.append(result)
        return results


def auto_verify_all_pending_statements() -> List[Dict]:
    """
    自动验证所有待验证的月结单
    
    Returns:
        验证结果列表
    """
    verifier = AutoVerifier()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 获取所有待验证的月结单
        cursor.execute('''
            SELECT id
            FROM savings_statements
            WHERE verification_status = 'pending'
            ORDER BY statement_date
        ''')
        
        statement_ids = [row['id'] for row in cursor.fetchall()]
    
    if not statement_ids:
        return []
    
    return verifier.batch_verify(statement_ids)
