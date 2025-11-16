"""
Ledger Classifier Service
用于识别交易的供应商和付款人类型
"""
import sqlite3
from typing import Tuple, Optional

class LedgerClassifier:
    def __init__(self, db_path='db/smart_loan_manager.db'):
        self.db_path = db_path
        self._load_aliases()
    
    def _load_aliases(self):
        """加载所有别名配置到内存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 加载供应商别名
        cursor.execute("""
            SELECT LOWER(alias), supplier_name 
            FROM supplier_aliases 
            WHERE is_active = 1
        """)
        self.supplier_aliases = {}
        for alias, supplier_name in cursor.fetchall():
            self.supplier_aliases[alias] = supplier_name
        
        # 加载付款人别名（按customer_id分组）
        cursor.execute("""
            SELECT customer_id, payer_type, LOWER(alias)
            FROM payer_aliases 
            WHERE is_active = 1
        """)
        self.payer_aliases = {}  # {customer_id: {'customer': [...], 'company': [...], 'infinite': [...]}}
        for customer_id, payer_type, alias in cursor.fetchall():
            if customer_id not in self.payer_aliases:
                self.payer_aliases[customer_id] = {'customer': [], 'company': [], 'infinite': []}
            self.payer_aliases[customer_id][payer_type].append(alias)
        
        # 加载转账收款人别名
        cursor.execute("""
            SELECT customer_id, recipient_name, LOWER(alias)
            FROM transfer_recipient_aliases 
            WHERE is_active = 1
        """)
        self.transfer_recipient_aliases = {}  # {customer_id: {alias: recipient_name}}
        for customer_id, recipient_name, alias in cursor.fetchall():
            if customer_id not in self.transfer_recipient_aliases:
                self.transfer_recipient_aliases[customer_id] = {}
            self.transfer_recipient_aliases[customer_id][alias] = recipient_name
        
        conn.close()
    
    def is_infinite_supplier(self, description: str) -> Tuple[bool, Optional[str]]:
        """
        检查交易描述是否包含INFINITE供应商
        
        返回: (是否INFINITE供应商, 供应商标准名称)
        """
        if not description:
            return False, None
        
        description_lower = description.lower()
        
        for alias, supplier_name in self.supplier_aliases.items():
            if alias in description_lower:
                return True, supplier_name
        
        return False, None
    
    def classify_payment(self, description: str, customer_id: int) -> str:
        """
        分类付款类型
        
        返回: 'customer' (客户本名), 'company' (公司KENG CHOW), 'infinite' (INFINITE)
        
        规则（按PDF文件要求）:
        1. CC账单CR付款记录有客户名字 → customer
        2. 无名付款 + 无details → customer (Owner's Payment)
        3. 无名付款 + 有details (payment on behalf/for client) → infinite (GZ's Payment)
        4. 其他 → infinite
        """
        # 完全空的描述 → Owner's Payment
        if not description or description.strip() == '':
            return 'customer'
        
        description_lower = description.lower()
        
        # 优先检查客户名字（最高优先级）
        if customer_id in self.payer_aliases:
            # 优先检查客户本名
            for alias in self.payer_aliases[customer_id]['customer']:
                if alias in description_lower:
                    return 'customer'
            
            # 检查公司名
            for alias in self.payer_aliases[customer_id]['company']:
                if alias in description_lower:
                    return 'company'
        
        # 检查是否包含GZ代客户付款的关键词
        gz_payment_keywords = [
            'on behalf',
            'behalf of',
            'for client',
            'client request',
            'payment for',
            'on behalf of client',
            'payment on behalf'
        ]
        
        for keyword in gz_payment_keywords:
            if keyword in description_lower:
                return 'infinite'  # GZ代客户付款
        
        # 默认为INFINITE付款
        return 'infinite'
    
    def is_transfer_to_customer(self, description: str, customer_id: int) -> Tuple[bool, Optional[str]]:
        """
        检查储蓄账户转账是否是转给客户
        
        返回: (是否转给客户, 收款人标准名称)
        """
        if not description:
            return False, None
        
        description_lower = description.lower()
        
        if customer_id in self.transfer_recipient_aliases:
            for alias, recipient_name in self.transfer_recipient_aliases[customer_id].items():
                if alias in description_lower:
                    return True, recipient_name
        
        return False, None
    
    def calculate_supplier_fee(self, amount: float, supplier_name: str = None) -> float:
        """
        计算供应商手续费（默认1%）
        
        可以根据supplier_name从supplier_fee_config表查询特定费率
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if supplier_name:
            cursor.execute("""
                SELECT fee_percentage FROM supplier_fee_config 
                WHERE supplier_name = ? AND is_active = 1
            """, (supplier_name,))
            result = cursor.fetchone()
            if result:
                fee_percentage = result[0]
            else:
                fee_percentage = 1.0
        else:
            fee_percentage = 1.0
        
        conn.close()
        
        return amount * (fee_percentage / 100.0)
    
    def add_supplier_alias(self, supplier_name: str, alias: str):
        """添加新的供应商别名"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO supplier_aliases (supplier_name, alias, is_active)
                VALUES (?, ?, 1)
            """, (supplier_name, alias.lower()))
            conn.commit()
            # 重新加载别名
            self._load_aliases()
            return True
        except Exception as e:
            print(f"Error adding supplier alias: {e}")
            return False
        finally:
            conn.close()
    
    def add_payer_alias(self, customer_id: int, payer_type: str, alias: str):
        """添加新的付款人别名"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO payer_aliases (customer_id, payer_type, alias, is_active)
                VALUES (?, ?, ?, 1)
            """, (customer_id, payer_type, alias.lower()))
            conn.commit()
            # 重新加载别名
            self._load_aliases()
            return True
        except Exception as e:
            print(f"Error adding payer alias: {e}")
            return False
        finally:
            conn.close()
    
    def add_transfer_recipient_alias(self, customer_id: int, recipient_name: str, alias: str):
        """添加新的转账收款人别名"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO transfer_recipient_aliases (customer_id, recipient_name, alias, is_active)
                VALUES (?, ?, ?, 1)
            """, (customer_id, recipient_name, alias.lower()))
            conn.commit()
            # 重新加载别名
            self._load_aliases()
            return True
        except Exception as e:
            print(f"Error adding transfer recipient alias: {e}")
            return False
        finally:
            conn.close()


