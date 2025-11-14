"""
PDF Renderer - PDF渲染器
PHASE 5: 将HTML报告转换为银行级PDF文档
"""
from typing import Dict, Optional
import io
from .report_builder import LoanReportBuilder

# Lazy import WeasyPrint (只在需要时导入)
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


def generate_personal_pdf(
    evaluation_result: Dict,
    customer_data: Dict,
    enriched_data: Optional[Dict] = None
) -> bytes:
    """
    生成个人贷款PDF报告
    
    Args:
        evaluation_result: 风控评估结果
        customer_data: 客户数据
        enriched_data: 数据增强信息
    
    Returns:
        PDF文件字节流
    """
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError(
            "WeasyPrint未安装。请运行: pip install weasyprint"
        )
    
    # 生成HTML报告
    html_content = LoanReportBuilder.build_personal_report(
        evaluation_result=evaluation_result,
        customer_data=customer_data,
        enriched_data=enriched_data
    )
    
    # 转换为PDF
    return _convert_html_to_pdf(html_content)


def generate_sme_pdf(
    evaluation_result: Dict,
    customer_data: Dict,
    enriched_data: Optional[Dict] = None
) -> bytes:
    """
    生成SME贷款PDF报告
    
    Args:
        evaluation_result: 风控评估结果
        customer_data: 企业数据
        enriched_data: 数据增强信息
    
    Returns:
        PDF文件字节流
    """
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError(
            "WeasyPrint未安装。请运行: pip install weasyprint"
        )
    
    # 生成HTML报告
    html_content = LoanReportBuilder.build_sme_report(
        evaluation_result=evaluation_result,
        customer_data=customer_data,
        enriched_data=enriched_data
    )
    
    # 转换为PDF
    return _convert_html_to_pdf(html_content)


def _convert_html_to_pdf(html_content: str) -> bytes:
    """
    将HTML转换为PDF
    
    Args:
        html_content: HTML字符串
    
    Returns:
        PDF字节流
    """
    # 创建PDF样式增强
    pdf_css = CSS(string="""
        @page {
            size: A4;
            margin: 2cm;
            @bottom-right {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10px;
                color: #999;
            }
        }
        
        body {
            font-size: 12pt;
        }
        
        .report-section {
            page-break-inside: avoid;
        }
        
        .report-header {
            page-break-after: avoid;
        }
        
        table {
            page-break-inside: avoid;
        }
        
        /* 打印优化 */
        @media print {
            .no-print {
                display: none;
            }
        }
    """)
    
    # 转换
    html = HTML(string=html_content)
    pdf_bytes = html.write_pdf(stylesheets=[pdf_css])
    
    return pdf_bytes


def save_pdf_to_file(
    pdf_bytes: bytes,
    filename: str
) -> str:
    """
    将PDF保存到文件
    
    Args:
        pdf_bytes: PDF字节流
        filename: 文件名
    
    Returns:
        文件路径
    """
    with open(filename, 'wb') as f:
        f.write(pdf_bytes)
    
    return filename


def get_pdf_stream(pdf_bytes: bytes) -> io.BytesIO:
    """
    获取PDF流对象（用于FastAPI响应）
    
    Args:
        pdf_bytes: PDF字节流
    
    Returns:
        BytesIO对象
    """
    return io.BytesIO(pdf_bytes)
