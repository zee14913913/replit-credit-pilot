"""
CORS配置 - 允许MiniMax前端和Replit前端访问
用于跨域API请求支持
"""
from flask_cors import CORS

def configure_cors(app):
    """配置CORS设置"""
    
    # 允许的域名列表
    allowed_origins = [
        # MiniMax前端（客户入口）
        "https://ynqoo4ipbuar.space.minimax.io",  # 当前Dashboard
        "https://iz6ki2qe01mh.space.minimax.io",  # 之前Dashboard
        
        # Replit前端（内部入口）
        "https://finance-pilot-businessgz.replit.app",
        "https://creditpilot.digital",
        
        # 本地开发
        "http://localhost:3000",
        "http://localhost:5000",
        "http://localhost:5678",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000",
    ]
    
    # 配置CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": [
                "Content-Type", 
                "Authorization", 
                "X-Requested-With",
                "X-Internal-API-Key"
            ],
            "supports_credentials": True,
            "max_age": 86400  # 24小时
        }
    })
    
    print("✅ CORS配置完成")
    print(f"✅ 允许的域名数量: {len(allowed_origins)}")
    
    return app
