import os, requests, json, time
from datetime import datetime
from dotenv import load_dotenv

# ========= 环境变量加载 ==========
load_dotenv()
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
TEST_EMAIL = os.getenv("TEST_EMAIL", "testuser@example.com")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "123456")

# ========= 动态测试参数 ==========
CUSTOMER_ID = "1"
STATEMENT_ID = "1"
TRANSACTION_ID = "1"
BUDGET_ID = "1"
REMINDER_ID = "1"
NEWS_ID = "1"

# ========= GET路由结构 ==========
GET_ROUTES = [
    "/",
    "/customer/login",
    "/customer/register",
    "/customer/logout",
    "/customer-authorization",  # 修正：用横线
    f"/customer/{CUSTOMER_ID}",
    f"/customer/download/{STATEMENT_ID}",
    "/customer/portal",
    f"/analytics/{CUSTOMER_ID}",
    f"/generate_report/{CUSTOMER_ID}",
    f"/advisory/{CUSTOMER_ID}",
    "/upload_statement",
    f"/loan_evaluation/{CUSTOMER_ID}",
    f"/budget/{CUSTOMER_ID}",
    f"/batch/upload/{CUSTOMER_ID}",
    f"/search/{CUSTOMER_ID}",
    f"/export/{CUSTOMER_ID}/pdf",
    "/admin-login",
    "/admin",
    "/admin/news",
    f"/admin/news/approve/{NEWS_ID}",
    f"/admin/news/reject/{NEWS_ID}",
    "/admin-logout",
    "/banking_news",
    "/reminders",
    "/refresh_bnm_rates",
    f"/validate_statement/{STATEMENT_ID}",
    f"/customer/{CUSTOMER_ID}/employment",
    "/set-language/en",
    "/set-language/zh"
]

# ========= POST路由结构 ==========
POST_ROUTES = {
    f"/confirm_statement/{STATEMENT_ID}": {},
    "/create_reminder": {"title": "Test Reminder", "amount": 100, "due_date": "2025-12-31"},
    f"/mark_paid/{REMINDER_ID}": {},
    "/add_news": {"title": "Automation Test News", "content": "System generated news"},
    "/admin/news/fetch": {},
    f"/transaction/{TRANSACTION_ID}/note": {"note": "Automated test note"},
    f"/transaction/{TRANSACTION_ID}/tag": {"tag": "QA-Test"},
    f"/consultation/request/{CUSTOMER_ID}": {"message": "Automated consultation request"},
    f"/customer/{CUSTOMER_ID}/employment": {"company": "TestCorp", "position": "QA Engineer"},
    f"/budget/delete/{BUDGET_ID}/{CUSTOMER_ID}": {}
}

session = requests.Session()
RESULTS = []

# ========= 辅助函数 ==========
def log_result(status, route, method, code=None, duration=None, error=None):
    timestamp = datetime.now().strftime("%H:%M:%S")
    RESULTS.append({
        "time": timestamp,
        "route": route,
        "method": method,
        "status": status,
        "code": code,
        "duration": duration,
        "error": error
    })
    status_icon = "✅" if "PASS" in status else "⚠️" if "FAIL" in status else "❌"
    print(f"[{status_icon} {status}] {method:<5} {route:<50} {code or ''} {f'{duration}s' if duration else ''} {error or ''}")

def test_login():
    url = f"{BASE_URL}/customer/login"
    data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    try:
        r = session.post(url, data=data, timeout=10)
        if r.status_code in [200, 302]:
            log_result("PASS", "/customer/login", "POST", r.status_code)
            return True
        log_result("FAIL", "/customer/login", "POST", r.status_code)
    except Exception as e:
        log_result("ERROR", "/customer/login", "POST", error=str(e))
    return False

def test_get_routes():
    for path in GET_ROUTES:
        url = f"{BASE_URL}{path}"
        try:
            start = time.time()
            r = session.get(url, timeout=8, allow_redirects=False)
            duration = round(time.time() - start, 2)
            if r.status_code in [200, 302]:
                log_result("PASS", path, "GET", r.status_code, duration)
            else:
                log_result("FAIL", path, "GET", r.status_code, duration)
        except Exception as e:
            log_result("ERROR", path, "GET", error=str(e))

