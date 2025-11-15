"""
INFINITE GZ Credit Card System - Core Processor
GZ信用卡系统核心处理器

功能：
1. 处理GZ转账（识别来源、判断用途）
2. 管理GZ OS Balance（信用卡代付专用账本）
3. 管理Loan Outstanding（借贷专用账本）
4. 付款分类（Owner's Payment / GZ's Payment Direct/Indirect）
5. 自动生成财务报表
"""

import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from services.gz_identifier import GZIdentifier
from services.gz_purpose_classifier import GZPurposeClassifier


class InfiniteGZProcessor:
    """INFINITE GZ核心处理器"""

    def __init__(self, db_path='db/smart_loan_manager.db'):
        self.db_path = db_path
        self.identifier = GZIdentifier(db_path)
        self.classifier = GZPurposeClassifier(db_path)

    def process_bank_transfer(self,
                               customer_id: int,
                               transfer_date: str,
                               amount: float,
                               description: str,
                               bank_name: Optional[str] = None,
                               notes: Optional[str] = None) -> Dict:
        """
        处理银行转账记录

        流程：
        1. 识别转账来源（是否来自GZ）
        2. 如果是GZ转账，判断用途（Card Due Assist / Loan Assist）
        3. 保存到gz_transfers表
        4. 更新对应的GZ OS Balance或Loan Outstanding

        Returns:
            {
                'status': str,
                'is_gz_transfer': bool,
                'transfer_purpose': str,
                'transfer_id': Optional[int],
                'message': str
            }
        """
        source_result = self.identifier.identify_transfer_source(
            transaction_date=transfer_date,
            amount=amount,
            description=description,
            bank_name=bank_name
        )

        if not source_result['is_from_gz']:
            return {
                'status': 'not_gz',
                'is_gz_transfer': False,
                'transfer_purpose': 'N/A',
                'transfer_id': None,
                'message': '这不是GZ转账'
            }

        combined_text = f"{description} {notes or ''}".lower()
        
        if self.classifier._check_keywords(combined_text, self.classifier.card_keywords):
            purpose = 'Card Due Assist'
            purpose_reason = '转账描述包含信用卡关键词'
        elif self.classifier._check_keywords(combined_text, self.classifier.loan_keywords):
            purpose = 'Loan/Credit Assist'
            purpose_reason = '转账描述包含借贷关键词'
        elif self.classifier._check_keywords(combined_text, self.classifier.profile_keywords):
            purpose = 'Build Profile'
            purpose_reason = '转账描述包含建立流水profile关键词'
        else:
            purpose = 'Unknown'
            purpose_reason = '无法自动判断用途，需要人工确认'
        
        purpose_result = {
            'purpose': purpose,
            'confidence': 'high' if purpose != 'Unknown' else 'low',
            'reason': purpose_reason
        }

        matched_account = source_result['matched_account']
        transfer_id = self.identifier.save_gz_transfer(
            customer_id=customer_id,
            transfer_date=transfer_date,
            amount=amount,
            source_account=matched_account['name'],
            source_bank=matched_account['bank'],
            transfer_purpose=purpose_result['purpose'],
            notes=f"{purpose_result['reason']} | {notes or ''}"
        )

        if purpose_result['purpose'] == 'Card Due Assist':
            self._update_gz_os_balance(
                customer_id=customer_id,
                transfer_date=transfer_date,
                amount=amount,
                transfer_id=transfer_id
            )
        elif purpose_result['purpose'] == 'Loan/Credit Assist':
            self._create_loan_outstanding(
                customer_id=customer_id,
                loan_date=transfer_date,
                principal_amount=amount,
                transfer_id=transfer_id
            )

        return {
            'status': 'success',
            'is_gz_transfer': True,
            'transfer_purpose': purpose_result['purpose'],
            'transfer_id': transfer_id,
            'matched_account': matched_account,
            'confidence': purpose_result['confidence'],
            'message': f"GZ转账处理成功：{purpose_result['purpose']}"
        }

    def _update_gz_os_balance(self, 
                               customer_id: int,
                               transfer_date: str,
                               amount: float,
                               transfer_id: int,
                               card_id: Optional[int] = None):
        """
        更新GZ OS Balance（信用卡代付专用账本）

        规则：
        - GZ转账给客户 → 增加GZ OS Balance
        - 客户还款给GZ → 减少GZ OS Balance
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        statement_month = transfer_date[:7]

        cursor.execute('''
            SELECT id, closing_balance 
            FROM gz_os_balance 
            WHERE customer_id = ? AND statement_month = ?
        ''', (customer_id, statement_month))

        existing = cursor.fetchone()

        if existing:
            balance_id, current_balance = existing
            new_balance = current_balance + amount

            cursor.execute('''
                UPDATE gz_os_balance
                SET gz_indirect_payment = gz_indirect_payment + ?,
                    closing_balance = ?
                WHERE id = ?
            ''', (amount, new_balance, balance_id))
        else:
            cursor.execute('''
                INSERT INTO gz_os_balance (
                    customer_id, card_id, statement_month,
                    opening_balance, gz_indirect_payment, closing_balance
                ) VALUES (?, ?, ?, 0, ?, ?)
            ''', (customer_id, card_id, statement_month, amount, amount))

        conn.commit()
        conn.close()

    def _create_loan_outstanding(self,
                                  customer_id: int,
                                  loan_date: str,
                                  principal_amount: float,
                                  transfer_id: int,
                                  interest_rate: float = 0,
                                  loan_purpose: Optional[str] = None):
        """
        创建Loan Outstanding记录（借贷专用账本）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        interest_amount = principal_amount * (interest_rate / 100)
        total_amount = principal_amount + interest_amount

        cursor.execute('''
            INSERT INTO loan_outstanding (
                customer_id, loan_date, principal_amount, interest_rate,
                interest_amount, total_amount, outstanding_amount,
                loan_purpose, loan_type, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Loan/Credit Assist', 'active')
        ''', (customer_id, loan_date, principal_amount, interest_rate,
              interest_amount, total_amount, total_amount, loan_purpose))

        conn.commit()
        conn.close()

    def classify_credit_card_payment(self,
                                      customer_id: int,
                                      payment_date: str,
                                      payment_amount: float,
                                      payer_name: str,
                                      payment_description: str = '') -> str:
        """
        分类信用卡付款

        分类规则：
        1. Owner's Payment: 客户自己的账户付款
        2. GZ's Payment Direct: GZ直接付到银行
        3. GZ's Payment Indirect: GZ转给客户，客户再付

        Returns:
            'Owner' | 'GZ Direct' | 'GZ Indirect'
        """
        is_gz, matched_account = self.identifier.is_from_gz(
            transaction_description=payer_name,
            bank_name=None
        )

        if is_gz:
            if 'direct' in payment_description.lower() or 'bank' in payment_description.lower():
                return 'GZ Direct'
            else:
                return 'GZ Indirect'
        else:
            return 'Owner'

    def get_gz_os_balance_summary(self, customer_id: int, month: Optional[str] = None) -> Dict:
        """
        获取GZ OS Balance汇总

        Returns:
            {
                'customer_id': int,
                'month': str,
                'opening_balance': float,
                'total_gz_expenses': float,
                'total_gz_payments': float,
                'closing_balance': float
            }
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if month:
            cursor.execute('''
                SELECT 
                    statement_month,
                    SUM(opening_balance) as opening,
                    SUM(gz_expenses) as expenses,
                    SUM(gz_direct_payment + gz_indirect_payment) as payments,
                    SUM(closing_balance) as closing
                FROM gz_os_balance
                WHERE customer_id = ? AND statement_month = ?
                GROUP BY statement_month
            ''', (customer_id, month))
        else:
            cursor.execute('''
                SELECT 
                    'All Time' as statement_month,
                    SUM(opening_balance) as opening,
                    SUM(gz_expenses) as expenses,
                    SUM(gz_direct_payment + gz_indirect_payment) as payments,
                    SUM(closing_balance) as closing
                FROM gz_os_balance
                WHERE customer_id = ?
            ''', (customer_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'customer_id': customer_id,
                'month': row[0],
                'opening_balance': row[1] or 0,
                'total_gz_expenses': row[2] or 0,
                'total_gz_payments': row[3] or 0,
                'closing_balance': row[4] or 0
            }
        else:
            return {
                'customer_id': customer_id,
                'month': month or 'All Time',
                'opening_balance': 0,
                'total_gz_expenses': 0,
                'total_gz_payments': 0,
                'closing_balance': 0
            }

    def get_loan_outstanding_summary(self, customer_id: int) -> Dict:
        """
        获取Loan Outstanding汇总
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                COUNT(*) as total_loans,
                SUM(principal_amount) as total_principal,
                SUM(interest_amount) as total_interest,
                SUM(outstanding_amount) as total_outstanding,
                SUM(repaid_amount) as total_repaid
            FROM loan_outstanding
            WHERE customer_id = ? AND status = 'active'
        ''', (customer_id,))

        row = cursor.fetchone()
        conn.close()

        return {
            'customer_id': customer_id,
            'total_loans': row[0] or 0,
            'total_principal': row[1] or 0,
            'total_interest': row[2] or 0,
            'total_outstanding': row[3] or 0,
            'total_repaid': row[4] or 0
        }


def test_infinite_gz_processor():
    """测试INFINITE GZ处理器"""
    processor = InfiniteGZProcessor()

    print("=" * 80)
    print("INFINITE GZ系统核心处理器测试")
    print("=" * 80)

    test_transfers = [
        {
            'customer_id': 1,
            'date': '2025-02-13',
            'amount': 10000,
            'description': 'DUITNOW TRSF CR 106805 AI SMART TECH SDN. B TRANSFER FROM ABMB',
            'bank': 'ABMB',
            'expected_purpose': 'Card Due Assist'
        },
        {
            'customer_id': 1,
            'date': '2025-01-07',
            'amount': 30000,
            'description': 'DUITNOW TRSF CR 272256 AI SMART TECH SDN. B TRANSFER FROM ABMB',
            'bank': 'ABMB',
            'notes': 'for credit card payment',
            'expected_purpose': 'Card Due Assist'
        }
    ]

    print("\n测试1: 处理GZ转账识别")
    print("-" * 80)

    for i, transfer in enumerate(test_transfers, 1):
        result = processor.process_bank_transfer(
            customer_id=transfer['customer_id'],
            transfer_date=transfer['date'],
            amount=transfer['amount'],
            description=transfer['description'],
            bank_name=transfer.get('bank'),
            notes=transfer.get('notes', '')
        )

        status = "✅" if result['transfer_purpose'] == transfer['expected_purpose'] else "❌"
        print(f"\n转账 {i}: {status}")
        print(f"金额: RM {transfer['amount']:,.2f}")
        print(f"日期: {transfer['date']}")
        print(f"描述: {transfer['description'][:60]}...")
        print(f"预期用途: {transfer['expected_purpose']}")
        print(f"实际用途: {result['transfer_purpose']}")
        print(f"置信度: {result.get('confidence', 'N/A')}")
        print(f"消息: {result['message']}")

    print("\n" + "=" * 80)

    print("\n测试2: 付款分类")
    print("-" * 80)

    payment_tests = [
        {'payer': 'CHANG CHOON CHOW', 'expected': 'Owner'},
        {'payer': 'AI SMART TECH SDN BHD', 'expected': 'GZ Indirect'},
        {'payer': 'TAN ZEE LIANG', 'expected': 'GZ Indirect'}
    ]

    for i, test in enumerate(payment_tests, 1):
        classification = processor.classify_credit_card_payment(
            customer_id=1,
            payment_date='2025-01-08',
            payment_amount=10000,
            payer_name=test['payer']
        )

        status = "✅" if classification == test['expected'] else "❌"
        print(f"\n付款 {i}: {status}")
        print(f"付款人: {test['payer']}")
        print(f"预期分类: {test['expected']}")
        print(f"实际分类: {classification}")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    test_infinite_gz_processor()
