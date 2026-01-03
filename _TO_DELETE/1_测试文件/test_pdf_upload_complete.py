#!/usr/bin/env python3
"""
完整PDF上传测试 - 3个场景
基于真实Hong Leong Bank月结单
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
COMPANY_ID = 1

def test_pdf_upload(pdf_path, scenario_name, description):
    """测试PDF上传"""
    print(f"\n{'='*80}")
    print(f"【{scenario_name}】{description}")
    print('='*80)
    
    try:
        # 读取PDF文件
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        filename = pdf_path.split('/')[-1]
        
        # 上传到 FastAPI endpoint
        files = {'file': (filename, pdf_content, 'application/pdf')}
        
        print(f"📤 正在上传: {filename}")
        print(f"📁 文件大小: {len(pdf_content) / 1024:.2f} KB")
        
        response = requests.post(
            f"{BASE_URL}/api/v2/import/bank-statement?company_id={COMPANY_ID}",
            files=files,
            timeout=60
        )
        
        print(f"✓ HTTP Status: {response.status_code}")
        
        try:
            result = response.json()
        except:
            result = {"error": "无法解析JSON响应", "raw_text": response.text[:500]}
        
        # 提取关键字段
        test_result = {
            "scenario": scenario_name,
            "description": description,
            "filename": filename,
            "file_size_kb": round(len(pdf_content) / 1024, 2),
            "http_status": response.status_code,
            "success": result.get("success"),
            "status": result.get("status"),
            "raw_document_id": result.get("raw_document_id"),
            "file_id": result.get("file_id"),
            "next_actions": result.get("next_actions", []),
            "error_code": result.get("error_code"),
            "message": result.get("message", ""),
            "analysis": result.get("analysis", {}),
        }
        
        # 显示详细结果
        print(f"\n📊 测试结果：")
        print(f"  HTTP状态码: {test_result['http_status']}")
        print(f"  success: {test_result['success']}")
        print(f"  status: {test_result['status']}")
        
        if test_result['file_id']:
            print(f"  file_id: {test_result['file_id']}")
            print(f"  ✅ detail页: 有 (/files/detail/{test_result['file_id']})")
        else:
            print(f"  ❌ detail页: 无")
        
        if test_result['next_actions']:
            print(f"  按钮: {test_result['next_actions']}")
        
        if test_result['error_code']:
            print(f"  错误码: {test_result['error_code']}")
        
        if test_result['message']:
            print(f"  消息: {test_result['message'][:200]}")
        
        return test_result
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "scenario": scenario_name,
            "error": str(e)
        }

if __name__ == "__main__":
    print("="*80)
    print("🧪 PDF上传功能完整测试 - 3个场景")
    print("="*80)
    print("📋 测试环境:")
    print(f"   Backend: {BASE_URL}")
    print(f"   Company ID: {COMPANY_ID}")
    print(f"   测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Scenario 1: 正常版PDF（真实Hong Leong Bank月结单）
    result1 = test_pdf_upload(
        'test_pdfs/PDF-1-Normal-HongLeong-May2025.pdf',
        'PDF-1 正常版',
        '真实Hong Leong Bank月结单（May 2025, 8页）'
    )
    results.append(result1)
    time.sleep(2)
    
    # Scenario 2: 缺列版PDF（缺少Credit列）
    result2 = test_pdf_upload(
        'test_pdfs/PDF-2-Missing-Column-May2025.pdf',
        'PDF-2 缺列版',
        '缺少Credit/Deposit列的月结单（应触发验证失败）'
    )
    results.append(result2)
    time.sleep(2)
    
    # Scenario 3: 扫描版PDF（无结构化表格）
    result3 = test_pdf_upload(
        'test_pdfs/PDF-3-Scanned-May2025.pdf',
        'PDF-3 扫描版',
        '模拟扫描件（无结构化表格数据）'
    )
    results.append(result3)
    
    # 生成总结报告
    print(f"\n{'='*80}")
    print("📊 测试总结报告")
    print('='*80)
    
    for r in results:
        if 'error' in r:
            print(f"\n❌ {r['scenario']}: ERROR")
            print(f"   错误: {r['error']}")
        else:
            detail_page = "有" if r['file_id'] else "无"
            buttons = r['next_actions'] if r['next_actions'] else "[]"
            
            print(f"\n{'✅' if r['success'] else '⚠️'} {r['scenario']}: HTTP={r['http_status']}, detail页={detail_page}, 按钮={buttons}")
            if r['message']:
                print(f"   消息: {r['message'][:150]}")
    
    # 保存完整报告
    report_path = '/tmp/pdf_upload_complete_test.json'
    with open(report_path, 'w') as f:
        json.dump({
            "test_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "base_url": BASE_URL,
            "company_id": COMPANY_ID,
            "scenarios": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 完整报告已保存: {report_path}")
    
    # 验证前端链路关键点
    print(f"\n{'='*80}")
    print("🔍 前端链路验证")
    print('='*80)
    
    print("\n1️⃣ 前端PDF→CSV转换提示:")
    print("   浏览器应显示: '🔄 正在将PDF转换为CSV格式...'")
    print("   (此项需要真实浏览器测试)")
    
    print("\n2️⃣ Network请求验证:")
    for r in results:
        if 'error' not in r:
            print(f"   {r['scenario']}: /api/v2/import/bank-statement → HTTP {r['http_status']}")
    
    print("\n3️⃣ 页面跳转验证:")
    for r in results:
        if 'error' not in r and r.get('file_id'):
            print(f"   {r['scenario']}: 应跳转 /files/detail/{r['file_id']}?highlight={r['file_id']}")
    
    print("\n4️⃣ 详情页按钮验证:")
    for r in results:
        if 'error' not in r and r.get('next_actions'):
            print(f"   {r['scenario']}: {r['next_actions']}")
    
    print(f"\n{'='*80}")
    print("✅ PDF上传测试完成！")
    print('='*80)
