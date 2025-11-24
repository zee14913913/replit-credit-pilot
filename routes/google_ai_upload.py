"""
Google Document AI上传路由
整合到Credit Card Statement Upload流程
"""
from flask import Blueprint, request, jsonify, session
from services.google_document_ai_service import GoogleDocumentAIService
from services.monthly_ledger_engine import MonthlyLedgerEngine
from services.ledger_classifier import LedgerClassifier
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

google_ai_bp = Blueprint('google_ai', __name__)

@google_ai_bp.route('/api/upload/google-ai', methods=['POST'])
def upload_google_ai():
    """
    使用Google Document AI处理上传的PDF
    完全替代DocParser
    """
    try:
        # 检查文件
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '未选择文件'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': '仅支持PDF文件'}), 400
        
        # 获取客户信息
        customer_code = request.form.get('customer_code')
        
        if not customer_code:
            return jsonify({'success': False, 'error': '缺少客户代码'}), 400
        
        # 保存临时文件
        upload_folder = Path('static/uploads/temp')
        upload_folder.mkdir(parents=True, exist_ok=True)
        
        temp_file = upload_folder / file.filename
        file.save(str(temp_file))
        
        logger.info(f"📄 收到文件: {file.filename}")
        
        # 使用Google Document AI解析
        logger.info("🔍 使用Google Document AI解析...")
        google_service = GoogleDocumentAIService()
        
        parsed_doc = google_service.parse_pdf(str(temp_file))
        fields = google_service.extract_bank_statement_fields(parsed_doc)
        
        # 提取关键字段
        card_last4 = fields.get('card_number', '')
        statement_date = fields.get('statement_date', '')
        previous_balance = fields.get('previous_balance', 0)
        current_balance = fields.get('current_balance', 0)
        transactions = fields.get('transactions', [])
        
        logger.info(f"✅ 解析完成: {len(transactions)}笔交易")
        
        # 分类交易（Owner vs INFINITE）
        classifier = LedgerClassifier()
        classified_transactions = []
        
        owner_total = 0
        infinite_total = 0
        
        for trans in transactions:
            classification = classifier.classify_transaction(
                description=trans.get('description', ''),
                amount=trans.get('amount', 0),
                transaction_type=trans.get('type', 'DR')
            )
            
            trans['owner'] = classification['owner']
            trans['ledger'] = classification['ledger']
            
            if classification['ledger'] == 'Owner':
                owner_total += trans['amount']
            else:
                infinite_total += trans['amount']
            
            classified_transactions.append(trans)
        
        # 保存到数据库
        ledger_engine = MonthlyLedgerEngine()
        
        statement_id = ledger_engine.save_monthly_statement(
            customer_code=customer_code,
            bank_name=fields.get('bank_name', 'Unknown'),
            card_last4=card_last4,
            statement_date=statement_date,
            previous_balance=previous_balance,
            current_balance=current_balance,
            owner_total=owner_total,
            infinite_total=infinite_total,
            transactions=classified_transactions
        )
        
        logger.info(f"💾 保存成功: Statement ID {statement_id}")
        
        # 删除临时文件
        os.remove(temp_file)
        
        return jsonify({
            'success': True,
            'statement_id': statement_id,
            'fields': {
                'card_number': card_last4,
                'statement_date': statement_date,
                'previous_balance': previous_balance,
                'current_balance': current_balance,
                'total_transactions': len(classified_transactions),
                'owner_total': owner_total,
                'infinite_total': infinite_total
            }
        })
    
    except Exception as e:
        logger.error(f"❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
