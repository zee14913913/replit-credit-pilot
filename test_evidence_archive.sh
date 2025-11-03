#!/bin/bash
# Evidence Archive System - 快速测试脚本

echo "🔐 Evidence Archive System - 快速测试"
echo "======================================"
echo ""

# 1. 检查证据包目录
echo "📦 1. 检查证据包目录状态..."
if [ -d "evidence_bundles" ]; then
    echo "✅ evidence_bundles目录存在"
    ls -lh evidence_bundles/
    echo ""
    echo "📊 证据包数量: $(ls -1 evidence_bundles/*.zip 2>/dev/null | wc -l)"
else
    echo "❌ evidence_bundles目录不存在"
fi
echo ""

# 2. 检查API端点（需要先登录）
echo "🌐 2. 检查Evidence Archive API端点..."
echo "提示：需要以Admin身份登录后才能访问"
echo "- GET /admin/evidence - 管理页面"
echo "- GET /downloads/evidence/list - 列出证据包"
echo "- GET /downloads/evidence/latest - 下载最新"
echo "- GET /downloads/evidence/file/<filename> - 下载指定文件"
echo "- POST /downloads/evidence/delete - 删除证据包"
echo "- POST /tasks/evidence/rotate - 执行轮转"
echo ""

# 3. 检查环境变量
echo "⚙️  3. 检查环境变量配置..."
echo "EVIDENCE_ROTATION_DAYS: ${EVIDENCE_ROTATION_DAYS:-30 (默认)}"
echo "EVIDENCE_KEEP_MONTHLY: ${EVIDENCE_KEEP_MONTHLY:-1 (默认)}"
echo "TASK_SECRET_TOKEN: ${TASK_SECRET_TOKEN:-dev-default-token (默认)}"
echo ""

# 4. 显示证据包详情
echo "📋 4. 证据包详细信息..."
for file in evidence_bundles/*.zip; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        filesize=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        sha256sum=$(sha256sum "$file" 2>/dev/null | awk '{print $1}' || shasum -a 256 "$file" 2>/dev/null | awk '{print $1}')
        
        echo "---"
        echo "文件名: $filename"
        echo "大小: $(numfmt --to=iec-i --suffix=B $filesize 2>/dev/null || echo $filesize bytes)"
        echo "SHA256: $sha256sum"
        echo "修改时间: $(stat -f%Sm "$file" 2>/dev/null || stat -c%y "$file" 2>/dev/null)"
    fi
done
echo ""

# 5. 测试提示
echo "🧪 5. 手动测试步骤..."
echo "1️⃣  访问 http://your-replit-url/admin/evidence"
echo "2️⃣  以Admin身份登录"
echo "3️⃣  查看证据包列表"
echo "4️⃣  点击 'Download Latest' 测试下载"
echo "5️⃣  点击 'Run Rotation Now' 测试轮转（需输入TASK_SECRET_TOKEN）"
echo "6️⃣  点击删除按钮测试删除功能"
echo ""

echo "✅ 测试脚本执行完毕"
echo "📖 详细测试指南请查看: EVIDENCE_ARCHIVE_TEST_GUIDE.md"

