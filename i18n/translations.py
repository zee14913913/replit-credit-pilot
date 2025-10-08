"""
Internationalization (i18n) System
Multi-language support for English and Chinese
"""

TRANSLATIONS = {
    'en': {
        # Navigation
        'nav_dashboard': 'Dashboard',
        'nav_upload': 'Upload',
        'nav_reminders': 'Reminders',
        'nav_news': 'News',
        'nav_advisory': 'Financial Advisory',
        
        # Common
        'company_name': 'INFINITE GZ SDN BHD',
        'system_name': 'Smart Credit & Loan Manager',
        'language': 'Language',
        
        # Dashboard
        'dashboard_title': 'Customer Dashboard',
        'dashboard_subtitle': 'Manage your credit cards, analyze spending, and evaluate loan opportunities.',
        'monthly_income': 'Monthly Income',
        'total_spending': 'Total Spending',
        'credit_cards': 'Credit Cards',
        'credit_limit': 'Credit Limit',
        'due_date': 'Due Date',
        'day': 'Day',
        
        # Quick Actions
        'quick_actions': 'Quick Actions',
        'search_filter': 'Search & Filter',
        'budget_manager': 'Budget Manager',
        'batch_upload': 'Batch Upload',
        'export_data': 'Export Data',
        'financial_advisory_service': 'Financial Advisory Service',
        'advisory_subtitle': 'Card Recommendations · Loan Optimization · Success-based Fee (50% profit sharing)',
        
        # Financial Advisory
        'advisory_title': 'Financial Optimization Advisory',
        'advisory_tagline': 'Tailored credit card recommendations and financial optimization solutions',
        'success_fee_policy': 'Our Commitment: Success-Based Fee Policy',
        'no_benefit_no_fee': 'NO RESULTS, NO FEE!',
        'no_benefit_text': 'If our optimization does not generate any savings or benefits for you, we will NOT charge any fees whatsoever.',
        'profit_sharing': '50% PROFIT SHARING:',
        'profit_sharing_text': 'When we successfully save you money or earn you additional benefits, we charge 50% of the total benefit as our service fee.',
        
        # Card Recommendations
        'card_recommendations': 'Smart Credit Card Recommendations',
        'card_reco_subtitle': 'Based on your spending habits, we recommend the following credit cards to help you maximize rewards and benefits:',
        'match_score': 'Match Score',
        'monthly_benefit': 'Monthly Benefit',
        'annual_benefit': 'Annual Net Benefit',
        'recommendation_reason': 'Reason',
        'special_promotions': 'Special Promotions',
        'no_recommendations': 'Your current credit cards are already well-suited to your spending habits. Keep it up!',
        
        # Financial Optimization
        'optimization_suggestions': 'Financial Optimization Suggestions',
        'optimization_subtitle': 'Based on the latest Bank Negara Malaysia (BNM) policies and current bank rates, we provide the following optimization solutions:',
        'debt_consolidation': 'Debt Consolidation',
        'balance_transfer': 'Balance Transfer',
        'refinancing': 'Loan Refinancing',
        'before_vs_after': 'Before vs After Comparison:',
        'item': 'Item',
        'before': 'Before',
        'after': 'After',
        'savings': 'Savings',
        'monthly_payment': 'Monthly Payment',
        'interest_rate': 'Interest Rate',
        'total_cost_3years': 'Total Cost (3 Years)',
        'additional_benefits': 'Additional Benefits',
        'recommended_bank': 'Recommended Bank',
        'recommended_product': 'Recommended Product',
        'benefit_highlight': 'With this solution, you will save RM {monthly} per month, totaling RM {total} over 3 years!',
        'interested': 'I Want to Learn More',
        'no_optimization': 'Your current financial situation is healthy. No optimization needed at this time.',
        
        # Consultation
        'need_consultation': 'Need One-on-One Professional Consultation?',
        'consultation_text': 'Our financial advisory team is ready to provide personalized financial planning advice',
        'consultation_type': 'Consultation Type',
        'select_type': 'Select consultation type...',
        'full_optimization': 'Complete Financial Optimization',
        'card_consultation': 'Credit Card Consultation',
        'loan_consultation': 'Loan Restructuring Consultation',
        'contact_method': 'Contact Method',
        'email_contact': 'Email Contact',
        'phone_contact': 'Phone Contact',
        'whatsapp_contact': 'WhatsApp Contact',
        'your_message': 'Your message or question (optional)',
        'submit_request': 'Submit Consultation Request',
        
        # Buttons
        'view_dashboard': 'View Dashboard',
        'upload_statement': 'Upload Statement',
        'view_analytics': 'View Analytics',
        'generate_report': 'Generate Financial Report',
        
        # Messages
        'consultation_submitted': 'Consultation request submitted! Our financial advisor will contact you soon.',
        'remember_policy': 'Remember: We only charge fees when we create value for you. If there are no benefits, we charge NOTHING!',
        
        # Footer
        'all_rights_reserved': 'All rights reserved.',
        'powered_by': 'Powered by',
    },
    'zh': {
        # Navigation
        'nav_dashboard': '仪表板',
        'nav_upload': '上传',
        'nav_reminders': '提醒',
        'nav_news': '资讯',
        'nav_advisory': '财务咨询',
        
        # Common
        'company_name': 'INFINITE GZ SDN BHD',
        'system_name': '智能信贷与贷款管理系统',
        'language': '语言',
        
        # Dashboard
        'dashboard_title': '客户仪表板',
        'dashboard_subtitle': '管理您的信用卡，分析消费，评估贷款机会。',
        'monthly_income': '月收入',
        'total_spending': '总消费',
        'credit_cards': '信用卡',
        'credit_limit': '信用额度',
        'due_date': '到期日',
        'day': '日',
        
        # Quick Actions
        'quick_actions': '快捷操作',
        'search_filter': '搜索与筛选',
        'budget_manager': '预算管理',
        'batch_upload': '批量上传',
        'export_data': '导出数据',
        'financial_advisory_service': '财务优化咨询服务',
        'advisory_subtitle': '信用卡推荐 · 贷款优化 · 成功收费（50%分成）',
        
        # Financial Advisory
        'advisory_title': '财务优化咨询服务',
        'advisory_tagline': '为您量身定制的信用卡推荐和财务优化方案',
        'success_fee_policy': '我们的承诺：成功收费政策',
        'no_benefit_no_fee': '无收益，不收费！',
        'no_benefit_text': '如果我们的优化方案未能为您节省或赚取任何收益，我们将不收取任何一分一毫的费用。',
        'profit_sharing': '50%收益分成：',
        'profit_sharing_text': '只有当我们成功为您节省费用或创造收益时，我们才收取总收益的50%作为服务费用。',
        
        # Card Recommendations
        'card_recommendations': '智能信用卡推荐',
        'card_reco_subtitle': '根据您的消费习惯，我们为您推荐以下信用卡，助您获取更多积分和福利：',
        'match_score': '匹配度',
        'monthly_benefit': '每月收益',
        'annual_benefit': '年度净收益',
        'recommendation_reason': '推荐理由',
        'special_promotions': '特别优惠',
        'no_recommendations': '您目前使用的信用卡已经很适合您的消费习惯。继续保持！',
        
        # Financial Optimization
        'optimization_suggestions': '财务优化建议',
        'optimization_subtitle': '基于马来西亚国家银行(BNM)最新政策和各大银行最新利率，我们为您提供以下优化方案：',
        'debt_consolidation': '债务整合',
        'balance_transfer': '余额转移',
        'refinancing': '贷款再融资',
        'before_vs_after': '优化前 vs 优化后对比：',
        'item': '项目',
        'before': '优化前',
        'after': '优化后',
        'savings': '节省',
        'monthly_payment': '月供',
        'interest_rate': '利率',
        'total_cost_3years': '总成本（3年）',
        'additional_benefits': '额外好处',
        'recommended_bank': '推荐银行',
        'recommended_product': '推荐产品',
        'benefit_highlight': '采用此方案，您将每月节省 RM {monthly}，3年总共节省 RM {total}！',
        'interested': '我想了解详情',
        'no_optimization': '您目前的财务状况良好，暂无需优化。继续保持良好的财务管理！',
        
        # Consultation
        'need_consultation': '需要一对一专业咨询？',
        'consultation_text': '我们的财务顾问团队随时为您提供个性化的财务规划建议',
        'consultation_type': '咨询类型',
        'select_type': '选择咨询类型...',
        'full_optimization': '完整财务优化方案',
        'card_consultation': '信用卡推荐咨询',
        'loan_consultation': '贷款重组咨询',
        'contact_method': '联系方式',
        'email_contact': 'Email联系',
        'phone_contact': '电话联系',
        'whatsapp_contact': 'WhatsApp联系',
        'your_message': '请简述您的需求或问题（可选）',
        'submit_request': '提交咨询请求',
        
        # Buttons
        'view_dashboard': '查看仪表板',
        'upload_statement': '上传账单',
        'view_analytics': '查看分析',
        'generate_report': '生成财务报告',
        
        # Messages
        'consultation_submitted': '咨询请求已提交！我们的财务顾问将尽快与您联系。',
        'remember_policy': '记住：只有当我们为您节省或赚取收益后，我们才收取费用（50%收益分成）。如果没有为您创造任何价值，我们不收取任何费用！',
        
        # Footer
        'all_rights_reserved': '版权所有。',
        'powered_by': '技术支持',
    }
}

def get_translation(key, lang='en'):
    """Get translation for a key in specified language"""
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)

def translate(key, lang='en', **kwargs):
    """Get translation with format support"""
    text = get_translation(key, lang)
    if kwargs:
        return text.format(**kwargs)
    return text
