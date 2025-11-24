"""
INFINITE GZ Transfer Source Identifier
识别转账是否来自GZ银行白名单

功能：
1. 检查转账描述是否包含GZ白名单账户名
2. 模糊匹配（银行流水中的名字可能是缩写）
3. 返回识别结果和匹配的GZ账户信息
"""

import sqlite3
from typing import Dict, List, Optional, Tuple
import re


class GZIdentifier:
    """GZ转账来源识别器"""

    def __init__(self, db_path='db/smart_loan_manager.db'):
        self.db_path = db_path
        self.whitelist = self._load_whitelist()

    def _load_whitelist(self) -> List[Dict]:
        """从数据库加载GZ银行白名单"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, account_holder_name, bank_name, account_type, notes
            FROM gz_bank_whitelist
            WHERE is_active = 1
        ''')

        whitelist = []
        for row in cursor.fetchall():
            whitelist.append({
                'id': row[0],
                'name': row[1],
                'bank': row[2],
                'type': row[3],
                'notes': row[4]
            })

        conn.close()
        return whitelist

    def _normalize_name(self, name: str) -> str:
        """标准化名字（去除特殊字符、转小写）"""
        normalized = name.lower()
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    def _extract_keywords(self, name: str) -> List[str]:
        """提取关键词用于匹配"""
        normalized = self._normalize_name(name)
        
        keywords = []
        if 'ai smart tech' in normalized:
            keywords.extend(['ai smart tech', 'ai smart', 'smart tech'])
        elif 'infinite gz' in normalized:
            keywords.extend(['infinite gz', 'infinite'])
        elif 'tan zee liang' in normalized:
            keywords.extend(['tan zee liang', 'tan'])
        elif 'yeo chee wang' in normalized:
            keywords.extend(['yeo chee wang', 'yeo'])
        elif 'teo yok chu' in normalized:
            keywords.extend(['teo yok chu', 'teo'])

        return keywords if keywords else [normalized]

    def is_from_gz(self, transaction_description: str, bank_name: Optional[str] = None) -> Tuple[bool, Optional[Dict]]:
        """
        判断转账是否来自GZ银行白名单

        Args:
            transaction_description: 转账描述文本
            bank_name: 银行名称（可选，用于精确匹配）

        Returns:
            (is_from_gz: bool, matched_account: Optional[Dict])
        """
        if not transaction_description:
            return False, None

        normalized_desc = self._normalize_name(transaction_description)

        for gz_account in self.whitelist:
            account_name = self._normalize_name(gz_account['name'])

            if account_name in normalized_desc:
                if bank_name:
                    if self._match_bank(gz_account['bank'], bank_name):
                        return True, gz_account
                else:
                    return True, gz_account

            keywords = self._extract_keywords(gz_account['name'])
            for keyword in keywords:
                if keyword in normalized_desc:
                    if bank_name:
                        if self._match_bank(gz_account['bank'], bank_name):
                            return True, gz_account
                    else:
                        return True, gz_account

        return False, None

    def _match_bank(self, whitelist_bank: str, transaction_bank: str) -> bool:
        """匹配银行名称（支持缩写）"""
        bank_mapping = {
            'PBB': ['public', 'pbb', 'public bank', 'public islamic'],
            'Alliance': ['alliance', 'abmb'],
            'HLB': ['hong leong', 'hlb', 'hl bank'],
            'GX bank': ['gx', 'gxs', 'gx bank'],
            'MBB': ['maybank', 'mbb', 'malayan'],
            'UOB': ['uob', 'united overseas'],
            'OCBC': ['ocbc']
        }

        whitelist_bank_lower = whitelist_bank.lower()
        transaction_bank_lower = transaction_bank.lower()

        for key, aliases in bank_mapping.items():
            if key.lower() in whitelist_bank_lower or key.lower() == whitelist_bank_lower:
                for alias in aliases:
                    if alias in transaction_bank_lower:
                        return True

        return whitelist_bank_lower in transaction_bank_lower

    def identify_transfer_source(self, 
                                   transaction_date: str,
                                   amount: float,
                                   description: str,
                                   bank_name: Optional[str] = None) -> Dict:
        """
        识别转账来源并返回详细信息

        Args:
            transaction_date: 转账日期
            amount: 转账金额
            description: 转账描述
            bank_name: 银行名称

        Returns:
            {
                'is_from_gz': bool,
                'matched_account': Optional[Dict],
                'confidence': str ('high', 'medium', 'low'),
                'source_type': str ('GZ Transfer', 'Other Transfer')
            }
        """
        is_from_gz, matched_account = self.is_from_gz(description, bank_name)

        confidence = 'low'
        if is_from_gz and matched_account:
            if bank_name and self._match_bank(matched_account['bank'], bank_name):
                confidence = 'high'
            else:
                confidence = 'medium'

        return {
            'is_from_gz': is_from_gz,
            'matched_account': matched_account,
            'confidence': confidence,
            'source_type': 'GZ Transfer' if is_from_gz else 'Other Transfer'
        }

    def save_gz_transfer(self, 
                         customer_id: int,
                         transfer_date: str,
                         amount: float,
                         source_account: str,
                         source_bank: str,
                         destination_account: Optional[str] = None,
                         transfer_purpose: str = 'Unknown',
                         bank_statement_id: Optional[int] = None,
                         notes: Optional[str] = None) -> int:
        """
        保存GZ转账记录到数据库

        Returns:
            transfer_id: 新创建的转账记录ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO gz_transfers (
                customer_id, transfer_date, amount, source_account, source_bank,
                destination_account, transfer_purpose, is_from_gz_whitelist,
                bank_statement_id, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        ''', (customer_id, transfer_date, amount, source_account, source_bank,
              destination_account, transfer_purpose, bank_statement_id, notes))

        transfer_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return transfer_id


def test_gz_identifier():
    """测试GZ识别器"""
    identifier = GZIdentifier()

    test_cases = [
        {
            'description': 'DUITNOW TRSF CR 106805 AI SMART TECH SDN. B TRANSFER FROM ABMB',
            'bank': 'ABMB',
            'expected': True
        },
        {
            'description': 'DUITNOW TRSF CR 146906 YONG SIOK NEE FUND TRANSFER',
            'bank': 'HLB',
            'expected': False
        },
        {
            'description': 'DUITNOW TRSF CR 098145 TAN ZEE LIANG TRANSFER',
            'bank': 'GX',
            'expected': True
        },
        {
            'description': 'DUITNOW TRSF CR 199073 TAN ZEE LIANG TRANSFER',
            'bank': 'GX',
            'expected': True
        }
    ]

    print("=" * 80)
    print("GZ转账识别器测试")
    print("=" * 80)

    for i, test in enumerate(test_cases, 1):
        result = identifier.identify_transfer_source(
            transaction_date='2025-01-01',
            amount=10000,
            description=test['description'],
            bank_name=test['bank']
        )

        status = "✅" if result['is_from_gz'] == test['expected'] else "❌"
        print(f"\n测试 {i}: {status}")
        print(f"描述: {test['description'][:60]}...")
        print(f"预期: {'GZ转账' if test['expected'] else '非GZ转账'}")
        print(f"结果: {result['source_type']}")
        print(f"置信度: {result['confidence']}")
        if result['matched_account']:
            print(f"匹配账户: {result['matched_account']['name']} ({result['matched_account']['bank']})")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    test_gz_identifier()
