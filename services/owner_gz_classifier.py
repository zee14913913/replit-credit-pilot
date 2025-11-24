"""
Owner/GZ自动分类服务
Automatic Owner/GZ Classification Service

功能：
1. 自动分类交易为Owner's Expenses或GZ's Expenses
2. 计算各类别总额
3. 生成对比表格（计算 vs 原件）
4. 验证计算准确性
"""
import os
from typing import Dict, List, Tuple
from datetime import datetime
import sqlite3

class OwnerGZClassifier:
    """
    Owner/GZ分类器
    
    业务规则（以LEE E KAI为例）：
    - Owner's Expenses: 个人消费
    - GZ's Expenses: INFINITE GZ SDN BHD的业务支出
    """
    
    # GZ供应商列表（公司业务支出）
    GZ_SUPPLIERS = [
        '7SL',
        'DINAS',
        'DINAS RAUB',
        'AI SMART',
        'AI SMART TECH',
        'HUAWEI',
        'TESCO',
        'LOTUS',
        'SHOPEE',
        'LAZADA',
        'GRAB',  # 公司用车
        'INVOICE',
        'SUPPLIER',
        'VENDOR'
    ]
    
    # Owner个人关键词
    OWNER_KEYWORDS = [
        'RESTAURANT',
        'CAFE',
        'STARBUCKS',
        'MCDONALD',
        'KFC',
        'SHOPPING',
        'MALL',
        'CINEMA',
        'GYM',
        'PHARMACY'
    ]
    
    def __init__(self, db_path: str = 'db/smart_loan_manager.db'):
        self.db_path = db_path
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def classify_transaction(self, merchant_name: str, description: str = '') -> str:
        """
        分类单个交易
        
        Args:
            merchant_name: 商户名称
            description: 交易描述
            
        Returns:
            'owner' 或 'gz'
        """
        # 转大写便于匹配
        merchant_upper = merchant_name.upper()
        desc_upper = description.upper() if description else ''
        
        # 检查是否GZ供应商
        for supplier in self.GZ_SUPPLIERS:
            if supplier in merchant_upper or supplier in desc_upper:
                return 'gz'
        
        # 检查是否Owner个人消费
        for keyword in self.OWNER_KEYWORDS:
            if keyword in merchant_upper or keyword in desc_upper:
                return 'owner'
        
        # 默认：根据金额大小判断
        # 大额交易（> RM 500）倾向于公司支出
        # 小额交易（< RM 500）倾向于个人消费
        # 这里默认返回owner，实际使用时需要传入amount
        return 'owner'
    
    def classify_transactions_batch(
        self,
        transactions: List[Dict]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        批量分类交易
        
        Args:
            transactions: 交易列表，每个交易包含：
                - merchant_name
                - description
                - amount
                - transaction_date
                
        Returns:
            (owner_transactions, gz_transactions)
        """
        owner_transactions = []
        gz_transactions = []
        
        for txn in transactions:
            merchant = txn.get('merchant_name', '')
            description = txn.get('description', '')
            amount = txn.get('amount', 0)
            
            # 基于商户分类
            category = self.classify_transaction(merchant, description)
            
            # 大额交易二次判断
            if amount > 500 and category == 'owner':
                # 检查是否可能是公司支出
                if any(kw in merchant.upper() for kw in ['TECH', 'SUPPLY', 'EQUIPMENT']):
                    category = 'gz'
            
            # 添加分类标签
            txn_with_category = txn.copy()
            txn_with_category['category'] = category
            
            if category == 'gz':
                gz_transactions.append(txn_with_category)
            else:
                owner_transactions.append(txn_with_category)
        
        return (owner_transactions, gz_transactions)
    
    def calculate_totals(
        self,
        owner_transactions: List[Dict],
        gz_transactions: List[Dict]
    ) -> Dict:
        """
        计算各类别总额
        
        Returns:
            {
                'owner_total': float,
                'gz_total': float,
                'calculated_total': float,
                'owner_count': int,
                'gz_count': int
            }
        """
        owner_total = sum(t.get('amount', 0) for t in owner_transactions)
        gz_total = sum(t.get('amount', 0) for t in gz_transactions)
        
        return {
            'owner_total': round(owner_total, 2),
            'gz_total': round(gz_total, 2),
            'calculated_total': round(owner_total + gz_total, 2),
            'owner_count': len(owner_transactions),
            'gz_count': len(gz_transactions)
        }
    
    def generate_comparison_result(
        self,
        calculated_total: float,
        statement_total: float,
        owner_total: float,
        gz_total: float,
        owner_count: int,
        gz_count: int
    ) -> Dict:
        """
        生成对比结果
        
        Args:
            calculated_total: 计算总额
            statement_total: 原件总额
            owner_total: Owner总额
            gz_total: GZ总额
            owner_count: Owner交易数
            gz_count: GZ交易数
            
        Returns:
            对比结果字典
        """
        difference = abs(calculated_total - statement_total)
        is_match = difference <= 0.01  # 允许1分的误差
        
        return {
            'owner_total': round(owner_total, 2),
            'gz_total': round(gz_total, 2),
            'calculated_total': round(calculated_total, 2),
            'statement_total': round(statement_total, 2),
            'difference': round(difference, 2),
            'is_match': is_match,
            'status': 'match' if is_match else 'mismatch',
            'owner_count': owner_count,
            'gz_count': gz_count,
            'total_count': owner_count + gz_count
        }
    
    def generate_comparison_table_text(
        self,
        customer_name: str,
        bank_name: str,
        statement_date: str,
        comparison_result: Dict,
        due_date: str = None,
        minimum_payment: float = None
    ) -> str:
        """
        生成对比表格（文本格式）
        
        返回：
        ┌────────────────────────────────────────┐
        │   LEE E KAI - AmBank Islamic          │
        │   Statement Date: 2025-10-28          │
        ├────────────────────────────────────────┤
        │                                        │
        │   原件数据（From PDF）                  │
        │   Statement Total:    RM 14,515.00    │
        │   Minimum Payment:    RM    450.00    │
        │   Due Date:           2025-11-15      │
        │                                        │
        │   计算数据（Calculated）                │
        │   Owner's Total:      RM  8,200.00    │
        │   GZ's Total:         RM  6,315.00    │
        │   Calculated Total:   RM 14,515.00    │
        │                                        │
        │   交易统计                              │
        │   Owner Transactions:  95笔           │
        │   GZ Transactions:     61笔           │
        │   Total Transactions:  156笔          │
        │                                        │
        │   验证结果                              │
        │   差异:               RM      0.00    │
        │   状态:               ✅ 验证通过       │
        │                                        │
        └────────────────────────────────────────┘
        """
        status_icon = "✅ 验证通过" if comparison_result['is_match'] else "❌ 需要审核"
        
        table = f"""
{'='*60}
  {customer_name} - {bank_name}
  Statement Date: {statement_date}
{'='*60}

📄 原件数据（From PDF）
  Statement Total:    RM {comparison_result['statement_total']:>12,.2f}
"""
        
        if minimum_payment:
            table += f"  Minimum Payment:    RM {minimum_payment:>12,.2f}\n"
        
        if due_date:
            table += f"  Due Date:           {due_date}\n"
        
        table += f"""
📊 计算数据（Calculated）
  Owner's Total:      RM {comparison_result['owner_total']:>12,.2f}
  GZ's Total:         RM {comparison_result['gz_total']:>12,.2f}
  Calculated Total:   RM {comparison_result['calculated_total']:>12,.2f}

📈 交易统计
  Owner Transactions:  {comparison_result['owner_count']:>4} 笔
  GZ Transactions:     {comparison_result['gz_count']:>4} 笔
  Total Transactions:  {comparison_result['total_count']:>4} 笔

✅ 验证结果
  差异:               RM {comparison_result['difference']:>12,.2f}
  状态:               {status_icon}

{'='*60}
"""
        return table
    
    def save_comparison_to_database(
        self,
        transaction_uuid: str,
        comparison_result: Dict
    ):
        """
        保存对比结果到数据库
        
        Args:
            transaction_uuid: 交易UUID
            comparison_result: 对比结果
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE upload_transactions
            SET 
                owner_total = ?,
                gz_total = ?,
                calculated_total = ?,
                statement_total_original = ?,
                calculation_difference = ?,
                comparison_status = ?
            WHERE transaction_uuid = ?
        ''', (
            comparison_result['owner_total'],
            comparison_result['gz_total'],
            comparison_result['calculated_total'],
            comparison_result['statement_total'],
            comparison_result['difference'],
            comparison_result['status'],
            transaction_uuid
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 对比结果已保存到数据库")
        print(f"   Owner Total: RM {comparison_result['owner_total']:.2f}")
        print(f"   GZ Total: RM {comparison_result['gz_total']:.2f}")
        print(f"   Difference: RM {comparison_result['difference']:.2f}")
        print(f"   Status: {comparison_result['status']}")
    
    def execute_full_classification(
        self,
        transaction_uuid: str,
        transactions: List[Dict],
        statement_total: float,
        customer_name: str,
        bank_name: str,
        statement_date: str,
        due_date: str = None,
        minimum_payment: float = None
    ) -> Dict:
        """
        执行完整的分类流程
        
        Args:
            transaction_uuid: 交易UUID
            transactions: 交易列表
            statement_total: 原件总额
            customer_name: 客户名称
            bank_name: 银行名称
            statement_date: 账单日期
            due_date: 到期日期（可选）
            minimum_payment: 最低还款（可选）
            
        Returns:
            分类结果
        """
        print(f"\n🔍 开始Owner/GZ分类...")
        print(f"   交易总数: {len(transactions)}")
        
        # 1. 批量分类
        owner_txns, gz_txns = self.classify_transactions_batch(transactions)
        
        # 2. 计算总额
        totals = self.calculate_totals(owner_txns, gz_txns)
        
        # 3. 生成对比结果
        comparison_result = self.generate_comparison_result(
            calculated_total=totals['calculated_total'],
            statement_total=statement_total,
            owner_total=totals['owner_total'],
            gz_total=totals['gz_total'],
            owner_count=totals['owner_count'],
            gz_count=totals['gz_count']
        )
        
        # 4. 生成对比表格
        comparison_table = self.generate_comparison_table_text(
            customer_name,
            bank_name,
            statement_date,
            comparison_result,
            due_date,
            minimum_payment
        )
        
        print(comparison_table)
        
        # 5. 保存到数据库
        self.save_comparison_to_database(transaction_uuid, comparison_result)
        
        # 6. 返回结果
        return {
            'success': comparison_result['is_match'],
            'comparison_result': comparison_result,
            'comparison_table': comparison_table,
            'owner_transactions': owner_txns,
            'gz_transactions': gz_txns
        }


# 全局实例
owner_gz_classifier = OwnerGZClassifier()


# 便捷函数
def classify_and_compare(
    transaction_uuid: str,
    transactions: List[Dict],
    statement_total: float,
    customer_name: str,
    bank_name: str,
    statement_date: str,
    **kwargs
) -> Dict:
    """便捷函数：执行完整分类和对比"""
    return owner_gz_classifier.execute_full_classification(
        transaction_uuid,
        transactions,
        statement_total,
        customer_name,
        bank_name,
        statement_date,
        **kwargs
    )
