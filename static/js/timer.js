const storageKey='studyflow-timer-v2';
let timer={minutes:25, remaining:1500, end:null, id:crypto.randomUUID(), pending:false};
try {const saved=JSON.parse(localStorage.getItem(storageKey));if(saved && [5,25,50].includes(saved.minutes) && Number.isFinite(saved.remaining) && saved.remaining>=0 && typeof saved.id==='string' && (saved.end===null || Number.isFinite(saved.end))) timer=saved;} catch(_) {}
let finishing=false;
function saveTimer(){try{localStorage.setItem(storageKey,JSON.stringify(timer));}catch(_) {}}
function updateDisplay(){
 const seconds=timer.end ? Math.max(0,Math.ceil((timer.end-Date.now())/1000)) : timer.remaining;
 const time=`${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}`;
 document.getElementById('timer-display').textContent=time;
 document.getElementById('timer-mode').textContent=timer.pending?'Сессия завершена · ожидает сохранения':timer.minutes===5?'Перерыв':'Фокус';
 document.getElementById('btn-start').textContent=timer.pending?'Повторить сохранение':timer.end?'Идёт сессия…':'▶ Старт';
 document.title=timer.end?`${time} — StudyFlow`:'Таймер — StudyFlow';
 document.querySelectorAll('.timer-modes .btn').forEach((b,i)=>b.classList.toggle('active',[25,50,5][i]===timer.minutes));
 if(timer.end && seconds===0) {timer.end=null;timer.remaining=0;timer.pending=true;saveTimer();finishSession();}
}
function startTimer(){if(timer.pending){finishSession();return;}if(!timer.end){timer.end=Date.now()+timer.remaining*1000;saveTimer();updateDisplay();}}
function pauseTimer(){if(timer.end){timer.remaining=Math.max(0,Math.ceil((timer.end-Date.now())/1000));timer.end=null;saveTimer();updateDisplay();}}
function resetTimer(){if(finishing)return;if(timer.pending && !confirm('Сессия ещё не сохранена. Сбросить?'))return;timer={minutes:timer.minutes,remaining:timer.minutes*60,end:null,id:crypto.randomUUID(),pending:false};saveTimer();updateDisplay();}
function setMode(minutes){if(finishing)return;if((timer.end || timer.pending) && !confirm('Сменить режим и сбросить текущую сессию?'))return;timer={minutes,remaining:minutes*60,end:null,id:crypto.randomUUID(),pending:false};saveTimer();updateDisplay();}
async function finishSession(){
 if(finishing)return;finishing=true;
 try {
  if(timer.minutes!==5){const result=await api('/api/timer/finish',{minutes:timer.minutes,id:timer.id});document.getElementById('timer-total').textContent=result.stats.total_minutes;document.getElementById('timer-count').textContent=result.stats.pomodoros;}
  timer.pending=false;finishing=false;resetTimer();showToast('Сессия завершена! Прогресс сохранён.');
 } catch(error){showToast('Не удалось сохранить. Нажми «Повторить сохранение».','error');} finally{finishing=false;updateDisplay();}
}
window.addEventListener('DOMContentLoaded',()=>{updateDisplay();if(timer.pending)finishSession();setInterval(updateDisplay,250);});
window.addEventListener('storage',e=>{if(e.key===storageKey && e.newValue){try{timer=JSON.parse(e.newValue);updateDisplay();}catch(_){}}});
