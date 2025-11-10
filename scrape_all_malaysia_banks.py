#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
马来西亚所有银行产品爬取主脚本
严格模式：不许幻想数据、必须访问详情页、12字段完整提取
"""

import json
import pandas as pd
from datetime import datetime
from accounting_app.services.malaysia_bank_comprehensive_scraper import scraper

def load_financial_institutions():
    """加载马来西亚金融机构列表"""
    with open('accounting_app/data/malaysia_financial_institutions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_banks = []
    all_banks.extend(data.get('commercial_banks', []))
    all_banks.extend(data.get('islamic_banks', []))
    all_banks.extend(data.get('development_banks', []))
    all_banks.extend(data.get('digital_banks', []))
    all_banks.extend(data.get('p2p_platforms', []))
    all_banks.extend(data.get('non_bank_credit', []))
    
    return all_banks

def generate_quality_report(all_products):
    """生成质量报告"""
    print(f"\n{'='*80}")
    print("📊 DATA QUALITY REPORT")
    print(f"{'='*80}")
    
    df = pd.DataFrame(all_products)
    total = len(df)
    
    if total == 0:
        print("❌ NO PRODUCTS EXTRACTED")
        return
    
    no_data_count = (df == '[NO DATA FOUND]').sum().sum()
    total_cells = total * 12
    no_data_rate = (no_data_count / total_cells) * 100
    
    print(f"Total products extracted: {total}")
    print(f"Total data cells: {total_cells}")
    print(f"[NO DATA FOUND] cells: {no_data_count}")
    print(f"[NO DATA FOUND] rate: {no_data_rate:.1f}%")
    
    if total < 100:
        print(f"\n⚠️  WARNING: Only {total} products found (expected >100)")
    
    if no_data_rate > 20:
        print(f"⚠️  WARNING: [NO DATA FOUND] rate {no_data_rate:.1f}% exceeds 20%")
    
    print(f"\n{'='*80}")
    print("📈 PRODUCTS BY COMPANY")
    print(f"{'='*80}")
    company_counts = df['company'].value_counts()
    for company, count in company_counts.head(10).items():
        print(f"  {company}: {count} products")
    
    print(f"\n{'='*80}")
    print("📈 PRODUCTS BY TYPE")
    print(f"{'='*80}")
    type_counts = df['loan_type'].value_counts()
    for loan_type, count in type_counts.head(10).items():
        print(f"  {loan_type}: {count} products")
    
    print(f"\n{'='*80}")
    print("🎯 FIELD COMPLETION RATES")
    print(f"{'='*80}")
    for field in df.columns:
        if field in ['company', 'loan_type', 'source_url']:
            continue
        completion = ((df[field] != '[NO DATA FOUND]').sum() / total) * 100
        status = "✅" if completion > 50 else "⚠️"
        print(f"  {status} {field}: {completion:.1f}%")
    
    print(f"\n{'='*80}")
    print("📋 RANDOM SAMPLES FOR MANUAL VERIFICATION")
    print(f"{'='*80}")
    samples = df.sample(min(5, total))
    for idx, row in samples.iterrows():
        print(f"\n  Sample {idx+1}:")
        print(f"    Company: {row['company']}")
        print(f"    Product: {row['loan_type']}")
        print(f"    URL: {row['source_url']}")
        print(f"    Fields with data: {sum(1 for v in row.values if v != '[NO DATA FOUND]')}/12")
    
    print(f"\n{'='*80}\n")

def main():
    """主函数"""
    print("\n" + "="*80)
    print("🚀 马来西亚银行产品完整爬取系统")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    banks = load_financial_institutions()
    print(f"✅ 加载了 {len(banks)} 家金融机构\n")
    
    all_products = []
    start_idx = scraper.progress.get('current_company_index', 0)
    
    print(f"📍 从第 {start_idx + 1} 家开始...\n")
    
    for idx in range(start_idx, len(banks)):
        bank = banks[idx]
        company_name = bank.get('name', 'Unknown')
        company_url = bank.get('website', '')
        
        if not company_url:
            print(f"⏭️  跳过 {company_name} - 没有网址")
            continue
        
        scraper.progress['current_company_index'] = idx
        
        try:
            products = scraper.scrape_company(company_name, company_url)
            all_products.extend(products)
            
            scraper.progress['completed_companies'].append(company_name)
            
            company_file = f"output/company_{idx:02d}_{company_name.replace(' ', '_')}.csv"
            if products:
                pd.DataFrame(products).to_csv(company_file, index=False, encoding='utf-8')
                print(f"💾 Saved: {company_file}")
            
        except Exception as e:
            print(f"❌ Error processing {company_name}: {str(e)}")
            scraper.progress['failed_companies'].append({
                'company': company_name,
                'error': str(e),
                'time': datetime.now().isoformat()
            })
        
        scraper.save_progress()
        
        progress_pct = ((idx + 1) / len(banks)) * 100
        print(f"\n📊 Overall Progress: {idx + 1}/{len(banks)} ({progress_pct:.1f}%)")
        print(f"📊 Total Products So Far: {len(all_products)}\n")
    
    final_file = 'malaysia_banks_all_products_COMPLETE.csv'
    if all_products:
        df = pd.DataFrame(all_products)
        df.to_csv(final_file, index=False, encoding='utf-8')
        print(f"\n✅ 最终文件已保存: {final_file}")
    
    generate_quality_report(all_products)
    
    print("\n" + "="*80)
    print("🎉 爬取完成")
    print("="*80)
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总产品数: {len(all_products)}")
    print(f"成功: {len(scraper.progress['completed_companies'])} 家")
    print(f"失败: {len(scraper.progress['failed_companies'])} 家")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
