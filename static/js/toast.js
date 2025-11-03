/**
 * 全局Toast通知组件
 * 统一的成功/失败/警告提示
 */

class ToastManager {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // 创建Toast容器 - 确保document.body已加载
        if (!document.body) {
            // If body doesn't exist yet, wait for DOM ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.init());
                return;
            }
        }
        
        if (!document.getElementById('toast-container')) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                min-width: 300px;
                max-width: 500px;
            `;
            document.body.appendChild(container);
            this.container = container;
        } else {
            this.container = document.getElementById('toast-container');
        }
    }

    show(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        // 图标映射
        const icons = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        };
        
        // 颜色映射
        const colors = {
            'success': '#FF007F',  // Hot Pink
            'error': '#ff0000',
            'warning': '#ff9900',
            'info': '#322446'  // Dark Purple
        };
        
        toast.innerHTML = `
            <div style="
                background: ${colors[type]};
                color: white;
                padding: 16px 20px;
                border-radius: 8px;
                margin-bottom: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.4);
                display: flex;
                align-items: center;
                gap: 12px;
                animation: slideIn 0.3s ease-out;
            ">
                <span style="font-size: 20px;">${icons[type]}</span>
                <div style="flex: 1; font-size: 14px; line-height: 1.4;">${message}</div>
                <button onclick="this.closest('.toast').remove()" style="
                    background: none;
                    border: none;
                    color: white;
                    font-size: 20px;
                    cursor: pointer;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                ">×</button>
            </div>
        `;
        
        this.container.appendChild(toast);
        
        // 自动关闭
        if (duration > 0) {
            setTimeout(() => {
                toast.style.animation = 'slideOut 0.3s ease-in';
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
        
        return toast;
    }

    success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 7000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration = 6000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    }
}

// 全局单例
window.Toast = new ToastManager();

// 添加动画CSS
if (!document.getElementById('toast-styles')) {
    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}
