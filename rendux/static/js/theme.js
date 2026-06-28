/* RendUX Theme Manager
   Reads/writes data-theme on <html> and persists preference to localStorage.
   The anti-FOUC inline script in base.html handles the initial theme application
   before this file loads. */

(function () {
  var STORAGE_KEY = 'rx-theme';

  function resolve(preference) {
    if (preference === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return preference;
  }

  function applyTheme(preference) {
    var theme = resolve(preference);
    document.documentElement.dataset.theme = theme;
    document.documentElement.dataset.themePreference = preference;
    updateSwitcherUI(preference);
  }

  function updateSwitcherUI(preference) {
    document.querySelectorAll('[data-theme-btn]').forEach(function (btn) {
      btn.classList.toggle('active', btn.dataset.themeBtn === preference);
      btn.setAttribute('aria-pressed', btn.dataset.themeBtn === preference ? 'true' : 'false');
    });
  }

  window.RendUX = window.RendUX || {};

  window.RendUX.setTheme = function (preference) {
    localStorage.setItem(STORAGE_KEY, preference);
    applyTheme(preference);
  };

  window.RendUX.getTheme = function () {
    return localStorage.getItem(STORAGE_KEY) || 'system';
  };

  /* Sync UI once DOM is ready */
  document.addEventListener('DOMContentLoaded', function () {
    updateSwitcherUI(window.RendUX.getTheme());
  });

  /* Follow system changes when preference is "system" */
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () {
    if (window.RendUX.getTheme() === 'system') {
      applyTheme('system');
    }
  });
})();