def test_post_routes():
    for path, data in POST_ROUTES.items():
        url = f"{BASE_URL}{path}"
        try:
            start = time.time()
            r = session.post(url, data=data, timeout=8, allow_redirects=False)
            duration = round(time.time() - start, 2)
            if r.status_code in [200, 302]:
                log_result("PASS", path, "POST", r.status_code, duration)
            else:
                log_result("FAIL", path, "POST", r.status_code, duration)
        except Exception as e:
            log_result("ERROR", path, "POST", error=str(e))

def analyze_performance():
    """分析性能瓶颈"""
    timed_results = [r for r in RESULTS if r['duration'] is not None]
    if not timed_results:
        return
    
    # 计算平均响应时间
    avg_time = sum(r['duration'] for r in timed_results) / len(timed_results)
    
    # 找出最慢的5个接口
    slowest = sorted(timed_results, key=lambda x: x['duration'], reverse=True)[:5]
    
    print("\n📊 性能分析：")
    print(f"   平均响应时间: {avg_time:.2f}s")
    print("\n   最慢的5个接口：")
    for i, r in enumerate(slowest, 1):
        print(f"   {i}. {r['route']} - {r['duration']}s ({r['method']})")

def save_reports():
    os.makedirs("logs", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary = f"logs/summary_{ts}.txt"
    detailed = f"logs/detailed_{ts}.txt"
    
    passed = sum(1 for r in RESULTS if "PASS" in r["status"])
    failed = sum(1 for r in RESULTS if "FAIL" in r["status"])
    errors = sum(1 for r in RESULTS if "ERROR" in r["status"])
    total = len(RESULTS)

    # 摘要报告
    with open(summary, "w", encoding="utf-8") as s:
        s.write("=" * 60 + "\n")
        s.write("INFINITE GZ SDN BHD - System Test Summary\n")
        s.write("=" * 60 + "\n")
        s.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        s.write(f"Base URL: {BASE_URL}\n\n")
        s.write(f"Total Tests: {total}\n")
        s.write(f"✅ PASS: {passed} ({passed/total*100:.1f}%)\n")
        s.write(f"⚠️ FAIL: {failed} ({failed/total*100:.1f}%)\n")
        s.write(f"❌ ERROR: {errors} ({errors/total*100:.1f}%)\n")
        s.write("=" * 60 + "\n")

    # 详细报告
    with open(detailed, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("INFINITE GZ SDN BHD - Detailed Test Report\n")
        f.write("=" * 80 + "\n\n")
        for r in RESULTS:
            status_str = f"[{r['status']}]".ljust(10)
            method_str = r['method'].ljust(5)
            route_str = r['route'].ljust(50)
            code_str = str(r['code'] or '').ljust(5)
            duration_str = f"{r['duration']}s" if r['duration'] else ""
            error_str = r['error'] or ""
            f.write(f"[{r['time']}] {status_str} {method_str} {route_str} {code_str} {duration_str} {error_str}\n")

    print(f"\n📝 报告已生成：")
    print(f"   摘要: {summary}")
    print(f"   详细: {detailed}\n")

def run_advanced_analysis():
    """运行高级分析脚本"""
    try:
        import subprocess
        result = subprocess.run(
            ["python3", "analyze_test_results.py"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"⚠️ 分析脚本执行出错：{result.stderr}")
    except Exception as e:
        print(f"⚠️ 无法运行高级分析：{str(e)}")

def main():
    print("\n" + "=" * 60)
    print("🚀 INFINITE GZ SDN BHD - 系统综合测试 v3.0")
    print("=" * 60 + "\n")
    
    if test_login():
        print("\n🔍 测试 GET 路由...\n")
        test_get_routes()
        
        print("\n📤 测试 POST 路由...\n")
        test_post_routes()
        
        analyze_performance()
        save_reports()
        
        # 自动运行高级分析
        run_advanced_analysis()
        
        print("\n✅ 所有测试完成。\n")
    else:
        print("\n❌ 登录失败，测试终止。\n")

if __name__ == "__main__":
    main()
