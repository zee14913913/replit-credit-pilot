import os
import re
import pandas as pd
from datetime import datetime

LOG_FOLDER = "logs"

def parse_log(file_path):
    """解析详细日志文件"""
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            m = re.search(r"\[(.*?)\]\s+\[(.*?)\]\s+(GET|POST)\s+([^\s]+)\s+(\d+)?\s*([\d.]+s)?", line)
            if m:
                timestamp, status, method, route, code, duration = m.groups()
                duration_val = float(duration.replace('s', '')) if duration else None
                data.append({
                    "time": timestamp,
                    "status": status.strip(),
                    "method": method,
                    "route": route,
                    "code": code,
                    "duration": duration_val
                })
    return pd.DataFrame(data)

def analyze_performance():
    """分析测试性能"""
    files = [f for f in os.listdir(LOG_FOLDER) if f.startswith("detailed_")]
    if not files:
        print("⚠️ 未找到详细日志文件，请先运行测试脚本。")
        return
    
    latest = sorted(files)[-1]
    path = os.path.join(LOG_FOLDER, latest)
    print(f"\n{'='*60}")
    print(f"📂 分析文件：{latest}")
    print(f"{'='*60}\n")
    
    df = parse_log(path)
    
    if df.empty:
        print("⚠️ 日志文件为空或格式不正确。")
        return
    
    total = len(df)
    passed = len(df[df["status"].str.contains("PASS")])
    failed = len(df[df["status"].str.contains("FAIL")])
    error = len(df[df["status"].str.contains("ERROR")])
    fail_ratio = round((failed + error) / total * 100, 2) if total > 0 else 0
    
    print(f"📊 测试结果摘要：")
    print(f"   总测试数：{total}")
    print(f"   ✅ 通过：{passed} ({passed/total*100:.1f}%)")
    print(f"   ⚠️ 失败：{failed} ({failed/total*100:.1f}%)")
    print(f"   ❌ 错误：{error} ({error/total*100:.1f}%)")
    print(f"   📉 总失败率：{fail_ratio}%")
    
    # 分析最慢的接口
    timed_df = df[df["duration"].notna()].copy()
    if not timed_df.empty:
        avg_time = timed_df["duration"].mean()
        # 转换为列表进行排序
        timed_list = []
        for _, row in timed_df.iterrows():
            timed_list.append({
                'status': row['status'],
                'method': row['method'],
                'route': row['route'],
                'duration': row['duration']
            })
        slowest = sorted(timed_list, key=lambda x: x['duration'], reverse=True)[:5]
        
        print(f"\n⏱️ 性能指标：")
        print(f"   平均响应时间：{avg_time:.2f}s")
        print(f"\n🐢 最慢的 5 个接口：")
        for idx, r in enumerate(slowest, 1):
            status_icon = "✅" if "PASS" in r['status'] else "⚠️" if "FAIL" in r['status'] else "❌"
            print(f"   {idx}. {status_icon} {r['method']:<5} {r['route']:<45} {r['duration']:.2f}s")
    
    # 高风险接口分析
    risky = df[df["status"].str.contains("FAIL|ERROR")]
    if not risky.empty:
        print(f"\n🚨 高风险接口列表 ({len(risky)} 个)：")
        for _, r in risky.iterrows():
            status_icon = "⚠️" if "FAIL" in r['status'] else "❌"
            print(f"   {status_icon} {r['method']:<5} {r['route']:<45} ({r['status']})")
    else:
        print("\n✅ 未检测到高风险接口 - 所有测试通过！")
    
    # 按HTTP方法分组统计
    print(f"\n📈 按请求方法统计：")
    method_stats = df.groupby('method')['status'].apply(
        lambda x: f"✅ {sum(x.str.contains('PASS'))} / ⚠️ {sum(x.str.contains('FAIL'))} / ❌ {sum(x.str.contains('ERROR'))}"
    )
    for method, stats in method_stats.items():
        print(f"   {method:<5} → {stats}")
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    analyze_performance()
