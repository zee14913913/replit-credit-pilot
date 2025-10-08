"""
Batch Operations Service
Handle batch upload and processing of multiple statements
"""

import os
from datetime import datetime
from typing import List, Dict
from db.database import get_db

class BatchService:
    """Service for batch operations"""
    
    def create_batch_job(self, job_type: str, customer_id: int, total_items: int) -> int:
        """Create a new batch job"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO batch_jobs (job_type, customer_id, total_items, status)
                VALUES (?, ?, ?, 'pending')
            ''', (job_type, customer_id, total_items))
            conn.commit()
            return cursor.lastrowid
    
    def update_batch_progress(self, batch_id: int, processed: int, failed: int = 0):
        """Update batch job progress"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE batch_jobs 
                SET processed_items = ?, failed_items = ?
                WHERE id = ?
            ''', (processed, failed, batch_id))
            conn.commit()
    
    def complete_batch_job(self, batch_id: int, status: str = 'completed', 
                          error_message: str = None, result_data: str = None):
        """Mark batch job as completed"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE batch_jobs 
                SET status = ?, completed_at = CURRENT_TIMESTAMP, 
                    error_message = ?, result_data = ?
                WHERE id = ?
            ''', (status, error_message, result_data, batch_id))
            conn.commit()
    
    def get_batch_job(self, batch_id: int) -> Dict:
        """Get batch job details"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM batch_jobs WHERE id = ?', (batch_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_customer_batch_jobs(self, customer_id: int, limit: int = 20) -> List[Dict]:
        """Get recent batch jobs for customer"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM batch_jobs 
                WHERE customer_id = ?
                ORDER BY started_at DESC
                LIMIT ?
            ''', (customer_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def link_statement_to_batch(self, statement_id: int, batch_id: int):
        """Link a statement to a batch job"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE statements 
                SET batch_job_id = ?
                WHERE id = ?
            ''', (batch_id, statement_id))
            conn.commit()
    
    def delete_batch(self, batch_id: int, customer_id: int) -> bool:
        """Delete batch and associated statements"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Get statements in this batch
            cursor.execute('''
                SELECT id FROM statements 
                WHERE batch_job_id = ?
            ''', (batch_id,))
            statement_ids = [row[0] for row in cursor.fetchall()]
            
            # Delete transactions
            for stmt_id in statement_ids:
                cursor.execute('DELETE FROM transactions WHERE statement_id = ?', (stmt_id,))
            
            # Delete statements
            cursor.execute('DELETE FROM statements WHERE batch_job_id = ?', (batch_id,))
            
            # Delete batch job
            cursor.execute('DELETE FROM batch_jobs WHERE id = ? AND customer_id = ?', 
                          (batch_id, customer_id))
            
            conn.commit()
            return cursor.rowcount > 0
