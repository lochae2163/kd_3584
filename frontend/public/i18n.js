// ========================================
// KvK Tracker - Internationalization (i18n)
// ========================================

const I18n = (function() {
    const SUPPORTED_LANGUAGES = ['en', 'ja'];
    const DEFAULT_LANGUAGE = 'en';
    const STORAGE_KEY = 'kvk_language';

    let currentLang = DEFAULT_LANGUAGE;
    let translations = {};
    let fallbackTranslations = {};
    let initPromise = null;

    function detectLanguage() {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored && SUPPORTED_LANGUAGES.includes(stored)) return stored;
        const browserLang = (navigator.language || '').slice(0, 2);
        if (SUPPORTED_LANGUAGES.includes(browserLang)) return browserLang;
        return DEFAULT_LANGUAGE;
    }

    async function loadTranslations(lang) {
        const response = await fetch(`i18n/${lang}.json`);
        if (!response.ok) throw new Error(`Failed to load ${lang}.json`);
        return response.json();
    }

    async function init() {
        if (initPromise) return initPromise;

        initPromise = (async () => {
            document.body.classList.add('i18n-loading');
            currentLang = detectLanguage();

            fallbackTranslations = await loadTranslations('en');
            if (currentLang !== 'en') {
                translations = await loadTranslations(currentLang);
            } else {
                translations = fallbackTranslations;
            }

            localStorage.setItem(STORAGE_KEY, currentLang);
            document.documentElement.lang = currentLang;
            translatePage();
            initLanguageSwitcher();
            document.body.classList.remove('i18n-loading');
        })();

        return initPromise;
    }

    function t(key, params) {
        const value = getNestedValue(translations, key)
            || getNestedValue(fallbackTranslations, key)
            || key;

        if (params && typeof value === 'string') {
            return value.replace(/\{(\w+)\}/g, (_, k) =>
                params[k] !== undefined ? params[k] : `{${k}}`
            );
        }
        return value;
    }

    function getNestedValue(obj, path) {
        return path.split('.').reduce((o, k) => (o && o[k] !== undefined) ? o[k] : null, obj);
    }

    function translatePage() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            el.textContent = t(el.getAttribute('data-i18n'));
        });
        document.querySelectorAll('[data-i18n-html]').forEach(el => {
            el.innerHTML = t(el.getAttribute('data-i18n-html'));
        });
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            el.placeholder = t(el.getAttribute('data-i18n-placeholder'));
        });
        document.querySelectorAll('select[data-i18n-options]').forEach(select => {
            select.querySelectorAll('option[data-i18n]').forEach(opt => {
                opt.textContent = t(opt.getAttribute('data-i18n'));
            });
        });
    }

    async function setLanguage(lang) {
        if (!SUPPORTED_LANGUAGES.includes(lang) || lang === currentLang) return;
        currentLang = lang;
        localStorage.setItem(STORAGE_KEY, lang);

        if (lang === 'en') {
            translations = fallbackTranslations;
        } else {
            translations = await loadTranslations(lang);
        }

        document.documentElement.lang = lang;
        translatePage();
        updateSwitcherUI();
        window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
    }

    function initLanguageSwitcher() {
        const switcher = document.getElementById('lang-switcher');
        if (!switcher) return;

        switcher.querySelectorAll('.lang-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.lang === currentLang);
            btn.addEventListener('click', () => setLanguage(btn.dataset.lang));
        });
    }

    function updateSwitcherUI() {
        const switcher = document.getElementById('lang-switcher');
        if (!switcher) return;
        switcher.querySelectorAll('.lang-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.lang === currentLang);
        });
    }

    function getLang() {
        return currentLang;
    }

    return { init, t, setLanguage, getLang, translatePage, SUPPORTED_LANGUAGES };
})();

// Global shorthand
const t = I18n.t;
