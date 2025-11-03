/**
 * I18n Manager - Bilingual Support System
 * Handles language switching and translation for the entire system
 */

class I18nManager {
    constructor() {
        this.currentLang = localStorage.getItem('language') || 'en';
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
        localStorage.setItem('language', lang);
        
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
        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.dataset.i18n;
            const translation = this.translate(key, lang);
            
            if (translation) {
                // Check if it's a placeholder
                if (element.hasAttribute('placeholder')) {
                    element.placeholder = translation;
                } else {
                    element.textContent = translation;
                }
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
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        i18n = new I18nManager();
    });
} else {
    i18n = new I18nManager();
}

// Export for global use
window.I18nManager = I18nManager;
window.i18n = i18n;
