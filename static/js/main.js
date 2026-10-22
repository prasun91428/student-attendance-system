// ─── Modal helpers ────────────────────────────────────────
function openModal(id) {
    const el = document.getElementById(id);
    if (el) { el.style.display = 'flex'; document.body.style.overflow = 'hidden'; }
}
function closeModal(id) {
    const el = document.getElementById(id);
    if (el) { el.style.display = 'none'; document.body.style.overflow = ''; }
}

// Close modal when clicking backdrop
document.addEventListener('click', e => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.style.display = 'none';
        document.body.style.overflow = '';
    }
});

// Auto-dismiss flash messages
document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
        el.style.transition = 'opacity .5s';
        el.style.opacity = '0';
        setTimeout(() => el.remove(), 500);
    }, 4000);
});

// Animate KPI values with count-up
function countUp(el) {
    const target = parseInt(el.textContent, 10);
    if (isNaN(target)) return;
    let current = 0;
    const step  = Math.ceil(target / 30);
    const timer = setInterval(() => {
        current = Math.min(current + step, target);
        el.textContent = current;
        if (current >= target) clearInterval(timer);
    }, 25);
}
document.querySelectorAll('.kpi-value').forEach(countUp);
