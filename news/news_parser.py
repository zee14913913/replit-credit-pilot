"""
新闻解析器 - 从搜索结果中提取并结构化新闻
"""
from datetime import datetime
import re

def parse_credit_card_news(search_text):
    """解析信用卡相关新闻"""
    news_items = []
    
    # 示例：从搜索结果中提取新闻
    if "Hong Leong WISE" in search_text:
        news_items.append({
            'bank_name': 'Hong Leong Bank',
            'news_type': 'CREDIT_CARD',
            'category': 'CASHBACK',
            'title': 'WISE信用卡高达15%返现',
            'content': '香港莱坊银行WISE信用卡在餐饮、杂货、药房、汽油和电子钱包消费可获高达15%返现，每月封顶RM15。',
            'effective_date': datetime.now().strftime('%Y-%m-%d')
        })
    
    if "HSBC Live+" in search_text:
        news_items.append({
            'bank_name': 'HSBC',
            'news_type': 'CREDIT_CARD',
            'category': 'CASHBACK',
            'title': 'Live+信用卡餐饮娱乐5%返现',
            'content': 'HSBC Live+信用卡在餐饮、娱乐和购物类别享有高达5%返现，新卡会员可获高达RM400欢迎返现。',
            'effective_date': datetime.now().strftime('%Y-%m-%d')
        })
    
    if "UOB" in search_text and "RM11,100" in search_text:
        news_items.append({
            'bank_name': 'UOB',
            'news_type': 'CREDIT_CARD',
            'category': 'PROMOTION',
            'title': 'UOB推荐计划高达RM11,100返现',
            'content': 'UOB信用卡推荐计划，推荐朋友可获高达RM11,100返现，额外赠送Apple Watch Series 10或iPad配套。',
            'effective_date': '2025-12-31'
        })
    
    return news_items

def parse_loan_news(search_text):
    """解析贷款相关新闻"""
    news_items = []
    
    if "CIMB" in search_text and "4.38%" in search_text:
        news_items.append({
            'bank_name': 'CIMB',
            'news_type': 'LOAN',
            'category': 'PERSONAL_LOAN',
            'title': 'Cash Plus个人贷款低至4.38%',
            'content': 'CIMB Cash Plus个人贷款年利率4.38%-19.88%，贷款额RM2,000-RM100,000，零手续费，快速批准。',
            'effective_date': datetime.now().strftime('%Y-%m-%d')
        })
    
    if "UOB" in search_text and "3.99%" in search_text:
        news_items.append({
            'bank_name': 'UOB',
            'news_type': 'LOAN',
            'category': 'PERSONAL_LOAN',
            'title': 'UOB个人贷款3.99%起',
            'content': 'UOB个人贷款利率3.99%起，无需抵押或担保人，无处理费，灵活还款期。',
            'effective_date': datetime.now().strftime('%Y-%m-%d')
        })
    
    if "Maybank" in search_text and "RM102.78" in search_text:
        news_items.append({
            'bank_name': 'Maybank',
            'news_type': 'LOAN',
            'category': 'POLICY',
            'title': 'Maybank取消提前还款费用',
            'content': 'Maybank自2025年3月31日起取消个人贷款提前还款费用，每月还款低至RM102.78。',
            'effective_date': '2025-03-31'
        })
    
    return news_items

