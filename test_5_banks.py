#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 爬取5家重点银行验证系统
"""

import json
import pandas as pd
from datetime import datetime
from accounting_app.services.malaysia_bank_comprehensive_scraper import scraper

def main():
    print("\n" + "="*80)
    print("🧪 测试严格模式爬虫 - 5家重点银行")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    # 加载银行列表
    with open('accounting_app/data/malaysia_financial_institutions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 选择5家重点银行
    test_banks = [
        data['commercial_banks'][10],  # Maybank
        data['commercial_banks'][5],   # CIMB
        data['commercial_banks'][12],  # Public Bank
        data['commercial_banks'][1],   # Alliance Bank
        data['commercial_banks'][2],   # AmBank
    ]
    
    print("📋 测试银行列表：")
    for i, bank in enumerate(test_banks, 1):
        print(f"  {i}. {bank['name']}")
    print("\n" + "="*80 + "\n")
    
    all_products = []
    
    for idx, bank in enumerate(test_banks):
        company_name = bank.get('name', 'Unknown')
        company_url = bank.get('website', '')
        
        print(f"\n{'='*80}")
        print(f"进度: {idx + 1}/5 银行")
        print(f"{'='*80}\n")
        
        try:
            products = scraper.scrape_company(company_name, company_url)
            all_products.extend(products)
            
            if products:
                company_file = f"output/TEST_{idx:02d}_{company_name.replace(' ', '_')}.csv"
                pd.DataFrame(products).to_csv(company_file, index=False, encoding='utf-8')
                print(f"💾 已保存: {company_file}")
            
            scraper.save_progress()
            
        except Exception as e:
            print(f"❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 保存测试结果
    if all_products:
        test_file = 'TEST_5banks_results.csv'
        df = pd.DataFrame(all_products)
        df.to_csv(test_file, index=False, encoding='utf-8')
        
        print("\n" + "="*80)
        print("📊 测试结果摘要")
        print("="*80)
        print(f"总产品数: {len(all_products)}")
        print(f"已保存: {test_file}")
        
        # 简单质量检查
        no_data_count = (df == '[NO DATA FOUND]').sum().sum()
        total_cells = len(df) * 12
        no_data_rate = (no_data_count / total_cells) * 100
        
        print(f"\n数据质量：")
        print(f"  [NO DATA FOUND] 比率: {no_data_rate:.1f}%")
        print(f"  {'✅ 优秀' if no_data_rate < 20 else '⚠️ 需优化'}")
        
        print(f"\n按银行统计：")
        for company, count in df['company'].value_counts().items():
            print(f"  {company}: {count} 产品")
        
        print(f"\n样本数据（前3个产品）：")
        for idx, row in df.head(3).iterrows():
            print(f"\n  产品 {idx+1}:")
            print(f"    公司: {row['company']}")
            print(f"    类型: {row['loan_type']}")
            print(f"    有数据字段: {sum(1 for v in row.values if v != '[NO DATA FOUND]')}/12")
            print(f"    URL: {row['source_url'][:60]}...")
    
    print("\n" + "="*80)
    print("✅ 测试完成")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
