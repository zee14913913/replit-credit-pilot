'use client';

import { useLanguage } from '@/contexts/LanguageContext';
import { Language } from '@/lib/i18n/translations';

export default function LanguageSwitcher() {
  const { language, setLanguage } = useLanguage();

  const languages: { code: Language; label: string }[] = [
    { code: 'en', label: 'EN' },
    { code: 'zh', label: 'CN' },
    { code: 'ms', label: 'BM' },
  ];

  return (
    <div className="flex items-center gap-2">
      {languages.map((lang) => (
        <button
          key={lang.code}
          onClick={() => setLanguage(lang.code)}
          className={`
            relative inline-flex items-center justify-center px-3 py-2 rounded-full
            border transition-all text-xs font-mono uppercase tracking-wider
            ${
              language === lang.code
                ? 'border-primary bg-primary text-background'
                : 'border-border bg-background text-secondary hover:border-primary/50 hover:text-primary'
            }
          `}
          aria-label={`Switch to ${lang.label}`}
        >
          {lang.label}
        </button>
      ))}
    </div>
  );
}
