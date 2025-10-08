"""
Tag and Notes Service
Manage custom tags and notes for transactions
"""

from typing import List, Dict, Optional
from db.database import get_db

class TagService:
    """Service for managing transaction tags and notes"""
    
    def create_tag(self, customer_id: int, tag_name: str, tag_color: str = '#1FAA59') -> int:
        """Create a new tag"""
        with get_db() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO tags (customer_id, tag_name, tag_color)
                    VALUES (?, ?, ?)
                ''', (customer_id, tag_name, tag_color))
                conn.commit()
                return cursor.lastrowid
            except:
                # Tag already exists
                cursor.execute('''
                    SELECT id FROM tags WHERE customer_id = ? AND tag_name = ?
                ''', (customer_id, tag_name))
                row = cursor.fetchone()
                return row[0] if row else 0
    
    def get_customer_tags(self, customer_id: int) -> List[Dict]:
        """Get all tags for a customer"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM tags 
                WHERE customer_id = ?
                ORDER BY usage_count DESC, tag_name
            ''', (customer_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def add_tag_to_transaction(self, transaction_id: int, tag_id: int) -> bool:
        """Add a tag to a transaction"""
        with get_db() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO transaction_tags (transaction_id, tag_id)
                    VALUES (?, ?)
                ''', (transaction_id, tag_id))
                
                # Increment usage count
                cursor.execute('''
                    UPDATE tags SET usage_count = usage_count + 1 WHERE id = ?
                ''', (tag_id,))
                
                conn.commit()
                return True
            except:
                return False
    
    def remove_tag_from_transaction(self, transaction_id: int, tag_id: int) -> bool:
        """Remove a tag from a transaction"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM transaction_tags 
                WHERE transaction_id = ? AND tag_id = ?
            ''', (transaction_id, tag_id))
            
            # Decrement usage count
            cursor.execute('''
                UPDATE tags SET usage_count = MAX(0, usage_count - 1) WHERE id = ?
            ''', (tag_id,))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def get_transaction_tags(self, transaction_id: int) -> List[Dict]:
        """Get all tags for a transaction"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.* FROM tags t
                INNER JOIN transaction_tags tt ON t.id = tt.tag_id
                WHERE tt.transaction_id = ?
            ''', (transaction_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_transaction_note(self, transaction_id: int, notes: str) -> bool:
        """Update transaction notes"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE transactions SET notes = ? WHERE id = ?
            ''', (notes, transaction_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_tag(self, tag_id: int, customer_id: int) -> bool:
        """Delete a tag"""
        with get_db() as conn:
            cursor = conn.cursor()
            # transaction_tags will be deleted by CASCADE
            cursor.execute('''
                DELETE FROM tags WHERE id = ? AND customer_id = ?
            ''', (tag_id, customer_id))
            conn.commit()
            return cursor.rowcount > 0
