const API_BASE = 'http://127.0.0.1:8000';

// --- Tab Navigation ---
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        
        btn.classList.add('active');
        document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
    });
});

// --- Status Polling ---
async function fetchStatus() {
    try {
        const res = await fetch(`${API_BASE}/status`);
        const data = await res.json();
        
        // Update Badge
        const badge = document.getElementById('daemon-badge');
        badge.textContent = data.daemon_state || 'UNKNOWN';
        badge.className = 'badge ' + (data.daemon_state || 'idle').toLowerCase();
        
        // Update HUD
        document.getElementById('hud-status').textContent = data.daemon_state;
        document.getElementById('hud-cpu').textContent = (data.metrics?.cpu || '--') + '%';
        document.getElementById('hud-ram').textContent = (data.metrics?.ram || '--') + '%';
        
    } catch (e) {
        document.getElementById('daemon-badge').textContent = 'OFFLINE';
        document.getElementById('daemon-badge').className = 'badge idle';
    }
}

setInterval(fetchStatus, 3000);
fetchStatus();

// --- Control Buttons ---
document.getElementById('btn-pause').addEventListener('click', async () => {
    await fetch(`${API_BASE}/pause`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({reason: 'USER_UI'}) });
    fetchStatus();
});

document.getElementById('btn-resume').addEventListener('click', async () => {
    await fetch(`${API_BASE}/resume`, { method: 'POST' });
    fetchStatus();
});

// --- Live Logs ---
async function fetchLogs() {
    try {
        const res = await fetch(`${API_BASE}/logs/tail?lines=50`);
        const logs = await res.json();
        
        const container = document.getElementById('log-container');
        container.innerHTML = logs.map(l => `<div>[${l.ts || '??'}] ${l.event || JSON.stringify(l)}</div>`).join('');
        container.scrollTop = container.scrollHeight;
    } catch (e) {}
}
setInterval(fetchLogs, 5000);
fetchLogs();

// --- Explorer ---
async function fetchEvents() {
    try {
        const res = await fetch(`${API_BASE}/events?limit=100`);
        const events = await res.json();
        
        const tbody = document.querySelector('#events-table tbody');
        tbody.innerHTML = events.map(e => `
            <tr>
                <td>${e.type}</td>
                <td>${e.id}</td>
                <td>${e.label || '-'}</td>
                <td>${e.ml_score?.toFixed(1) || '-'}</td>
                <td>${e.created_at || '-'}</td>
            </tr>
        `).join('');
    } catch (e) {}
}
fetchEvents();

// --- Audio Lab (Placeholder) ---
// WebAudio spectrogram code would go here
