"""
Owner Classifier Service
Purpose: Classify transactions as OWNER (Own's) vs GZ (GZ's)
"""

import sys
sys.path.insert(0, '.')
from db.database import get_db


class OwnerClassifier:
    """
    Classifies credit card transactions into OWNER vs GZ categories
    
    Classification Rules:
    - EXPENSES (purchases):
        - Own's Expenses: Customer's personal spending
        - GZ's Expenses: GZ's spending / supplier transactions
    
    - PAYMENTS:
        - Own's Payment: Customer's own payments
        - GZ's Payment: Third-party payer payments (e.g., 'GZ' in description)
    
    - BALANCES:
        - Own's OS Bal: Customer's outstanding balance
        - GZ's OS Bal: GZ's outstanding balance
    """
    
    def __init__(self):
        self.gz_keywords = [
            'GZ',
            'Galaxy', 
            'Galaxy Zone',
            'INFINITE',
            '供应商',
            'Supplier'
        ]
        
        # Load supplier configuration from database
        self.load_supplier_config()
    
    def load_supplier_config(self):
        """Load supplier names from supplier_config table"""
        self.suppliers = set()
        
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT supplier_name FROM supplier_config WHERE is_active = 1")
                results = cursor.fetchall()
                self.suppliers = {row[0].upper() for row in results}
        except Exception as e:
            print(f"Warning: Could not load supplier config: {e}")
    
    def classify_transaction(self, transaction, override_dict=None):
        """
        Classify a single transaction
        
        Args:
            transaction: dict with keys: description, amount, transaction_type, payer_name, supplier_name
            override_dict: Optional dict of {transaction_id: 'own'/'gz'} for manual overrides
        
        Returns:
            str: 'own' or 'gz'
        """
        
        # Check for manual override first
        if override_dict and transaction.get('id') in override_dict:
            return override_dict[transaction['id']]
        
        txn_type = (transaction.get('transaction_type') or '').lower()
        description = (transaction.get('description') or '').upper()
        payer_name = (transaction.get('payer_name') or '').upper()
        supplier_name = (transaction.get('supplier_name') or '').upper()
        
        # Rule 1: Supplier-marked transactions
        if transaction.get('is_supplier') == 1:
            return 'gz'
        
        # Rule 2: Supplier name match
        if supplier_name and supplier_name in self.suppliers:
            return 'gz'
        
        # Rule 3: Payment classification
        if txn_type == 'payment':
            # Check if payer is GZ or third-party
            for keyword in self.gz_keywords:
                if keyword in payer_name or keyword in description:
                    return 'gz'
            # Default: own payment
            return 'own'
        
        # Rule 4: Purchase/expense classification
        if txn_type in ['purchase', 'fee']:
            # Check description for GZ keywords
            for keyword in self.gz_keywords:
                if keyword in description:
                    return 'gz'
            # Default: own expense
            return 'own'
        
        # Default fallback
        return 'own'
    
    def classify_transaction_batch(self, transactions, override_dict=None):
        """
        Classify a batch of transactions
        
        Args:
            transactions: list of transaction dicts
            override_dict: Optional dict of manual overrides
        
        Returns:
            dict: {transaction_id: 'own'/'gz'}
        """
        results = {}
        for txn in transactions:
            txn_id = txn.get('id')
            classification = self.classify_transaction(txn, override_dict)
            if txn_id:
                results[txn_id] = classification
        
        return results
    
    def get_manual_overrides(self):
        """Load manual overrides from database"""
        overrides = {}
        
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT transaction_id, owner_flag FROM transaction_owner_overrides")
                results = cursor.fetchall()
                overrides = {row[0]: row[1] for row in results}
        except Exception as e:
            print(f"Warning: Could not load manual overrides: {e}")
        
        return overrides
    
    def apply_overrides(self, transaction_id, owner_flag, reason, admin_user):
        """
        Manually override a transaction's classification
        
        Args:
            transaction_id: int
            owner_flag: 'own' or 'gz'
            reason: str, explanation
            admin_user: str, admin username
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO transaction_owner_overrides 
                (transaction_id, owner_flag, override_reason, overridden_by)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(transaction_id) DO UPDATE SET
                    owner_flag = excluded.owner_flag,
                    override_reason = excluded.override_reason,
                    overridden_by = excluded.overridden_by,
                    overridden_at = CURRENT_TIMESTAMP
            """, (transaction_id, owner_flag, reason, admin_user))
            
            # Also update the transaction record
            cursor.execute("""
                UPDATE transactions 
                SET owner_flag = ?,
                    classification_source = 'override'
                WHERE id = ?
            """, (owner_flag, transaction_id))
            
            conn.commit()


# Utility functions
def classify_transactions_for_statement(statement_id):
    """Classify all transactions for a given statement"""
    classifier = OwnerClassifier()
    overrides = classifier.get_manual_overrides()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get all transactions for this statement
        cursor.execute("""
            SELECT 
                id, description, amount, transaction_type,
                payer_name, supplier_name, is_supplier
            FROM transactions
            WHERE statement_id = ?
        """, (statement_id,))
        
        columns = [col[0] for col in cursor.description]
        transactions = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Classify
        results = classifier.classify_transaction_batch(transactions, overrides)
        
        # Update database
        for txn_id, owner_flag in results.items():
            classification_source = 'override' if txn_id in overrides else 'auto'
            cursor.execute("""
                UPDATE transactions
                SET owner_flag = ?,
                    classification_source = ?
                WHERE id = ?
            """, (owner_flag, classification_source, txn_id))
        
        conn.commit()
        
        return results


if __name__ == '__main__':
    # Test the classifier
    classifier = OwnerClassifier()
    
    test_transactions = [
        {'id': 1, 'description': 'GRAB FOOD', 'transaction_type': 'purchase', 'payer_name': '', 'supplier_name': '', 'is_supplier': 0},
        {'id': 2, 'description': 'GALAXY ZONE PAYMENT', 'transaction_type': 'purchase', 'payer_name': '', 'supplier_name': '', 'is_supplier': 0},
        {'id': 3, 'description': 'PAYMENT RECEIVED', 'transaction_type': 'payment', 'payer_name': 'GZ', 'supplier_name': '', 'is_supplier': 0},
        {'id': 4, 'description': 'PAYMENT', 'transaction_type': 'payment', 'payer_name': 'CHANG CHOON CHOW', 'supplier_name': '', 'is_supplier': 0},
    ]
    
    results = classifier.classify_transaction_batch(test_transactions)
    
    print("Classification Test:")
    for txn in test_transactions:
        print(f"  {txn['description']:30s} -> {results.get(txn['id'], 'unknown').upper()}")
