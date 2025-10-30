"""
Financial Optimization Advisory Service
Analyzes customer finances and provides optimization suggestions based on latest BNM policies and bank rates
"""

from typing import List, Dict
from db.database import get_db
from datetime import datetime, date
from advisory.bnm_api import fetch_bnm_rates
import json

class FinancialOptimizer:
    """财务优化建议服务"""
    
    def generate_optimization_suggestions(self, customer_id: int) -> List[Dict]:
        """生成财务优化建议"""
        
        suggestions = []
        
        # Get customer financial data
        customer = self._get_customer_info(customer_id)
        current_repayments = self._calculate_current_repayments(customer_id)
        current_dsr = current_repayments / customer['monthly_income'] if customer['monthly_income'] > 0 else 0
        
        # Get latest BNM rates
        bnm_rates = fetch_bnm_rates()
        current_opr = bnm_rates.get('opr', 3.0)
        current_sbr = bnm_rates.get('sbr', 5.5)
        
        # 1. Debt Consolidation Opportunity
        if current_dsr > 0.35:  # DSR > 35%
            consolidation_suggestion = self._analyze_debt_consolidation(
                customer, current_repayments, current_dsr, current_sbr
            )
            if consolidation_suggestion:
                suggestions.append(consolidation_suggestion)
        
        # 2. Credit Card Balance Transfer
        high_interest_cards = self._find_high_interest_cards(customer_id)
        if high_interest_cards:
            balance_transfer_suggestion = self._analyze_balance_transfer(
                customer, high_interest_cards, current_sbr
            )
            if balance_transfer_suggestion:
                suggestions.append(balance_transfer_suggestion)
        
        # 3. Personal Loan Refinancing
        refinancing_suggestion = self._analyze_loan_refinancing(
            customer, current_repayments, current_sbr
        )
        if refinancing_suggestion:
            suggestions.append(refinancing_suggestion)
        
        # Save suggestions to database
        self._save_suggestions(customer_id, suggestions, bnm_rates)
        
        return suggestions
    
    def _get_customer_info(self, customer_id: int) -> Dict:
        """获取客户信息"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
            row = cursor.fetchone()
            return dict(row) if row else {}
    
    def _calculate_current_repayments(self, customer_id: int) -> float:
        """计算当前月供总额"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT SUM(credit_limit * 0.05) as total_repayment
                FROM credit_cards
                WHERE customer_id = ?
            ''', (customer_id,))
            row = cursor.fetchone()
            return row['total_repayment'] if row and row['total_repayment'] else 0
    
    def _find_high_interest_cards(self, customer_id: int) -> List[Dict]:
        """查找高利息信用卡"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT cc.*, SUM(t.amount) as outstanding_balance
                FROM credit_cards cc
                LEFT JOIN statements s ON cc.id = s.card_id
                LEFT JOIN transactions t ON s.id = t.statement_id
                WHERE cc.customer_id = ? AND s.is_confirmed = 1
                GROUP BY cc.id
                HAVING outstanding_balance > 1000
            ''', (customer_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def _analyze_debt_consolidation(self, customer: Dict, current_repayments: float, 
                                    current_dsr: float, sbr: float) -> Dict:
        """分析债务整合机会"""
        
        # Current situation
        # Assume average credit card interest rate 18% (industry standard in Malaysia)
        current_interest_rate = 18.0
        current_monthly_payment = current_repayments
        current_total_debt = current_monthly_payment * 12  # Simplified estimation
        
        # Optimized situation with personal loan consolidation
        # Personal loan rate typically SBR + 3-5%
        optimized_interest_rate = sbr + 4.0  # More competitive rate
        
        # Calculate new monthly payment
        # Using simple interest for demonstration (real calculation would use amortization)
        monthly_interest_current = (current_total_debt * current_interest_rate / 100) / 12
        monthly_interest_optimized = (current_total_debt * optimized_interest_rate / 100) / 12
        
        optimized_monthly_payment = current_monthly_payment - (monthly_interest_current - monthly_interest_optimized)
        optimized_dsr = optimized_monthly_payment / customer['monthly_income']
        
        # Calculate savings
        monthly_savings = current_monthly_payment - optimized_monthly_payment
        total_savings_3years = monthly_savings * 36  # 3 year loan term
        
        if monthly_savings > 100:  # Only suggest if significant savings
            return {
                'optimization_type': 'debt_consolidation',
                'current_monthly_payment': current_monthly_payment,
                'current_interest_rate': current_interest_rate,
                'current_total_cost': current_monthly_payment * 36,
                'optimized_monthly_payment': optimized_monthly_payment,
                'optimized_interest_rate': optimized_interest_rate,
                'optimized_total_cost': optimized_monthly_payment * 36,
                'monthly_savings': monthly_savings,
                'total_savings': total_savings_3years,
                'additional_benefits': f"Reduce DSR from {current_dsr*100:.1f}% to {optimized_dsr*100:.1f}%, Improve loan eligibility",
                'recommended_bank': 'Alliance Bank / CIMB',
                'recommended_product': 'Personal Loan Debt Consolidation Plan',
                'implementation_steps': '1. Apply for consolidation loan\n2. Use proceeds to pay off credit cards\n3. Close unused credit cards\n4. Maintain single monthly payment'
            }
        return None
    
    def _analyze_balance_transfer(self, customer: Dict, high_interest_cards: List[Dict], 
                                   sbr: float) -> Dict:
        """分析余额转移机会"""
        
        total_balance = sum(card.get('outstanding_balance', 0) for card in high_interest_cards)
        
        if total_balance > 3000:  # Minimum balance to be worthwhile
            # Current: 18% credit card interest
            current_interest_rate = 18.0
            current_monthly_interest = (total_balance * current_interest_rate / 100) / 12
            
            # Balance transfer: 0% for 6-12 months, then ~6%
            # One-time fee: 3-5%
            transfer_fee = total_balance * 0.03  # 3% transfer fee
            optimized_interest_rate = 0  # Promotional rate
            
            # Savings calculation
            monthly_savings = current_monthly_interest
            total_savings_12months = (monthly_savings * 12) - transfer_fee
            
            if total_savings_12months > 200:
                return {
                    'optimization_type': 'balance_transfer',
                    'current_monthly_payment': current_monthly_interest + (total_balance * 0.05),
                    'current_interest_rate': current_interest_rate,
                    'current_total_cost': (current_monthly_interest * 12),
                    'optimized_monthly_payment': total_balance / 12,  # 0% interest, pay principal only
                    'optimized_interest_rate': 0,
                    'optimized_total_cost': transfer_fee,
                    'monthly_savings': monthly_savings,
                    'total_savings': total_savings_12months,
                    'additional_benefits': f"0% interest for 12 months, Save RM{total_savings_12months:.2f} in interest",
                    'recommended_bank': 'Maybank / CIMB / Public Bank',
                    'recommended_product': 'Balance Transfer Program',
                    'implementation_steps': f'1. Apply for balance transfer (RM{total_balance:.2f})\n2. One-time fee: RM{transfer_fee:.2f} (3%)\n3. Enjoy 0% interest for 12 months\n4. Pay RM{total_balance/12:.2f}/month to clear in 12 months'
                }
        return None
    
    def _analyze_loan_refinancing(self, customer: Dict, current_repayments: float, 
                                   sbr: float) -> Dict:
        """分析贷款再融资机会"""
        
        # Check if customer has significant monthly obligations
        if current_repayments > customer['monthly_income'] * 0.3:
            # Current loan rate estimation
            current_rate = sbr + 2.5
            # Optimized rate (shop around for better rates)
            optimized_rate = sbr + 1.5
            
            # Estimate savings
            rate_difference = current_rate - optimized_rate
            principal_estimate = current_repayments * 12 * 5  # 5 year loan
            
            monthly_savings = (principal_estimate * rate_difference / 100) / 12
            total_savings = monthly_savings * 60  # 5 years
            
            if monthly_savings > 50:
                return {
                    'optimization_type': 'refinancing',
                    'current_monthly_payment': current_repayments,
                    'current_interest_rate': current_rate,
                    'current_total_cost': current_repayments * 60,
                    'optimized_monthly_payment': current_repayments - monthly_savings,
                    'optimized_interest_rate': optimized_rate,
                    'optimized_total_cost': (current_repayments - monthly_savings) * 60,
                    'monthly_savings': monthly_savings,
                    'total_savings': total_savings,
                    'additional_benefits': f"Lower interest rate by {rate_difference:.1f}%, Reduce total interest paid",
                    'recommended_bank': 'Hong Leong / RHB / AmBank',
                    'recommended_product': 'Personal Loan Refinancing',
                    'implementation_steps': '1. Get refinancing quotes from 3 banks\n2. Compare total costs including fees\n3. Choose best offer\n4. Complete refinancing process'
                }
        return None
    
    def _save_suggestions(self, customer_id: int, suggestions: List[Dict], bnm_rates: Dict):
        """保存优化建议到数据库"""
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            for sug in suggestions:
                cursor.execute('''
                    INSERT INTO financial_optimization_suggestions (
                        customer_id, optimization_type,
                        current_monthly_payment, current_interest_rate, current_total_cost,
                        optimized_monthly_payment, optimized_interest_rate, optimized_total_cost,
                        monthly_savings, total_savings, additional_benefits,
                        recommended_bank, recommended_product, implementation_steps,
                        bnm_policy_reference, bank_rates_reference, data_as_of_date,
                        status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'proposed')
                ''', (
                    customer_id, sug['optimization_type'],
                    sug['current_monthly_payment'], sug['current_interest_rate'], sug['current_total_cost'],
                    sug['optimized_monthly_payment'], sug['optimized_interest_rate'], sug['optimized_total_cost'],
                    sug['monthly_savings'], sug['total_savings'], sug['additional_benefits'],
                    sug['recommended_bank'], sug['recommended_product'], sug['implementation_steps'],
                    f"BNM OPR: {bnm_rates.get('opr', 'N/A')}%", 
                    f"SBR: {bnm_rates.get('sbr', 'N/A')}%",
                    date.today()
                ))
            
            conn.commit()
