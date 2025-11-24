"""
文件完整性检查服务
File Integrity Check Service

确保所有上传的文件都被正确保存和索引
"""
import os
import hashlib
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import uuid

class FileIntegrityService:
    """文件完整性检查服务"""
    
    def __init__(self, db_path: str = 'db/smart_loan_manager.db'):
        self.db_path = db_path
        self.backup_root = 'static/uploads_backup'
        
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """
        计算文件MD5哈希
        
        Args:
            file_path: 文件路径
            
        Returns:
            MD5哈希值，如果文件不存在返回None
        """
        if not os.path.exists(file_path):
            return None
        
        try:
            md5_hash = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            print(f"Error calculating hash for {file_path}: {e}")
            return None
    
    def register_file(
        self,
        file_path: str,
        customer_id: int,
        customer_code: str,
        business_type: str,
        file_category: str,
        original_filename: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        uploaded_by: Optional[str] = None
    ) -> Optional[str]:
        """
        注册文件到file_registry
        
        Args:
            file_path: 文件存储路径
            customer_id: 客户ID
            customer_code: 客户代码
            business_type: 业务类型（personal/company/mixed）
            file_category: 文件类别
            original_filename: 原始文件名
            entity_type: 关联实体类型
            entity_id: 关联实体ID
            uploaded_by: 上传人
            
        Returns:
            file_uuid，如果失败返回None
        """
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return None
        
        # 生成UUID
        file_uuid = str(uuid.uuid4())
        
        # 计算文件哈希
        file_hash = self.calculate_file_hash(file_path)
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        if not original_filename:
            original_filename = os.path.basename(file_path)
        
        # 创建备份
        backup_path = self._create_backup(file_path, customer_code, file_category)
        
        # 插入到数据库
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO file_registry (
                    file_uuid, original_filename, file_path, file_size, file_hash,
                    customer_id, customer_code, business_type,
                    file_category, entity_type, entity_id,
                    uploaded_by, upload_source, status, is_original,
                    backup_path, last_verified, verification_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_uuid, original_filename, file_path, file_size, file_hash,
                customer_id, customer_code, business_type,
                file_category, entity_type, entity_id,
                uploaded_by, 'system', 'active', 1,
                backup_path, datetime.now().isoformat(), 'verified'
            ))
            
            conn.commit()
            print(f"✅ 文件已注册: {file_uuid} - {original_filename}")
            return file_uuid
            
        except sqlite3.IntegrityError as e:
            # 可能是重复文件
            if 'UNIQUE constraint failed' in str(e):
                print(f"⚠️  文件UUID冲突，重新生成...")
                return self.register_file(
                    file_path, customer_id, customer_code, business_type,
                    file_category, original_filename, entity_type, entity_id, uploaded_by
                )
            else:
                print(f"❌ 数据库错误: {e}")
                return None
        finally:
            conn.close()
    
    def _create_backup(self, file_path: str, customer_code: str, file_category: str) -> str:
        """
        创建文件备份
        
        Args:
            file_path: 原始文件路径
            customer_code: 客户代码
            file_category: 文件类别
            
        Returns:
            备份路径
        """
        # 生成备份路径
        backup_dir = os.path.join(
            self.backup_root,
            customer_code,
            file_category,
            datetime.now().strftime('%Y-%m')
        )
        
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(file_path)}"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # 复制文件
        shutil.copy2(file_path, backup_path)
        
        return backup_path
    
    def check_file_exists(self, file_hash: str) -> Optional[Dict]:
        """
        检查文件是否已存在（基于哈希）
        
        Args:
            file_hash: 文件MD5哈希
            
        Returns:
            如果存在返回文件信息，否则返回None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_uuid, original_filename, file_path, upload_date, status
            FROM file_registry
            WHERE file_hash = ? AND status = 'active'
            ORDER BY upload_date DESC
            LIMIT 1
        ''', (file_hash,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'file_uuid': result[0],
                'original_filename': result[1],
                'file_path': result[2],
                'upload_date': result[3],
                'status': result[4]
            }
        return None
    
    def verify_all_files(self) -> Dict[str, List]:
        """
        验证所有注册文件的完整性
        
        Returns:
            验证结果字典
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, file_uuid, original_filename, file_path, file_hash, backup_path
            FROM file_registry
            WHERE status = 'active'
        ''')
        
        files = cursor.fetchall()
        
        results = {
            'verified': [],
            'missing': [],
            'hash_mismatch': [],
            'recovered': []
        }
        
        for file_record in files:
            file_id, file_uuid, filename, file_path, expected_hash, backup_path = file_record
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                print(f"❌ 文件丢失: {filename} ({file_path})")
                
                # 尝试从备份恢复
                if backup_path and os.path.exists(backup_path):
                    try:
                        # 确保目录存在
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        shutil.copy2(backup_path, file_path)
                        print(f"✅ 从备份恢复: {filename}")
                        results['recovered'].append({
                            'file_uuid': file_uuid,
                            'filename': filename,
                            'path': file_path
                        })
                        
                        # 更新验证状态
                        cursor.execute('''
                            UPDATE file_registry
                            SET last_verified = ?, verification_status = 'recovered'
                            WHERE id = ?
                        ''', (datetime.now().isoformat(), file_id))
                        
                    except Exception as e:
                        print(f"❌ 恢复失败: {e}")
                        results['missing'].append({
                            'file_uuid': file_uuid,
                            'filename': filename,
                            'path': file_path
                        })
                else:
                    results['missing'].append({
                        'file_uuid': file_uuid,
                        'filename': filename,
                        'path': file_path
                    })
                    
                    # 标记为missing
                    cursor.execute('''
                        UPDATE file_registry
                        SET verification_status = 'missing'
                        WHERE id = ?
                    ''', (file_id,))
                
                continue
            
            # 验证文件哈希
            current_hash = self.calculate_file_hash(file_path)
            if current_hash != expected_hash:
                print(f"⚠️  文件哈希不匹配: {filename}")
                results['hash_mismatch'].append({
                    'file_uuid': file_uuid,
                    'filename': filename,
                    'path': file_path,
                    'expected_hash': expected_hash,
                    'current_hash': current_hash
                })
                
                # 标记为hash_mismatch
                cursor.execute('''
                    UPDATE file_registry
                    SET verification_status = 'hash_mismatch', last_verified = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), file_id))
            else:
                # 验证成功
                results['verified'].append({
                    'file_uuid': file_uuid,
                    'filename': filename
                })
                
                # 更新验证时间
                cursor.execute('''
                    UPDATE file_registry
                    SET last_verified = ?, verification_status = 'verified'
                    WHERE id = ?
                ''', (datetime.now().isoformat(), file_id))
        
        conn.commit()
        conn.close()
        
        # 打印统计
        print("\n" + "=" * 80)
        print("文件完整性检查结果:")
        print("=" * 80)
        print(f"✅ 验证通过: {len(results['verified'])}")
        print(f"✅ 从备份恢复: {len(results['recovered'])}")
        print(f"❌ 文件丢失: {len(results['missing'])}")
        print(f"⚠️  哈希不匹配: {len(results['hash_mismatch'])}")
        
        return results
    
    def get_customer_files(
        self,
        customer_code: str,
        business_type: Optional[str] = None,
        file_category: Optional[str] = None
    ) -> List[Dict]:
        """
        获取客户的所有文件
        
        Args:
            customer_code: 客户代码
            business_type: 业务类型过滤（可选）
            file_category: 文件类别过滤（可选）
            
        Returns:
            文件列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT file_uuid, original_filename, file_path, file_size, 
                   business_type, file_category, upload_date, status, verification_status
            FROM file_registry
            WHERE customer_code = ? AND status = 'active'
        '''
        params = [customer_code]
        
        if business_type:
            query += ' AND business_type = ?'
            params.append(business_type)
        
        if file_category:
            query += ' AND file_category = ?'
            params.append(file_category)
        
        query += ' ORDER BY upload_date DESC'
        
        cursor.execute(query, params)
        
        files = []
        for row in cursor.fetchall():
            files.append({
                'file_uuid': row[0],
                'original_filename': row[1],
                'file_path': row[2],
                'file_size': row[3],
                'business_type': row[4],
                'file_category': row[5],
                'upload_date': row[6],
                'status': row[7],
                'verification_status': row[8]
            })
        
        conn.close()
        return files


# 全局实例
file_integrity_service = FileIntegrityService()


# 便捷函数
def register_file(*args, **kwargs):
    """注册文件到file_registry"""
    return file_integrity_service.register_file(*args, **kwargs)


def check_file_exists(file_hash: str):
    """检查文件是否存在"""
    return file_integrity_service.check_file_exists(file_hash)


def verify_all_files():
    """验证所有文件完整性"""
    return file_integrity_service.verify_all_files()


def get_customer_files(customer_code: str, business_type: Optional[str] = None, file_category: Optional[str] = None):
    """获取客户文件列表"""
    return file_integrity_service.get_customer_files(customer_code, business_type, file_category)
