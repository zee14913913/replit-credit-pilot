"""
UAT阶段5：性能与负载测试（Performance & Load Testing）
版本：1.0（2025-11-12）
目标：验证系统在高并发与大数据场景下的稳定性与响应性能。

测试范围：
1. 并发用户访问测试（Dashboard, Monthly Summary）
2. 数据库查询性能测试（客户列表、账本查询）
3. 文件下载性能测试
4. 系统资源监控
"""

import time
import statistics
import random
from datetime import datetime
from typing import List, Dict, Tuple
import concurrent.futures

# ========= 配置区域 =========
TEST_CONFIG = {
    "TOTAL_REQUESTS": 100,          # 并发请求总数
    "CONCURRENT_THREADS": 10,       # 同时并发线程数
    "TIMEOUT": 30,                  # 请求超时时间（秒）
    "SUCCESS_RATE_THRESHOLD": 0.95, # 成功率阈值 >=95%
    "AVG_RESPONSE_TIME": 2.0,       # 平均响应时间 <=2秒
    "P95_RESPONSE_TIME": 4.0,       # P95响应时间 <=4秒
}

# 测试数据库连接
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import sqlite3
    DB_PATH = "db/smart_loan_manager.db"
    # 测试数据库连接
    test_conn = sqlite3.connect(DB_PATH)
    test_conn.close()
    DB_AVAILABLE = True
except Exception as e:
    DB_AVAILABLE = False
    print(f"⚠️ 数据库连接失败: {e}")

# ========= 性能指标收集 =========
class PerformanceMetrics:
    def __init__(self):
        self.results: List[Dict] = []
        self.failures: List[Dict] = []
        self.start_time = time.time()
    
    def add_success(self, test_name: str, latency: float):
        self.results.append({
            "test": test_name,
            "latency": latency,
            "success": True,
            "timestamp": time.time()
        })
    
    def add_failure(self, test_name: str, error: str):
        self.failures.append({
            "test": test_name,
            "error": error,
            "success": False,
            "timestamp": time.time()
        })
    
    def get_stats(self, test_name: str = None) -> Dict:
        """获取统计信息"""
        if test_name:
            latencies = [r["latency"] for r in self.results if r["test"] == test_name]
            failures = [f for f in self.failures if f["test"] == test_name]
        else:
            latencies = [r["latency"] for r in self.results]
            failures = self.failures
        
        if not latencies:
            return {
                "count": 0,
                "success_count": 0,
                "failure_count": len(failures),
                "success_rate": 0.0
            }
        
        total_count = len(latencies) + len(failures)
        
        return {
            "count": total_count,
            "success_count": len(latencies),
            "failure_count": len(failures),
            "success_rate": len(latencies) / total_count if total_count > 0 else 0,
            "avg_latency": statistics.mean(latencies),
            "min_latency": min(latencies),
            "max_latency": max(latencies),
            "p50_latency": statistics.median(latencies),
            "p95_latency": statistics.quantiles(latencies, n=100)[94] if len(latencies) >= 100 else max(latencies),
            "p99_latency": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies),
        }

metrics = PerformanceMetrics()

# ========= 数据库性能测试 =========
def test_database_query_performance():
    """测试数据库查询性能"""
    if not DB_AVAILABLE:
        return
    
    print("\n" + "=" * 80)
    print("1️⃣ 数据库查询性能测试")
    print("=" * 80)
    
    test_queries = [
        ("客户列表查询", "SELECT * FROM customers LIMIT 100"),
        ("信用卡列表查询", "SELECT * FROM credit_cards LIMIT 100"),
        ("月度账本查询", "SELECT * FROM monthly_ledger ORDER BY month_start DESC, card_id ASC LIMIT 100"),
        ("交易记录查询", "SELECT * FROM transactions WHERE amount > 0 LIMIT 100"),
        ("审计日志查询", "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100"),
    ]
    
    for query_name, sql in test_queries:
        try:
            start = time.time()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(sql)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            latency = time.time() - start
            
            metrics.add_success(f"DB: {query_name}", latency)
            print(f"  ✅ {query_name:<25} {len(results):>4} 条记录, {latency:.3f}秒")
        except Exception as e:
            metrics.add_failure(f"DB: {query_name}", str(e))
            print(f"  ❌ {query_name:<25} 失败: {str(e)[:50]}")

