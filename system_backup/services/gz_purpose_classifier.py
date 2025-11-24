"""
INFINITE GZ Transfer Purpose Classifier
转账用途分类器

功能：
1. 判断GZ转账用途（Card Due Assist vs Loan/Credit Assist vs Build Profile）
2. 分析转账描述关键词
3. 检查转账后是否有相关信用卡付款记录
"""

import sqlite3
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re


class GZPurposeClassifier:
    """GZ转账用途分类器"""

    def __init__(self, db_path='db/smart_loan_manager.db'):
        self.db_path = db_path

        self.card_keywords = [
            'card', 'credit card', 'visa', 'mastercard', 'payment',
            'card due', 'card payment', 'cc payment'
        ]

        self.loan_keywords = [
            'loan', 'credit', 'borrow', 'lending', 'advance',
            'loan assist', 'credit assist'
        ]

        self.profile_keywords = [
            'build profile', 'profile', 'statement', 'flow',
            'bank statement', 'transaction history'
        ]

    def _normalize_text(self, text: str) -> str:
        """标准化文本"""
        if not text:
            return ''
        return text.lower().strip()

    def _check_keywords(self, text: str, keywords: List[str]) -> bool:
        """检查文本是否包含关键词"""
        normalized = self._normalize_text(text)
        for keyword in keywords:
            if keyword in normalized:
                return True
        return False

    def _find_related_card_payments(self, 
                                     customer_id: int, 
                                     transfer_date: str,
                                     transfer_amount: float,
                                     days_window: int = 7) -> List[Dict]:
        """
        查找转账后X天内的信用卡付款记录

        Args:
            customer_id: 客户ID
            transfer_date: 转账日期
            transfer_amount: 转账金额
            days_window: 时间窗口（天）

        Returns:
            匹配的信用卡付款记录列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        transfer_dt = datetime.strptime(transfer_date, '%Y-%m-%d')
        end_date = (transfer_dt + timedelta(days=days_window)).strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT 
                t.id, t.transaction_date, t.amount, t.description,
                cc.card_number_last4, cc.bank_name
            FROM transactions t
            INNER JOIN monthly_statements ms ON t.monthly_statement_id = ms.id
            LEFT JOIN credit_cards cc ON ms.card_id = cc.id
            WHERE ms.customer_id = ?
                AND t.transaction_date >= ?
                AND t.transaction_date <= ?
                AND t.transaction_type = 'payment'
                AND cc.id IS NOT NULL
            ORDER BY t.transaction_date ASC
        ''', (customer_id, transfer_date, end_date))

        payments = []
        for row in cursor.fetchall():
            payments.append({
                'id': row[0],
                'date': row[1],
                'amount': row[2],
                'description': row[3],
                'card_last4': row[4],
                'bank': row[5]
            })

        conn.close()
        return payments

    def classify_transfer_purpose(self,
                                   customer_id: int,
                                   transfer_date: str,
                                   transfer_amount: float,
                                   description: str = '',
                                   notes: str = '') -> Dict:
        """
        分类GZ转账用途

        Args:
            customer_id: 客户ID
            transfer_date: 转账日期
            transfer_amount: 转账金额
            description: 转账描述
            notes: 备注

        Returns:
            {
                'purpose': str,  # 'Card Due Assist', 'Loan/Credit Assist', 'Build Profile', 'Unknown'
                'confidence': str,  # 'high', 'medium', 'low'
                'reason': str,
                'related_payments': List[Dict]
            }
        """
        combined_text = f"{description} {notes}".lower()

        if self._check_keywords(combined_text, self.card_keywords):
            return {
                'purpose': 'Card Due Assist',
                'confidence': 'high',
                'reason': '转账描述包含信用卡关键词',
                'related_payments': []
            }

        related_payments = self._find_related_card_payments(
            customer_id, transfer_date, transfer_amount
        )

        if related_payments:
            matching_payment = None
            for payment in related_payments:
                amount_diff = abs(payment['amount'] - transfer_amount)
                if amount_diff < 100:
                    matching_payment = payment
                    break

            if matching_payment:
                return {
                    'purpose': 'Card Due Assist',
                    'confidence': 'high',
                    'reason': f"转账后{matching_payment['date']}有金额相近的信用卡付款",
                    'related_payments': [matching_payment]
                }
            else:
                return {
                    'purpose': 'Card Due Assist',
                    'confidence': 'medium',
                    'reason': f'转账后{len(related_payments)}天内有信用卡付款记录',
                    'related_payments': related_payments
                }

        if self._check_keywords(combined_text, self.loan_keywords):
            return {
                'purpose': 'Loan/Credit Assist',
                'confidence': 'high',
                'reason': '转账描述包含借贷关键词',
                'related_payments': []
            }

        if self._check_keywords(combined_text, self.profile_keywords):
            return {
                'purpose': 'Build Profile',
                'confidence': 'high',
                'reason': '转账描述包含建立流水profile关键词',
                'related_payments': []
            }

        return {
            'purpose': 'Unknown',
            'confidence': 'low',
            'reason': '无法自动判断用途，需要人工确认',
            'related_payments': []
        }

    def update_transfer_purpose(self, transfer_id: int, purpose: str, notes: Optional[str] = None):
        """更新GZ转账记录的用途"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if notes:
            cursor.execute('''
                UPDATE gz_transfers
                SET transfer_purpose = ?, notes = ?
                WHERE id = ?
            ''', (purpose, notes, transfer_id))
        else:
            cursor.execute('''
                UPDATE gz_transfers
                SET transfer_purpose = ?
                WHERE id = ?
            ''', (purpose, transfer_id))

        conn.commit()
        conn.close()

    def batch_classify_transfers(self, customer_id: Optional[int] = None) -> Dict:
        """
        批量分类GZ转账用途

        Args:
            customer_id: 客户ID（None表示所有客户）

        Returns:
            统计信息
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if customer_id:
            cursor.execute('''
                SELECT id, customer_id, transfer_date, amount, source_account, notes
                FROM gz_transfers
                WHERE customer_id = ? AND transfer_purpose = 'Unknown'
            ''', (customer_id,))
        else:
            cursor.execute('''
                SELECT id, customer_id, transfer_date, amount, source_account, notes
                FROM gz_transfers
                WHERE transfer_purpose = 'Unknown'
            ''')

        transfers = cursor.fetchall()
        conn.close()

        stats = {
            'total': len(transfers),
            'card_due_assist': 0,
            'loan_assist': 0,
            'build_profile': 0,
            'still_unknown': 0
        }

        for transfer in transfers:
            transfer_id, cust_id, date, amount, source, notes = transfer

            result = self.classify_transfer_purpose(
                customer_id=cust_id,
                transfer_date=date,
                transfer_amount=amount,
                description=source,
                notes=notes or ''
            )

            self.update_transfer_purpose(
                transfer_id, 
                result['purpose'],
                result['reason']
            )

            if result['purpose'] == 'Card Due Assist':
                stats['card_due_assist'] += 1
            elif result['purpose'] == 'Loan/Credit Assist':
                stats['loan_assist'] += 1
            elif result['purpose'] == 'Build Profile':
                stats['build_profile'] += 1
            else:
                stats['still_unknown'] += 1

        return stats


def test_purpose_classifier():
    """测试用途分类器（简化版，只测试关键词匹配）"""
    classifier = GZPurposeClassifier()

    test_cases = [
        {
            'description': 'CHANG CHOON CHO PAYMENT CREDIT CARD',
            'notes': '',
            'expected': 'Card Due Assist'
        },
        {
            'description': 'FUND TRANSFER',
            'notes': 'for loan assistance',
            'expected': 'Loan/Credit Assist'
        },
        {
            'description': 'TRANSFER',
            'notes': 'help build bank statement profile',
            'expected': 'Build Profile'
        },
        {
            'description': 'DIRECTOR FEES',
            'notes': '',
            'expected': 'Unknown'
        }
    ]

    print("=" * 80)
    print("GZ转账用途分类器测试（关键词匹配）")
    print("=" * 80)

    for i, test in enumerate(test_cases, 1):
        combined_text = f"{test['description']} {test['notes']}".lower()
        
        if classifier._check_keywords(combined_text, classifier.card_keywords):
            purpose = 'Card Due Assist'
            confidence = 'high'
            reason = '转账描述包含信用卡关键词'
        elif classifier._check_keywords(combined_text, classifier.loan_keywords):
            purpose = 'Loan/Credit Assist'
            confidence = 'high'
            reason = '转账描述包含借贷关键词'
        elif classifier._check_keywords(combined_text, classifier.profile_keywords):
            purpose = 'Build Profile'
            confidence = 'high'
            reason = '转账描述包含建立流水profile关键词'
        else:
            purpose = 'Unknown'
            confidence = 'low'
            reason = '无法自动判断用途，需要人工确认'

        status = "✅" if purpose == test['expected'] else "❌"
        print(f"\n测试 {i}: {status}")
        print(f"描述: {test['description']}")
        print(f"备注: {test['notes']}")
        print(f"预期: {test['expected']}")
        print(f"结果: {purpose}")
        print(f"置信度: {confidence}")
        print(f"原因: {reason}")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    test_purpose_classifier()
