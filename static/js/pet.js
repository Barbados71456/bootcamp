async function feedPet() {
    const data = await api('/api/pet/feed', {});
    if (data.ok) { updatePet(data.pet); showToast("Питомец покормлен! 🍎"); }
}

async function playPet() {
    const data = await api('/api/pet/play', {});
    if (data.ok) { updatePet(data.pet); showToast("Питомец рад! 🎮"); }
}

async function renamePet() {
    const name = prompt("Как назовём питомца?", document.getElementById("pet-name").textContent);
    if (!name) return;
    const data = await api('/api/pet/rename', {name});
    if (data.ok) { updatePet(data.pet); showToast("Имя обновлено"); }
}

function updatePet(p) {
    document.getElementById("pet-name").textContent = p.name;
    document.getElementById("pet-level").textContent = p.level;
    document.getElementById("pet-xp").textContent = p.xp;
    document.getElementById("pet-hunger").textContent = p.hunger;
    document.getElementById("pet-happy").textContent = p.happiness;
    document.getElementById("pet-xp-bar").style.width = p.xp + "%";

    // Меняем эмодзи в зависимости от уровня
    const emojis = ["🥚", "🐣", "🐤", "🐥", "🐔", "🦅", "🦉", "🐉"];
    const idx = Math.min(emojis.length - 1, Math.floor(p.level / 3));
    const big = document.getElementById("pet-big");
    big.textContent = emojis[idx];
    big.style.transform = "scale(1.15)";
    setTimeout(() => { big.style.transform = "scale(1)"; }, 350);
}