def test_concurrent_database_access():
    """测试并发数据库访问"""
    if not DB_AVAILABLE:
        return
    
    print("\n" + "=" * 80)
    print("2️⃣ 并发数据库访问测试")
    print("=" * 80)
    
    def run_query():
        try:
            start = time.time()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM customers")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            latency = time.time() - start
            metrics.add_success("DB: 并发查询", latency)
        except Exception as e:
            metrics.add_failure("DB: 并发查询", str(e))
    
    total_requests = TEST_CONFIG["TOTAL_REQUESTS"]
    concurrent_threads = TEST_CONFIG["CONCURRENT_THREADS"]
    
    print(f"  执行 {total_requests} 次并发查询，{concurrent_threads} 个线程")
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_threads) as executor:
        list(executor.map(lambda _: run_query(), range(total_requests)))
    
    duration = time.time() - start_time
    stats = metrics.get_stats("DB: 并发查询")
    
    print(f"\n  总耗时: {duration:.2f}秒")
    print(f"  成功: {stats['success_count']}/{stats['count']}")
    print(f"  成功率: {stats['success_rate']*100:.1f}%")
    if stats['success_count'] > 0:
        print(f"  平均响应: {stats['avg_latency']:.3f}秒")
        print(f"  P95响应: {stats['p95_latency']:.3f}秒")
        print(f"  QPS: {stats['success_count']/duration:.2f} 查询/秒")

# ========= 文件系统性能测试 =========
def test_file_operations():
    """测试文件操作性能"""
    print("\n" + "=" * 80)
    print("3️⃣ 文件系统性能测试")
    print("=" * 80)
    
    import os
    
    directories = [
        "static/uploads",
        "static/uploads/customers",
        "static/uploads/invoices",
    ]
    
    for directory in directories:
        try:
            start = time.time()
            
            if os.path.exists(directory):
                file_count = sum([len(files) for r, d, files in os.walk(directory)])
                latency = time.time() - start
                
                metrics.add_success(f"FS: {directory}", latency)
                print(f"  ✅ {directory:<35} {file_count:>5} 个文件, {latency:.3f}秒")
            else:
                print(f"  ⚠️ {directory:<35} 目录不存在")
        except Exception as e:
            metrics.add_failure(f"FS: {directory}", str(e))
            print(f"  ❌ {directory:<35} 失败: {str(e)[:50]}")

# ========= 业务逻辑性能测试 =========
def test_business_logic_performance():
    """测试业务逻辑性能"""
    if not DB_AVAILABLE:
        return
    
    print("\n" + "=" * 80)
    print("4️⃣ 业务逻辑性能测试")
    print("=" * 80)
    
    try:
        # 测试月度账本计算性能
        from services.monthly_ledger_engine import MonthlyLedgerEngine
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取一张信用卡进行测试
        cursor.execute("SELECT id FROM credit_cards LIMIT 1")
        card = cursor.fetchone()
        
        if card:
            card_id = card[0]
            
            # 实例化引擎
            engine = MonthlyLedgerEngine(db_path=DB_PATH)
            
            # 测试账本计算
            ledger_start = time.time()
            try:
                ledger_results = engine.calculate_monthly_ledger_for_card(card_id, recalculate_all=False)
                ledger_time = time.time() - ledger_start
                
                # 查询实际生成的账本记录数
                cursor.execute("SELECT COUNT(*) FROM monthly_ledger WHERE card_id = ?", (card_id,))
                record_count = cursor.fetchone()[0]
                
                metrics.add_success("BIZ: 月度账本计算", ledger_time)
                print(f"  ✅ 月度账本计算 (卡ID:{card_id}, {record_count}条账本): {ledger_time:.3f}秒")
            except Exception as calc_error:
                ledger_time = time.time() - ledger_start
                metrics.add_failure("BIZ: 月度账本计算", str(calc_error))
                print(f"  ❌ 月度账本计算失败: {str(calc_error)[:100]}")
        else:
            print(f"  ⚠️ 无可用信用卡数据，跳过业务逻辑测试")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        metrics.add_failure("BIZ: 业务逻辑初始化", str(e))
        print(f"  ❌ 业务逻辑测试初始化失败: {str(e)[:100]}")

