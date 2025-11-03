#!/usr/bin/env python3
"""
Critical修复验证：语言切换机制
验证3个场景：
1. GET /?lang=zh → POST 登录失败 → flash必须是中文
2. GET /?lang=en → POST 登录失败 → flash必须是英文
3. GET /?lang=zh → 上传坏CSV → 错误提示必须是中文
"""
import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:5000"

def extract_flash_messages(html):
    """提取所有Flash消息"""
    soup = BeautifulSoup(html, 'html.parser')
    alerts = soup.find_all('div', class_='alert')
    messages = []
    for alert in alerts:
        # 移除关闭按钮文本
        for button in alert.find_all('button'):
            button.decompose()
        text = alert.get_text(strip=True)
        messages.append(text)
    return messages

print("="*70)
print("🧪 语言切换机制Critical修复 - 验证测试")
print("="*70)

# ============================================================
# 测试1: GET /?lang=zh → POST 登录失败 → 中文flash
# ============================================================
print("\n【测试1】GET /?lang=zh → POST admin/login失败 → 期望中文")
print("-" * 70)

session1 = requests.Session()

# Step 1: GET /?lang=zh
resp1 = session1.get(f"{BASE_URL}/", params={"lang": "zh"})
print(f"✓ GET /?lang=zh - 状态码: {resp1.status_code}")

# Step 2: POST /admin/login with empty credentials
resp2 = session1.post(f"{BASE_URL}/admin/login", data={
    "username": "",
    "password": ""
}, allow_redirects=True)

flash_msgs = extract_flash_messages(resp2.text)
print(f"✓ POST /admin/login - 状态码: {resp2.status_code}")
print(f"✓ Flash消息数量: {len(flash_msgs)}")

if flash_msgs:
    for i, msg in enumerate(flash_msgs, 1):
        print(f"  Flash #{i}: 「{msg}」")
    
    # 验证是否为中文
    expected_zh = "请输入用户名和密码"
    if expected_zh in flash_msgs[0]:
        print(f"✅ 测试1 PASS - Flash消息是中文")
    else:
        print(f"❌ 测试1 FAIL - 期望中文「{expected_zh}」，实际「{flash_msgs[0]}」")
else:
    print(f"❌ 测试1 FAIL - 未找到Flash消息")

# ============================================================
# 测试2: GET /?lang=en → POST 登录失败 → 英文flash
# ============================================================
print("\n【测试2】GET /?lang=en → POST admin/login失败 → 期望英文")
print("-" * 70)

session2 = requests.Session()

# Step 1: GET /?lang=en
resp3 = session2.get(f"{BASE_URL}/", params={"lang": "en"})
print(f"✓ GET /?lang=en - 状态码: {resp3.status_code}")

# Step 2: POST /admin/login with empty credentials
resp4 = session2.post(f"{BASE_URL}/admin/login", data={
    "username": "",
    "password": ""
}, allow_redirects=True)

flash_msgs2 = extract_flash_messages(resp4.text)
print(f"✓ POST /admin/login - 状态码: {resp4.status_code}")
print(f"✓ Flash消息数量: {len(flash_msgs2)}")

if flash_msgs2:
    for i, msg in enumerate(flash_msgs2, 1):
        print(f"  Flash #{i}: 「{msg}」")
    
    # 验证是否为英文
    expected_en = "Please Enter Username And Password"
    if expected_en in flash_msgs2[0]:
        print(f"✅ 测试2 PASS - Flash消息是英文")
    else:
        print(f"❌ 测试2 FAIL - 期望英文「{expected_en}」，实际「{flash_msgs2[0]}」")
else:
    print(f"❌ 测试2 FAIL - 未找到Flash消息")

# ============================================================
# 测试3: GET /?lang=zh → 尝试添加客户缺字段 → 中文flash
# ============================================================
print("\n【测试3】GET /?lang=zh → POST add_customer缺字段 → 期望中文")
print("-" * 70)

session3 = requests.Session()

# Step 1: GET /?lang=zh
resp5 = session3.get(f"{BASE_URL}/", params={"lang": "zh"})
print(f"✓ GET /?lang=zh - 状态码: {resp5.status_code}")

# Step 2: POST /add_customer with missing fields
resp6 = session3.post(f"{BASE_URL}/add_customer", data={
    "name": "",  # Missing
    "email": "",  # Missing
    "phone": ""   # Missing
}, allow_redirects=True)

flash_msgs3 = extract_flash_messages(resp6.text)
print(f"✓ POST /add_customer - 状态码: {resp6.status_code}")
print(f"✓ Flash消息数量: {len(flash_msgs3)}")

if flash_msgs3:
    for i, msg in enumerate(flash_msgs3, 1):
        print(f"  Flash #{i}: 「{msg}」")
    
    # 验证是否为中文
    expected_zh3 = "所有字段为必填项"
    if expected_zh3 in flash_msgs3[0]:
        print(f"✅ 测试3 PASS - Flash消息是中文")
    else:
        print(f"❌ 测试3 FAIL - 期望中文「{expected_zh3}」，实际「{flash_msgs3[0]}」")
else:
    print(f"❌ 测试3 FAIL - 未找到Flash消息")

# ============================================================
# 总结
# ============================================================
print("\n" + "="*70)
print("📊 测试总结")
print("="*70)

test_results = []
if flash_msgs and "请输入用户名和密码" in flash_msgs[0]:
    test_results.append("✅ 测试1 PASS")
else:
    test_results.append("❌ 测试1 FAIL")

if flash_msgs2 and "Please Enter Username And Password" in flash_msgs2[0]:
    test_results.append("✅ 测试2 PASS")
else:
    test_results.append("❌ 测试2 FAIL")

if flash_msgs3 and "所有字段为必填项" in flash_msgs3[0]:
    test_results.append("✅ 测试3 PASS")
else:
    test_results.append("❌ 测试3 FAIL")

for result in test_results:
    print(result)

all_passed = all("PASS" in r for r in test_results)
if all_passed:
    print("\n🎉 所有测试通过！语言切换机制修复成功！")
else:
    print("\n⚠️ 部分测试失败，需要继续调试")

print("="*70)
