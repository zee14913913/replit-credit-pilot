#!/usr/bin/env python3
"""
Google Document AI 批量解析脚本
用途：批量解析42个信用卡账单PDF，自动分类归档
"""
import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from services.google_document_ai_service import GoogleDocumentAIService
from services.ai_pdf_parser import AIBankStatementParser

# 配置目录
UPLOAD_DIR = "static/uploads/customers/Be_rich_CJY/credit_cards"
RESULT_DIR = "results/google_ai_parsed"
LOG_DIR = "logs"

# 创建必要目录
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


def log_message(message: str, error: bool = False):
    """记录日志"""
    log_file = os.path.join(LOG_DIR, "error.log" if error else "operation.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")
    
    print(message)


def main():
    """主函数：批量处理所有PDF"""
    
    print("="*80)
    print("🚀 Google Document AI 批量解析 - 42个信用卡账单")
    print("="*80)
    
    # 初始化服务
    try:
        google_ai = GoogleDocumentAIService()
        ai_parser = AIBankStatementParser()
    except Exception as e:
        log_message(f"❌ 服务初始化失败: {e}", error=True)
        sys.exit(1)
    
    # 获取所有PDF文件
    upload_path = Path(UPLOAD_DIR)
    
    if not upload_path.exists():
        log_message(f"❌ 目录不存在: {UPLOAD_DIR}", error=True)
        sys.exit(1)
    
    pdf_files = list(upload_path.glob("**/*.pdf"))
    
    log_message(f"\n📁 找到 {len(pdf_files)} 个PDF文件")
    log_message(f"📂 输出目录: {RESULT_DIR}")
    
    if len(pdf_files) == 0:
        log_message("⚠️  未找到PDF文件！", error=True)
        sys.exit(1)
    
    # 统计数据
    total_files = len(pdf_files)
    success_count = 0
    failed_count = 0
    all_results = []
    
    # 批量处理
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n{'='*80}")
        print(f"【{i}/{total_files}】{pdf_file.name}")
        print('='*80)
        
        try:
            # 1. 使用Google Document AI解析
            log_message(f"⏳ 解析中...")
            parsed_json = google_ai.parse_pdf(str(pdf_file))
            
            # 2. 提取字段
            fields = google_ai.extract_bank_statement_fields(parsed_json)
            
            # 3. 使用AI识别银行
            text = ai_parser.extract_text_from_pdf(str(pdf_file))
            bank_code = ai_parser.detect_bank(text)
            
            if bank_code:
                fields['bank_name'] = bank_code
                log_message(f"🏦 识别银行: {bank_code}")
            
            # 4. 保存结果
            result = {
                'filename': pdf_file.name,
                'filepath': str(pdf_file),
                'bank': fields.get('bank_name', 'UNKNOWN'),
                'card_number': fields.get('card_number'),
                'statement_date': fields.get('statement_date'),
                'previous_balance': fields.get('previous_balance', 0),
                'current_balance': fields.get('current_balance', 0),
                'transaction_count': len(fields.get('transactions', [])),
                'success': True,
                'parsed_at': datetime.now().isoformat()
            }
            
            all_results.append(result)
            
            # 保存详细JSON
            json_path = Path(RESULT_DIR) / f"{pdf_file.stem}_parsed.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': result,
                    'fields': fields,
                    'raw_response': parsed_json
                }, f, ensure_ascii=False, indent=2)
            
            log_message(f"✅ 解析成功！")
            log_message(f"   卡号: {fields.get('card_number', 'N/A')}")
            log_message(f"   日期: {fields.get('statement_date', 'N/A')}")
            log_message(f"   上期结余: RM {fields.get('previous_balance', 0):.2f}")
            log_message(f"   本期结余: RM {fields.get('current_balance', 0):.2f}")
            log_message(f"   交易数量: {len(fields.get('transactions', []))}")
            log_message(f"💾 保存到: {json_path.name}")
            
            success_count += 1
        
        except Exception as e:
            log_message(f"❌ 解析失败: {e}", error=True)
            
            all_results.append({
                'filename': pdf_file.name,
                'filepath': str(pdf_file),
                'success': False,
                'error': str(e),
                'parsed_at': datetime.now().isoformat()
            })
            
            failed_count += 1
    
    # 生成汇总报告
    print(f"\n{'='*80}")
    print("📊 处理完成 - 汇总报告")
    print('='*80)
    
    log_message(f"\n✅ 成功: {success_count}/{total_files}")
    log_message(f"❌ 失败: {failed_count}/{total_files}")
    log_message(f"📈 成功率: {(success_count/total_files*100):.1f}%")
    
    # 保存汇总Excel
    df = pd.DataFrame(all_results)
    excel_path = Path(RESULT_DIR) / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(excel_path, index=False)
    
    log_message(f"\n📊 汇总报告已保存: {excel_path}")
    
    # 保存汇总CSV
    csv_path = Path(RESULT_DIR) / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    log_message(f"📊 CSV报告已保存: {csv_path}")
    
    print(f"\n{'='*80}")
    print("🎉 全部处理完成！")
    print(f"📁 所有结果保存在: {RESULT_DIR}")
    print(f"📋 日志文件: {LOG_DIR}")
    print('='*80)


if __name__ == '__main__':
    main()
