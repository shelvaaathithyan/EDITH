// Tab switching logic
document.querySelectorAll('.nav-links li').forEach(li => {
    li.addEventListener('click', () => {
        // Remove active class from all tabs
        document.querySelectorAll('.nav-links li').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
        
        // Add active class to clicked tab
        li.classList.add('active');
        const tabId = 'tab-' + li.getAttribute('data-tab');
        document.getElementById(tabId).classList.add('active');
        
        // Trigger tab-specific refresh if needed
        refreshTab(li.getAttribute('data-tab'));
    });
});

// Periodic refresh timer
setInterval(() => {
    const activeTab = document.querySelector('.nav-links li.active').getAttribute('data-tab');
    refreshTab(activeTab, true);
}, 2000);

function refreshTab(tabId, isPolling = false) {
    if (!window.pywebview) return;
    
    switch (tabId) {
        case 'health': refreshHealth(); break;
        case 'telemetry': refreshTelemetry(); break;
        case 'events': if (!isPolling) refreshEvents(); break;
        case 'memory': refreshMemory(); break;
        case 'context': refreshContext(); break;
    }
}

// ── Refresh Functions ───────────────────────────────────────────

async function refreshHealth() {
    try {
        const report = await pywebview.api.get_health_report();
        const overallEl = document.getElementById('health-overall');
        overallEl.textContent = report.overall_status.toUpperCase();
        overallEl.className = 'badge ' + report.overall_status;
        
        const subTbody = document.querySelector('#health-subsystems-table tbody');
        subTbody.innerHTML = '';
        report.subsystems.forEach(sub => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${sub.name}</td>
                <td><span class="badge ${sub.status.toLowerCase()}">${sub.status}</span></td>
                <td>${sub.latency_ms}</td>
            `;
            subTbody.appendChild(tr);
        });
        
        const capTbody = document.querySelector('#health-capabilities-table tbody');
        capTbody.innerHTML = '';
        Object.entries(report.capabilities).forEach(([id, status]) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${id}</td>
                <td><span class="badge ${status.toLowerCase()}">${status}</span></td>
            `;
            capTbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to load health", e);
    }
}

async function refreshTelemetry() {
    try {
        const tel = await pywebview.api.get_telemetry();
        const tbody = document.querySelector('#telemetry-table tbody');
        tbody.innerHTML = '';
        if (Object.keys(tel).length === 0) {
            tbody.innerHTML = '<tr><td colspan="2">No telemetry available yet.</td></tr>';
            return;
        }
        
        Object.entries(tel).forEach(([key, val]) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${key}</td><td>${val.toFixed(3)}</td>`;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to load telemetry", e);
    }
}

async function refreshContext() {
    try {
        const ctx = await pywebview.api.get_interaction_context();
        document.getElementById('context-json').textContent = JSON.stringify(ctx, null, 2);
    } catch (e) {
        console.error("Failed to load context", e);
    }
}

async function refreshMemory() {
    try {
        const memories = await pywebview.api.get_memories();
        const tbody = document.querySelector('#memory-table tbody');
        tbody.innerHTML = '';
        
        if (memories.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4">No memories found.</td></tr>';
            return;
        }
        
        memories.forEach(mem => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${mem.category}</td>
                <td>${mem.title}</td>
                <td>${mem.value}</td>
                <td>${mem.confidence.toFixed(2)}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Failed to load memory", e);
    }
}

async function refreshEvents() {
    try {
        const events = await pywebview.api.get_event_log();
        const stream = document.getElementById('event-stream');
        stream.innerHTML = '';
        
        events.forEach(ev => {
            const div = document.createElement('div');
            div.innerHTML = `<span class="event-time">[${ev.time}]</span> <span class="event-type">${ev.event}</span>: ${JSON.stringify(ev.data)}`;
            stream.appendChild(div);
        });
    } catch (e) {
        console.error("Failed to load events", e);
    }
}

// ── Python Event Listener (Push) ────────────────────────────────

window.update_state = function(state, data) {
    const statusText = document.getElementById('status-text');
    const subText = document.getElementById('sub-text');
    const orb = document.getElementById('ai-orb');
    
    // Clear old classes
    orb.className = 'orb';
    
    if (state === 'LISTENING') {
        orb.classList.add('state-listening');
        statusText.textContent = 'Listening...';
        subText.textContent = '';
    } else if (state === 'PROCESSING') {
        orb.classList.add('state-processing');
        statusText.textContent = 'Processing';
        if (data && data.input) subText.textContent = `"${data.input}"`;
    } else if (state === 'RESPONDING') {
        orb.classList.add('state-processing'); // Same visual as processing for now
        statusText.textContent = 'Responding';
        if (data && data.response) subText.textContent = `"${data.response}"`;
    } else if (state === 'ERROR') {
        orb.classList.add('state-error');
        statusText.textContent = 'Error';
        if (data && data.error) subText.textContent = data.error;
    } else {
        orb.classList.add('state-ready');
        statusText.textContent = 'System Ready';
        subText.textContent = 'Awaiting Wake Word';
    }
    
    // Update timeline if there's an event
    if (data && data.event) {
        const timeline = document.getElementById('pipeline-timeline');
        
        // Remove "No recent activity" if it exists
        if (timeline.textContent === 'No recent activity.') {
            timeline.innerHTML = '';
        }
        
        const item = document.createElement('div');
        item.className = 'timeline-item';
        item.innerHTML = `
            <div class="time">${new Date().toLocaleTimeString()}</div>
            <div class="event">${state} - ${data.event}</div>
            <div class="detail">${data.detail || ''}</div>
        `;
        
        // Prepend and limit to 5 items
        timeline.insertBefore(item, timeline.firstChild);
        if (timeline.children.length > 5) {
            timeline.removeChild(timeline.lastChild);
        }
    }
};
