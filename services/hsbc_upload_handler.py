"""
HSBC Statement Upload Handler with Smart Detection
处理HSBC账单上传，智能检测PDF类型并提供用户引导
"""
import pdfplumber
from parsers.hsbc_parser import HSBCParser
from parsers.hsbc_ocr_parser import HSBCOCRParser

class HSBCUploadHandler:
    """HSBC账单上传智能处理器"""
    
    @staticmethod
    def detect_pdf_type(pdf_path):
        """
        检测PDF类型
        返回: 'text' (文本PDF) 或 'scanned' (扫描PDF)
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # 检查前两页的文本内容
                text_length = 0
                for i, page in enumerate(pdf.pages[:2]):
                    text = page.extract_text()
                    if text:
                        text_length += len(text)
                
                # 如果前两页有超过100个字符，认为是文本PDF
                if text_length > 100:
                    return 'text'
                else:
                    return 'scanned'
        except:
            return 'unknown'
    
    @staticmethod
    def parse_with_guidance(pdf_path):
        """
        智能解析HSBC账单，提供用户引导
        
        返回格式:
        {
            'status': 'success' | 'needs_conversion' | 'error',
            'pdf_type': 'text' | 'scanned' | 'unknown',
            'result': 解析结果 (如果成功),
            'user_message': 用户提示信息,
            'solution_steps': 解决步骤 (如果需要)
        }
        """
        # 1. 检测PDF类型
        pdf_type = HSBCUploadHandler.detect_pdf_type(pdf_path)
        
        # 2. 根据类型处理
        if pdf_type == 'text':
            # 文本PDF - 直接解析
            try:
                parser = HSBCParser()
                result = parser.parse_statement(pdf_path)
                
                return {
                    'status': 'success',
                    'pdf_type': 'text',
                    'result': result,
                    'user_message': f'✅ HSBC账单解析成功！已识别 {len(result["transactions"])} 笔交易。',
                    'solution_steps': None
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'pdf_type': 'text',
                    'result': None,
                    'user_message': f'❌ 账单解析失败：{str(e)}',
                    'solution_steps': None
                }
        
        elif pdf_type == 'scanned':
            # 扫描PDF - 需要转换
            return {
                'status': 'needs_conversion',
                'pdf_type': 'scanned',
                'result': None,
                'user_message': '⚠️ 检测到HSBC扫描版PDF账单',
                'solution_steps': [
                    {
                        'step': 1,
                        'title': '为什么需要转换？',
                        'description': 'HSBC扫描版PDF是图片格式，系统需要文本格式才能准确提取交易记录。'
                    },
                    {
                        'step': 2,
                        'title': '简单转换方法（1分钟完成）',
                        'description': '使用Microsoft Word或WPS打开PDF → 另存为PDF → 重新上传',
                        'detailed_steps': [
                            '1. 右键点击PDF文件 → 选择"用Word打开"',
                            '2. Word会自动转换（等待几秒）',
                            '3. 点击"文件" → "另存为PDF"',
                            '4. 将转换后的PDF重新上传到系统'
                        ]
                    },
                    {
                        'step': 3,
                        'title': '或从HSBC网银重新下载',
                        'description': '登录HSBC网银 → 选择"可搜索PDF"格式下载账单'
                    }
                ]
            }
        
        else:
            # 未知格式
            return {
                'status': 'error',
                'pdf_type': 'unknown',
                'result': None,
                'user_message': '❌ 无法识别的PDF格式',
                'solution_steps': None
            }
    
    @staticmethod
    def get_user_friendly_message(upload_result):
        """生成用户友好的提示消息（HTML格式）"""
        
        if upload_result['status'] == 'success':
            return f'''
            <div class="alert alert-success">
                <i class="bi bi-check-circle-fill"></i>
                <strong>{upload_result['user_message']}</strong>
            </div>
            '''
        
        elif upload_result['status'] == 'needs_conversion':
            steps_html = ''
            for step_info in upload_result['solution_steps']:
                detailed = ''
                if 'detailed_steps' in step_info:
                    detailed = '<ul class="mt-2 mb-0">'
                    for detail in step_info['detailed_steps']:
                        detailed += f'<li>{detail}</li>'
                    detailed += '</ul>'
                
                steps_html += f'''
                <div class="conversion-step mb-3">
                    <strong>步骤 {step_info['step']}: {step_info['title']}</strong>
                    <p class="mb-1">{step_info['description']}</p>
                    {detailed}
                </div>
                '''
            
            return f'''
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle-fill"></i>
                <strong>{upload_result['user_message']}</strong>
                
                <div class="mt-3">
                    <p class="mb-2"><strong>💡 解决方法很简单：</strong></p>
                    {steps_html}
                    
                    <div class="alert alert-info mt-3">
                        <i class="bi bi-info-circle"></i>
                        <strong>温馨提示：</strong>转换后的PDF可永久使用，只需转换一次！
                    </div>
                </div>
            </div>
            '''
        
        else:
            return f'''
            <div class="alert alert-danger">
                <i class="bi bi-x-circle-fill"></i>
                <strong>{upload_result['user_message']}</strong>
                <p class="mt-2">请联系技术支持获取帮助。</p>
            </div>
            '''
