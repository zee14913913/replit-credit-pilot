/**
 * I18n Manager - Bilingual Support System
 * Handles language switching and translation for the entire system
 */

class I18nManager {
    constructor() {
        // 从服务器端获取当前语言（session 管理）
        // 不使用 localStorage，避免跨会话持久化
        this.currentLang = document.documentElement.lang === 'zh-CN' ? 'zh' : 'en';
        this.translations = {};
        this.init();
    }

    async init() {
        // Load translation files
        await this.loadTranslations();
        // Apply initial language
        this.applyLanguage(this.currentLang);
        // Setup language switcher buttons
        this.setupLanguageSwitcher();
    }

    async loadTranslations() {
        try {
            // Load both language files
            const [zhResponse, enResponse] = await Promise.all([
                fetch('/static/i18n/zh.json'),
                fetch('/static/i18n/en.json')
            ]);
            
            this.translations.zh = await zhResponse.json();
            this.translations.en = await enResponse.json();
        } catch (error) {
            console.error('Failed to load translations:', error);
            // Fallback to empty translations
            this.translations = { zh: {}, en: {} };
        }
    }

    setupLanguageSwitcher() {
        // Find all language switcher buttons
        const langButtons = document.querySelectorAll('.lang-btn');
        langButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const lang = btn.dataset.lang;
                if (lang) {
                    this.setLanguage(lang);
                }
            });
        });
    }

    setLanguage(lang) {
        if (!['en', 'zh'].includes(lang)) return;
        
        this.currentLang = lang;
        // 不使用 localStorage，由服务器端 session 管理
        // 这样关闭浏览器后会恢复默认英文，但会话期间保持用户选择
        
        // Apply language to all elements
        this.applyLanguage(lang);
        
        // Update active state of language buttons
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.lang === lang);
        });
        
        // Update HTML lang attribute
        document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
        
        // Dispatch custom event for other components to listen
        window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
    }

    applyLanguage(lang) {
        // Update document title if key exists
        const pageTitle = this.translate('dashboard_page_title', lang);
        if (pageTitle && pageTitle !== 'dashboard_page_title') {
            document.title = pageTitle;
        }
        
        // Update all elements with data-i18n attribute (text content)
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.dataset.i18n;
            const translation = this.translate(key, lang);
            
            if (translation) {
                element.textContent = translation;
            }
        });
        
        // Update all elements with data-i18n-placeholder attribute (placeholders)
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.dataset.i18nPlaceholder;
            const translation = this.translate(key, lang);
            
            if (translation) {
                element.placeholder = translation;
            }
        });
    }

    translate(key, lang = null) {
        const targetLang = lang || this.currentLang;
        return this.translations[targetLang]?.[key] || key;
    }

    // Utility function for Title Case formatting
    toTitleCase(str) {
        return str.replace(/\w\S*/g, (txt) => {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        });
    }

    // Utility function for ALL CAPS formatting
    toAllCaps(str) {
        return str.toUpperCase();
    }
}

// Initialize I18n Manager when DOM is ready
let i18n;
const i18nReadyPromise = new Promise((resolve) => {
    const initI18n = async () => {
        i18n = new I18nManager();
        window.i18n = i18n;
        // Wait for translations to load
        await i18n.init();
        // Dispatch ready event
        window.dispatchEvent(new CustomEvent('i18nReady'));
        resolve(i18n);
    };
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initI18n);
    } else {
        initI18n();
    }
});

// Utility: wait for i18n to be ready
window.waitForI18n = () => i18nReadyPromise;

// Export for global use
window.I18nManager = I18nManager;
