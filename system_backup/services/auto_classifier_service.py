"""
批量文件自动归类服务
Auto File Classifier Service

功能：
1. 从文件名提取客户标识（客户名/编号/身份证号）
2. 从文件内容解析客户信息（PDF/Excel/Word/图片OCR）
3. 自动匹配客户库
4. 归档到对应客户目录
5. 未识别文件归入unassigned目录
"""

import os
import re
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from pathlib import Path

# PDF处理
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Excel处理
try:
    import openpyxl
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False

# OCR处理
try:
    from PIL import Image
    import pytesseract
    OCR_SUPPORT = True
except ImportError:
    OCR_SUPPORT = False

from db.database import get_db
from services.file_storage_manager import FileStorageManager


class AutoFileClassifier:
    """批量文件自动归类器"""
    
    # 未归档目录
    UNASSIGNED_DIR = "static/uploads/unassigned"
    
    # 客户名/编号正则模式（支持多种命名规范）
    CUSTOMER_PATTERNS = [
        r'CUST(\d{4,})',  # CUST12345
        r'客户([^\W_]+)',  # 客户A, 客户张三
        r'([A-Z][a-z]+_[A-Z][a-z]+(?:_[A-Z]+)?)',  # Be_rich_CCC, John_Doe_LLC
        r'IC(\d{12})',  # IC123456789012 (身份证)
        r'(\d{12})',  # 12位身份证号
    ]
    
    # PDF内容客户字段正则
    PDF_CUSTOMER_FIELDS = [
        r'客户[名称]?\s*[:：]\s*([\u4e00-\u9fa5A-Za-z0-9\s]+)',
        r'Customer\s+Name\s*:\s*([A-Za-z\s]+)',
        r'姓名\s*[:：]\s*([\u4e00-\u9fa5]+)',
        r'Name\s*:\s*([A-Za-z\s]+)',
        r'编号\s*[:：]\s*([A-Za-z0-9]+)',
        r'Code\s*:\s*([A-Za-z0-9]+)',
    ]
    
    def __init__(self):
        """初始化归类器"""
        os.makedirs(self.UNASSIGNED_DIR, exist_ok=True)
    
    def extract_customer_from_filename(self, filename: str) -> Optional[str]:
        """
        从文件名提取客户标识
        
        Args:
            filename: 文件名（如：客户A_202501.pdf, CUST5678_loan.pdf）
            
        Returns:
            客户标识字符串，未找到返回None
        """
        for pattern in self.CUSTOMER_PATTERNS:
            match = re.search(pattern, filename)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return None
    
    def extract_customer_from_pdf(self, filepath: str) -> Optional[str]:
        """
        从PDF内容提取客户信息
        
        Args:
            filepath: PDF文件路径
            
        Returns:
            客户标识，未找到返回None
        """
        if not PDF_SUPPORT:
            return None
        
        try:
            with pdfplumber.open(filepath) as pdf:
                # 只读取前3页（提高性能）
                pages_to_check = min(3, len(pdf.pages))
                for page_num in range(pages_to_check):
                    text = pdf.pages[page_num].extract_text()
                    if not text:
                        continue
                    
                    # 尝试所有客户字段模式
                    for pattern in self.PDF_CUSTOMER_FIELDS:
                        match = re.search(pattern, text)
                        if match:
                            return match.group(1).strip()
        except Exception as e:
            print(f"PDF解析错误: {str(e)}")
        
        return None
    
    def extract_customer_from_excel(self, filepath: str) -> Optional[str]:
        """
        从Excel内容提取客户信息
        
        Args:
            filepath: Excel文件路径
            
        Returns:
            客户标识，未找到返回None
        """
        if not EXCEL_SUPPORT:
            return None
        
        try:
            wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
            sheet = wb.active
            
            # 检查常见位置：A1, B1, A2, B2
            check_cells = ['A1', 'B1', 'A2', 'B2', 'C1', 'C2']
            for cell_ref in check_cells:
                val = sheet[cell_ref].value
                if val and isinstance(val, str):
                    # 检查是否包含客户标识
                    if '客户' in val or 'CUST' in val.upper() or 'Customer' in val:
                        # 尝试提取
                        for pattern in self.CUSTOMER_PATTERNS:
                            match = re.search(pattern, val)
                            if match:
                                return match.group(1) if match.groups() else match.group(0)
                        return val.strip()
            
            wb.close()
        except Exception as e:
            print(f"Excel解析错误: {str(e)}")
        
        return None
    
    def extract_customer_from_image(self, filepath: str) -> Optional[str]:
        """
        从图片OCR提取客户信息
        
        Args:
            filepath: 图片文件路径
            
        Returns:
            客户标识，未找到返回None
        """
        if not OCR_SUPPORT:
            return None
        
        try:
            image = Image.open(filepath)
            text = pytesseract.image_to_string(image, lang='eng+chi_sim')
            
            # 尝试所有客户字段模式
            for pattern in self.PDF_CUSTOMER_FIELDS:
                match = re.search(pattern, text)
                if match:
                    return match.group(1).strip()
        except Exception as e:
            print(f"OCR解析错误: {str(e)}")
        
        return None
    
    def match_customer_in_db(self, customer_identifier: str) -> Optional[Dict]:
        """
        在客户数据库中匹配客户
        
        Args:
            customer_identifier: 客户标识（名称/编号/IC）
            
        Returns:
            客户信息字典（id, name, customer_code），未找到返回None
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # 尝试多种匹配方式
                # 1. 精确匹配客户代码
                cursor.execute(
                    'SELECT id, name, customer_code FROM customers WHERE customer_code = ? AND is_active = 1',
                    (customer_identifier,)
                )
                result = cursor.fetchone()
                if result:
                    return {'id': result[0], 'name': result[1], 'customer_code': result[2]}
                
                # 2. 模糊匹配客户名称
                cursor.execute(
                    'SELECT id, name, customer_code FROM customers WHERE name LIKE ? AND is_active = 1',
                    (f'%{customer_identifier}%',)
                )
                result = cursor.fetchone()
                if result:
                    return {'id': result[0], 'name': result[1], 'customer_code': result[2]}
                
                # 3. 匹配邮箱/电话（如果标识符是这些）
                if '@' in customer_identifier:
                    cursor.execute(
                        'SELECT id, name, customer_code FROM customers WHERE email = ? AND is_active = 1',
                        (customer_identifier,)
                    )
                    result = cursor.fetchone()
                    if result:
                        return {'id': result[0], 'name': result[1], 'customer_code': result[2]}
                
                if customer_identifier.replace('-', '').replace(' ', '').isdigit():
                    cursor.execute(
                        'SELECT id, name, customer_code FROM customers WHERE phone LIKE ? AND is_active = 1',
                        (f'%{customer_identifier}%',)
                    )
                    result = cursor.fetchone()
                    if result:
                        return {'id': result[0], 'name': result[1], 'customer_code': result[2]}
        
        except Exception as e:
            print(f"数据库查询错误: {str(e)}")
        
        return None
    
    def classify_single_file(self, file_path: str, original_filename: str) -> Dict:
        """
        分类单个文件
        
        Args:
            file_path: 文件临时路径
            original_filename: 原始文件名
            
        Returns:
            分类结果字典
        """
        result = {
            'filename': original_filename,
            'status': 'unassigned',  # success, unassigned, error
            'customer_id': None,
            'customer_name': None,
            'customer_code': None,
            'final_path': None,
            'identification_method': None,  # filename, pdf_content, excel_content, image_ocr
            'identifier_found': None,
            'error_message': None
        }
        
        file_ext = Path(original_filename).suffix.lower()
        customer_identifier = None
        method = None
        
        # 步骤1: 文件名识别（优先）
        customer_identifier = self.extract_customer_from_filename(original_filename)
        if customer_identifier:
            method = 'filename'
        
        # 步骤2: 文件内容解析（次级）
        if not customer_identifier:
            if file_ext == '.pdf':
                customer_identifier = self.extract_customer_from_pdf(file_path)
                if customer_identifier:
                    method = 'pdf_content'
            
            elif file_ext in ['.xlsx', '.xls']:
                customer_identifier = self.extract_customer_from_excel(file_path)
                if customer_identifier:
                    method = 'excel_content'
            
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                customer_identifier = self.extract_customer_from_image(file_path)
                if customer_identifier:
                    method = 'image_ocr'
        
        result['identifier_found'] = customer_identifier
        result['identification_method'] = method
        
        # 步骤3: 客户库匹配
        if customer_identifier:
            customer_info = self.match_customer_in_db(customer_identifier)
            if customer_info:
                result['customer_id'] = customer_info['id']
                result['customer_name'] = customer_info['name']
                result['customer_code'] = customer_info['customer_code']
                
                # 步骤4: 归档到客户目录
                try:
                    # 使用FileStorageManager生成标准路径
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    safe_filename = FileStorageManager.sanitize_filename(original_filename)
                    dest_path = os.path.join(
                        FileStorageManager.BASE_DIR,
                        customer_info['customer_code'],
                        'auto_classified',
                        datetime.now().strftime('%Y-%m'),
                        f"{timestamp}_{safe_filename}"
                    )
                    
                    # 确保目录存在
                    FileStorageManager.ensure_directory(dest_path)
                    
                    # 移动文件
                    import shutil
                    shutil.move(file_path, dest_path)
                    
                    result['status'] = 'success'
                    result['final_path'] = dest_path.replace('\\', '/')
                    
                except Exception as e:
                    result['status'] = 'error'
                    result['error_message'] = f"文件归档失败: {str(e)}"
                    # 归档失败，移到unassigned
                    self._move_to_unassigned(file_path, original_filename, result)
            else:
                # 未找到匹配客户
                self._move_to_unassigned(file_path, original_filename, result)
                result['error_message'] = f"未找到匹配客户: {customer_identifier}"
        else:
            # 无法识别客户标识
            self._move_to_unassigned(file_path, original_filename, result)
            result['error_message'] = "无法从文件名或内容识别客户信息"
        
        return result
    
    def _move_to_unassigned(self, file_path: str, original_filename: str, result: Dict):
        """
        移动文件到未归档区
        
        Args:
            file_path: 文件路径
            original_filename: 原始文件名
            result: 结果字典（会更新final_path）
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = FileStorageManager.sanitize_filename(original_filename)
            dest_path = os.path.join(
                self.UNASSIGNED_DIR,
                datetime.now().strftime('%Y-%m'),
                f"{timestamp}_{safe_filename}"
            )
            
            FileStorageManager.ensure_directory(dest_path)
            
            import shutil
            shutil.move(file_path, dest_path)
            
            result['final_path'] = dest_path.replace('\\', '/')
        except Exception as e:
            print(f"移动到unassigned失败: {str(e)}")
            result['error_message'] = f"移动到未归档区失败: {str(e)}"
    
    def classify_batch_files(self, files_info: List[Dict]) -> Dict:
        """
        批量分类文件
        
        Args:
            files_info: 文件信息列表，每项包含 {'path': '临时路径', 'filename': '原始文件名'}
            
        Returns:
            批量处理结果字典
        """
        results = {
            'total': len(files_info),
            'success': 0,
            'unassigned': 0,
            'error': 0,
            'files': []
        }
        
        for file_info in files_info:
            try:
                result = self.classify_single_file(
                    file_info['path'],
                    file_info['filename']
                )
                results['files'].append(result)
                
                if result['status'] == 'success':
                    results['success'] += 1
                elif result['status'] == 'unassigned':
                    results['unassigned'] += 1
                else:
                    results['error'] += 1
            
            except Exception as e:
                results['files'].append({
                    'filename': file_info['filename'],
                    'status': 'error',
                    'error_message': str(e)
                })
                results['error'] += 1
        
        return results
    
    def get_unassigned_files(self) -> List[Dict]:
        """
        获取所有未归档文件
        
        Returns:
            未归档文件列表
        """
        unassigned_files = []
        
        if not os.path.exists(self.UNASSIGNED_DIR):
            return unassigned_files
        
        for root, dirs, files in os.walk(self.UNASSIGNED_DIR):
            for filename in files:
                file_path = os.path.join(root, filename).replace('\\', '/')
                file_stat = os.stat(file_path)
                
                unassigned_files.append({
                    'filename': filename,
                    'path': file_path,
                    'size': file_stat.st_size,
                    'upload_time': datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return unassigned_files
    
    def manually_assign_file(self, file_path: str, customer_id: int) -> Dict:
        """
        手动分配文件到客户
        
        Args:
            file_path: 未归档文件路径
            customer_id: 目标客户ID
            
        Returns:
            分配结果
        """
        result = {
            'status': 'error',
            'message': None,
            'final_path': None
        }
        
        try:
            # 安全验证：确保文件在unassigned目录内（防止路径遍历、符号链接和TOCTOU攻击）
            
            # 1. 规范化路径（不解析符号链接）
            normalized_path = os.path.abspath(os.path.normpath(file_path))
            unassigned_base = os.path.abspath(os.path.normpath(self.UNASSIGNED_DIR))
            
            # 2. 验证文件存在
            if not os.path.exists(normalized_path):
                result['message'] = '文件不存在'
                return result
            
            # 3. 禁止符号链接（防止symlink逃逸和TOCTOU攻击）
            if os.path.islink(normalized_path):
                result['message'] = 'Security error: Symbolic links are not allowed'
                return result
            
            # 4. 严格验证路径在unassigned目录内
            try:
                common_base = os.path.commonpath([unassigned_base, normalized_path])
                if common_base != unassigned_base:
                    result['message'] = 'Security error: File outside allowed directory'
                    return result
            except ValueError:
                # 不同驱动器或根路径
                result['message'] = 'Security error: Invalid file path'
                return result
            
            # 5. 验证是普通文件（不是目录、设备等）
            if not os.path.isfile(normalized_path):
                result['message'] = 'Security error: Not a regular file'
                return result
            
            # 获取客户信息
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT name, customer_code FROM customers WHERE id = ? AND is_active = 1',
                    (customer_id,)
                )
                customer_info = cursor.fetchone()
                
                if not customer_info:
                    result['message'] = '客户不存在或已禁用'
                    return result
            
            # 生成目标路径
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.basename(normalized_path)
            dest_path = os.path.join(
                FileStorageManager.BASE_DIR,
                customer_info[1],  # customer_code
                'auto_classified',
                datetime.now().strftime('%Y-%m'),
                f"{timestamp}_{filename}"
            )
            
            # TOCTOU防护：移动文件前后验证（防止竞态替换攻击）
            try:
                # 1. 移动前：获取源文件inode（文件唯一标识）
                src_stat_before = os.stat(normalized_path, follow_symlinks=False)
                src_inode_before = src_stat_before.st_ino
                src_dev_before = src_stat_before.st_dev
                
                # 2. 再次验证不是符号链接（防止竞态替换）
                if os.path.islink(normalized_path):
                    result['message'] = 'Security error: File was replaced with symlink'
                    return result
                
                # 3. 执行移动（禁止跟随符号链接）
                FileStorageManager.ensure_directory(dest_path)
                import shutil
                shutil.move(normalized_path, dest_path)
                
                # 4. 移动后：验证目标文件inode与源文件匹配（确保移动的是同一个文件）
                dest_stat_after = os.stat(dest_path, follow_symlinks=False)
                dest_inode_after = dest_stat_after.st_ino
                dest_dev_after = dest_stat_after.st_dev
                
                if src_inode_before != dest_inode_after or src_dev_before != dest_dev_after:
                    # inode不匹配，可能发生了文件替换攻击
                    # 尝试回滚（删除目标文件，恢复源文件）
                    try:
                        os.remove(dest_path)
                    except:
                        pass
                    result['message'] = 'Security error: File identity changed during move (TOCTOU attack detected)'
                    return result
                
            except OSError as e:
                result['message'] = f'文件移动失败: {str(e)}'
                return result
            
            result['status'] = 'success'
            result['message'] = f'文件已归档到客户: {customer_info[0]}'
            result['final_path'] = dest_path.replace('\\', '/')
        
        except Exception as e:
            result['message'] = f'分配失败: {str(e)}'
        
        return result


# 便捷函数
def classify_uploaded_files(files_info: List[Dict]) -> Dict:
    """
    批量分类上传文件（便捷函数）
    
    Args:
        files_info: 文件信息列表
        
    Returns:
        分类结果
    """
    classifier = AutoFileClassifier()
    return classifier.classify_batch_files(files_info)
