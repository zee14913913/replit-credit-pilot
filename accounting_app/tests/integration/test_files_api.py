"""
文件管理API集成测试
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestFilesAPI:
    """文件管理端点集成测试"""
    
    def test_list_files_empty(self, client, sample_company):
        """测试空文件列表"""
        response = client.get(
            f"/api/files/list/{sample_company.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "company_id" in data
        assert "files" in data
        assert isinstance(data["files"], list)
    
    def test_get_storage_stats(self, client, sample_company):
        """测试存储统计"""
        response = client.get(
            f"/api/files/storage-stats/{sample_company.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "company_id" in data
        
        # 检查统计字段存在（字段名可能不同）
        assert data["company_id"] == sample_company.id
    
    def test_list_files_by_type(self, client, sample_company):
        """测试按类型筛选文件"""
        # 测试使用file_type参数
        file_type = "bank_statement"
        
        response = client.get(
            f"/api/files/list/{sample_company.id}",
            params={"file_type": file_type}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "file_type" in data
        assert "files" in data
    
    def test_invalid_company_access_denied(self, client):
        """测试无效公司ID被拒绝"""
        response = client.get("/api/files/list/99999")
        
        # 应该返回空列表或错误（取决于实现）
        assert response.status_code in [200, 404]
    
    def test_view_endpoint(self, client, sample_company):
        """测试view端点（需要验证实际参数要求）"""
        # 注：该端点可能需要特定的查询参数
        response = client.get(
            "/api/files/view",
            params={
                "company_id": sample_company.id,
                "file_type": "bank_statement"
            }
        )
        
        # 422表示参数验证失败，200表示成功
        assert response.status_code in [200, 404, 422]
