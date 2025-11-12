"""
Card Optimizer API Routes
智能排卡优化系统的Flask Blueprint API
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime, date
import sqlite3
from typing import Dict, List

# 导入核心算法引擎
from services.float_calculator import FloatDaysCalculator
from services.card_optimizer import CardOptimizer
from services.payment_prioritizer import PaymentPrioritizer
from services.risk_validator import RiskValidator

# 导入认证模块
from auth.admin_auth_helper import require_admin_or_accountant, get_current_user

# 数据库连接
from db.database import get_db

# 创建Blueprint
card_optimizer_bp = Blueprint('card_optimizer', __name__, url_prefix='/api/card-optimizer')


# ==================== 核心API ====================

@card_optimizer_bp.route('/generate-plan', methods=['POST'])
@require_admin_or_accountant
def generate_plan():
    """
    生成智能排卡优化方案
    
    Request Body:
    {
        "customer_id": int,
        "purchase_date": "YYYY-MM-DD",
        "expected_amount": float,
        "monthly_income": float (optional)
    }
    
    Response:
    {
        "success": bool,
        "plan": {
            "recommended_cards": [...],
            "total_available": float,
            "is_sufficient": bool,
            "warnings": [...]
        }
    }
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
        
        # 获取客户的所有信用卡
        conn = sqlite3.connect('db/smart_loan_manager.db')
        conn.row_factory = sqlite3.Row
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
        conn.close()
        
        if not cards_raw:
            return jsonify({
                'success': False,
                'error': '此客户没有设置账单日/到期日的信用卡'
            }), 404
        
        # 转换为字典格式
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
        
        # 使用排卡优化引擎
        optimizer = CardOptimizer()
        plan = optimizer.optimize_for_customer(
            cards, 
            purchase_date, 
            expected_amount
        )
        
        # 风险验证
        risk_validator = RiskValidator()
        risks_by_card = []
        
        for card in plan['recommended_cards']:
            # 找回完整的卡信息
            full_card = next((c for c in cards if c['id'] == card['card_id']), None)
            if full_card:
                risk = risk_validator.validate_card_usage(
                    full_card,
                    expected_amount,
                    monthly_income
                )
                risks_by_card.append({
                    'card_id': card['card_id'],
                    'risk_level': risk['risk_level'],
                    'risk_score': risk['risk_score'],
                    'warnings': risk['warnings'],
                    'requires_consent': risk['requires_consent']
                })
        
        # 保存计划到数据库（可选，用于历史记录）
        plan_id = _save_plan_to_db(
            customer_id,
            purchase_date,
            expected_amount,
            plan
        )
        
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@card_optimizer_bp.route('/simulate-float', methods=['POST'])
@require_admin_or_accountant
def simulate_float():
    """
    模拟免息期：比较多张卡在指定日期的免息天数
    
    Request Body:
    {
        "card_ids": [int, ...],
        "purchase_date": "YYYY-MM-DD"
    }
    
    Response:
    {
        "success": bool,
        "comparison": [
            {
                "card_id": int,
                "bank_name": str,
                "float_days": int,
                "statement_date": str,
                "due_date": str,
                "is_optimal": bool
            },
            ...
        ]
    }
    """
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
        
        # 获取卡片信息
        conn = sqlite3.connect('db/smart_loan_manager.db')
        conn.row_factory = sqlite3.Row
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
        conn.close()
        
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


