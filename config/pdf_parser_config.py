"""
PDF解析器配置 - INFINITE GZ文件处理强制规范
============================================

本配置文件定义PDF账单文件的解析优先级和强制规则。

核心原则：
- VBA客户端解析是主要方式（准确度高、成本低）
- OCR/Python解析仅作为备用（仅在VBA不可用时使用）
"""

# ============================================================
# 解析器优先级配置（强制规则）
# ============================================================

class ParserPriority:
    """PDF解析器优先级枚举"""
    VBA_ONLY = "vba_only"           # 强制仅VBA（推荐）
    VBA_PRIMARY = "vba_primary"     # VBA优先，失败后OCR
    OCR_BACKUP = "ocr_backup"       # OCR备用（仅手动触发）
    
    
# ============================================================
# 全局配置
# ============================================================

# 当前强制执行的解析策略
PARSER_MODE = ParserPriority.VBA_ONLY

# 允许的上传方式
ALLOWED_UPLOAD_METHODS = {
    'vba_json': True,           # ✅ VBA解析后的JSON上传（主要方式）
    'vba_batch': True,          # ✅ VBA批量JSON上传
    'direct_pdf_upload': True,  # ✅ 允许直接上传PDF文件（保存文件）
    'auto_parse_pdf': False,    # ❌ 禁止自动解析PDF（必须用VBA）
    'ocr_manual': True,         # ✅ 允许管理员手动触发OCR（备用）
}

# VBA API端点
VBA_ENDPOINTS = {
    'single': '/api/upload/vba-json',      # 单文件上传
    'batch': '/api/upload/vba-batch',      # 批量上传
}

# PDF处理工作流程
PDF_WORKFLOW = """
标准PDF处理流程（强制执行）:
==========================

1. 客户端（Windows Excel + VBA）:
   - 接收PDF账单文件
   - VBA解析PDF → Excel数据
   - 标准化为JSON格式
   
2. 上传到Replit:
   - 调用VBA API端点
   - 上传标准化JSON
   
3. Replit服务器:
   - 接收JSON数据
   - 验证数据完整性
   - 入库SQLite数据库
   
4. OCR备用方案（仅手动）:
   - 仅在VBA不可用时
   - 管理员手动触发
   - 使用pytesseract OCR识别
"""


# ============================================================
# 禁止性规定
# ============================================================

FORBIDDEN_OPERATIONS = [
    "自动解析PDF（Python/OCR）",
    "跳过VBA直接解析并入库",
    "上传后自动触发解析",
]

ALLOWED_OPERATIONS = [
    "上传PDF文件并保存到正确位置",
    "使用VBA客户端解析PDF生成JSON",
    "VBA JSON上传入库（推荐）",
    "VBA批量JSON上传",
    "管理员手动OCR（备用）",
]


# ============================================================
# 错误消息模板
# ============================================================

ERROR_MESSAGES = {
    'pdf_upload_disabled': {
        'zh': '❌ PDF直接上传已禁用。请使用VBA客户端解析后上传JSON数据。',
        'en': '❌ Direct PDF upload is disabled. Please use VBA client to parse and upload JSON data.'
    },
    'vba_required': {
        'zh': '⚠️ 系统强制要求使用VBA解析。OCR仅作备用。',
        'en': '⚠️ VBA parsing is mandatory. OCR is backup only.'
    },
    'use_vba_endpoint': {
        'zh': f'✅ 请使用VBA端点: {VBA_ENDPOINTS["single"]} 或 {VBA_ENDPOINTS["batch"]}',
        'en': f'✅ Please use VBA endpoints: {VBA_ENDPOINTS["single"]} or {VBA_ENDPOINTS["batch"]}'
    }
}


# ============================================================
# 验证函数
# ============================================================

def is_vba_upload_allowed() -> bool:
    """检查VBA上传是否允许"""
    return ALLOWED_UPLOAD_METHODS.get('vba_json', False)


def is_pdf_upload_allowed() -> bool:
    """检查PDF文件上传是否允许（仅保存文件，不自动解析）"""
    return ALLOWED_UPLOAD_METHODS.get('direct_pdf_upload', True)


def is_auto_parse_allowed() -> bool:
    """检查是否允许自动解析PDF（禁止自动解析，必须用VBA）"""
    return ALLOWED_UPLOAD_METHODS.get('auto_parse_pdf', False)


def is_ocr_manual_allowed() -> bool:
    """检查手动OCR是否允许"""
    return ALLOWED_UPLOAD_METHODS.get('ocr_manual', False)


def get_upload_guidance(lang='zh') -> str:
    """获取上传指引"""
    if lang == 'zh':
        return f"""
📋 PDF账单处理指引
==================

✅ 推荐方式（VBA）:
  1. 使用Windows Excel + VBA解析PDF
  2. 生成标准JSON格式
  3. 上传到: {VBA_ENDPOINTS['single']}
  4. 批量上传: {VBA_ENDPOINTS['batch']}

❌ 禁止方式:
  - 直接上传PDF自动解析
  - 跳过VBA客户端

🔄 备用方式（仅管理员）:
  - 手动触发OCR识别
  - 仅在VBA不可用时使用

当前模式: {PARSER_MODE}
"""
    else:
        return f"""
📋 PDF Statement Processing Guide
==================================

✅ Recommended (VBA):
  1. Use Windows Excel + VBA to parse PDF
  2. Generate standard JSON format
  3. Upload to: {VBA_ENDPOINTS['single']}
  4. Batch upload: {VBA_ENDPOINTS['batch']}

❌ Forbidden:
  - Direct PDF upload with auto-parsing
  - Skip VBA client

🔄 Backup (Admin only):
  - Manual OCR trigger
  - Only when VBA unavailable

Current mode: {PARSER_MODE}
"""


# ============================================================
# 配置验证
# ============================================================

def validate_config():
    """验证配置的一致性"""
    errors = []
    
    # 检查：如果VBA_ONLY模式，直接PDF上传必须禁用
    if PARSER_MODE == ParserPriority.VBA_ONLY:
        if ALLOWED_UPLOAD_METHODS.get('direct_pdf', False):
            errors.append("VBA_ONLY模式下direct_pdf必须为False")
    
    # 检查：VBA端点必须启用
    if not ALLOWED_UPLOAD_METHODS.get('vba_json', False):
        errors.append("VBA上传必须启用")
    
    if errors:
        raise ValueError(f"配置错误: {'; '.join(errors)}")
    
    return True


# 启动时验证配置
validate_config()


# ============================================================
# 使用示例
# ============================================================

"""
在Flask路由中使用:

from config.pdf_parser_config import (
    PARSER_MODE, 
    is_direct_pdf_allowed, 
    ERROR_MESSAGES,
    get_upload_guidance
)

@app.route('/upload/pdf', methods=['POST'])
def upload_pdf():
    # 检查是否允许直接PDF上传
    if not is_direct_pdf_allowed():
        return jsonify({
            'success': False,
            'message': ERROR_MESSAGES['pdf_upload_disabled']['zh'],
            'guidance': get_upload_guidance('zh')
        }), 403
    
    # ... 后续处理
"""