# 测试代码
if __name__ == "__main__":
    classifier = LedgerClassifier()
    
    print("=== 供应商识别测试 ===")
    test_descriptions = [
        "PAYMENT TO 7SL SDN BHD",
        "HUAWEI TECHNOLOGIES",
        "PASAR RAYA STORE",
        "PUCHONG HERBS TRADING",
        "DINAS RESTAURANT",
        "RAUB SYC HAINAN",
        "AI SMART TECH",
        "RANDOM MERCHANT"
    ]
    
    for desc in test_descriptions:
        is_supplier, supplier_name = classifier.is_infinite_supplier(desc)
        print(f"  {desc:<35} -> {'✅ ' + supplier_name if is_supplier else '❌ Not INFINITE'}")
    
    print("\n=== 付款分类测试 ===")
    payment_descriptions = [
        "PAYMENT BY CHANG CHOON CHOW",
        "PAYMENT BY KENG CHOW SDN BHD",
        "PAYMENT FROM ACCOUNT 1234",
        "AUTO DEBIT PAYMENT"
    ]
    
    customer_id = 5
    for desc in payment_descriptions:
        payment_type = classifier.classify_payment(desc, customer_id)
        type_label = {'customer': '客户本名', 'company': '公司KENG CHOW', 'infinite': 'INFINITE'}[payment_type]
        print(f"  {desc:<35} -> {type_label}")
    
    print("\n=== 转账识别测试 ===")
    transfer_descriptions = [
        "TRANSFER TO CHANG CHOON CHOW",
        "IBG TO KENG CHOW",
        "TRANSFER TO MAKAN DULU",
        "TRANSFER TO LEE CHEE HWA",
        "TRANSFER TO WING CHOW",
        "TRANSFER TO OTHER PERSON"
    ]
    
    for desc in transfer_descriptions:
        is_transfer, recipient = classifier.is_transfer_to_customer(desc, customer_id)
        print(f"  {desc:<35} -> {'✅ ' + recipient if is_transfer else '❌ Not customer transfer'}")
    
    print("\n=== 手续费计算测试 ===")
    print(f"  RM 10,000 x 1% = RM {classifier.calculate_supplier_fee(10000):.2f}")
    print(f"  RM 5,500 x 1% = RM {classifier.calculate_supplier_fee(5500):.2f}")
