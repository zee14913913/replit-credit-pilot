/**
 * 统一状态标识组件
 * 为所有文件状态提供一致的视觉呈现
 */

const StatusBadge = {
    /**
     * 状态配置 - 严格3色调色板
     */
    config: {
        active: {
            label: '正常',
            labelEn: 'Active',
            color: '#FF007F',  // Hot Pink
            icon: '✓',
            bgColor: 'rgba(255, 0, 127, 0.15)',
            borderColor: 'rgba(255, 0, 127, 0.4)'
        },
        processing: {
            label: '处理中',
            labelEn: 'Processing',
            color: '#FF007F',  // Hot Pink
            icon: '⟳',
            bgColor: 'rgba(255, 0, 127, 0.15)',
            borderColor: 'rgba(255, 0, 127, 0.4)'
        },
        failed: {
            label: '失败',
            labelEn: 'Failed',
            color: '#FF007F',  // Hot Pink（错误也用主色，通过图标区分）
            icon: '✕',
            bgColor: 'rgba(255, 0, 127, 0.15)',
            borderColor: 'rgba(255, 0, 127, 0.4)'
        },
        archived: {
            label: '已归档',
            labelEn: 'Archived',
            color: '#322446',  // Dark Purple
            icon: '📦',
            bgColor: 'rgba(50, 36, 70, 0.3)',
            borderColor: 'rgba(50, 36, 70, 0.6)'
        },
        deleted: {
            label: '已删除',
            labelEn: 'Deleted',
            color: '#322446',  // Dark Purple
            icon: '🗑',
            bgColor: 'rgba(50, 36, 70, 0.3)',
            borderColor: 'rgba(50, 36, 70, 0.6)'
        },
        pending: {
            label: '待处理',
            labelEn: 'Pending',
            color: '#FF007F',  // Hot Pink
            icon: '⏳',
            bgColor: 'rgba(255, 0, 127, 0.15)',
            borderColor: 'rgba(255, 0, 127, 0.4)'
        }
    },

    /**
     * 生成HTML状态徽章
     * @param {string} status - 状态值 (active/processing/failed/archived/deleted/pending)
     * @param {string} lang - 语言 ('zh' | 'en')
     * @param {object} options - 配置选项 {size: 'small'|'medium'|'large', showIcon: boolean}
     * @returns {string} HTML字符串
     */
    render(status, lang = 'zh', options = {}) {
        const defaults = {
            size: 'medium',
            showIcon: true
        };
        const opts = { ...defaults, ...options };
        
        const statusLower = (status || 'pending').toLowerCase();
        const statusConfig = this.config[statusLower] || this.config.pending;
        
        // 尺寸配置
        const sizeMap = {
            small: { padding: '4px 10px', fontSize: '0.75rem' },
            medium: { padding: '6px 14px', fontSize: '0.85rem' },
            large: { padding: '8px 18px', fontSize: '1rem' }
        };
        const sizeStyle = sizeMap[opts.size] || sizeMap.medium;
        
        const label = lang === 'en' ? statusConfig.labelEn : statusConfig.label;
        const iconHtml = opts.showIcon ? `${statusConfig.icon} ` : '';
        
        return `
            <span style="
                display: inline-block;
                padding: ${sizeStyle.padding};
                background: ${statusConfig.bgColor};
                border: 2px solid ${statusConfig.borderColor};
                border-radius: 20px;
                color: ${statusConfig.color};
                font-size: ${sizeStyle.fontSize};
                font-weight: bold;
                white-space: nowrap;
            ">
                ${iconHtml}${label}
            </span>
        `;
    },

    /**
     * 创建DOM元素
     * @param {string} status - 状态值
     * @param {string} lang - 语言
     * @param {object} options - 配置选项
     * @returns {HTMLElement} DOM元素
     */
    create(status, lang = 'zh', options = {}) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = this.render(status, lang, options);
        return tempDiv.firstElementChild;
    },

    /**
     * 获取状态颜色
     * @param {string} status - 状态值
     * @returns {string} 颜色值
     */
    getColor(status) {
        const statusLower = (status || 'pending').toLowerCase();
        const statusConfig = this.config[statusLower] || this.config.pending;
        return statusConfig.color;
    },

    /**
     * 判断状态是否为活动状态
     * @param {string} status - 状态值
     * @returns {boolean}
     */
    isActive(status) {
        return status && status.toLowerCase() === 'active';
    },

    /**
     * 判断状态是否为失败状态
     * @param {string} status - 状态值
     * @returns {boolean}
     */
    isFailed(status) {
        return status && status.toLowerCase() === 'failed';
    }
};

// 全局暴露
window.StatusBadge = StatusBadge;
