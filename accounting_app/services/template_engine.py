"""
TemplateEngine - CSV导出模板引擎
负责应用模板配置生成符合不同会计软件格式的CSV文件
"""
import logging
import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..models import ExportTemplate

logger = logging.getLogger(__name__)


class TemplateEngine:
    """
    模板引擎 - 核心CSV生成逻辑
    
    职责：
    1. 应用模板配置生成CSV
    2. 验证模板配置有效性
    3. 处理字段映射和格式转换
    4. 更新模板使用统计
    """
    
    def __init__(self, db: Session, company_id: int):
        self.db = db
        self.company_id = company_id
        self._templates_cache: Dict[str, List[ExportTemplate]] = {}
    
    def clear_cache(self, software_name: Optional[str] = None):
        """清除缓存"""
        if software_name is None:
            self._templates_cache.clear()
            logger.debug(f"✅ 清除所有模板缓存 (Company: {self.company_id})")
        elif software_name in self._templates_cache:
            del self._templates_cache[software_name]
            logger.debug(f"✅ 清除模板缓存: {software_name} (Company: {self.company_id})")
    
    def get_all_templates(
        self, 
        software_name: Optional[str] = None,
        export_type: Optional[str] = None,
        force_refresh: bool = False
    ) -> List[ExportTemplate]:
        """
        获取所有启用的模板
        
        Args:
            software_name: 过滤软件名称
            export_type: 过滤导出类型
            force_refresh: 强制刷新缓存
        """
        cache_key = f"{software_name}_{export_type}"
        
        if cache_key not in self._templates_cache or force_refresh:
            query = self.db.query(ExportTemplate).filter(
                ExportTemplate.company_id == self.company_id,
                ExportTemplate.is_active == True
            )
            
            if software_name:
                query = query.filter(ExportTemplate.software_name == software_name)
            if export_type:
                query = query.filter(ExportTemplate.export_type == export_type)
            
            self._templates_cache[cache_key] = query.all()
        
        return self._templates_cache[cache_key]
    
    def get_default_template(self, software_name: str, export_type: str) -> Optional[ExportTemplate]:
        """获取默认模板"""
        return self.db.query(ExportTemplate).filter(
            ExportTemplate.company_id == self.company_id,
            ExportTemplate.software_name == software_name,
            ExportTemplate.export_type == export_type,
            ExportTemplate.is_default == True,
            ExportTemplate.is_active == True
        ).first()
    
    def validate_template(self, template: ExportTemplate) -> tuple[bool, Optional[str]]:
        """
        验证模板配置
        
        Returns:
            (is_valid, error_message)
        """
        # 验证column_mappings格式
        if not isinstance(template.column_mappings, dict):
            return False, "column_mappings must be a dictionary"
        
        if not template.column_mappings:
            return False, "column_mappings cannot be empty"
        
        # 验证必需字段
        if not template.template_name:
            return False, "template_name is required"
        
        if not template.software_name:
            return False, "software_name is required"
        
        if not template.export_type:
            return False, "export_type is required"
        
        return True, None
    
    def apply_template(
        self,
        template: ExportTemplate,
        data: List[Dict[str, Any]]
    ) -> str:
        """
        应用模板生成CSV
        
        Args:
            template: 导出模板
            data: 要导出的数据（字典列表）
        
        Returns:
            CSV字符串
        """
        if not data:
            return ""
        
        output = io.StringIO()
        
        # 获取列映射
        column_mappings = template.column_mappings
        
        # 提取CSV列名（按映射顺序）
        csv_columns = list(column_mappings.keys())
        
        # 创建CSV writer
        writer = csv.DictWriter(
            output,
            fieldnames=csv_columns,
            delimiter=template.delimiter,
            quoting=csv.QUOTE_MINIMAL
        )
        
        # 写入表头
        if template.include_header:
            writer.writeheader()
        
        # 写入数据行
        for row in data:
            csv_row = {}
            for csv_col, source_field in column_mappings.items():
                # 从原始数据获取值
                value = row.get(source_field, "")
                
                # 格式化值
                formatted_value = self._format_value(
                    value,
                    template.date_format,
                    template.decimal_places
                )
                
                csv_row[csv_col] = formatted_value
            
            writer.writerow(csv_row)
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content
    
    def _format_value(
        self,
        value: Any,
        date_format: str,
        decimal_places: int
    ) -> str:
        """格式化单个值"""
        if value is None or value == "":
            return ""
        
        # 日期格式化
        if isinstance(value, datetime):
            # 转换Pythonic日期格式（如YYYY-MM-DD）
            format_str = date_format.replace('YYYY', '%Y').replace('MM', '%m').replace('DD', '%d')
            return value.strftime(format_str)
        
        # 数字格式化
        if isinstance(value, (int, float)):
            if decimal_places == 0:
                return str(int(value))
            else:
                return f"{value:.{decimal_places}f}"
        
        # 其他类型转字符串
        return str(value)
    
    def update_usage_stats(self, template_id: int):
        """更新模板使用统计"""
        template = self.db.query(ExportTemplate).filter(
            ExportTemplate.id == template_id,
            ExportTemplate.company_id == self.company_id
        ).first()
        
        if template:
            template.usage_count += 1
            template.last_used_at = datetime.now()
            self.db.commit()
            logger.info(f"✅ 模板使用统计已更新: {template.template_name} (count: {template.usage_count})")
    
    def test_template(
        self,
        template: ExportTemplate,
        sample_data: List[Dict[str, Any]],
        preview_rows: int = 5
    ) -> tuple[bool, str, Optional[str]]:
        """
        测试模板
        
        Returns:
            (success, csv_preview, error_message)
        """
        try:
            # 限制预览行数
            limited_data = sample_data[:preview_rows]
            
            # 生成CSV
            csv_content = self.apply_template(template, limited_data)
            
            return True, csv_content, None
            
        except Exception as e:
            logger.error(f"❌ 模板测试失败: {e}")
            return False, "", str(e)
