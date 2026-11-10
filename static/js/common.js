async function api(url, body) {
 const response = await fetch(url, body === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
 const result = await response.json();
 if (!response.ok || result.ok === false) throw new Error(result.error || 'Не удалось сохранить изменения');
 return result;
}
window.addEventListener('unhandledrejection', e => {showToast(e.reason?.message || 'Нет связи с сервером. Повторите попытку.', 'error'); e.preventDefault();});
try {document.documentElement.dataset.theme = localStorage.getItem('studyflow-theme') || 'light';} catch (_) {}
document.getElementById('theme-toggle').onclick = () => {
 const theme = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
 document.documentElement.dataset.theme = theme;
 try {localStorage.setItem('studyflow-theme', theme);} catch (_) {}
};
document.querySelectorAll('nav a').forEach(a => {if (a.pathname === location.pathname) a.setAttribute('aria-current','page');});
