const lessons = [...document.querySelectorAll('.lesson')];
function filterLessons() {
 const query = document.getElementById('lesson-search').value.toLocaleLowerCase().trim();
 const filter = document.getElementById('lesson-filter').value;
 let count = 0;
 lessons.forEach(el => {
  const match = el.dataset.search.toLocaleLowerCase().includes(query) && (filter === 'all' || filter === 'pending' && el.dataset.done !== 'true' || filter === 'done' && el.dataset.done === 'true' || filter === 'saved' && el.dataset.saved === 'true');
  el.hidden = !match; if (match) count++;
 });
 document.querySelectorAll('.course-block').forEach(el => el.hidden = ![...el.querySelectorAll('.lesson')].some(l => !l.hidden));
 document.getElementById('empty-search').hidden = count > 0;
 document.getElementById('search-count').textContent = `Найдено: ${count}`;
}
document.getElementById('lesson-search').addEventListener('input', filterLessons);
document.getElementById('lesson-filter').addEventListener('change', filterLessons);
lessons.forEach(el => {
 const payload = {course: el.dataset.course, lesson: Number(el.dataset.lesson)};
 el.querySelector('.complete').addEventListener('click', async event => {
  const button = event.target; button.disabled = true;
  try {
   await api('/api/lesson/complete', payload); el.dataset.done = 'true'; button.textContent = '✓ Урок завершён';
   const course = el.closest('.course-block'), done = course.querySelectorAll('[data-done="true"]').length;
   course.querySelector('progress').value = done;
   course.querySelector('.course-count').textContent = `${done}/${course.querySelectorAll('.lesson').length}`;
   showToast('Урок пройден. Прогресс сохранён!'); filterLessons();
  } catch (error) {button.disabled = false; throw error;}
 });
 el.querySelector('.bookmark').addEventListener('click', async event => {
  const bookmark = el.dataset.saved !== 'true'; await api('/api/lesson/bookmark', {...payload, bookmark});
  el.dataset.saved = String(bookmark); event.target.setAttribute('aria-pressed', String(bookmark));
  event.target.textContent = bookmark ? '★ В закладках' : '☆ В закладки'; filterLessons();
 });
 const note = el.querySelector('textarea');
 note.addEventListener('input', () => {note.dataset.dirty = 'true'; el.querySelector('.note-status').textContent = ' Не сохранено';});
 el.querySelector('.save-note').addEventListener('click', async () => {
  const value = note.value; await api('/api/lesson/note', {...payload, note:value});
  if (note.value === value) {note.dataset.dirty = ''; el.querySelector('.note-status').textContent = ' Сохранено';}
 });
});
window.addEventListener('beforeunload', e => {if (document.querySelector('[data-dirty="true"]')) {e.preventDefault(); e.returnValue = '';}});
const target = document.getElementById(location.hash.slice(1)); if (target?.tagName === 'DETAILS') target.open = true;
filterLessons();
