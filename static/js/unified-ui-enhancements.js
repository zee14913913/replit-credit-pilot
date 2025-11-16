/**
 * 统一UI增强系统 / Unified UI Enhancements
 * 
 * 包含：
 * - 统一导航系统（面包屑 + 快速操作）
 * - Next-Action智能按钮
 * - 双语支持（中英文切换）
 * - 统一错误处理
 * - 加载状态优化（Skeleton动画）
 * - 响应式优化
 * - 无障碍改进（ARIA标签）
 */

// ============================================
// 任务10: 统一导航系统
// ============================================
class UnifiedNavigation {
    constructor() {
        this.breadcrumbs = [];
        this.quickActions = [];
        this.init();
    }
    
    init() {
        this.renderBreadcrumbs();
        this.renderQuickActions();
    }
    
    setBreadcrumbs(breadcrumbs) {
        this.breadcrumbs = breadcrumbs;
        this.renderBreadcrumbs();
    }
    
    setQuickActions(actions) {
        this.quickActions = actions;
        this.renderQuickActions();
    }
    
    renderBreadcrumbs() {
        const container = document.getElementById('breadcrumb-container');
        if (!container) return;
        
        const html = `
            <nav aria-label="breadcrumb" class="mb-3">
                <ol class="breadcrumb">
                    ${this.breadcrumbs.map((crumb, index) => `
                        <li class="breadcrumb-item ${index === this.breadcrumbs.length - 1 ? 'active' : ''}">
                            ${index === this.breadcrumbs.length - 1 
                                ? `<span aria-current="page">${crumb.label}</span>` 
                                : `<a href="${crumb.url}">${crumb.label}</a>`}
                        </li>
                    `).join('')}
                </ol>
            </nav>
        `;
        container.innerHTML = html;
    }
    
    renderQuickActions() {
        const container = document.getElementById('quick-actions-container');
        if (!container) return;
        
        const html = `
            <div class="d-flex justify-content-end gap-2 mb-3">
                ${this.quickActions.map(action => `
                    <button class="btn btn-${action.color || 'primary'}" 
                            onclick="${action.onclick}"
                            ${action.disabled ? 'disabled' : ''}
                            aria-label="${action.ariaLabel || action.label}">
                        <i class="bi bi-${action.icon}"></i> ${action.label}
                    </button>
                `).join('')}
            </div>
        `;
        container.innerHTML = html;
    }
}

// ============================================
// 任务11: Next-Action智能按钮
// ============================================
class NextActionButton {
    static ACTION_CONFIGS = {
        'review_manually': { icon: 'eye', key: 'manual_review', color: 'warning' },
        'upload_new_file': { icon: 'upload', key: 're_upload', color: 'primary' },
        'edit_record': { icon: 'pencil', key: 'edit_button', color: 'info' },
        'delete_record': { icon: 'trash', key: 'delete_button', color: 'danger' },
        'retry': { icon: 'arrow-repeat', key: 'retry_button', color: 'success' },
        'ignore': { icon: 'x-circle', key: 'ignore_button', color: 'secondary' }
    };
    
    static render(action, recordId, language = 'zh') {
        const t = (key, fallback) => window.i18n?.translate(key) || fallback;
        const config = this.ACTION_CONFIGS[action] || {
            icon: 'question',
            key: action,
            color: 'secondary'
        };
        
        const label = config.key ? t(config.key, action) : action;
        
        return `
            <button class="btn btn-sm btn-${config.color}" 
                    onclick="handleNextAction('${action}', ${recordId})"
                    data-bs-toggle="tooltip"
                    title="${label}"
                    aria-label="${label}">
                <i class="bi bi-${config.icon}"></i>
            </button>
        `;
    }
}

// ============================================
// 任务12: 双语支持系统
// ============================================
class I18nManager {
    constructor() {
        this.currentLanguage = localStorage.getItem('language') || 'zh';
        this.translations = {};
        this.init();
    }
    
    init() {
        this.updateLanguageSelector();
        this.applyLanguage();
    }
    
    setLanguage(lang) {
        this.currentLanguage = lang;
        localStorage.setItem('language', lang);
        this.applyLanguage();
        location.reload();
    }
    
    translate(key, defaultValue) {
        const translation = this.translations[this.currentLanguage];
        return (translation && translation[key]) || defaultValue;
    }
    
