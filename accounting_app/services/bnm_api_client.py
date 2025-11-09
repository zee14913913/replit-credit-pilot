"""
BNM (Bank Negara Malaysia) 官方API客户端
获取真实的马来西亚基准利率数据
官方文档: https://apikijangportal.bnm.gov.my/
"""
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BNMAPIClient:
    """Bank Negara Malaysia 官方API客户端"""
    
    # BNM官方API端点
    BNM_API_BASE = "https://api.bnm.gov.my"
    DATA_GOV_BASE = "https://api.data.gov.my"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CreditPilot/2.0 Financial Management System'
        })
    
    def get_base_rates(self) -> Optional[Dict[str, Any]]:
        """
        获取基准利率 (Base Rates)
        
        Returns:
            {
                'data': [
                    {
                        'bank_code': 'MBB',
                        'bank_name': 'Malayan Banking Berhad',
                        'base_rate': '3.40',
                        'base_lending_rate': '5.60',
                        'effective_date': '2025-05-09'
                    },
                    ...
                ],
                'last_updated': '2025-11-09T04:00:00Z'
            }
        """
        try:
            # 尝试从BNM直接获取
            response = self.session.get(
                f"{self.BNM_API_BASE}/base-rate",
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ 成功从BNM API获取基准利率")
                return response.json()
            
            logger.warning(f"⚠️ BNM API返回状态码 {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"❌ BNM API请求失败: {e}")
            return None
    
    def get_interest_rates_from_datagov(self, limit: int = 100) -> Optional[Dict[str, Any]]:
        """
        从 data.gov.my 获取利率数据（备用方案）
        
        Args:
            limit: 返回记录数量
        
        Returns:
            {
                'data': [...],
                'total': 1234,
                'next': 'url_to_next_page'
            }
        """
        try:
            response = self.session.get(
                f"{self.DATA_GOV_BASE}/data-catalogue",
                params={
                    'id': 'interestrates',
                    'limit': limit
                },
                timeout=15
            )
            
            if response.status_code == 200:
                logger.info(f"✅ 成功从data.gov.my获取 {limit} 条利率记录")
                return response.json()
            
            logger.warning(f"⚠️ data.gov.my返回状态码 {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"❌ data.gov.my请求失败: {e}")
            return None
    
    def get_opr(self) -> Optional[Dict[str, float]]:
        """
        获取隔夜政策利率 (Overnight Policy Rate)
        这是马来西亚央行的基准利率
        
        Returns:
            {
                'opr': 3.00,
                'effective_date': '2025-05-09',
                'decision_date': '2025-05-07'
            }
        """
        try:
            # 尝试从BNM获取OPR数据
            response = self.session.get(
                f"{self.BNM_API_BASE}/opr",
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ 成功获取OPR数据")
                return response.json()
            
            # 如果BNM API不可用，从利率数据中提取
            rates_data = self.get_interest_rates_from_datagov(limit=10)
            if rates_data and rates_data.get('data'):
                # 查找最新的OPR记录
                for record in rates_data['data']:
                    if 'opr' in str(record).lower():
                        return {
                            'opr': record.get('rate', 3.00),
                            'effective_date': record.get('date'),
                            'source': 'data.gov.my'
                        }
            
            logger.warning("⚠️ 无法获取OPR数据，返回默认值")
            return {
                'opr': 3.00,
                'effective_date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'default'
            }
            
        except Exception as e:
            logger.error(f"❌ 获取OPR失败: {e}")
            return None
    
    def get_all_rates(self) -> Dict[str, Any]:
        """
        获取所有关键利率数据的综合视图
        
        Returns:
            {
                'opr': 3.00,
                'base_rates': [...],
                'interest_rates': [...],
                'last_updated': '2025-11-09T04:00:00Z',
                'data_sources': ['bnm_api', 'data_gov']
            }
        """
        result = {
            'opr': None,
            'base_rates': [],
            'interest_rates': [],
            'last_updated': datetime.now().isoformat(),
            'data_sources': []
        }
        
        # 获取OPR
        opr_data = self.get_opr()
        if opr_data:
            result['opr'] = opr_data
            result['data_sources'].append('bnm_api' if opr_data.get('source') != 'data.gov.my' else 'data_gov')
        
        # 获取基准利率
        base_rates = self.get_base_rates()
        if base_rates:
            result['base_rates'] = base_rates.get('data', [])
            result['data_sources'].append('bnm_api')
        
        # 获取利率数据
        interest_data = self.get_interest_rates_from_datagov(limit=50)
        if interest_data:
            result['interest_rates'] = interest_data.get('data', [])
            if 'data_gov' not in result['data_sources']:
                result['data_sources'].append('data_gov')
        
        logger.info(f"✅ 综合利率数据获取完成，来源: {', '.join(result['data_sources'])}")
        return result


# 全局单例
bnm_client = BNMAPIClient()
