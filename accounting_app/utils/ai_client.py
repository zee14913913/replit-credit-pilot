"""
智能AI客户端工厂
支持多种AI提供商：OpenAI、Perplexity
根据环境变量自动切换
"""
import os
from typing import Optional


class AIClient:
    """
    统一AI客户端接口
    支持OpenAI和Perplexity无缝切换
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        初始化AI客户端
        
        参数:
            provider: AI提供商 ('openai' 或 'perplexity')
                     如果未指定，从环境变量AI_PROVIDER读取，默认perplexity
        """
        self.provider = provider or os.getenv("AI_PROVIDER", "perplexity")
        self.client = None
        self.model = None
        
        if self.provider == "perplexity":
            self._init_perplexity()
        elif self.provider == "openai":
            self._init_openai()
        else:
            raise ValueError(f"不支持的AI提供商: {self.provider}")
    
    def _init_perplexity(self):
        """初始化Perplexity客户端"""
        try:
            from openai import OpenAI
            
            api_key = os.getenv("PERPLEXITY_API_KEY")
            if not api_key:
                raise ValueError("PERPLEXITY_API_KEY未配置")
            
            # Perplexity使用OpenAI兼容API
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.perplexity.ai"
            )
            
            # Perplexity新模型（2025更新）
            # 可选模型:
            # - sonar: 轻量级搜索，127K上下文（推荐财务日报）
            # - sonar-pro: 高级搜索，复杂查询
            # - sonar-reasoning: 快速推理
            # - sonar-reasoning-pro: 高级推理（DeepSeek R1）
            self.model = "sonar"  # 支持实时网络搜索，适合财务数据查询
            
            print(f"✅ 使用Perplexity AI（模型: {self.model}）")
            
        except Exception as e:
            print(f"⚠️ Perplexity初始化失败: {e}")
            print("回退到OpenAI...")
            self._init_openai()
    
    def _init_openai(self):
        """初始化OpenAI客户端"""
        from openai import OpenAI
        
        api_key = os.getenv("AI_INTEGRATIONS_OPENAI_API_KEY")
        base_url = os.getenv("AI_INTEGRATIONS_OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        if not api_key:
            raise ValueError("OpenAI API密钥未配置")
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = "gpt-4o-mini"
        self.provider = "openai"
        
        print(f"✅ 使用OpenAI（模型: {self.model}）")
    
    def chat(self, messages: list, temperature: float = 0.7, max_tokens: int = 800) -> str:
        """
        发送聊天请求
        
        参数:
            messages: OpenAI格式的消息列表
            temperature: 温度参数（0-1）
            max_tokens: 最大返回token数
        
        返回:
            AI生成的文本内容
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            return content.strip()
            
        except Exception as e:
            error_msg = f"AI请求失败 ({self.provider}): {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def generate_completion(self, prompt: str, **kwargs) -> str:
        """
        便捷方法：根据单个提示词生成回复
        
        参数:
            prompt: 用户提示词
            **kwargs: 传递给chat()的其他参数
        
        返回:
            AI生成的文本
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, **kwargs)


# 便捷函数
def get_ai_client(provider: Optional[str] = None) -> AIClient:
    """
    获取AI客户端实例
    
    参数:
        provider: 可选，指定AI提供商
    
    返回:
        AIClient实例
    """
    return AIClient(provider)


# 支持直接调用
if __name__ == "__main__":
    print("🧪 测试AI客户端...")
    
    # 测试Perplexity
    try:
        client = get_ai_client("perplexity")
        response = client.generate_completion("什么是马来西亚的当前基准利率？", max_tokens=200)
        print(f"\n📝 Perplexity回复:\n{response}\n")
    except Exception as e:
        print(f"❌ Perplexity测试失败: {e}")
    
    # 测试OpenAI
    try:
        client = get_ai_client("openai")
        response = client.generate_completion("用一句话解释什么是信用卡使用率", max_tokens=100)
        print(f"\n📝 OpenAI回复:\n{response}\n")
    except Exception as e:
        print(f"❌ OpenAI测试失败: {e}")