@card_optimizer_bp.route('/calendar-heatmap', methods=['GET'])
@require_admin_or_accountant
def calendar_heatmap():
    """
    生成日历热力图：显示某张卡在整个月每一天的免息天数
    
    Query Params:
    - card_id: int
    - month: "YYYY-MM"
    
    Response:
    {
        "success": bool,
        "heatmap": {
            "card_id": int,
            "bank_name": str,
            "month": str,
            "best_window": {...},
            "calendar_data": {
                "YYYY-MM-DD": int (float_days),
                ...
            }
        }
    }
    """
    try:
        card_id = request.args.get('card_id', type=int)
        month = request.args.get('month')
        
        if not card_id or not month:
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400
        
        # 获取卡片信息
        conn = sqlite3.connect('db/smart_loan_manager.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id,
                bank_name,
                statement_cutoff_day,
                payment_due_day
            FROM credit_cards
            WHERE id = ?
        """, (card_id,))
        
        card = cursor.fetchone()
        conn.close()
        
        if not card:
            return jsonify({
                'success': False,
                'error': '信用卡不存在'
            }), 404
        
        if not card['statement_cutoff_day'] or not card['payment_due_day']:
            return jsonify({
                'success': False,
                'error': '此卡未设置账单日/到期日'
            }), 400
        
        # 使用排卡优化器生成热力图
        optimizer = CardOptimizer()
        heatmap = optimizer.suggest_optimal_window(
            {
                'id': card['id'],
                'bank_name': card['bank_name'],
                'cutoff_day': card['statement_cutoff_day'],
                'due_day': card['payment_due_day']
            },
            month
        )
        
        # 转换日期为字符串
        calendar_data = {}
        for dt, float_days in heatmap['calendar_heatmap'].items():
            calendar_data[dt.isoformat()] = float_days
        
        heatmap['best_window']['start'] = heatmap['best_window']['start'].isoformat()
        heatmap['best_window']['end'] = heatmap['best_window']['end'].isoformat()
        heatmap['worst_window']['start'] = heatmap['worst_window']['start'].isoformat()
        
        return jsonify({
            'success': True,
            'heatmap': {
                'card_id': heatmap['card_id'],
                'bank_name': heatmap['bank_name'],
                'month': month,
                'best_window': heatmap['best_window'],
                'worst_window': heatmap['worst_window'],
                'calendar_data': calendar_data
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@card_optimizer_bp.route('/payment-priority', methods=['POST'])
@require_admin_or_accountant
def payment_priority():
    """
    计算还款优先级
    
    Request Body:
    {
        "customer_id": int,
        "available_funds": float
    }
    
    Response:
    {
        "success": bool,
        "payment_plans": [...],
        "total_minimum": float,
        "total_recommended": float,
        "funding_gap": float,
        "warnings": [...]
    }
    """
    try:
        data = request.get_json()
        customer_id = data.get('customer_id')
        available_funds = float(data.get('available_funds', 0))
        
        if not customer_id:
            return jsonify({
                'success': False,
                'error': '缺少customer_id'
            }), 400
        
        # 获取客户的所有信用卡及其到期信息
        conn = sqlite3.connect('db/smart_loan_manager.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取每张卡的下一个到期日
        cursor.execute("""
            SELECT 
                cc.id,
                cc.bank_name,
                cc.current_balance,
                cc.payment_due_day,
                cc.min_payment_rate,
                cc.interest_rate
            FROM credit_cards cc
            WHERE cc.customer_id = ?
            AND cc.current_balance > 0
        """, (customer_id,))
        
        cards_raw = cursor.fetchall()
        conn.close()
        
        if not cards_raw:
            return jsonify({
                'success': False,
                'error': '此客户没有需要还款的信用卡'
            }), 404
        
        # 转换为字典并计算下一个到期日
        cards = []
        today = date.today()
        
        for card in cards_raw:
            # 简单计算：本月或下月的到期日
            due_day = card['payment_due_day']
            if due_day:
                if today.day <= due_day:
                    # 本月到期
                    next_due = date(today.year, today.month, min(due_day, 28))
                else:
                    # 下月到期
                    next_month = today.month + 1 if today.month < 12 else 1
                    next_year = today.year if today.month < 12 else today.year + 1
                    next_due = date(next_year, next_month, min(due_day, 28))
            else:
                next_due = today + timedelta(days=30)  # 默认30天后
            
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


@card_optimizer_bp.route('/confirm-plan', methods=['POST'])
@require_admin_or_accountant
def confirm_plan():
    """
    确认排卡方案并记录风险告知
    
    Request Body:
    {
        "plan_id": int,
        "customer_id": int,
        "selected_card_id": int,
        "risk_acknowledged": bool,
        "consent_signature": str (optional)
    }
    
    Response:
    {
        "success": bool,
        "message": str
    }
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
        
        # 记录风险确认
        conn = sqlite3.connect('db/smart_loan_manager.db')
        cursor = conn.cursor()
        
        # 获取客户端信息
        ip_address = request.remote_addr
        user_agent = request.user_agent.string
        
        cursor.execute("""
            INSERT INTO risk_consents
            (customer_id, plan_id, risk_type, risk_description, consent_given, 
             consent_timestamp, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, datetime('now'), ?, ?)
        """, (
            customer_id,
            plan_id,
            'card_optimizer_usage',
            f'客户确认使用卡片ID {selected_card_id}',
            1,
            ip_address,
            user_agent
        ))
        
        # 更新计划状态
        cursor.execute("""
            UPDATE card_usage_plans
            SET status = 'confirmed',
                confirmed_at = datetime('now')
            WHERE id = ?
        """, (plan_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '方案确认成功'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 辅助函数 ====================

def _save_plan_to_db(customer_id: int, 
                    purchase_date: date,
                    expected_amount: float,
                    plan: Dict) -> int:
    """保存排卡方案到数据库"""
    conn = sqlite3.connect('db/smart_loan_manager.db')
    cursor = conn.cursor()
    
    try:
        # 插入主方案记录
        cursor.execute("""
            INSERT INTO card_usage_plans
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
        
        # 插入每张卡的推荐记录
        for i, card in enumerate(plan['recommended_cards'], 1):
            cursor.execute("""
                INSERT INTO card_recommendations
                (plan_id, card_id, priority_rank, float_days, risk_level,
                 recommendation_reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                plan_id,
                card['card_id'],
                i,
                card['float_days'],
                card.get('risk_level', 'low'),
                card.get('recommendation', '')
            ))
        
        conn.commit()
        return plan_id
    
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ==================== Blueprint注册辅助 ====================

def register_card_optimizer_routes(app):
    """注册Blueprint到Flask App"""
    app.register_blueprint(card_optimizer_bp)
    print("✅ Card Optimizer API Routes registered")
