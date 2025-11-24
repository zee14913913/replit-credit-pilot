"""
Upload Intake Orchestrator（上传接收编排器）
强制性文件处理Pipeline - 防止健忘机制

Architect设计要求：
- 强制性阶段序列，不能跳过任何步骤
- 每个阶段都有检查点（Checkpoint）
- 所有状态变更都记录到audit log
- 置信度低于0.98自动转人工审核
"""
import os
import hashlib
import uuid
import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Tuple, List
from pathlib import Path

class UploadOrchestrator:
    """
    上传编排器 - 强制执行完整的文件处理流程
    
    Pipeline阶段（强制顺序）：
    1. File Receipt（文件接收）→ PendingChecksum
    2. Checksum Validation（校验和验证）→ PendingParse
    3. Content Parsing（内容解析）→ PendingAttribution
    4. Entity Attribution（归属识别）→ PendingClassification
    5. Business Classification（业务分类）→ ApprovedForStorage
    6. Dual-Write Storage（双写存储）→ StorageComplete
    7. Audit Logging（审计日志）
    
    🚫 任何阶段失败 → Failed 或 PendingReview
    """
    
    # 强制性置信度阈值
    MIN_CONFIDENCE_THRESHOLD = 0.98
    
    # 强制性解析字段
    MANDATORY_PARSE_FIELDS = [
        'owner_name',
        'customer_code',
        'bank_name',
        'statement_date',
        'due_date',
        'statement_total',
        'minimum_payment'
    ]
    
    def __init__(self, db_path: str = 'db/smart_loan_manager.db'):
        self.db_path = db_path
        self.quarantine_dir = 'static/quarantine'
        os.makedirs(self.quarantine_dir, exist_ok=True)
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def _log_state_change(
        self,
        transaction_uuid: str,
        from_status: Optional[str],
        to_status: str,
        reason: str,
        metadata: Optional[Dict] = None
    ):
        """
        记录状态变更（强制审计）
        
        Architect要求：每个状态变更都必须记录
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO upload_state_changes (
                transaction_uuid, from_status, to_status, reason, metadata
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            transaction_uuid,
            from_status,
            to_status,
            reason,
            json.dumps(metadata) if metadata else None
        ))
        
        conn.commit()
        conn.close()
        
        print(f"📝 状态变更: {from_status} → {to_status} | {reason}")
    
    def _update_transaction_status(
        self,
        transaction_uuid: str,
        new_status: str,
        updates: Optional[Dict] = None
    ):
        """
        更新交易状态
        
        Args:
            transaction_uuid: 交易UUID
            new_status: 新状态
            updates: 其他要更新的字段
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 获取当前状态
        cursor.execute('''
            SELECT status FROM upload_transactions
            WHERE transaction_uuid = ?
        ''', (transaction_uuid,))
        
        result = cursor.fetchone()
        old_status = result[0] if result else None
        
        # 更新状态
        update_fields = ['status = ?', 'updated_at = ?']
        values = [new_status, datetime.now().isoformat()]
        
        if updates:
            for key, value in updates.items():
                update_fields.append(f'{key} = ?')
                values.append(value)
        
        values.append(transaction_uuid)
        
        cursor.execute(f'''
            UPDATE upload_transactions
            SET {', '.join(update_fields)}
            WHERE transaction_uuid = ?
        ''', values)
        
        conn.commit()
        conn.close()
        
        # 记录状态变更
        self._log_state_change(
            transaction_uuid,
            old_status,
            new_status,
            f"Status updated to {new_status}",
            updates
        )
    
    # ========================================
    # Stage 1: File Receipt（文件接收）
    # ========================================
    
    def initiate_upload(
        self,
        file_path: str,
        original_filename: str,
        uploaded_by: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """
        启动上传事务
        
        Args:
            file_path: 临时文件路径
            original_filename: 原始文件名
            uploaded_by: 上传人
            ip_address: IP地址
            
        Returns:
            transaction_uuid
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 生成交易UUID
        transaction_uuid = str(uuid.uuid4())
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        
        # 移动到隔离区
        quarantine_path = os.path.join(
            self.quarantine_dir,
            f"{transaction_uuid}_{original_filename}"
        )
        import shutil
        shutil.copy2(file_path, quarantine_path)
        
        # 创建交易记录
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO upload_transactions (
                transaction_uuid, original_filename, file_size,
                status, uploaded_by, ip_address
            ) VALUES (?, ?, ?, 'PendingChecksum', ?, ?)
        ''', (
            transaction_uuid, original_filename, file_size,
            uploaded_by, ip_address
        ))
        
        conn.commit()
        conn.close()
        
        # 记录状态变更
        self._log_state_change(
            transaction_uuid,
            None,
            'PendingChecksum',
            'Upload initiated, file moved to quarantine',
            {'quarantine_path': quarantine_path}
        )
        
        print(f"✅ 上传事务已启动: {transaction_uuid}")
        print(f"   文件: {original_filename}")
        print(f"   大小: {file_size} bytes")
        print(f"   隔离区: {quarantine_path}")
        
        return transaction_uuid
    
    # ========================================
    # Stage 2: Checksum Validation（校验和验证）
    # Checkpoint 1: 重复检测
    # ========================================
    
    def checkpoint_1_validate_checksum(self, transaction_uuid: str) -> Tuple[bool, Optional[str]]:
        """
        检查点1：校验和验证 + 重复检测
        
        Architect要求：
        - 必须计算文件MD5
        - 检查是否重复上传
        - 如果重复，提示现有文件位置
        
        Returns:
            (is_duplicate, existing_file_info)
        """
        print(f"\n🔍 检查点1：校验和验证...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 获取交易信息
        cursor.execute('''
            SELECT original_filename FROM upload_transactions
            WHERE transaction_uuid = ?
        ''', (transaction_uuid,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            raise ValueError(f"交易不存在: {transaction_uuid}")
        
        original_filename = result[0]
        
        # 获取隔离区文件路径
        quarantine_path = os.path.join(
            self.quarantine_dir,
            f"{transaction_uuid}_{original_filename}"
        )
        
        # 计算MD5
        md5_hash = self._calculate_md5(quarantine_path)
        
        # 更新校验和
        cursor.execute('''
            UPDATE upload_transactions
            SET file_checksum = ?
            WHERE transaction_uuid = ?
        ''', (md5_hash, transaction_uuid))
        
        # 检查是否重复（查询file_registry）
        cursor.execute('''
            SELECT file_uuid, original_filename, file_path, upload_date
            FROM file_registry
            WHERE file_hash = ? AND status = 'active'
            ORDER BY upload_date DESC
            LIMIT 1
        ''', (md5_hash,))
        
        duplicate = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        if duplicate:
            # 🚫 重复文件！
            existing_info = {
                'file_uuid': duplicate[0],
                'filename': duplicate[1],
                'path': duplicate[2],
                'upload_date': duplicate[3]
            }
            
            print(f"❌ 重复文件检测！")
            print(f"   现有文件: {existing_info['filename']}")
            print(f"   位置: {existing_info['path']}")
            print(f"   上传时间: {existing_info['upload_date']}")
            
            # 标记为失败
            self._update_transaction_status(
                transaction_uuid,
                'Failed',
                {
                    'failure_reason': f"Duplicate file detected: {existing_info['file_uuid']}",
                    'failure_stage': 'Checksum'
                }
            )
            
            return (True, json.dumps(existing_info))
        
        # ✅ 校验成功，进入下一阶段
        self._update_transaction_status(
            transaction_uuid,
            'PendingParse',
            {'file_checksum': md5_hash}
        )
        
        print(f"✅ 校验成功，MD5: {md5_hash[:16]}...")
        return (False, None)
    
    def _calculate_md5(self, file_path: str) -> str:
        """计算文件MD5哈希"""
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    # ========================================
    # Stage 3: Content Parsing（内容解析）
    # Checkpoint 2: 强制字段提取
    # ========================================
    
    def checkpoint_2_parse_content(self, transaction_uuid: str, parser_service) -> Tuple[bool, Optional[Dict]]:
        """
        检查点2：内容解析
        
        Architect要求：
        - 必须提取7个强制字段
        - owner_name, customer_code, bank_name
        - statement_date, due_date, statement_total, minimum_payment
        - 任何字段缺失 → 人工审核
        
        Args:
            transaction_uuid: 交易UUID
            parser_service: PDF解析服务
            
        Returns:
            (success, parsed_data)
        """
        print(f"\n🔍 检查点2：内容解析...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 获取文件路径
        cursor.execute('''
            SELECT original_filename FROM upload_transactions
            WHERE transaction_uuid = ?
        ''', (transaction_uuid,))
        
        result = cursor.fetchone()
        original_filename = result[0]
        
        quarantine_path = os.path.join(
            self.quarantine_dir,
            f"{transaction_uuid}_{original_filename}"
        )
        
        # 调用解析服务
        try:
            parsed_data = parser_service.parse_pdf(quarantine_path)
            
            # 验证强制字段
            missing_fields = []
            for field in self.MANDATORY_PARSE_FIELDS:
                if field not in parsed_data or not parsed_data[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                # ⚠️ 字段缺失，转人工审核
                print(f"⚠️  缺失强制字段: {', '.join(missing_fields)}")
                
                self._update_transaction_status(
                    transaction_uuid,
                    'PendingReview',
                    {
                        'review_required': 1,
                        'review_reason': f"Missing mandatory fields: {', '.join(missing_fields)}",
                        'failure_stage': 'Parse'
                    }
                )
                
                conn.close()
                return (False, None)
            
            # ✅ 解析成功，保存结果
            cursor.execute('''
                UPDATE upload_transactions
                SET 
                    parsed_owner_name = ?,
                    parsed_customer_code = ?,
                    parsed_bank_name = ?,
                    parsed_statement_date = ?,
                    parsed_due_date = ?,
                    parsed_statement_total = ?,
                    parsed_minimum_payment = ?,
                    status = 'PendingAttribution'
                WHERE transaction_uuid = ?
            ''', (
                parsed_data.get('owner_name'),
                parsed_data.get('customer_code'),
                parsed_data.get('bank_name'),
                parsed_data.get('statement_date'),
                parsed_data.get('due_date'),
                parsed_data.get('statement_total'),
                parsed_data.get('minimum_payment'),
                transaction_uuid
            ))
            
            conn.commit()
            conn.close()
            
            self._log_state_change(
                transaction_uuid,
                'PendingParse',
                'PendingAttribution',
                'Parsing successful, all mandatory fields extracted',
                parsed_data
            )
            
            print(f"✅ 解析成功")
            print(f"   主人: {parsed_data.get('owner_name')}")
            print(f"   银行: {parsed_data.get('bank_name')}")
            print(f"   日期: {parsed_data.get('statement_date')}")
            
            return (True, parsed_data)
            
        except Exception as e:
            # ❌ 解析失败
            print(f"❌ 解析失败: {e}")
            
            self._update_transaction_status(
                transaction_uuid,
                'PendingReview',
                {
                    'review_required': 1,
                    'review_reason': f"Parse failed: {str(e)}",
                    'failure_stage': 'Parse'
                }
            )
            
            conn.close()
            return (False, None)
    
    # ========================================
    # Stage 4: Entity Attribution（归属识别）
    # Checkpoint 3: 客户匹配 + 置信度评分
    # ========================================
    
    def checkpoint_3_attribute_entity(self, transaction_uuid: str) -> Tuple[bool, Optional[Dict]]:
        """
        检查点3：归属识别
        
        Architect要求：
        - 交叉引用customers表
        - 计算匹配置信度
        - 置信度 < 0.98 → 人工审核
        
        Returns:
            (success, attribution_result)
        """
        print(f"\n🔍 检查点3：归属识别...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 获取解析结果
        cursor.execute('''
            SELECT parsed_owner_name, parsed_customer_code
            FROM upload_transactions
            WHERE transaction_uuid = ?
        ''', (transaction_uuid,))
        
        result = cursor.fetchone()
        parsed_owner_name, parsed_customer_code = result
        
        # 查询customers表匹配
        cursor.execute('''
            SELECT id, customer_code, name
            FROM customers
            WHERE LOWER(name) LIKE LOWER(?) 
               OR customer_code = ?
            LIMIT 5
        ''', (f'%{parsed_owner_name}%', parsed_customer_code))
        
        matches = cursor.fetchall()
        
        if not matches:
            # ⚠️ 无匹配客户，转人工审核
            print(f"⚠️  未找到匹配客户: {parsed_owner_name}")
            
            self._update_transaction_status(
                transaction_uuid,
                'PendingReview',
                {
                    'review_required': 1,
                    'review_reason': f"No customer match found for: {parsed_owner_name}",
                    'failure_stage': 'Attribution'
                }
            )
            
            conn.close()
            return (False, None)
        
        # 计算置信度（简单实现：精确匹配=1.0，模糊匹配<1.0）
        best_match = matches[0]
        customer_id, customer_code, customer_name = best_match
        
        # 置信度评分
        confidence = self._calculate_attribution_confidence(
            parsed_owner_name,
            parsed_customer_code,
            customer_name,
            customer_code
        )
        
        print(f"   最佳匹配: {customer_name} ({customer_code})")
        print(f"   置信度: {confidence:.4f}")
        
        if confidence < self.MIN_CONFIDENCE_THRESHOLD:
            # ⚠️ 置信度不足，转人工审核
            print(f"⚠️  置信度低于阈值({self.MIN_CONFIDENCE_THRESHOLD})")
            
            self._update_transaction_status(
                transaction_uuid,
                'PendingReview',
                {
                    'review_required': 1,
                    'review_reason': f"Low attribution confidence: {confidence:.4f} < {self.MIN_CONFIDENCE_THRESHOLD}",
                    'attributed_customer_id': customer_id,
                    'attributed_customer_code': customer_code,
                    'attribution_confidence': confidence,
                    'failure_stage': 'Attribution'
                }
            )
            
            conn.close()
            return (False, None)
        
        # ✅ 归属成功
        self._update_transaction_status(
            transaction_uuid,
            'PendingClassification',
            {
                'attributed_customer_id': customer_id,
                'attributed_customer_code': customer_code,
                'attribution_confidence': confidence
            }
        )
        
        print(f"✅ 归属成功: {customer_name}")
        
        conn.close()
        return (True, {
            'customer_id': customer_id,
            'customer_code': customer_code,
            'customer_name': customer_name,
            'confidence': confidence
        })
    
    def _calculate_attribution_confidence(
        self,
        parsed_name: str,
        parsed_code: str,
        db_name: str,
        db_code: str
    ) -> float:
        """
        计算归属置信度
        
        规则：
        - customer_code精确匹配 = 1.0
        - name精确匹配（忽略大小写）= 1.0
        - name包含匹配 = 0.9
        - 其他 = 0.7
        """
        # 精确匹配customer_code
        if parsed_code and parsed_code.upper() == db_code.upper():
            return 1.0
        
        # 精确匹配name（忽略大小写和空格）
        parsed_clean = parsed_name.upper().replace(' ', '')
        db_clean = db_name.upper().replace(' ', '')
        
        if parsed_clean == db_clean:
            return 1.0
        
        # 包含匹配
        if parsed_clean in db_clean or db_clean in parsed_clean:
            return 0.9
        
        # 模糊匹配
        return 0.7
    
    # ========================================
    # Stage 5: Business Classification（业务分类）
    # Checkpoint 4: 自动分类
    # ========================================
    
    def checkpoint_4_classify_business_type(
        self,
        transaction_uuid: str,
        business_type: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        检查点4：业务分类
        
        Args:
            transaction_uuid: 交易UUID
            business_type: 业务类型（如果用户已指定）
                          None = 自动分类
                          'personal' / 'company' / 'mixed' = 用户指定
        
        Returns:
            (success, business_type)
        """
        print(f"\n🔍 检查点4：业务分类...")
        
        if business_type:
            # 用户已指定
            print(f"✅ 用户指定业务类型: {business_type}")
            
            self._update_transaction_status(
                transaction_uuid,
                'ApprovedForStorage',
                {
                    'classified_business_type': business_type,
                    'classification_confidence': 1.0,
                    'classification_reason': 'User specified'
                }
            )
            
            return (True, business_type)
        
        # TODO: 自动分类逻辑
        # 简单实现：默认为personal，等待人工确认
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT parsed_owner_name, attributed_customer_code
            FROM upload_transactions
            WHERE transaction_uuid = ?
        ''', (transaction_uuid,))
        
        result = cursor.fetchone()
        owner_name, customer_code = result
        
        # 简单规则：如果owner_name包含公司关键字
        company_keywords = ['SDN BHD', 'PTY LTD', 'COMPANY', 'CORPORATION', 'INFINITE']
        is_company = any(kw in owner_name.upper() for kw in company_keywords)
        
        if is_company:
            classified_type = 'company'
            confidence = 0.9
        else:
            classified_type = 'personal'
            confidence = 0.85
        
        if confidence < self.MIN_CONFIDENCE_THRESHOLD:
            # 转人工审核
            print(f"⚠️  分类置信度不足: {confidence:.4f}")
            
            self._update_transaction_status(
                transaction_uuid,
                'PendingReview',
                {
                    'review_required': 1,
                    'review_reason': f"Low classification confidence: {confidence:.4f}",
                    'classified_business_type': classified_type,
                    'classification_confidence': confidence,
                    'failure_stage': 'Classification'
                }
            )
            
            conn.close()
            return (False, classified_type)
        
        # ✅ 分类成功
        self._update_transaction_status(
            transaction_uuid,
            'ApprovedForStorage',
            {
                'classified_business_type': classified_type,
                'classification_confidence': confidence,
                'classification_reason': 'Auto-classified based on keywords'
            }
        )
        
        print(f"✅ 自动分类: {classified_type} (置信度: {confidence:.4f})")
        
        conn.close()
        return (True, classified_type)
    
    # ========================================
    # Stage 6: Dual-Write Storage（双写存储）
    # Final Checkpoint: 强制双写
    # ========================================
    
    def final_checkpoint_dual_write_storage(
        self,
        transaction_uuid: str,
        file_storage_manager,
        file_integrity_service
    ) -> bool:
        """
        最终检查点：双写存储
        
        Architect要求：
        - 必须同时写入主存储和备份
        - 必须注册到file_registry
        - 任何失败 → 回滚
        
        Returns:
            success
        """
        print(f"\n🔍 最终检查点：双写存储...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 获取事务信息
        cursor.execute('''
            SELECT 
                original_filename, file_checksum,
                attributed_customer_id, attributed_customer_code,
                classified_business_type,
                parsed_bank_name, parsed_statement_date
            FROM upload_transactions
            WHERE transaction_uuid = ? AND status = 'ApprovedForStorage'
        ''', (transaction_uuid,))
        
        result = cursor.fetchone()
        if not result:
            print(f"❌ 事务未批准存储")
            conn.close()
            return False
        
        (original_filename, file_checksum, customer_id, customer_code,
         business_type, bank_name, statement_date) = result
        
        # 获取隔离区文件
        quarantine_path = os.path.join(
            self.quarantine_dir,
            f"{transaction_uuid}_{original_filename}"
        )
        
        try:
            # 1. 生成标准路径
            from datetime import datetime as dt
            stmt_date = dt.fromisoformat(statement_date)
            
            final_path = file_storage_manager.generate_credit_card_path(
                customer_code,
                bank_name,
                '0000',  # 卡号后4位（从parsed_data获取）
                stmt_date
            )
            
            # 2. 双写：主存储 + 备份
            # 主存储
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            import shutil
            shutil.copy2(quarantine_path, final_path)
            
            # 备份
            backup_path = final_path.replace('static/uploads', 'static/uploads_backup')
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(quarantine_path, backup_path)
            
            # 3. 注册到file_registry
            file_uuid = file_integrity_service.register_file(
                file_path=final_path,
                customer_id=customer_id,
                customer_code=customer_code,
                business_type=business_type,
                file_category='credit_card_statement',
                original_filename=original_filename
            )
            
            if not file_uuid:
                raise Exception("Failed to register file in file_registry")
            
            # 4. 更新事务状态
            cursor.execute('''
                UPDATE upload_transactions
                SET 
                    final_file_path = ?,
                    backup_file_path = ?,
                    file_registry_id = (SELECT id FROM file_registry WHERE file_uuid = ?),
                    status = 'StorageComplete'
                WHERE transaction_uuid = ?
            ''', (final_path, backup_path, file_uuid, transaction_uuid))
            
            conn.commit()
            
            # 5. 删除隔离区文件
            os.remove(quarantine_path)
            
            # 记录状态变更
            self._log_state_change(
                transaction_uuid,
                'ApprovedForStorage',
                'StorageComplete',
                'File stored successfully with dual-write',
                {
                    'final_path': final_path,
                    'backup_path': backup_path,
                    'file_uuid': file_uuid
                }
            )
            
            print(f"✅ 存储完成！")
            print(f"   主路径: {final_path}")
            print(f"   备份路径: {backup_path}")
            print(f"   File UUID: {file_uuid}")
            
            conn.close()
            return True
            
        except Exception as e:
            # 回滚
            print(f"❌ 存储失败: {e}")
            
            # 清理已创建的文件
            if os.path.exists(final_path):
                os.remove(final_path)
            if os.path.exists(backup_path):
                os.remove(backup_path)
            
            self._update_transaction_status(
                transaction_uuid,
                'Failed',
                {
                    'failure_reason': f"Storage failed: {str(e)}",
                    'failure_stage': 'Storage'
                }
            )
            
            conn.close()
            return False
    
    # ========================================
    # 完整Pipeline执行
    # ========================================
    
    def execute_full_pipeline(
        self,
        file_path: str,
        original_filename: str,
        parser_service,
        file_storage_manager,
        file_integrity_service,
        business_type: Optional[str] = None,
        uploaded_by: Optional[str] = None
    ) -> Dict:
        """
        执行完整的上传Pipeline
        
        强制性阶段（不可跳过）：
        1. Initiate Upload
        2. Checkpoint 1: Checksum Validation
        3. Checkpoint 2: Content Parsing
        4. Checkpoint 3: Entity Attribution
        5. Checkpoint 4: Business Classification
        6. Final Checkpoint: Dual-Write Storage
        
        Returns:
            结果字典
        """
        print("=" * 80)
        print("🚀 启动强制性上传Pipeline")
        print("=" * 80)
        
        # Stage 1: 启动
        transaction_uuid = self.initiate_upload(
            file_path, original_filename, uploaded_by
        )
        
        # Stage 2: Checkpoint 1 - Checksum
        is_duplicate, duplicate_info = self.checkpoint_1_validate_checksum(transaction_uuid)
        if is_duplicate:
            return {
                'success': False,
                'reason': 'Duplicate file detected',
                'duplicate_info': json.loads(duplicate_info),
                'transaction_uuid': transaction_uuid
            }
        
        # Stage 3: Checkpoint 2 - Parse
        parse_success, parsed_data = self.checkpoint_2_parse_content(
            transaction_uuid, parser_service
        )
        if not parse_success:
            return {
                'success': False,
                'reason': 'Parsing failed, pending review',
                'transaction_uuid': transaction_uuid
            }
        
        # Stage 4: Checkpoint 3 - Attribution
        attribution_success, attribution_result = self.checkpoint_3_attribute_entity(
            transaction_uuid
        )
        if not attribution_success:
            return {
                'success': False,
                'reason': 'Attribution failed, pending review',
                'transaction_uuid': transaction_uuid
            }
        
        # Stage 5: Checkpoint 4 - Classification
        classification_success, classified_type = self.checkpoint_4_classify_business_type(
            transaction_uuid, business_type
        )
        if not classification_success:
            return {
                'success': False,
                'reason': 'Classification confidence too low, pending review',
                'transaction_uuid': transaction_uuid
            }
        
        # Stage 6: Final Checkpoint - Storage
        storage_success = self.final_checkpoint_dual_write_storage(
            transaction_uuid,
            file_storage_manager,
            file_integrity_service
        )
        
        if not storage_success:
            return {
                'success': False,
                'reason': 'Storage failed',
                'transaction_uuid': transaction_uuid
            }
        
        # ✅ Pipeline完成！
        print("\n" + "=" * 80)
        print("✅ 上传Pipeline完成！")
        print("=" * 80)
        
        return {
            'success': True,
            'transaction_uuid': transaction_uuid,
            'customer': attribution_result,
            'business_type': classified_type,
            'parsed_data': parsed_data
        }


# 全局实例
upload_orchestrator = UploadOrchestrator()
