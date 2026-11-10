let state = { todo: [], doing: [], done: [] };

async function loadKanban() {
    const res = await fetch("/api/kanban");
    state = await res.json();
    render();
}

function render() {
    for (const col of ["todo", "doing", "done"]) {
        const container = document.getElementById("col-" + col);
        container.innerHTML = "";
        state[col].forEach(card => container.appendChild(renderCard(card, col)));
        setupDrop(container, col);
    }
}

function renderCard(card, col) {
    const el = document.createElement("div");
    el.className = "kanban-card";
    el.draggable = true;
    el.dataset.id = card.id;
    el.dataset.col = col;
    el.innerHTML = `
        <span>${escapeHtml(card.title)}</span>
        <button class="del" title="Удалить" onclick="deleteCard('${card.id}')">✕</button>
    `;
    el.addEventListener("dragstart", e => {
        e.dataTransfer.setData("text/plain", card.id);
        el.classList.add("dragging");
    });
    el.addEventListener("dragend", () => el.classList.remove("dragging"));
    return el;
}

function setupDrop(container, col) {
    container.addEventListener("dragover", e => {
        e.preventDefault();
        container.classList.add("drag-over");
    });
    container.addEventListener("dragleave", () => container.classList.remove("drag-over"));
    container.addEventListener("drop", async e => {
        e.preventDefault();
        container.classList.remove("drag-over");
        const id = e.dataTransfer.getData("text/plain");
        await fetch("/api/kanban/move", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ id, to: col })
        });
        await loadKanban();
        showToast(col === "done" ? "Задача выполнена! +10 XP 🎉" : "Карточка перемещена");
    });
}

async function addTask(e) {
    e.preventDefault();
    const title = document.getElementById("task-title").value.trim();
    const column = document.getElementById("task-col").value;
    if (!title) return;
    const res = await fetch("/api/kanban/add", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ title, column })
    });
    const data = await res.json();
    if (data.ok) {
        document.getElementById("task-title").value = "";
        await loadKanban();
        showToast("Задача добавлена");
    }
}

async function deleteCard(id) {
    if (!confirm("Удалить задачу?")) return;
    await fetch("/api/kanban/delete", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ id })
    });
    await loadKanban();
}

function escapeHtml(s) {
    return s.replace(/[&<>"']/g, m => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[m]));
}

loadKanban();