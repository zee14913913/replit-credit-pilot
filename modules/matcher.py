"""
贷款产品智能匹配引擎
根据客户资料和DSR自动匹配符合条件的贷款产品
"""

import json
import os

def load_all_products(folder):
    """从指定文件夹加载所有银行产品JSON"""
    products = []
    if not os.path.exists(folder):
        return products
    
    for fn in os.listdir(folder):
        if fn.endswith('.json'):
            with open(os.path.join(folder, fn), 'r', encoding='utf-8') as f:
                data = json.load(f)
                products.extend(data)
    return products

def pass_basic(value, minv):
    """检查是否满足最低值要求"""
    return (minv is None) or (value is None) or (value >= minv)

def pass_max(value, maxv):
    """检查是否不超过最大值"""
    return (maxv is None) or (value is None) or (value <= maxv)

def match_loans(client, products):
    """
    匹配贷款产品
    
    Args:
        client: 客户信息字典
        products: 产品列表
        
    Returns:
        (eligible, ineligible) 符合和不符合的产品列表
    """
    eligible, ineligible = [], []
    
    for p in products:
        reasons = []
        
        # 公民身份检查
        if p.get("citizenship") == "MY" and client.get("citizenship") != "MY":
            reasons.append("仅限马来西亚公民")
        
        # 年龄检查
        if not pass_basic(client.get("age"), p.get("age_min")):
            reasons.append(f"年龄不足（最低{p.get('age_min')}岁）")
        if not pass_max(client.get("age"), p.get("age_max")):
            reasons.append(f"年龄超限（最高{p.get('age_max')}岁）")
        
        # 收入检查
        if not pass_basic(client.get("income"), p.get("income_min")):
            min_income = p.get("income_min", 0)
            reasons.append(f"收入低于门槛（需≥RM{min_income:,.0f}）")
        
        # SME/商业贷款特殊检查
        if p.get("category") in ["sme", "biz"]:
            if not pass_basic(client.get("company_age_months"), p.get("company_age_min_months")):
                reasons.append("企业成立时间不足")
            if p.get("biz_turnover_cap") and client.get("annual_turnover"):
                if client["annual_turnover"] > p["biz_turnover_cap"]:
                    reasons.append("年营收超出该产品线上限")
        
        # Maybank特定产品规则
        if p.get("product_id") == "MBB-HOME-HOUZKEY":
            if client.get("existing_home_financing_count", 0) > 1:
                reasons.append("现有房贷超过1笔，不符合HouzKEY条件")
        
        if p.get("product_id") == "MBB-HOME-2GETHER":
            cond = (client.get("child_age", 0) >= 21 and 
                   client.get("child_age", 0) <= 31 and
                   client.get("child_employed") and 
                   client.get("child_first_home"))
            if not cond:
                reasons.append("不符合Home 2gether子女购房条件")
        
        # DSR检查
        dsr_max = p.get("dsr_max", 70)
        if client.get("dsr") is not None and client["dsr"] > dsr_max:
            reasons.append(f"DSR超限（当前{client['dsr']}% > 限制{dsr_max}%）")
        
        # 分类结果
        if reasons:
            ineligible.append({"product": p, "reasons": reasons})
        else:
            eligible.append({"product": p})
    
    # 排序：优先速度快、额度高的产品
    def score(item):
        p = item["product"]
        speed = p.get("speed_rank", 3)  # 1=最快, 3=普通
        cap = (p.get("amount_max") or 0)
        return (-(100 - speed), cap)
    
    eligible.sort(key=score, reverse=True)
    
    return eligible, ineligible
