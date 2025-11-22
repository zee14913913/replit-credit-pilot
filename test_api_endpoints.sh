#!/bin/bash
# CreditPilot API端点完整测试脚本
# 使用方法: bash test_api_endpoints.sh

echo "======================================================"
echo "🚀 CreditPilot API 端点验证测试"
echo "======================================================"
echo ""

BASE_URL="http://localhost:5000"
MINIMAX_ORIGIN="https://ynqoo4ipbuar.space.minimax.io"

# 颜色代码
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数器
PASS=0
FAIL=0

# 测试函数
test_endpoint() {
    local name=$1
    local url=$2
    local method=$3
    local expected=$4
    
    echo -n "测试 ${name}... "
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s "${BASE_URL}${url}")
    fi
    
    if echo "$response" | grep -q "$expected"; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASS++))
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "  响应: $response"
        ((FAIL++))
    fi
}

echo "1️⃣ 测试基础API端点"
echo "------------------------------------------------------"

# Test 1: Health Check
test_endpoint "Health Check" "/api/health" "GET" "healthy"

# Test 2: Customers List
test_endpoint "Customers List" "/api/customers" "GET" "\"success\": true"

# Test 3: Dashboard Stats
test_endpoint "Dashboard Stats" "/api/dashboard/stats" "GET" "\"customer_count\":"

# Test 4: Dashboard Summary (NEW)
test_endpoint "Dashboard Summary (NEW)" "/api/dashboard/summary" "GET" "\"customers\":"

# Test 5: OCR Status (NEW)
test_endpoint "OCR Status (NEW)" "/api/bill/ocr-status" "GET" "\"status\": \"ready\""

echo ""
echo "2️⃣ 测试CORS配置"
echo "------------------------------------------------------"

echo -n "测试 CORS Headers... "
cors_response=$(curl -s -I -H "Origin: ${MINIMAX_ORIGIN}" "${BASE_URL}/api/customers" 2>&1 | grep -i "access-control-allow-origin")

if echo "$cors_response" | grep -q "$MINIMAX_ORIGIN"; then
    echo -e "${GREEN}✅ PASS${NC}"
    echo "  Origin: $MINIMAX_ORIGIN"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "  响应: $cors_response"
    ((FAIL++))
fi

echo ""
echo "3️⃣ 测试数据返回（真实数据验证）"
echo "------------------------------------------------------"

# Test: Dashboard Summary returns non-zero data
echo -n "测试 真实数据返回... "
summary_data=$(curl -s "${BASE_URL}/api/dashboard/summary")
customers=$(echo "$summary_data" | python3 -c "import sys,json; print(json.load(sys.stdin).get('summary',{}).get('customers', 0))" 2>/dev/null)

if [ "$customers" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    echo "  客户数: $customers (非零)"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "  客户数: $customers"
    ((FAIL++))
fi

echo ""
echo "4️⃣ 测试API响应格式"
echo "------------------------------------------------------"

# Test: JSON Format
echo -n "测试 JSON格式... "
json_test=$(curl -s "${BASE_URL}/api/customers" | python3 -c "import sys,json; json.load(sys.stdin); print('valid')" 2>/dev/null)

if [ "$json_test" == "valid" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAIL++))
fi

echo ""
echo "======================================================"
echo "📊 测试结果总结"
echo "======================================================"
echo ""
echo -e "${GREEN}通过: $PASS${NC}"
echo -e "${RED}失败: $FAIL${NC}"
echo ""

TOTAL=$((PASS + FAIL))
if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！系统就绪！${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  有 $FAIL 个测试失败，需要修复${NC}"
    exit 1
fi
