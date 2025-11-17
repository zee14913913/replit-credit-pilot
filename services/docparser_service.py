"""
DocParser云端PDF解析服务
用途：自动调用DocParser API解析银行对账单PDF
"""
import os
import requests
import logging
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class DocParserService:
    """DocParser API客户端"""
    
    BASE_URL = "https://api.docparser.com/v1"
    
    def __init__(self, api_key: Optional[str] = None, parser_id: Optional[str] = None):
        """
        初始化DocParser服务
        
        Args:
            api_key: DocParser API密钥（如不提供则从环境变量读取）
            parser_id: Parser ID（如不提供则从环境变量读取）
        """
        self.api_key = api_key or os.getenv('DOCPARSER_API_KEY')
        self.parser_id = parser_id or os.getenv('DOCPARSER_PARSER_ID')
        
        if not self.api_key:
            raise ValueError("DocParser API Key未配置！请设置环境变量 DOCPARSER_API_KEY")
        
        if not self.parser_id:
            raise ValueError("DocParser Parser ID未配置！请设置环境变量 DOCPARSER_PARSER_ID")
        
        self.session = requests.Session()
        self.session.auth = (self.api_key, '')
    
    def ping(self) -> bool:
        """
        测试API连接
        
        Returns:
            bool: 连接成功返回True
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/ping")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"DocParser ping失败: {e}")
            return False
    
    def list_parsers(self) -> List[Dict]:
        """
        列出所有可用的Parser
        
        Returns:
            List[Dict]: Parser列表
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/parsers")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取Parser列表失败: {e}")
            return []
    
    def upload_document(self, file_path: str, remote_id: Optional[str] = None) -> Dict:
        """
        上传PDF文档到DocParser进行解析
        
        Args:
            file_path: PDF文件路径
            remote_id: 可选的远程ID（用于追踪文档）
        
        Returns:
            Dict: 上传响应，包含document_id等信息
        """
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            if not file_path_obj.suffix.lower() == '.pdf':
                raise ValueError(f"仅支持PDF文件，当前文件: {file_path_obj.suffix}")
            
            logger.info(f"正在上传PDF到DocParser: {file_path_obj.name}")
            
            with open(file_path, 'rb') as pdf_file:
                files = {'file': (file_path_obj.name, pdf_file, 'application/pdf')}
                data = {}
                
                if remote_id:
                    data['remote_id'] = remote_id
                
                url = f"{self.BASE_URL}/document/upload/{self.parser_id}"
                response = self.session.post(url, files=files, data=data)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"✅ 上传成功！Document ID: {result.get('id')}, "
                          f"配额剩余: {result.get('quota_left', 'N/A')}")
                
                return result
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ DocParser API请求失败: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ 上传文档失败: {e}")
            raise
    
    def get_results(self, document_id: str, format: str = 'object') -> Dict:
        """
        获取已解析的文档结果
        
        Args:
            document_id: 文档ID（从upload_document返回）
            format: 结果格式（object/xlsx/csv）
        
        Returns:
            Dict: 解析结果
        """
        try:
            url = f"{self.BASE_URL}/results/{self.parser_id}/{document_id}"
            params = {'format': format}
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"获取解析结果失败: {e}")
            raise
    
    def parse_pdf_sync(self, file_path: str, remote_id: Optional[str] = None, 
                       max_wait_seconds: int = 60) -> Dict:
        """
        同步解析PDF（上传后等待解析完成）
        
        Args:
            file_path: PDF文件路径
            remote_id: 可选的远程ID
            max_wait_seconds: 最大等待时间（秒）
        
        Returns:
            Dict: 解析结果
        """
        import time
        
        upload_result = self.upload_document(file_path, remote_id)
        document_id = upload_result.get('id')
        
        if not document_id:
            raise ValueError("上传成功但未返回document_id")
        
        logger.info(f"等待DocParser解析文档 {document_id}...")
        
        wait_time = 0
        interval = 2
        
        while wait_time < max_wait_seconds:
            try:
                result = self.get_results(document_id)
                
                if result:
                    logger.info(f"✅ 解析完成！耗时 {wait_time}秒")
                    return result
                    
            except Exception as e:
                logger.debug(f"等待中... ({wait_time}s)")
            
            time.sleep(interval)
            wait_time += interval
        
        raise TimeoutError(f"解析超时（{max_wait_seconds}秒）")
    
    def delete_document(self, document_id: str) -> bool:
        """
        删除已上传的文档
        
        Args:
            document_id: 文档ID
        
        Returns:
            bool: 成功返回True
        """
        try:
            url = f"{self.BASE_URL}/document/delete/{self.parser_id}/{document_id}"
            response = self.session.delete(url)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False


def test_docparser_connection():
    """测试DocParser连接"""
    try:
        service = DocParserService()
        
        print("="*80)
        print("DocParser连接测试")
        print("="*80)
        
        if service.api_key:
            print(f"\n✅ API Key: {service.api_key[:10]}***")
        print(f"✅ Parser ID: {service.parser_id}")
        
        if service.ping():
            print("\n✅ API连接成功！")
        else:
            print("\n❌ API连接失败！")
            return False
        
        parsers = service.list_parsers()
        print(f"\n可用Parser数量: {len(parsers)}")
        
        if parsers:
            for parser in parsers:
                print(f"  - {parser.get('label')} (ID: {parser.get('id')})")
        
        print("\n" + "="*80)
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


if __name__ == '__main__':
    test_docparser_connection()
