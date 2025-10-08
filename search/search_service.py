"""
Search and Filter Service
Advanced transaction search with saved filters
"""

from typing import List, Dict, Optional
from db.database import get_db
import json

class SearchService:
    """Advanced search and filtering for transactions"""
    
    def search_transactions(self, customer_id: int, query: str = '', filters: Optional[Dict] = None) -> List[Dict]:
        """Search transactions with full-text and filters"""
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            sql = '''
                SELECT t.*, s.statement_date, cc.bank_name, cc.card_number_last4,
                       GROUP_CONCAT(tg.tag_name, ', ') as tags
                FROM transactions t
                INNER JOIN statements s ON t.statement_id = s.id
                INNER JOIN credit_cards cc ON s.card_id = cc.id
                LEFT JOIN transaction_tags tt ON t.id = tt.transaction_id
                LEFT JOIN tags tg ON tt.tag_id = tg.id
                WHERE cc.customer_id = ? AND s.is_confirmed = 1
            '''
            
            params = [customer_id]
            
            # Full-text search
            if query:
                sql += ' AND (t.description LIKE ? OR t.notes LIKE ? OR tg.tag_name LIKE ?)'
                search_term = f'%{query}%'
                params.extend([search_term, search_term, search_term])
            
            # Apply filters
            if filters:
                if filters.get('category'):
                    sql += ' AND t.category = ?'
                    params.append(filters['category'])
                if filters.get('start_date'):
                    sql += ' AND t.transaction_date >= ?'
                    params.append(filters['start_date'])
                if filters.get('end_date'):
                    sql += ' AND t.transaction_date <= ?'
                    params.append(filters['end_date'])
                if filters.get('min_amount'):
                    sql += ' AND t.amount >= ?'
                    params.append(float(filters['min_amount']))
                if filters.get('max_amount'):
                    sql += ' AND t.amount <= ?'
                    params.append(float(filters['max_amount']))
                if filters.get('bank'):
                    sql += ' AND cc.bank_name = ?'
                    params.append(filters['bank'])
            
            sql += ' GROUP BY t.id ORDER BY t.transaction_date DESC LIMIT 1000'
            
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def save_filter(self, customer_id: int, filter_name: str, filter_criteria: Dict) -> int:
        """Save a filter configuration"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO saved_filters 
                (customer_id, filter_name, filter_criteria, usage_count)
                VALUES (?, ?, ?, COALESCE((SELECT usage_count FROM saved_filters 
                        WHERE customer_id = ? AND filter_name = ?), 0))
            ''', (customer_id, filter_name, json.dumps(filter_criteria), customer_id, filter_name))
            conn.commit()
            return cursor.lastrowid
    
    def get_saved_filters(self, customer_id: int) -> List[Dict]:
        """Get all saved filters for a customer"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, filter_name, filter_criteria, is_default, usage_count, created_at
                FROM saved_filters
                WHERE customer_id = ?
                ORDER BY usage_count DESC, created_at DESC
            ''', (customer_id,))
            
            filters = []
            for row in cursor.fetchall():
                filter_dict = dict(row)
                filter_dict['filter_criteria'] = json.loads(filter_dict['filter_criteria'])
                filters.append(filter_dict)
            return filters
    
    def delete_filter(self, filter_id: int, customer_id: int) -> bool:
        """Delete a saved filter"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM saved_filters 
                WHERE id = ? AND customer_id = ?
            ''', (filter_id, customer_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_filter_suggestions(self, customer_id: int) -> Dict:
        """Get smart filter suggestions based on data"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get unique categories
            cursor.execute('''
                SELECT DISTINCT t.category
                FROM transactions t
                INNER JOIN statements s ON t.statement_id = s.id
                INNER JOIN credit_cards cc ON s.card_id = cc.id
                WHERE cc.customer_id = ? AND t.category IS NOT NULL
                ORDER BY t.category
            ''', (customer_id,))
            categories = [row[0] for row in cursor.fetchall()]
            
            # Get unique banks
            cursor.execute('''
                SELECT DISTINCT bank_name
                FROM credit_cards
                WHERE customer_id = ?
                ORDER BY bank_name
            ''', (customer_id,))
            banks = [row[0] for row in cursor.fetchall()]
            
            # Get date range
            cursor.execute('''
                SELECT MIN(t.transaction_date), MAX(t.transaction_date)
                FROM transactions t
                INNER JOIN statements s ON t.statement_id = s.id
                INNER JOIN credit_cards cc ON s.card_id = cc.id
                WHERE cc.customer_id = ?
            ''', (customer_id,))
            date_range = cursor.fetchone()
            
            return {
                'categories': categories,
                'banks': banks,
                'date_range': {
                    'start': date_range[0] if date_range else None,
                    'end': date_range[1] if date_range else None
                }
            }
