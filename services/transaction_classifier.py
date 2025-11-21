
"""
交易分类器 - Transaction Classifier (Infinite GZ Module 4)
自动分类信用卡交易为: Owner's Expenses, GZ's Expenses, Owner's Payment, GZ's Payment

业务规则：
1. 费用分类：基于供应商名称模糊匹配（80%相似度）
2. 付款分类：基于客户姓名和GZ账户信息
3. 保守处理原则：不确定时归为Owner
"""

import sqlite3
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher


class TransactionClassifier:
    """智能交易分类器 - Infinite GZ Module 4"""
    
    def __init__(self, 
                 db_path: str = 'db/smart_loan_manager.db',
                 suppliers_list: Optional[List[str]] = None,
                 gz_bank_accounts: Optional[List[str]] = None,
                 customer_name: Optional[str] = None):
        """
        初始化分类器
        
        Args:
            db_path: 数据库路径
            suppliers_list: 7个主要供应商列表
            gz_bank_accounts: GZ公司银行账户列表
            customer_name: 客户姓名（用于付款分类）
        """
        self.db_path = db_path
        
        # 7个主要供应商（可自定义或使用默认值）
        self.suppliers = suppliers_list or [
            '7SL',
            'Dinas Raub',
            'SYC Hainan',
            'Ai Smart Tech',
            'HUAWEI',
            'Pasar Raya',
            'Puchong Herbs'
        ]
        
        # GZ公司银行账户
        self.gz_bank_accounts = gz_bank_accounts or [
            'INFINITE GZ SDN BHD',
            'INFINITE GZ',
            'GZ SDN BHD'
        ]
        
        # 客户姓名
        self.customer_name = customer_name
        
        # 模糊匹配阈值（98%相似度）
        self.similarity_threshold = 0.98
        
        # 付款关键词
        self.payment_keywords = [
            'PAYMENT', 'BAYARAN', 'DIRECT DEBIT', 'AUTO DEBIT',
            'BANK TRANSFER', 'ONLINE PAYMENT', 'PAYMENT RECEIVED',
            'CREDIT', 'CR'
        ]
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        计算两个字符串的相似度
        
        Args:
            str1: 字符串1
            str2: 字符串2
            
        Returns:
            相似度分数 (0-1)
        """
        str1_upper = str1.upper().strip()
        str2_upper = str2.upper().strip()
        
        return SequenceMatcher(None, str1_upper, str2_upper).ratio()
    
    def _is_supplier_fuzzy_match(self, merchant_name: str) -> Tuple[bool, Optional[str]]:
        """
        模糊匹配供应商名称
        
        Args:
            merchant_name: 商家名称
            
        Returns:
            (是否匹配, 匹配的供应商名称)
        """
        if not merchant_name:
            return False, None
        
        merchant_upper = merchant_name.upper().strip()
        
        # 1. 精确匹配（包含关系）
        for supplier in self.suppliers:
            if supplier.upper() in merchant_upper:
                return True, supplier
        
        # 2. 模糊匹配（80%相似度）
        for supplier in self.suppliers:
            similarity = self._calculate_similarity(merchant_name, supplier)
            if similarity >= self.similarity_threshold:
                return True, supplier
        
        # 3. 特殊处理：处理商家名称变体
        # 例如: "7-ELEVEN" vs "7SL", "DINAS" vs "Dinas Raub"
        merchant_normalized = merchant_upper.replace('-', '').replace('_', '').replace(' ', '')
        for supplier in self.suppliers:
            supplier_normalized = supplier.upper().replace('-', '').replace('_', '').replace(' ', '')
            if supplier_normalized in merchant_normalized or merchant_normalized in supplier_normalized:
                return True, supplier
        
        return False, None
    
    def classify_expense(self, merchant_name: str) -> Dict:
        """
        分类费用交易（消费）
        
        业务规则：
        - 如果是7个供应商之一 -> "GZ's Expenses"
        - 否则 -> "Owner's Expenses"
        
        Args:
            merchant_name: 商家名称
            
        Returns:
            {
                'category': str,  # 分类结果
                'is_supplier': bool,  # 是否为供应商
                'matched_supplier': str,  # 匹配的供应商名称
                'confidence': str  # 置信度
            }
        """
        try:
            is_supplier, matched_supplier = self._is_supplier_fuzzy_match(merchant_name)
            
            if is_supplier:
                return {
                    'category': "GZ's Expenses",
                    'is_supplier': True,
                    'matched_supplier': matched_supplier,
                    'confidence': 'high'
                }
            else:
                return {
                    'category': "Owner's Expenses",
                    'is_supplier': False,
                    'matched_supplier': None,
                    'confidence': 'high'
                }
        
        except Exception as e:
            # 错误处理：保守归为Owner
            return {
                'category': "Owner's Expenses",
                'is_supplier': False,
                'matched_supplier': None,
                'confidence': 'low',
                'error': str(e)
            }
    
    def classify_payment(self, description: str, payer_info: str = '') -> Dict:
        """
        分类付款交易
        
        业务规则：
        - Rule 1: 如果客户姓名出现在description中 -> "Owner's Payment"
        - Rule 2: 如果GZ账户出现在payer_info中 -> "GZ's Payment"
        - Rule 3: 默认保守处理 -> "Owner's Payment"
        
        Args:
            description: 交易描述
            payer_info: 付款人信息
            
        Returns:
            {
                'category': str,  # 分类结果
                'rule_applied': str,  # 应用的规则
                'confidence': str  # 置信度
            }
        """
        try:
            description_upper = description.upper() if description else ''
            payer_info_upper = payer_info.upper() if payer_info else ''
            
            # Rule 1: 客户姓名匹配
            if self.customer_name and self.customer_name.upper() in description_upper:
                return {
                    'category': "Owner's Payment",
                    'rule_applied': 'Rule 1: Customer name in description',
                    'confidence': 'high'
                }
            
            # Rule 2: GZ账户匹配
            for gz_account in self.gz_bank_accounts:
                if gz_account.upper() in payer_info_upper or gz_account.upper() in description_upper:
                    return {
                        'category': "GZ's Payment",
                        'rule_applied': 'Rule 2: GZ account in payer info',
                        'confidence': 'high',
                        'matched_account': gz_account
                    }
            
            # Rule 3: 默认保守处理
            return {
                'category': "Owner's Payment",
                'rule_applied': 'Rule 3: Default conservative',
                'confidence': 'medium'
            }
        
        except Exception as e:
            # 错误处理：保守归为Owner
            return {
                'category': "Owner's Payment",
                'rule_applied': 'Error fallback',
                'confidence': 'low',
                'error': str(e)
            }
    
    def classify_single_transaction(self, 
                                   transaction_type: str,
                                   description: str,
                                   merchant_name: str = '',
                                   payer_info: str = '') -> Dict:
        """
        分类单个交易（统一接口）
        
        Args:
            transaction_type: 交易类型 ('expense' 或 'payment')
            description: 交易描述
            merchant_name: 商家名称（用于费用分类）
            payer_info: 付款人信息（用于付款分类）
            
        Returns:
            分类结果字典
        """
        if transaction_type.lower() in ['expense', 'purchase', 'debit']:
            return self.classify_expense(merchant_name or description)
        elif transaction_type.lower() in ['payment', 'credit', 'cr']:
            return self.classify_payment(description, payer_info)
        else:
            return {
                'category': "Owner's Expenses",
                'rule_applied': 'Unknown type fallback',
                'confidence': 'low'
            }
    
    def batch_classify_transactions(self, transactions: List[Dict]) -> Dict:
        """
        批量分类交易
        
        Args:
            transactions: 交易列表，每个交易包含：
                {
                    'id': int,
                    'transaction_type': str,
                    'description': str,
                    'merchant_name': str (可选),
                    'payer_info': str (可选)
                }
        
        Returns:
            {
                'total': int,
                'classified': int,
                'results': List[Dict],
                'summary': {
                    "Owner's Expenses": int,
                    "GZ's Expenses": int,
                    "Owner's Payment": int,
                    "GZ's Payment": int
                },
                'errors': List[Dict]
            }
        """
        results = []
        summary = {
            "Owner's Expenses": 0,
            "GZ's Expenses": 0,
            "Owner's Payment": 0,
            "GZ's Payment": 0
        }
        errors = []
        
        for txn in transactions:
            try:
                result = self.classify_single_transaction(
                    transaction_type=txn.get('transaction_type', 'expense'),
                    description=txn.get('description', ''),
                    merchant_name=txn.get('merchant_name', ''),
                    payer_info=txn.get('payer_info', '')
                )
                
                result['transaction_id'] = txn.get('id')
                results.append(result)
                
                category = result.get('category', "Owner's Expenses")
                summary[category] = summary.get(category, 0) + 1
                
            except Exception as e:
                errors.append({
                    'transaction_id': txn.get('id'),
                    'error': str(e)
                })
        
        return {
            'total': len(transactions),
            'classified': len(results),
            'results': results,
            'summary': summary,
            'errors': errors
        }
    
    def update_database_classifications(self, transaction_results: List[Dict]) -> int:
        """
        将分类结果更新到数据库
        
        Args:
            transaction_results: batch_classify_transactions 返回的 results
            
        Returns:
            更新的记录数
        """
        updated = 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for result in transaction_results:
                txn_id = result.get('transaction_id')
                category = result.get('category')
                
                if txn_id and category:
                    cursor.execute("""
                        UPDATE transactions 
                        SET category = ?
                        WHERE id = ?
                    """, (category, txn_id))
                    updated += 1
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"数据库更新错误: {e}")
        
        return updated


# ============================================================
# 单元测试和示例数据
# ============================================================

def run_unit_tests():
    """运行单元测试"""
    print("=" * 80)
    print("Infinite GZ Transaction Classifier - 单元测试")
    print("=" * 80)
    
    # 初始化分类器
    classifier = TransactionClassifier(
        customer_name='CHANG CHOON CHOW',
        suppliers_list=['7SL', 'Dinas Raub', 'SYC Hainan', 'Ai Smart Tech', 'HUAWEI', 'Pasar Raya', 'Puchong Herbs'],
        gz_bank_accounts=['INFINITE GZ SDN BHD', 'INFINITE GZ']
    )
    
    # 测试1: 费用分类 - 供应商精确匹配
    print("\n【测试1】费用分类 - 供应商精确匹配")
    result = classifier.classify_expense('7SL TECH SDN BHD')
    print(f"商家: 7SL TECH SDN BHD")
    print(f"分类: {result['category']}")
    print(f"是否供应商: {result['is_supplier']}")
    print(f"匹配供应商: {result['matched_supplier']}")
    assert result['category'] == "GZ's Expenses", "测试1失败"
    print("✅ 测试1通过")
    
    # 测试2: 费用分类 - 供应商模糊匹配
    print("\n【测试2】费用分类 - 供应商模糊匹配")
    result = classifier.classify_expense('HUAWEI TECHNOLOGY')
    print(f"商家: HUAWEI TECHNOLOGY")
    print(f"分类: {result['category']}")
    print(f"相似度匹配: {result['matched_supplier']}")
    assert result['category'] == "GZ's Expenses", "测试2失败"
    print("✅ 测试2通过")
    
    # 测试3: 费用分类 - 非供应商
    print("\n【测试3】费用分类 - 非供应商")
    result = classifier.classify_expense('GRAB FOOD DELIVERY')
    print(f"商家: GRAB FOOD DELIVERY")
    print(f"分类: {result['category']}")
    assert result['category'] == "Owner's Expenses", "测试3失败"
    print("✅ 测试3通过")
    
    # 测试4: 付款分类 - Rule 1 (客户姓名)
    print("\n【测试4】付款分类 - Rule 1 (客户姓名)")
    result = classifier.classify_payment('PAYMENT FROM CHANG CHOON CHOW', '')
    print(f"描述: PAYMENT FROM CHANG CHOON CHOW")
    print(f"分类: {result['category']}")
    print(f"应用规则: {result['rule_applied']}")
    assert result['category'] == "Owner's Payment", "测试4失败"
    print("✅ 测试4通过")
    
    # 测试5: 付款分类 - Rule 2 (GZ账户)
    print("\n【测试5】付款分类 - Rule 2 (GZ账户)")
    result = classifier.classify_payment('BANK TRANSFER', 'FROM INFINITE GZ SDN BHD')
    print(f"描述: BANK TRANSFER")
    print(f"付款人: FROM INFINITE GZ SDN BHD")
    print(f"分类: {result['category']}")
    print(f"应用规则: {result['rule_applied']}")
    assert result['category'] == "GZ's Payment", "测试5失败"
    print("✅ 测试5通过")
    
    # 测试6: 批量分类
    print("\n【测试6】批量分类交易")
    test_transactions = [
        {'id': 1, 'transaction_type': 'expense', 'description': '7SL PURCHASE', 'merchant_name': '7SL'},
        {'id': 2, 'transaction_type': 'expense', 'description': 'GRAB FOOD', 'merchant_name': 'GRAB'},
        {'id': 3, 'transaction_type': 'payment', 'description': 'PAYMENT FROM CHANG CHOON CHOW', 'payer_info': ''},
        {'id': 4, 'transaction_type': 'payment', 'description': 'PAYMENT', 'payer_info': 'INFINITE GZ SDN BHD'},
    ]
    
    batch_result = classifier.batch_classify_transactions(test_transactions)
    print(f"总交易数: {batch_result['total']}")
    print(f"分类成功: {batch_result['classified']}")
    print(f"分类汇总: {batch_result['summary']}")
    assert batch_result['total'] == 4, "测试6失败"
    assert batch_result['classified'] == 4, "测试6失败"
    print("✅ 测试6通过")
    
    print("\n" + "=" * 80)
    print("✅ 所有测试通过！")
    print("=" * 80)


# 示例数据
EXAMPLE_TRANSACTIONS = [
    {
        'id': 1,
        'transaction_type': 'expense',
        'description': '7SL TECH SDN BHD - OFFICE SUPPLIES',
        'merchant_name': '7SL TECH SDN BHD',
        'amount': 150.00
    },
    {
        'id': 2,
        'transaction_type': 'expense',
        'description': 'HUAWEI CLOUD SERVICES',
        'merchant_name': 'HUAWEI',
        'amount': 300.00
    },
    {
        'id': 3,
        'transaction_type': 'expense',
        'description': 'GRAB FOOD DELIVERY',
        'merchant_name': 'GRAB',
        'amount': 25.50
    },
    {
        'id': 4,
        'transaction_type': 'payment',
        'description': 'PAYMENT RECEIVED FROM CHANG CHOON CHOW',
        'payer_info': 'CHANG CHOON CHOW',
        'amount': -500.00
    },
    {
        'id': 5,
        'transaction_type': 'payment',
        'description': 'BANK TRANSFER',
        'payer_info': 'INFINITE GZ SDN BHD',
        'amount': -1000.00
    }
]


if __name__ == '__main__':
    # 运行单元测试
    run_unit_tests()
    
    # 演示批量分类
    print("\n\n" + "=" * 80)
    print("示例：批量分类交易")
    print("=" * 80)
    
    classifier = TransactionClassifier(
        customer_name='CHANG CHOON CHOW',
        suppliers_list=['7SL', 'Dinas Raub', 'SYC Hainan', 'Ai Smart Tech', 'HUAWEI', 'Pasar Raya', 'Puchong Herbs']
    )
    
    result = classifier.batch_classify_transactions(EXAMPLE_TRANSACTIONS)
    
    print(f"\n总交易数: {result['total']}")
    print(f"分类成功: {result['classified']}")
    print(f"\n分类汇总:")
    for category, count in result['summary'].items():
        print(f"  {category}: {count}")
    
    print(f"\n详细结果:")
    for r in result['results']:
        print(f"  交易 {r['transaction_id']}: {r['category']} (置信度: {r['confidence']})")
