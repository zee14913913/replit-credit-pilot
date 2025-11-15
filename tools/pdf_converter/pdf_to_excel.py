"""
INFINITE GZ - PDF转Excel自动化工具
===================================
使用Tabula和PDFPlumber将PDF账单转换为Excel格式

功能：
- 自动识别PDF中的表格
- 批量转换多个PDF文件
- 支持信用卡账单和银行流水
- 导出为Excel (.xlsx) 格式

依赖安装：
pip install tabula-py openpyxl pdfplumber pandas

注意：tabula-py需要Java环境
"""

import os
import sys
from typing import List, Dict
import pandas as pd

try:
    import tabula
except ImportError:
    print("错误: 未安装 tabula-py")
    print("请运行: pip install tabula-py")
    sys.exit(1)

try:
    import pdfplumber
except ImportError:
    print("错误: 未安装 pdfplumber")
    print("请运行: pip install pdfplumber")
    sys.exit(1)


class PDFToExcelConverter:
    """PDF转Excel转换器"""
    
    def __init__(self):
        self.supported_banks = [
            'Public Bank',
            'Maybank', 
            'CIMB',
            'RHB',
            'Hong Leong Bank',
            'HSBC',
            'Alliance Bank'
        ]
    
    def convert_single_file(self, pdf_path: str, output_path: str = None, method: str = 'auto') -> str:
        """
        转换单个PDF文件
        
        Args:
            pdf_path: PDF文件路径
            output_path: 输出Excel路径（可选）
            method: 'tabula', 'pdfplumber', or 'auto'
            
        Returns:
            输出文件路径
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        if output_path is None:
            output_path = pdf_path.replace('.pdf', '.xlsx')
        
        print(f"\n处理: {pdf_path}")
        print(f"方法: {method}")
        
        try:
            if method == 'tabula' or method == 'auto':
                # 优先使用Tabula（专门提取表格）
                df_list = tabula.read_pdf(
                    pdf_path,
                    pages='all',
                    multiple_tables=True,
                    pandas_options={'header': None}
                )
                
                if df_list and len(df_list) > 0:
                    # 合并所有表格
                    df = pd.concat(df_list, ignore_index=True)
                    df.to_excel(output_path, index=False, header=False)
                    print(f"✓ Tabula转换成功: {output_path}")
                    return output_path
                elif method == 'auto':
                    print("  Tabula未找到表格，尝试PDFPlumber...")
                else:
                    raise ValueError("Tabula未找到表格")
            
            if method == 'pdfplumber' or method == 'auto':
                # 使用PDFPlumber作为备用
                tables = []
                
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        page_tables = page.extract_tables()
                        
                        if page_tables:
                            for table in page_tables:
                                tables.append(pd.DataFrame(table))
                
                if tables:
                    df = pd.concat(tables, ignore_index=True)
                    df.to_excel(output_path, index=False, header=False)
                    print(f"✓ PDFPlumber转换成功: {output_path}")
                    return output_path
                else:
                    raise ValueError("PDFPlumber未找到表格")
        
        except Exception as e:
            print(f"✗ 转换失败: {e}")
            raise
    
    def convert_batch(self, pdf_folder: str, output_folder: str = None) -> List[str]:
        """
        批量转换文件夹中的所有PDF
        
        Args:
            pdf_folder: PDF文件夹路径
            output_folder: 输出文件夹（可选）
            
        Returns:
            成功转换的文件列表
        """
        if output_folder is None:
            output_folder = pdf_folder
        
        os.makedirs(output_folder, exist_ok=True)
        
        pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
        
        if not pdf_files:
            print(f"错误: 文件夹中没有PDF文件: {pdf_folder}")
            return []
        
        print(f"\n找到 {len(pdf_files)} 个PDF文件")
        print("=" * 80)
        
        converted_files = []
        failed_files = []
        
        for i, pdf_file in enumerate(pdf_files, 1):
            pdf_path = os.path.join(pdf_folder, pdf_file)
            excel_filename = pdf_file.replace('.pdf', '.xlsx')
            output_path = os.path.join(output_folder, excel_filename)
            
            print(f"\n[{i}/{len(pdf_files)}] 转换: {pdf_file}")
            
            try:
                result = self.convert_single_file(pdf_path, output_path)
                converted_files.append(result)
            except Exception as e:
                print(f"  ✗ 失败: {e}")
                failed_files.append(pdf_file)
        
        print("\n" + "=" * 80)
        print(f"✓ 成功: {len(converted_files)} 个文件")
        print(f"✗ 失败: {len(failed_files)} 个文件")
        
        if failed_files:
            print("\n失败文件列表:")
            for f in failed_files:
                print(f"  - {f}")
        
        return converted_files


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PDF账单转Excel工具')
    parser.add_argument('input', help='PDF文件或文件夹路径')
    parser.add_argument('-o', '--output', help='输出Excel文件或文件夹路径')
    parser.add_argument('-m', '--method', 
                        choices=['tabula', 'pdfplumber', 'auto'],
                        default='auto',
                        help='转换方法 (默认: auto)')
    parser.add_argument('-b', '--batch', action='store_true', help='批量处理模式')
    
    args = parser.parse_args()
    
    converter = PDFToExcelConverter()
    
    try:
        if args.batch or os.path.isdir(args.input):
            # 批量转换
            converter.convert_batch(args.input, args.output)
        else:
            # 单文件转换
            converter.convert_single_file(args.input, args.output, args.method)
    
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
