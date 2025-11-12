"""
Card Optimizer API Routes (Fixed Version)
修复了architect指出的所有问题：
1. 使用get_db()而非硬编码sqlite3连接
2. 正确持久化数据到数据库
3. 按每张卡的实际金额验证风险
4. 使用正确的表名（card_optimizer_*）
5. 完整的错误处理和事务管理
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime, date, timedelta
from typing import Dict, List

# 导入核心算法引擎
from services.float_calculator import FloatDaysCalculator
from services.card_optimizer import CardOptimizer
from services.payment_prioritizer import PaymentPrioritizer
from services.risk_validator import RiskValidator

# 导入认证模块
from auth.admin_auth_helper import require_admin_or_accountant, get_current_user

# 数据库连接（修复：使用get_db而非直接sqlite3）
from db.database import get_db, log_audit

# 创建Blueprint
card_optimizer_bp = Blueprint('card_optimizer', __name__, url_prefix='/api/card-optimizer')


# ==================== 核心API ====================

@card_optimizer_bp.route('/generate-plan', methods=['POST'])
@require_admin_or_accountant
def generate_plan():
    """
    生成智能排卡优化方案
    
    修复：
    1. 使用get_db()作为context manager
    2. 单事务持久化所有数据
    3. 按每张卡的实际承担金额验证风险
    """
    try:
        data = request.get_json()
        customer_id = data.get('customer_id')
        purchase_date_str = data.get('purchase_date')
        expected_amount = float(data.get('expected_amount', 0))
        monthly_income = data.get('monthly_income')
        
        # 验证参数
        if not customer_id or not purchase_date_str:
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400
        
        # 解析日期
        purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
        
        # Step 1: 获取客户的所有信用卡（使用get_db）
        with get_db() as conn:
            conn.row_factory = lambda cursor, row: {
                col[0]: row[idx] for idx, col in enumerate(cursor.description)
            }
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    id,
                    bank_name,
                    card_type,
                    credit_limit,
                    current_balance,
                    statement_cutoff_day,
                    payment_due_day,
                    SUBSTR(card_number, -4) as card_number_last4
                FROM credit_cards
                WHERE customer_id = ?
                AND statement_cutoff_day IS NOT NULL
                AND payment_due_day IS NOT NULL
            """, (customer_id,))
            
            cards_raw = cursor.fetchall()
        
        if not cards_raw:
            return jsonify({
                'success': False,
                'error': '此客户没有设置账单日/到期日的信用卡'
            }), 404
        
        # 转换为算法引擎所需格式
        cards = []
        for card in cards_raw:
            cards.append({
                'id': card['id'],
                'bank_name': card['bank_name'],
                'credit_limit': card['credit_limit'] or 0,
                'current_balance': card['current_balance'] or 0,
                'cutoff_day': card['statement_cutoff_day'],
                'due_day': card['payment_due_day'],
                'card_number_last4': card['card_number_last4']
            })
        
        # Step 2: 使用排卡优化引擎生成方案
        optimizer = CardOptimizer()
        plan = optimizer.optimize_for_customer(
            cards, 
            purchase_date, 
            expected_amount
        )
        
        # Step 3: 风险验证（修复：为每张卡使用实际承担金额）
        risk_validator = RiskValidator()
        risks_by_card = []
        
        for card_rec in plan['recommended_cards']:
            # 找回完整的卡信息
            full_card = next((c for c in cards if c['id'] == card_rec['card_id']), None)
            if not full_card:
                continue
            
            # 修复：使用实际金额而非总金额
            # 假设用户选择推荐的第一张卡来承担全部消费
            card_amount = expected_amount if card_rec['priority_rank'] == 1 else 0
            
            risk = risk_validator.validate_card_usage(
                full_card,
                card_amount,
                monthly_income
            )
            
            risks_by_card.append({
                'card_id': card_rec['card_id'],
                'risk_level': risk['risk_level'],
                'risk_score': risk['risk_score'],
                'warnings': risk['warnings'],
                'requires_consent': risk['requires_consent']
            })
        
        # Step 4: 持久化到数据库（单事务）
        with get_db() as conn:
            cursor = conn.cursor()
            
            try:
                # 4a. 插入主方案记录到card_optimizer_plans
                cursor.execute("""
                    INSERT INTO card_optimizer_plans
                    (customer_id, plan_month, expected_amount, total_available_credit,
                     status, created_at)
                    VALUES (?, ?, ?, ?, 'draft', datetime('now'))
                """, (
                    customer_id,
                    purchase_date.strftime('%Y-%m'),
                    expected_amount,
                    plan['total_available']
                ))
                
                plan_id = cursor.lastrowid
                
                # 4b. 批量插入每张卡的推荐记录到card_optimizer_cards
                for card_rec in plan['recommended_cards']:
                    cursor.execute("""
                        INSERT INTO card_optimizer_cards
                        (plan_id, card_id, priority_rank, float_days, risk_level,
                         recommendation_reason, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                    """, (
                        plan_id,
                        card_rec['card_id'],
                        card_rec['priority_rank'],
                        card_rec['float_days'],
                        card_rec.get('risk_level', 'low'),
                        card_rec.get('recommendation', '')
                    ))
                
                # 4c. 插入风险记录到card_risk_consents（仅高风险）
                for risk in risks_by_card:
                    if risk['requires_consent']:
                        cursor.execute("""
                            INSERT INTO card_risk_consents
                            (customer_id, plan_id, risk_type, risk_description,
                             consent_given, created_at)
                            VALUES (?, ?, ?, ?, 0, datetime('now'))
                        """, (
                            customer_id,
                            plan_id,
                            'high_utilization',
                            '; '.join(risk['warnings'])
                        ))
                
                # 4d. 提交事务
                conn.commit()
                
                # 记录审计日志
                current_user = get_current_user()
                if current_user:
                    log_audit(
                        user_id=current_user.get('id'),
                        action_type='generate_card_optimizer_plan',
                        entity_type='card_optimizer_plan',
                        entity_id=plan_id,
                        description=f'Generated optimization plan for customer {customer_id}, amount RM{expected_amount}'
                    )
                
            except Exception as db_error:
                conn.rollback()
                raise Exception(f'数据库写入失败: {db_error}')
        
        # Step 5: 返回完整结果
        return jsonify({
            'success': True,
            'plan_id': plan_id,
            'plan': {
                'recommended_cards': plan['recommended_cards'],
                'total_available': plan['total_available'],
                'is_sufficient': plan['is_sufficient'],
                'warnings': plan['warnings']
            },
            'risks': risks_by_card,
            'purchase_date': purchase_date_str,
            'expected_amount': expected_amount
        })
    
    except Exception as e:
        # 统一错误处理
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@card_optimizer_bp.route('/simulate-float', methods=['POST'])
@require_admin_or_accountant
def simulate_float():
    """模拟免息期：比较多张卡在指定日期的免息天数"""
    try:
        data = request.get_json()
        card_ids = data.get('card_ids', [])
        purchase_date_str = data.get('purchase_date')
        
        if not card_ids or not purchase_date_str:
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400
        
        purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
        
        # 使用get_db获取卡片信息
        with get_db() as conn:
            conn.row_factory = lambda cursor, row: {
                col[0]: row[idx] for idx, col in enumerate(cursor.description)
            }
            cursor = conn.cursor()
            
            placeholders = ','.join(['?'] * len(card_ids))
            cursor.execute(f"""
                SELECT 
                    id,
                    bank_name,
                    statement_cutoff_day,
                    payment_due_day,
                    SUBSTR(card_number, -4) as card_number_last4
                FROM credit_cards
                WHERE id IN ({placeholders})
                AND statement_cutoff_day IS NOT NULL
                AND payment_due_day IS NOT NULL
            """, card_ids)
            
            cards_raw = cursor.fetchall()
        
        if not cards_raw:
            return jsonify({
                'success': False,
                'error': '没有找到有效的信用卡'
            }), 404
        
        # 转换格式
        cards = []
        for card in cards_raw:
            cards.append({
                'id': card['id'],
                'bank_name': card['bank_name'],
                'cutoff_day': card['statement_cutoff_day'],
                'due_day': card['payment_due_day'],
                'card_number_last4': card['card_number_last4']
            })
        
        # 使用免息期计算器
        calc = FloatDaysCalculator()
        comparison = calc.compare_cards_float_days(cards, purchase_date)
        
        # 转换日期为字符串
        for item in comparison:
            item['statement_date'] = item['statement_date'].isoformat()
            item['due_date'] = item['due_date'].isoformat()
        
        return jsonify({
            'success': True,
            'purchase_date': purchase_date_str,
            'comparison': comparison
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@card_optimizer_bp.route('/confirm-plan', methods=['POST'])
@require_admin_or_accountant
def confirm_plan():
    """
    确认排卡方案并记录风险告知
    
    修复：使用正确的表名card_optimizer_plans和card_risk_consents
    """
    try:
        data = request.get_json()
        plan_id = data.get('plan_id')
        customer_id = data.get('customer_id')
        selected_card_id = data.get('selected_card_id')
        risk_acknowledged = data.get('risk_acknowledged', False)
        
        if not all([plan_id, customer_id, selected_card_id]):
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400
        
        # 如果存在风险，必须确认
        if not risk_acknowledged:
            return jsonify({
                'success': False,
                'error': '请阅读并确认风险告知'
            }), 400
        
        # 使用get_db记录确认
        with get_db() as conn:
            cursor = conn.cursor()
            
            try:
                # 获取客户端信息
                ip_address = request.remote_addr
                user_agent = request.user_agent.string
                
                # 更新风险确认记录
                cursor.execute("""
                    UPDATE card_risk_consents
                    SET consent_given = 1,
                        consent_timestamp = datetime('now'),
                        ip_address = ?,
                        user_agent = ?
                    WHERE plan_id = ? AND customer_id = ?
                """, (ip_address, user_agent, plan_id, customer_id))
                
                # 更新计划状态
                cursor.execute("""
                    UPDATE card_optimizer_plans
                    SET status = 'confirmed',
                        confirmed_at = datetime('now')
                    WHERE id = ? AND customer_id = ?
                """, (plan_id, customer_id))
                
                conn.commit()
                
                # 记录审计日志
                current_user = get_current_user()
                if current_user:
                    log_audit(
                        user_id=current_user.get('id'),
                        action_type='confirm_card_optimizer_plan',
                        entity_type='card_optimizer_plan',
                        entity_id=plan_id,
                        description=f'Confirmed plan {plan_id}, selected card {selected_card_id}'
                    )
                
            except Exception as db_error:
                conn.rollback()
                raise Exception(f'确认失败: {db_error}')
        
        return jsonify({
            'success': True,
            'message': '方案确认成功'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@card_optimizer_bp.route('/payment-priority', methods=['POST'])
@require_admin_or_accountant
def payment_priority():
    """计算还款优先级"""
    try:
        data = request.get_json()
        customer_id = data.get('customer_id')
        available_funds = float(data.get('available_funds', 0))
        
        if not customer_id:
            return jsonify({
                'success': False,
                'error': '缺少customer_id'
            }), 400
        
        # 使用get_db获取信用卡信息
        with get_db() as conn:
            conn.row_factory = lambda cursor, row: {
                col[0]: row[idx] for idx, col in enumerate(cursor.description)
            }
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    id,
                    bank_name,
                    current_balance,
                    payment_due_day,
                    min_payment_rate,
                    interest_rate
                FROM credit_cards
                WHERE customer_id = ?
                AND current_balance > 0
            """, (customer_id,))
            
            cards_raw = cursor.fetchall()
        
        if not cards_raw:
            return jsonify({
                'success': False,
                'error': '此客户没有需要还款的信用卡'
            }), 404
        
        # 转换并计算下一个到期日
        cards = []
        today = date.today()
        
        for card in cards_raw:
            due_day = card['payment_due_day']
            if due_day:
                if today.day <= due_day:
                    next_due = date(today.year, today.month, min(due_day, 28))
                else:
                    next_month = today.month + 1 if today.month < 12 else 1
                    next_year = today.year if today.month < 12 else today.year + 1
                    next_due = date(next_year, next_month, min(due_day, 28))
            else:
                next_due = today + timedelta(days=30)
            
            cards.append({
                'id': card['id'],
                'bank_name': card['bank_name'],
                'current_balance': card['current_balance'] or 0,
                'next_due_date': next_due,
                'interest_rate': card['interest_rate'] or 18.0,
                'min_payment_rate': card['min_payment_rate'] or 5.0
            })
        
        # 使用还款优先级引擎
        prioritizer = PaymentPrioritizer()
        result = prioritizer.prioritize_payments(cards, available_funds)
        
        # 转换日期为字符串
        for plan in result['payment_plans']:
            plan['due_date'] = plan['due_date'].isoformat()
        
        return jsonify({
            'success': True,
            'payment_plans': result['payment_plans'],
            'total_minimum': result['total_minimum'],
            'total_recommended': result['total_recommended'],
            'funding_gap': result['funding_gap'],
            'warnings': result['warnings']
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== Blueprint注册 ====================

def register_card_optimizer_routes(app):
    """注册Blueprint到Flask App"""
    app.register_blueprint(card_optimizer_bp)
    print("✅ Card Optimizer API Routes (Fixed) registered")