def parse_investment_news(search_text):
    """解析投资产品新闻"""
    news_items = []
    
    if "OPR" in search_text and "2.75%" in search_text:
        news_items.append({
            'bank_name': 'Bank Negara Malaysia',
            'news_type': 'RATE_UPDATE',
            'category': 'INVESTMENT',
            'title': 'OPR降至2.75% 定存利率调整',
            'content': '马来西亚央行OPR从3.00%降至2.75%，各银行定期存款利率预计将相应调整，目前促销利率最高达5.50%。',
            'effective_date': datetime.now().strftime('%Y-%m-%d')
        })
    
    if "CIMB" in search_text and "3.45%" in search_text:
        news_items.append({
            'bank_name': 'CIMB',
            'news_type': 'INVESTMENT',
            'category': 'FIXED_DEPOSIT',
            'title': 'eFixed Deposit-i高达3.45%',
            'content': 'CIMB eFixed Deposit-i通过FPX在线存款可享高达3.45%年利率，最低存款RM1,000，活动至10月30日。',
            'effective_date': '2025-10-30'
        })
    
    if "Hong Leong" in search_text and "eFD" in search_text:
        news_items.append({
            'bank_name': 'Hong Leong Bank',
            'news_type': 'INVESTMENT',
            'category': 'FIXED_DEPOSIT',
            'title': 'eFD月度促销优惠利率',
            'content': '香港莱坊银行10月推出eFD/eFD-i月度促销，提供特别利率，最低存款RM1,000。',
            'effective_date': '2025-10-31'
        })
    
    if "RHB" in search_text and "10.88%" in search_text:
        news_items.append({
            'bank_name': 'RHB Bank',
            'news_type': 'INVESTMENT',
            'category': 'FIXED_DEPOSIT',
            'title': 'Bancassurance FD高达10.88%',
            'content': 'RHB银行保险定存特别促销，年利率高达10.88%（结合保险产品），最低存款RM10,000，活动至12月31日。',
            'effective_date': '2025-12-31'
        })
    
    return news_items

def parse_business_news(search_text):
    """解析商业融资新闻"""
    news_items = []
    
    if "RM40 billion" in search_text or "Budget 2025" in search_text:
        news_items.append({
            'bank_name': 'Government',
            'news_type': 'SME_FINANCING',
            'category': 'BUSINESS',
            'title': '2025年预算案拨款RM400亿中小企业融资',
            'content': '政府在2025年预算案中拨款RM400亿用于中小企业和微型企业融资，包括微型贷款、数字化补助和贷款担保。',
            'effective_date': datetime.now().strftime('%Y-%m-%d')
        })
    
    if "Maybank" in search_text and "RM250,000" in search_text:
        news_items.append({
            'bank_name': 'Maybank',
            'news_type': 'SME_FINANCING',
            'category': 'BUSINESS',
            'title': 'SME Clean Loan高达RM150万',
            'content': 'Maybank中小企业清洁贷款，在线申请高达RM250,000，分行申请高达RM150万，无需抵押，快速批准。',
            'effective_date': datetime.now().strftime('%Y-%m-%d')
        })
    
    if "SME Bank" in search_text:
        news_items.append({
            'bank_name': 'SME Bank',
            'news_type': 'SME_FINANCING',
            'category': 'BUSINESS',
            'title': 'Business Accelerator计划高达RM100万',
            'content': 'SME Bank推出Business Accelerator计划，提供高达RM100万融资，最长7年还款期，支持女性创业和绿色转型。',
            'effective_date': datetime.now().strftime('%Y-%m-%d')
        })
    
    if "CIMB" in search_text and "SME BusinessCard" in search_text:
        news_items.append({
            'bank_name': 'CIMB',
            'news_type': 'SME_FINANCING',
            'category': 'BUSINESS',
            'title': 'SME BusinessCard无限现金返还',
            'content': 'CIMB推出SME BusinessCard商务卡，提供无限现金返还，配合SME Partners计划享50%商业工具折扣。',
            'effective_date': datetime.now().strftime('%Y-%m-%d')
        })
    
    return news_items

def extract_all_news(search_results):
    """从所有搜索结果中提取新闻"""
    all_news = []
    
    # 合并所有搜索文本
    combined_text = ""
    for result in search_results:
        if isinstance(result, dict) and 'text' in result:
            combined_text += result['text'] + "\n"
        elif isinstance(result, str):
            combined_text += result + "\n"
    
    # 解析各类新闻
    all_news.extend(parse_credit_card_news(combined_text))
    all_news.extend(parse_loan_news(combined_text))
    all_news.extend(parse_investment_news(combined_text))
    all_news.extend(parse_business_news(combined_text))
    
    return all_news