    updateLanguageSelector() {
        const selector = document.getElementById('language-selector');
        if (!selector) return;
        
        const t = (key, fallback) => window.i18n?.translate(key) || fallback;
        selector.innerHTML = `
            <select class="form-select form-select-sm" onchange="i18n.setLanguage(this.value)" aria-label="${t('select_language', 'Select Language')}">
                <option value="zh" ${this.currentLanguage === 'zh' ? 'selected' : ''}>${t('chinese', '中文')}</option>
                <option value="en" ${this.currentLanguage === 'en' ? 'selected' : ''}>${t('english', 'English')}</option>
            </select>
        `;
    }
    
    applyLanguage() {
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translated = this.translate(key, element.textContent);
            element.textContent = translated;
        });
    }
}

// ============================================
// 任务13: 统一错误处理
// ============================================
class ErrorHandler {
    static show(message, options = {}) {
        const t = (key, fallback) => window.i18n?.translate(key) || fallback;
        const {
            title = t('error_title', 'Error'),
            type = 'error',
            duration = 5000,
            showRetry = false,
            onRetry = null
        } = options;
        
        const alertClass = type === 'error' ? 'danger' : type === 'warning' ? 'warning' : 'info';
        
        const alertHTML = `
            <div class="alert alert-${alertClass} alert-dismissible fade show" role="alert">
                <h5 class="alert-heading">
                    <i class="bi bi-exclamation-triangle-fill"></i> ${title}
                </h5>
                <p class="mb-0">${message}</p>
                ${showRetry ? `
                    <hr>
                    <button class="btn btn-sm btn-outline-${alertClass}" onclick="errorRetry()">
                        <i class="bi bi-arrow-repeat"></i> ${t('retry_button', 'Retry')}
                    </button>
                ` : ''}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        
        const container = document.getElementById('error-container') || this.createErrorContainer();
        container.insertAdjacentHTML('beforeend', alertHTML);
        
        if (duration > 0) {
            setTimeout(() => {
                const alerts = container.querySelectorAll('.alert');
                if (alerts.length > 0) {
                    alerts[0].remove();
                }
            }, duration);
        }
        
        if (onRetry) {
            window.errorRetry = onRetry;
        }
    }
    
    static createErrorContainer() {
        const container = document.createElement('div');
        container.id = 'error-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }
    
    static success(message) {
        const t = (key, fallback) => window.i18n?.translate(key) || fallback;
        this.show(message, {
            title: t('success_title', 'Success'),
            type: 'success'
        });
    }
    
    static warning(message) {
        const t = (key, fallback) => window.i18n?.translate(key) || fallback;
        this.show(message, {
            title: t('warning_title', 'Warning'),
            type: 'warning'
        });
    }
}

// ============================================
// 任务14: 加载状态优化（Skeleton动画）
// ============================================
class LoadingState {
    static showSkeleton(containerId, count = 3) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const skeletonHTML = `
            <div class="skeleton-loader">
                ${Array(count).fill(0).map(() => `
                    <div class="card mb-3">
                        <div class="card-body">
                            <div class="skeleton-line mb-2" style="width: 60%"></div>
                            <div class="skeleton-line mb-2" style="width: 80%"></div>
                            <div class="skeleton-line" style="width: 40%"></div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        container.innerHTML = skeletonHTML;
    }
    
    static hideSkeleton(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const skeleton = container.querySelector('.skeleton-loader');
        if (skeleton) {
            skeleton.remove();
        }
    }
    
    static showSpinner(message = null) {
        const t = (key, fallback) => window.i18n?.translate(key) || fallback;
        const displayMessage = message || t('loading_text', 'Loading...');
        
        const spinnerHTML = `
            <div id="global-spinner" class="position-fixed top-50 start-50 translate-middle" style="z-index: 9999;">
                <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
                    <span class="visually-hidden">${displayMessage}</span>
                </div>
                <p class="mt-2 text-center">${displayMessage}</p>
            </div>
            <div id="global-spinner-overlay" class="position-fixed top-0 start-0 w-100 h-100" 
                 style="background: rgba(0,0,0,0.3); z-index: 9998;"></div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', spinnerHTML);
    }
    
    static hideSpinner() {
        const spinner = document.getElementById('global-spinner');
        const overlay = document.getElementById('global-spinner-overlay');
        
        if (spinner) spinner.remove();
        if (overlay) overlay.remove();
    }
    
    static showProgress(percent, message = null) {
        const t = (key, fallback) => window.i18n?.translate(key) || fallback;
        const displayMessage = message || t('processing_text', 'Processing...');
        
        const progressHTML = `
            <div id="global-progress" class="position-fixed top-50 start-50 translate-middle" style="z-index: 9999; width: 400px;">
                <div class="card">
                    <div class="card-body">
                        <p class="mb-2">${displayMessage}</p>
                        <div class="progress">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                 role="progressbar" 
                                 style="width: ${percent}%"
                                 aria-valuenow="${percent}" 
                                 aria-valuemin="0" 
                                 aria-valuemax="100">
                                ${percent}%
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div id="global-progress-overlay" class="position-fixed top-0 start-0 w-100 h-100" 
                 style="background: rgba(0,0,0,0.3); z-index: 9998;"></div>
        `;
        
        const existing = document.getElementById('global-progress');
        if (existing) {
            const progressBar = existing.querySelector('.progress-bar');
            progressBar.style.width = `${percent}%`;
            progressBar.setAttribute('aria-valuenow', percent);
            progressBar.textContent = `${percent}%`;
        } else {
            document.body.insertAdjacentHTML('beforeend', progressHTML);
        }
    }
    
    static hideProgress() {
        const progress = document.getElementById('global-progress');
        const overlay = document.getElementById('global-progress-overlay');
        
        if (progress) progress.remove();
        if (overlay) overlay.remove();
    }
}

// ============================================
// 任务15 + 16: 响应式优化 + 无障碍改进
// ============================================
class AccessibilityManager {
    static init() {
        this.addAriaLabels();
        this.enableKeyboardNavigation();
        this.addFocusIndicators();
    }
    
    static addAriaLabels() {
        document.querySelectorAll('button:not([aria-label])').forEach(button => {
            const text = button.textContent.trim();
            if (text) {
                button.setAttribute('aria-label', text);
            }
        });
        
        document.querySelectorAll('input:not([aria-label])').forEach(input => {
            const label = input.closest('label') || document.querySelector(`label[for="${input.id}"]`);
            if (label) {
                input.setAttribute('aria-label', label.textContent.trim());
            }
        });
    }
    
    static enableKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modal = document.querySelector('.modal.show');
                if (modal) {
                    const closeButton = modal.querySelector('[data-bs-dismiss="modal"]');
                    if (closeButton) closeButton.click();
                }
                
                LoadingState.hideSpinner();
                LoadingState.hideProgress();
            }
            
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                const saveButton = document.querySelector('[data-action="save"]');
                if (saveButton) saveButton.click();
            }
        });
    }
    
    static addFocusIndicators() {
        const style = document.createElement('style');
        style.textContent = `
            *:focus-visible {
                outline: 2px solid #FF007F !important;
                outline-offset: 2px;
            }
            
            .btn:focus-visible {
                box-shadow: 0 0 0 0.25rem rgba(255, 0, 127, 0.25) !important;
            }
        `;
        document.head.appendChild(style);
    }
}

// ============================================
// CSS Skeleton样式注入
// ============================================
const skeletonStyles = document.createElement('style');
skeletonStyles.textContent = `
    .skeleton-loader {
        animation: fadeIn 0.3s ease-in;
    }
    
    .skeleton-line {
        height: 1rem;
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: skeleton-loading 1.5s ease-in-out infinite;
        border-radius: 4px;
    }
    
    @keyframes skeleton-loading {
        0% {
            background-position: 200% 0;
        }
        100% {
            background-position: -200% 0;
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @media (max-width: 768px) {
        .btn {
            font-size: 0.875rem;
            padding: 0.375rem 0.75rem;
        }
        
        .card {
            margin-bottom: 1rem;
        }
        
        .table-responsive {
            font-size: 0.875rem;
        }
    }
`;
document.head.appendChild(skeletonStyles);

// ============================================
// 初始化
// ============================================
const nav = new UnifiedNavigation();
const i18n = new I18nManager();

document.addEventListener('DOMContentLoaded', () => {
    AccessibilityManager.init();
    
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
});

// 导出全局对象
window.UnifiedNav = nav;
window.I18n = i18n;
window.ErrorHandler = ErrorHandler;
window.LoadingState = LoadingState;
window.NextActionButton = NextActionButton;
