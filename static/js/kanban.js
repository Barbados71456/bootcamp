let state = {todo:[], doing:[], done:[]};
const names = {todo:'Сделать', doing:'В работе', done:'Готово'};
async function loadKanban() {state = await api('/api/kanban'); render();}
function render() {
 const query = document.getElementById('task-search').value.toLocaleLowerCase();
 const priority = document.getElementById('priority-filter').value;
 for (const col of Object.keys(names)) {
  const container = document.getElementById('col-' + col); container.replaceChildren();
  const cards = state[col].filter(c => c.title.toLocaleLowerCase().includes(query) && (priority === 'all' || (c.priority || 'normal') === priority));
  cards.forEach(card => container.append(renderCard(card, col)));
  if (!cards.length) {const p=document.createElement('p'); p.className='empty-state'; p.textContent='Здесь пока нет задач'; container.append(p);}
  container.ondragover = e => e.preventDefault();
  container.ondrop = async e => {e.preventDefault(); await api('/api/kanban/move',{id:e.dataTransfer.getData('text/plain'),to:col}); await loadKanban();};
 }
}
function renderCard(card, col) {
 const el=document.createElement('article'); el.className='kanban-card'; el.draggable=true;
 el.ondragstart=e=>e.dataTransfer.setData('text/plain',card.id);
 const title=document.createElement('strong'); title.textContent=card.title;
 const meta=document.createElement('p'); meta.className='muted';
 meta.textContent=({high:'● Высокий',normal:'Обычный',low:'Низкий'}[card.priority || 'normal']) + (card.due ? ' · до '+card.due : '');
 if(card.due && card.due < new Date().toLocaleDateString('sv-SE') && col !== 'done') {meta.classList.add('overdue');meta.textContent+=' · Просрочено';}
 const controls=document.createElement('div'); controls.className='task-actions';
 const select=document.createElement('select'); select.setAttribute('aria-label','Переместить: '+card.title);
 for(const [value,label] of Object.entries(names)) {const opt=new Option(label,value); opt.selected=value===col;select.add(opt);}
 select.onchange=async()=>{await api('/api/kanban/move',{id:card.id,to:select.value});await loadKanban();};
 const edit=document.createElement('button');edit.className='btn small';edit.textContent='Править';
 edit.onclick=()=>{document.getElementById('edit-id').value=card.id;document.getElementById('edit-title').value=card.title;document.getElementById('edit-priority').value=card.priority||'normal';document.getElementById('edit-due').value=card.due||'';document.getElementById('edit-task').showModal();};
 const del=document.createElement('button');del.className='btn small';del.textContent='Удалить';del.onclick=async()=>{if(confirm('Удалить задачу?')) {await api('/api/kanban/delete',{id:card.id});await loadKanban();}};
 controls.append(select,edit,del);el.append(title,meta,controls);return el;
}
async function addTask(e) {
 e.preventDefault();const button=e.target.querySelector('button');button.disabled=true;
 try {await api('/api/kanban/add',{title:document.getElementById('task-title').value,column:document.getElementById('task-col').value,priority:document.getElementById('task-priority').value,due:document.getElementById('task-due').value});document.getElementById('task-title').value='';await loadKanban();showToast('Задача добавлена');} finally {button.disabled=false;}
}
document.getElementById('edit-form').onsubmit=async e=>{e.preventDefault();await api('/api/kanban/edit',{id:document.getElementById('edit-id').value,title:document.getElementById('edit-title').value,priority:document.getElementById('edit-priority').value,due:document.getElementById('edit-due').value});document.getElementById('edit-task').close();await loadKanban();};
document.getElementById('task-search').oninput=render;document.getElementById('priority-filter').onchange=render;
window.addEventListener('DOMContentLoaded',loadKanban);