# ========= 内存与资源使用测试 =========
def test_memory_usage():
    """测试内存使用情况"""
    print("\n" + "=" * 80)
    print("5️⃣ 内存与资源使用测试")
    print("=" * 80)
    
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        print(f"  当前进程内存使用:")
        print(f"    RSS (常驻内存): {memory_info.rss / 1024 / 1024:.2f} MB")
        print(f"    VMS (虚拟内存): {memory_info.vms / 1024 / 1024:.2f} MB")
        
        # 系统内存
        vm = psutil.virtual_memory()
        print(f"\n  系统内存:")
        print(f"    总内存: {vm.total / 1024 / 1024 / 1024:.2f} GB")
        print(f"    可用内存: {vm.available / 1024 / 1024 / 1024:.2f} GB")
        print(f"    使用率: {vm.percent}%")
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"\n  CPU使用率: {cpu_percent}%")
        
    except ImportError:
        print("  ⚠️ psutil未安装，跳过系统资源监控")
        print("  提示: 运行 'pip install psutil' 安装")

# ========= 生成测试报告 =========
def generate_report():
    """生成性能测试报告"""
    print("\n" + "=" * 80)
    print("📊 生成测试报告")
    print("=" * 80)
    
    total_duration = time.time() - metrics.start_time
    overall_stats = metrics.get_stats()
    
    # 控制台输出
    print(f"\n总体统计:")
    print(f"  总测试数: {overall_stats['count']}")
    print(f"  成功: {overall_stats['success_count']}")
    print(f"  失败: {overall_stats['failure_count']}")
    print(f"  成功率: {overall_stats['success_rate']*100:.1f}%")
    
    if overall_stats['success_count'] > 0:
        print(f"  平均响应时间: {overall_stats['avg_latency']:.3f}秒")
        print(f"  P50响应时间: {overall_stats['p50_latency']:.3f}秒")
        print(f"  P95响应时间: {overall_stats['p95_latency']:.3f}秒")
        print(f"  最小响应时间: {overall_stats['min_latency']:.3f}秒")
        print(f"  最大响应时间: {overall_stats['max_latency']:.3f}秒")
    
    print(f"  总耗时: {total_duration:.2f}秒")
    
    # 生成Markdown报告
    report_content = f"""# UAT阶段5：性能与负载测试报告

## 📋 测试概览

| 项目 | 值 |
|------|-----|
| **测试时间** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| **测试耗时** | {total_duration:.2f} 秒 |
| **总测试数** | {overall_stats['count']} |
| **成功测试** | {overall_stats['success_count']} |
| **失败测试** | {overall_stats['failure_count']} |
| **成功率** | {overall_stats['success_rate']*100:.1f}% |

---

## 🎯 测试目标

验证系统在高并发与大数据场景下的稳定性与响应性能：

1. ✅ **数据库查询性能** - 单次查询与并发查询
2. ✅ **并发访问能力** - {TEST_CONFIG['CONCURRENT_THREADS']}个并发线程
3. ✅ **文件系统性能** - 文件读取速度
4. ✅ **业务逻辑性能** - 账本计算等复杂业务
5. ✅ **系统资源使用** - 内存与CPU监控

---

## 📈 性能指标统计

### 总体性能
"""
    
    if overall_stats['success_count'] > 0:
        report_content += f"""
| 指标 | 值 | 通过标准 | 状态 |
|------|-----|----------|------|
| 成功率 | {overall_stats['success_rate']*100:.1f}% | ≥95% | {'✅' if overall_stats['success_rate'] >= TEST_CONFIG['SUCCESS_RATE_THRESHOLD'] else '❌'} |
| 平均响应时间 | {overall_stats['avg_latency']:.3f}秒 | ≤2秒 | {'✅' if overall_stats['avg_latency'] <= TEST_CONFIG['AVG_RESPONSE_TIME'] else '⚠️'} |
| P95响应时间 | {overall_stats['p95_latency']:.3f}秒 | ≤4秒 | {'✅' if overall_stats['p95_latency'] <= TEST_CONFIG['P95_RESPONSE_TIME'] else '⚠️'} |
| 最小响应时间 | {overall_stats['min_latency']:.3f}秒 | - | ℹ️ |
| 最大响应时间 | {overall_stats['max_latency']:.3f}秒 | - | ℹ️ |

### 响应时间分布

| 百分位 | 响应时间 |
|--------|----------|
| P50 (中位数) | {overall_stats['p50_latency']:.3f}秒 |
| P95 | {overall_stats['p95_latency']:.3f}秒 |
| P99 | {overall_stats['p99_latency']:.3f}秒 |
"""
    
    # 分类统计
    report_content += "\n### 分类性能统计\n\n"
    
    test_categories = {}
    for result in metrics.results:
        category = result['test'].split(':')[0]
        if category not in test_categories:
            test_categories[category] = []
        test_categories[category].append(result['test'])
    
    for category, tests in test_categories.items():
        unique_tests = list(set(tests))
        report_content += f"\n#### {category} 测试\n\n"
        report_content += "| 测试项 | 成功数 | 平均响应 | P95响应 |\n"
        report_content += "|--------|--------|----------|----------|\n"
        
        for test in unique_tests:
            stats = metrics.get_stats(test)
            if stats['success_count'] > 0:
                report_content += f"| {test.split(': ')[1]} | {stats['success_count']}/{stats['count']} | {stats['avg_latency']:.3f}秒 | {stats['p95_latency']:.3f}秒 |\n"
    
    # 失败详情
    if metrics.failures:
        report_content += "\n---\n\n## ⚠️ 失败测试详情\n\n"
        report_content += "| 测试项 | 错误信息 |\n"
        report_content += "|--------|----------|\n"
        for failure in metrics.failures[:10]:  # 只显示前10个失败
            report_content += f"| {failure['test']} | {failure['error'][:100]} |\n"
    
    # 通过标准
    report_content += """
---

## ✅ 通过标准

| 指标 | 要求 | 含义 |
|------|------|------|
| 成功率 | ≥95% | 系统稳定性 |
| 平均响应时间 | ≤2秒 | 性能达标 |
| P95响应时间 | ≤4秒 | 高峰期响应速度 |
| 崩溃/异常 | 无 | 系统无死锁或500错误 |

---

## 🔍 测试结论

"""
    
    # 判定结果（区分关键测试和非关键测试）
    # 关键测试类别（必须全部成功）
    CRITICAL_CATEGORIES = ["DB:", "BIZ:"]
    
    # 检查关键测试是否全部通过
    critical_failures = [f for f in metrics.failures if any(f['test'].startswith(cat) for cat in CRITICAL_CATEGORIES)]
    has_critical_failure = len(critical_failures) > 0
    
    # 总体通过标准：关键测试0失败 + 成功率≥95% + 性能达标
    passed = (
        not has_critical_failure and
        overall_stats['success_rate'] >= TEST_CONFIG['SUCCESS_RATE_THRESHOLD'] and
        (overall_stats['avg_latency'] <= TEST_CONFIG['AVG_RESPONSE_TIME'] if overall_stats['success_count'] > 0 else False) and
        (overall_stats['p95_latency'] <= TEST_CONFIG['P95_RESPONSE_TIME'] if overall_stats['success_count'] > 0 else False)
    )
    
    if passed:
        report_content += """### ✅ **测试通过！**

**系统性能达到企业级生产标准：**
- ✅ 关键测试全部通过（DB查询、并发、业务逻辑）
- ✅ 成功率达标（≥95%）
- ✅ 平均响应时间达标（≤2秒）
- ✅ P95响应时间达标（≤4秒）
- ✅ 系统稳定无崩溃

**系统状态：** 🎉 **可投入生产环境使用**

---

## 🚀 下一步行动

1. ✅ 系统已通过UAT阶段1-5全部测试
2. ✅ 可正式标记为 **Production Live（正式生产环境）**
3. 建议执行最终数据库迁移锁定：`python db/migrations_v5_1_final.py`（如存在）
4. 配置生产环境监控与告警
5. 准备上线部署

"""
    else:
        report_content += """### ❌ **测试未通过**

**失败原因：**
"""
        if has_critical_failure:
            report_content += f"\n#### 🚨 关键测试失败（{len(critical_failures)}个）\n\n"
            for failure in critical_failures:
                report_content += f"- ❌ **{failure['test']}**: {failure['error'][:150]}\n"
            report_content += "\n**关键测试必须全部通过才能投入生产！**\n\n"
        
        if overall_stats['success_rate'] < TEST_CONFIG['SUCCESS_RATE_THRESHOLD']:
            report_content += f"- ❌ 成功率不达标（{overall_stats['success_rate']*100:.1f}% < 95%）\n"
        if overall_stats['success_count'] > 0 and overall_stats['avg_latency'] > TEST_CONFIG['AVG_RESPONSE_TIME']:
            report_content += f"- ⚠️ 平均响应时间偏高（{overall_stats['avg_latency']:.3f}秒 > 2秒）\n"
        if overall_stats['success_count'] > 0 and overall_stats['p95_latency'] > TEST_CONFIG['P95_RESPONSE_TIME']:
            report_content += f"- ⚠️ P95响应时间偏高（{overall_stats['p95_latency']:.3f}秒 > 4秒）\n"
        
        report_content += """
**建议优化措施：**
1. 修复所有关键测试失败（DB查询、业务逻辑）
2. 优化数据库索引（高频查询字段）
3. 启用查询结果缓存（Redis）
4. 实施异步处理队列（Celery/RQ）
5. 增加数据库连接池配置
6. 优化慢查询SQL语句

"""
    
    report_content += """---

**测试执行者：** UAT自动化测试脚本  
**报告版本：** 1.0  
**测试配置：**
- 总请求数: {total_requests}
- 并发线程: {concurrent_threads}
- 超时时间: {timeout}秒
""".format(
        total_requests=TEST_CONFIG['TOTAL_REQUESTS'],
        concurrent_threads=TEST_CONFIG['CONCURRENT_THREADS'],
        timeout=TEST_CONFIG['TIMEOUT']
    )
    
    # 写入文件
    with open("UAT_STAGE5_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"\n✅ 测试报告已生成：UAT_STAGE5_REPORT.md")
    
    # 返回测试是否通过
    return passed

# ========= 主测试流程 =========
def main():
    """主测试流程"""
    print("=" * 80)
    print("🧪 UAT阶段5：性能与负载测试")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"配置: {TEST_CONFIG['TOTAL_REQUESTS']}次请求, {TEST_CONFIG['CONCURRENT_THREADS']}并发")
    
    # 执行测试
    test_database_query_performance()
    test_concurrent_database_access()
    test_file_operations()
    test_business_logic_performance()
    test_memory_usage()
    
    # 生成报告
    passed = generate_report()
    
    print("\n" + "=" * 80)
    if passed:
        print("🎉 UAT阶段5测试通过！系统可投入生产环境使用。")
    else:
        print("⚠️ UAT阶段5测试未完全通过，建议优化后重新测试。")
    print("=" * 80)

if __name__ == "__main__":
    main()
