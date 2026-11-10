let totalSeconds = 25 * 60;
let remaining = totalSeconds;
let interval = null;
let isRunning = false;
let currentMinutes = 25;

const display = document.getElementById("timer-display");
const modeEl = document.getElementById("timer-mode");
const startBtn = document.getElementById("btn-start");

function updateDisplay() {
    const m = Math.floor(remaining / 60).toString().padStart(2, "0");
    const s = (remaining % 60).toString().padStart(2, "0");
    display.textContent = `${m}:${s}`;
    document.title = isRunning ? `${m}:${s} — StudyFlow` : "Таймер — StudyFlow";
}

function startTimer() {
    if (isRunning) return;
    isRunning = true;
    startBtn.textContent = "▶ Работает…";
    interval = setInterval(() => {
        remaining--;
        if (remaining <= 0) {
            clearInterval(interval);
            isRunning = false;
            finishSession();
        }
        updateDisplay();
    }, 1000);
}

function pauseTimer() {
    if (!isRunning) return;
    clearInterval(interval);
    isRunning = false;
    startBtn.textContent = "▶ Старт";
}

function resetTimer() {
    clearInterval(interval);
    isRunning = false;
    remaining = totalSeconds;
    startBtn.textContent = "▶ Старт";
    updateDisplay();
}

function setMode(min, btn) {
    currentMinutes = min;
    totalSeconds = min * 60;
    resetTimer();
    modeEl.textContent = min === 5 ? "Перерыв" : "Работа";
    document.querySelectorAll(".timer-modes .btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
}

async function finishSession() {
    // звук
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain); gain.connect(ctx.destination);
        osc.frequency.value = 880;
        gain.gain.setValueAtTime(0.2, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8);
        osc.start(); osc.stop(ctx.currentTime + 0.8);
    } catch (e) {}

    if (currentMinutes === 5) {
        showToast("Перерыв закончен! Пора работать 🌟");
        resetTimer();
        return;
    }

    const res = await fetch("/api/timer/finish", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ minutes: currentMinutes })
    });
    const data = await res.json();
    showToast(`Помидор завершён! +${Math.floor(currentMinutes / 5)} XP 🍅`);
    startBtn.textContent = "▶ Старт";
    remaining = totalSeconds;
    updateDisplay();
}

updateDisplay();