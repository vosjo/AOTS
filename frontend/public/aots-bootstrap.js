(function () {
  try {
    var theme = localStorage.getItem('aots-theme')
    document.documentElement.setAttribute('data-theme', theme === 'light' ? 'light' : 'dark')
  } catch {
    document.documentElement.setAttribute('data-theme', 'dark')
  }
})()

;(function () {
  var csrfMeta = document.querySelector('meta[name="csrf-token"]')
  var testMeta = document.querySelector('meta[name="aots-test-installation"]')
  var routerMeta = document.querySelector('meta[name="aots-router-base"]')
  window.__AOTS_BOOTSTRAP__ = {
    csrfToken: csrfMeta ? csrfMeta.getAttribute('content') || '' : '',
    testInstallation: testMeta ? testMeta.getAttribute('content') === 'true' : false,
    routerBase: routerMeta ? routerMeta.getAttribute('content') || '/' : '/',
  }
})()
