"""
CreditPilot 核心计算引擎 - Credit Card Core Calculation Engine
=============================================================
完全按照用户指定的计算规则实施：

第1轮计算（6个基础项目）：
1. Owner's Expenses = SUM(所有非Suppliers的DR交易)
2. GZ's Expenses = SUM(所有Suppliers的DR交易)
3. Owner's Payment = SUM(客户自己的CR还款)
4. GZ's Payment1 = SUM(所有CR记录) - Owner's Payment
5. Owner's OS Bal = Previous Balance + Owner's Expenses - Owner's Payment
6. GZ's OS Bal = Previous Balance + GZ's Expenses - GZ's Payment1

第2轮计算：
7. GZ's Payment2 = SUM(从9个GZ Bank转账到客户银行账户的金额)

最终计算：
8. FINAL Owner OS Bal = Owner's OS Bal（第1轮）
9. FINAL GZ OS Bal = GZ's OS Bal（第1轮）- GZ's Payment2

⚠️ 关键规则：
- 允许负数余额（表示客户多还了钱）
- 7个Suppliers: 7SL, Dinas Raub, SYC Hainan, Ai Smart Tech, HUAWEI, Pasar Raya, Puchong Herbs
- 9个GZ Bank组合必须精确匹配
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import sqlite3
from db.database import get_db


class CreditCardCore:
    """CreditPilot 核心计算引擎"""
    
    # 7个供应商（Ji-Suan文档指定）
    SUPPLIERS = [
        '7SL', 
        'DINAS RAUB',
        'SYC HAINAN', 
        'AI SMART TECH', 
        'HUAWEI', 
        'PASAR RAYA', 
        'PUCHONG HERBS'
    ]
    
    # 9个GZ银行的精确组合（银行+持卡人） - 强制完整法定名称
    # 遵循ARCHITECT_CONSTRAINTS.md §1.2.1规范
    # ⚠️ 持卡人名称必须完整，只允许银行名称别名
    GZ_BANK_COMBINATIONS = [
        # 1. Tan Zee Liang (GX Bank) - 支持银行别名
        ('GX BANK', 'TAN ZEE LIANG'),
        ('GXBANK', 'TAN ZEE LIANG'),
        
        # 2. Yeo Chee Wang (Maybank)
        ('MAYBANK', 'YEO CHEE WANG'),
        
        # 3. Yeo Chee Wang (GX Bank) - 支持银行别名
        ('GX BANK', 'YEO CHEE WANG'),
        ('GXBANK', 'YEO CHEE WANG'),
        
        # 4. Yeo Chee Wang (UOB)
        ('UOB', 'YEO CHEE WANG'),
        
        # 5. Yeo Chee Wang (OCBC)
        ('OCBC', 'YEO CHEE WANG'),
        
        # 6. Teo Yok Chu (OCBC)
        ('OCBC', 'TEO YOK CHU'),
        
        # 7. Infinite GZ Sdn Bhd (Hong Leong Bank) - 完整法定名称强制执行，支持银行别名
        ('HONG LEONG BANK', 'INFINITE GZ SDN BHD'),
        ('HONG LEONG', 'INFINITE GZ SDN BHD'),
        ('HLB', 'INFINITE GZ SDN BHD'),
        
        # 8. Ai Smart Tech (Public Bank) - 支持银行别名
        ('PUBLIC BANK', 'AI SMART TECH'),
        ('PBB', 'AI SMART TECH'),
        
        # 9. Ai Smart Tech (Alliance Bank) - 支持银行别名
        ('ALLIANCE BANK', 'AI SMART TECH'),
        ('ALLIANCE', 'AI SMART TECH')
    ]
    
    def __init__(self, db_path: str = 'db/smart_loan_manager.db'):
        self.db_path = db_path
    
    def calculate_statement(self, statement_id: int) -> Dict[str, Decimal]:
        """
        计算单个账单的完整财务数据
        
        Args:
            statement_id: 账单ID
            
        Returns:
            包含所有计算结果的字典
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取账单基本信息
            cursor.execute("""
                SELECT s.id, s.statement_month, s.previous_balance_total,
                       cc.bank_name, cc.card_holder_name, c.name as customer_name
                FROM statements s
                JOIN credit_cards cc ON s.card_id = cc.id
                JOIN customers c ON cc.customer_id = c.id
                WHERE s.id = ?
            """, (statement_id,))
            
            stmt_row = cursor.fetchone()
            if not stmt_row:
                raise ValueError(f"Statement {statement_id} not found")
            
            statement_info = {
                'id': stmt_row[0],
                'statement_month': stmt_row[1],
                'previous_balance': Decimal(str(stmt_row[2] or 0)),
                'bank_name': stmt_row[3],
                'card_holder_name': stmt_row[4],
                'customer_name': stmt_row[5]
            }
            
            # 获取所有交易
            cursor.execute("""
                SELECT id, transaction_date, description, amount, 
                       transaction_type, category
                FROM transactions
                WHERE statement_id = ?
                ORDER BY transaction_date
            """, (statement_id,))
            
            transactions = []
            for row in cursor.fetchall():
                transactions.append({
                    'id': row[0],
                    'date': row[1],
                    'description': row[2] or '',
                    'amount': Decimal(str(row[3] or 0)),
                    'type': row[4],  # 'DR' or 'CR'
                    'category': row[5] or ''
                })
        
        # 执行第1轮计算
        round1_results = self._calculate_round_1(
            statement_info, 
            transactions
        )
        
        # 执行第2轮计算（GZ's Payment2）
        gz_payment2 = self._calculate_gz_payment2(
            statement_info['statement_month'],
            statement_info['customer_name']
        )
        
        # 最终计算
        final_results = self._calculate_final(round1_results, gz_payment2)
        
        return {
            **statement_info,
            **round1_results,
            'gz_payment2': gz_payment2,
            **final_results
        }
    
    def _calculate_round_1(self, statement_info: Dict, transactions: List[Dict]) -> Dict[str, Decimal]:
        """
        第1轮计算：6个基础项目
        
        Returns:
            {
                'owner_expenses': Decimal,
                'gz_expenses': Decimal,
                'owner_payment': Decimal,
                'gz_payment1': Decimal,
                'owner_os_bal_round1': Decimal,
                'gz_os_bal_round1': Decimal,
                'total_dr': Decimal,
                'total_cr': Decimal
            }
        """
        owner_expenses = Decimal('0')
        gz_expenses = Decimal('0')
        total_cr = Decimal('0')
        owner_payment = Decimal('0')
        total_dr = Decimal('0')
        
        customer_name_upper = statement_info['customer_name'].upper()
        
        for txn in transactions:
            desc_upper = txn['description'].upper()
            amount = txn['amount']
            
            if txn['type'] == 'DR':
                total_dr += amount
                
                # 判断是否为Supplier交易
                is_supplier = any(supplier in desc_upper for supplier in self.SUPPLIERS)
                
                if is_supplier:
                    # Supplier交易归入 GZ's Expenses
                    gz_expenses += amount
                else:
                    # 非Supplier交易归入 Owner's Expenses
                    owner_expenses += amount
            
            elif txn['type'] == 'CR':
                total_cr += amount
                
                # 规则1: CR记录有客户名字 → Owner's Payment
                # 规则2: CR记录无任何details → Owner's Payment
                if customer_name_upper in desc_upper or not txn['description'].strip():
                    owner_payment += amount
        
        # 4. GZ's Payment1 = 所有CR - Owner's Payment（使用排除法）
        gz_payment1 = total_cr - owner_payment
        
        # 5. Owner's OS Bal = Previous Balance + Owner's Expenses - Owner's Payment
        # ⚠️ 允许负数！
        owner_os_bal_round1 = (
            statement_info['previous_balance'] + 
            owner_expenses - 
            owner_payment
        )
        
        # 6. GZ's OS Bal = Previous Balance + GZ's Expenses - GZ's Payment1
        # ⚠️ 允许负数！
        gz_os_bal_round1 = (
            statement_info['previous_balance'] + 
            gz_expenses - 
            gz_payment1
        )
        
        return {
            'owner_expenses': owner_expenses,
            'gz_expenses': gz_expenses,
            'owner_payment': owner_payment,
            'gz_payment1': gz_payment1,
            'owner_os_bal_round1': owner_os_bal_round1,
            'gz_os_bal_round1': gz_os_bal_round1,
            'total_dr': total_dr,
            'total_cr': total_cr
        }
    
    def _calculate_gz_payment2(self, statement_month: str, customer_name: str) -> Decimal:
        """
        第2轮计算：GZ's Payment2
        
        计算从9个GZ Bank转账到客户银行账户的金额
        **强制执行9个银行+持卡人精确配对**
        
        Args:
            statement_month: 账单月份 (YYYY-MM格式)
            customer_name: 客户名称
            
        Returns:
            GZ's Payment2金额
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 获取该月所有CR转账记录
            cursor.execute("""
                SELECT id, source_bank, source_account_holder, amount
                FROM bank_transfers
                WHERE customer_name = ?
                  AND strftime('%Y-%m', transfer_date) = ?
                  AND transfer_type = 'CR'
            """, (customer_name, statement_month))
            
            transfers = cursor.fetchall()
            
            # 强制执行9个GZ Bank组合匹配
            gz_payment2_total = Decimal('0.00')
            
            for transfer in transfers:
                source_bank = (transfer[1] or '').upper()
                source_holder = (transfer[2] or '').upper()
                amount = Decimal(str(transfer[3] or 0))
                
                # 检查是否匹配9个GZ Bank组合
                is_gz_transfer = False
                for bank, holder in self.GZ_BANK_COMBINATIONS:
                    if bank in source_bank and holder in source_holder:
                        is_gz_transfer = True
                        break
                
                if is_gz_transfer:
                    gz_payment2_total += amount
            
            return gz_payment2_total
    
    def _calculate_final(self, round1: Dict[str, Decimal], gz_payment2: Decimal) -> Dict[str, Decimal]:
        """
        最终计算
        
        Args:
            round1: 第1轮计算结果
            gz_payment2: GZ's Payment2
            
        Returns:
            {
                'final_owner_os_bal': Decimal,
                'final_gz_os_bal': Decimal
            }
        """
        # 8. FINAL Owner OS Bal = Owner's OS Bal（第1轮）
        final_owner_os_bal = round1['owner_os_bal_round1']
        
        # 9. FINAL GZ OS Bal = GZ's OS Bal（第1轮）- GZ's Payment2
        final_gz_os_bal = round1['gz_os_bal_round1'] - gz_payment2
        
        return {
            'final_owner_os_bal': final_owner_os_bal,
            'final_gz_os_bal': final_gz_os_bal
        }
    
    def batch_calculate_month(self, customer_id: int, year_month: str) -> List[Dict]:
        """
        批量计算某客户某月的所有账单
        
        Args:
            customer_id: 客户ID
            year_month: 年月 (YYYY-MM格式)
            
        Returns:
            所有账单的计算结果列表
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT s.id
                FROM statements s
                JOIN credit_cards cc ON s.card_id = cc.id
                WHERE cc.customer_id = ?
                  AND s.statement_month = ?
            """, (customer_id, year_month))
            
            statement_ids = [row[0] for row in cursor.fetchall()]
        
        results = []
        for stmt_id in statement_ids:
            try:
                calc_result = self.calculate_statement(stmt_id)
                results.append(calc_result)
            except Exception as e:
                print(f"❌ 计算账单 {stmt_id} 失败: {e}")
                continue
        
        return results
