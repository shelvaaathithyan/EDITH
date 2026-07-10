// ── State ────────────────────────────────────────────────────────
let devMode = false;
let investigationMode = true;
let eventTimeline = [];
let currentTrace = null; // Accumulates stages for a single trace

// ── DOM Elements ───────────────────────────────────────────────
const stages = {
    'WAKE_WORD_DETECTED': 'stage-wake',
    'LISTENING_STARTED': 'stage-recording',
    'LISTENING_FINISHED': 'stage-recording',
    'STT_STARTED': 'stage-stt',
    'STT_FINISHED': 'stage-stt',
    'PLANNER_STARTED': 'stage-planner',
    'PLANNER_COMPLETED': 'stage-planner',
    'CAPABILITY_RESOLVER_STARTED': 'stage-resolver',
    'CAPABILITY_RESOLVER_FINISHED': 'stage-resolver',
    'CAPABILITY_STARTED': 'stage-capability',
    'CAPABILITY_FINISHED': 'stage-capability',
    'GENERATOR_STARTED': 'stage-generator',
    'GENERATOR_FINISHED': 'stage-generator',
    'VOICE_STARTED': 'stage-tts',
    'VOICE_STOPPED': 'stage-tts'
};

// ── Initialization ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Tab switching
    document.querySelectorAll('.nav-links li').forEach(li => {
        li.addEventListener('click', () => {
            document.querySelectorAll('.nav-links li').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
            
            li.classList.add('active');
            const tabId = 'tab-' + li.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
            
            if (li.getAttribute('data-tab') === 'memory') loadMemory();
            if (li.getAttribute('data-tab') === 'capabilities') loadCapabilities();
            if (li.getAttribute('data-tab') === 'context') loadContext();
        });
    });

    // Dev Mode Toggle
    const devToggle = document.getElementById('dev-mode-switch');
    devToggle.addEventListener('change', (e) => {
        devMode = e.target.checked;
        document.querySelectorAll('.dev-only').forEach(el => {
            el.style.display = devMode ? 'block' : 'none';
        });
    });

    // Investigation Mode Toggle
    const invToggle = document.getElementById('investigation-mode');
    invToggle.addEventListener('change', (e) => {
        investigationMode = e.target.checked;
    });

    // Clear events
    document.getElementById('btn-clear-events').addEventListener('click', () => {
        document.getElementById('event-timeline').innerHTML = '';
        eventTimeline = [];
    });

    // Periodic polling for system metrics ONLY
    setInterval(pollMetrics, 2000);
});

// ── Polling Metrics ────────────────────────────────────────────
async function pollMetrics() {
    if (!window.pywebview) return;
    try {
        const metrics = await pywebview.api.get_system_metrics();
        document.getElementById('hud-cpu').innerText = `${metrics.cpu_percent.toFixed(1)}%`;
        document.getElementById('hud-ram').innerText = `${metrics.ram_mb.toFixed(0)} MB`;
        document.getElementById('hud-threads').innerText = metrics.thread_count;
        
        // Also simulate voice audio level if recording is active
        if (currentTrace && currentTrace.recording) {
            updateAudioViz(true);
        } else {
            updateAudioViz(false);
        }
    } catch(e) {}
}

function updateAudioViz(active) {
    const bars = document.querySelectorAll('#audio-viz .bar');
    bars.forEach(bar => {
        if (active) {
            bar.style.height = Math.floor(Math.random() * 50 + 10) + 'px';
        } else {
            bar.style.height = '4px';
        }
    });
}

// ── Event-Driven Handler (from Python) ─────────────────────────
window.onAppEvent = function(jsonStr) {
    let ev;
    try {
        ev = JSON.parse(jsonStr);
    } catch(e) { return; }

    addTimelineEvent(ev);
    addConsoleLog(ev);

    const stageId = stages[ev.event];
    if (stageId) {
        updatePipelineStage(stageId, ev.event, ev.data);
    }

    // Specific Event Behaviors
    switch(ev.event) {
        case 'WAKE_WORD_DETECTED':
            resetPipeline();
            currentTrace = { start: Date.now(), stages: [], recording: false };
            updatePipelineStage('stage-wake', 'success');
            break;
            
        case 'LISTENING_STARTED':
            if(currentTrace) currentTrace.recording = true;
            document.getElementById('voice-state').innerText = 'Listening';
            break;
            
        case 'LISTENING_FINISHED':
            if(currentTrace) currentTrace.recording = false;
            updateAudioViz(false);
            if(ev.data && ev.data.value) {
                document.getElementById('voice-last-text').innerText = `"${ev.data.value}"`;
            }
            document.getElementById('voice-state').innerText = 'Processing';
            break;
            
        case 'PLANNER_COMPLETED':
            if (ev.data && ev.data.confidence) {
                document.getElementById('voice-stt-conf').innerText = `${(ev.data.confidence * 100).toFixed(0)}%`;
            }
            break;
            
        case 'CAPABILITY_FINISHED':
            showToast('Capability Executed', 'Capability executed successfully.');
            break;
            
        case 'REQUEST_COMPLETED':
            document.getElementById('voice-state').innerText = 'Idle';
            updateHUDLatencies(ev.data.telemetry);
            finalizeTrace(ev.data);
            setTimeout(resetPipeline, 3000);
            break;
            
        case 'ERROR_OCCURRED':
            document.getElementById('voice-state').innerText = 'Error';
            markPipelineError(ev.data.error || 'Unknown Error', ev.data.traceback);
            break;
    }
};

// ── Pipeline Functions ─────────────────────────────────────────
function updatePipelineStage(id, eventName, data) {
    const el = document.getElementById(id);
    if (!el) return;
    
    const statusSpan = el.querySelector('.status');
    const errDiv = el.querySelector('.stage-error');
    errDiv.style.display = 'none';

    // Remove old classes
    el.classList.remove('active', 'success', 'error');
    statusSpan.classList.remove('waiting', 'running', 'success', 'error');

    if (eventName.endsWith('_STARTED')) {
        el.classList.add('active');
        statusSpan.classList.add('running');
        statusSpan.innerText = 'Running...';
    } else if (eventName.endsWith('_FINISHED') || eventName.endsWith('_COMPLETED') || eventName === 'WAKE_WORD_DETECTED') {
        el.classList.add('success');
        statusSpan.classList.add('success');
        statusSpan.innerText = 'Success';
    }
    
    // Save to trace
    if (currentTrace) {
        currentTrace.stages.push({id, eventName, time: Date.now()});
    }
}

function resetPipeline() {
    document.querySelectorAll('.pipeline-stage').forEach(el => {
        el.classList.remove('active', 'success', 'error');
        const span = el.querySelector('.status');
        span.className = 'status waiting';
        span.innerText = 'Waiting';
        el.querySelector('.stage-error').style.display = 'none';
    });
}

function markPipelineError(errorMsg, traceback) {
    if (!investigationMode) return;
    
    // Find the currently active stage
    const activeEl = document.querySelector('.pipeline-stage.active') || document.querySelector('.pipeline-stage:last-of-type');
    if (activeEl) {
        activeEl.classList.remove('active', 'success');
        activeEl.classList.add('error');
        const span = activeEl.querySelector('.status');
        span.className = 'status error';
        span.innerText = 'Failed';
        
        const errDiv = activeEl.querySelector('.stage-error');
        errDiv.innerText = `Reason: ${errorMsg}\n\n${devMode && traceback ? traceback : ''}`;
        errDiv.style.display = 'block';
    }
}

// ── Traces ─────────────────────────────────────────────────────
function finalizeTrace(data) {
    if (!currentTrace) return;
    
    const duration = Date.now() - currentTrace.start;
    const container = document.getElementById('traces-container');
    
    const input = data.context?.user_input || "Unknown Command";
    const goal = data.context?.planner_response?.goal || "N/A";
    const tool = data.context?.planner_response?.type || "N/A";
    
    const traceHTML = `
        <div class="trace-item">
            <div class="trace-header" onclick="this.parentElement.classList.toggle('open')">
                <strong>"${input}"</strong>
                <span class="badge ${data.error ? 'error' : 'healthy'}">${data.error ? 'Failed' : 'Success'} - ${duration}ms</span>
            </div>
            <div class="trace-body">
                <div class="trace-step"><span class="step-name">Goal:</span> <span class="step-val">${goal}</span></div>
                <div class="trace-step"><span class="step-name">Tool:</span> <span class="step-val">${tool}</span></div>
                <div class="trace-step"><span class="step-name">Response:</span> <span class="step-val">${data.context?.final_response || 'N/A'}</span></div>
            </div>
        </div>
    `;
    container.insertAdjacentHTML('afterbegin', traceHTML);
    currentTrace = null;
}

// ── Sub-Panels ─────────────────────────────────────────────────
function updateHUDLatencies(telemetry) {
    if (!telemetry) return;
    document.getElementById('hud-planner').innerText = `${(telemetry.planner_duration || 0).toFixed(3)} s`;
    document.getElementById('hud-pipeline').innerText = `${(telemetry.total_request_duration || 0).toFixed(3)} s`;
}

function addTimelineEvent(ev) {
    const container = document.getElementById('event-timeline');
    
    let typeClass = 'info';
    if(ev.event.includes('ERROR') || ev.event.includes('FAILED')) typeClass = 'error';
    else if(ev.event.includes('COMPLETED') || ev.event.includes('FINISHED') || ev.event.includes('SUCCESS')) typeClass = 'success';
    else if(ev.event.includes('STARTED') || ev.event.includes('RUNNING')) typeClass = 'running';

    const div = document.createElement('div');
    div.className = `timeline-item ${typeClass}`;
    div.innerHTML = `
        <div class="timeline-header">
            <span class="timeline-time">${ev.time}</span>
            <span class="timeline-sys">${ev.event}</span>
        </div>
        ${devMode ? `<div class="timeline-data">${JSON.stringify(ev.data)}</div>` : ''}
    `;
    container.prepend(div);
    if(container.children.length > 500) container.removeChild(container.lastChild);
}

function addConsoleLog(ev) {
    const container = document.getElementById('debug-console');
    const div = document.createElement('div');
    div.className = 'log-line';
    
    let level = 'info';
    if(ev.event.includes('ERROR')) level = 'error';
    if(ev.event.includes('WARN')) level = 'warn';

    div.innerHTML = `
        <span class="time">[${ev.time}]</span>
        <span class="level ${level}">${level.toUpperCase()}</span>
        <span class="msg">${ev.event} - ${JSON.stringify(ev.data)}</span>
    `;
    container.prepend(div);
}

function showToast(title, msg) {
    const container = document.getElementById('toast-container');
    const div = document.createElement('div');
    div.className = 'toast';
    div.innerHTML = `<h4>${title}</h4><p>${msg}</p>`;
    container.appendChild(div);
    setTimeout(() => {
        div.style.opacity = '0';
        setTimeout(() => div.remove(), 300);
    }, 4000);
}

async function loadMemory() {
    if (!window.pywebview) return;
    try {
        const memories = await pywebview.api.get_memories();
        const container = document.getElementById('memory-container');
        container.innerHTML = '';
        
        memories.forEach(mem => {
            const card = `
                <div class="mem-card">
                    <div class="cat">${mem.category}</div>
                    <div class="title">${mem.title}</div>
                    <div class="value">${mem.value}</div>
                    <div class="mem-meta">
                        <span>Conf: ${(mem.confidence * 100).toFixed(0)}%</span>
                        <span>Src: ${mem.source}</span>
                    </div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', card);
        });
    } catch(e) {}
}

async function loadCapabilities() {
    if (!window.pywebview) return;
    try {
        const report = await pywebview.api.get_health_report();
        const container = document.getElementById('capabilities-container');
        container.innerHTML = '';
        
        Object.entries(report.capabilities).forEach(([id, status]) => {
            const isHealthy = status.toLowerCase() === 'healthy';
            const card = `
                <div class="cap-card">
                    <div class="cap-header">
                        <h3>${id}</h3>
                        <span class="badge ${isHealthy ? 'healthy' : 'error'}">${status}</span>
                    </div>
                    <div class="cap-stat"><span>Version</span> <span>1.0</span></div>
                    <div class="cap-stat"><span>Last State</span> <span>Waiting</span></div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', card);
        });
    } catch(e) {}
}

async function loadContext() {
    if (!window.pywebview) return;
    try {
        const ctx = await pywebview.api.get_interaction_context();
        const container = document.getElementById('context-container');
        container.innerHTML = '';
        
        const makeCard = (title, val) => `
            <div class="mem-card">
                <div class="cat">Context</div>
                <div class="title">${title}</div>
                <div class="value" style="font-family:'JetBrains Mono', monospace; font-size:0.85rem; max-height: 150px; overflow-y: auto;">
                    ${typeof val === 'object' ? JSON.stringify(val, null, 2) : (val || 'None')}
                </div>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', makeCard("Current User Input", ctx.user_input));
        container.insertAdjacentHTML('beforeend', makeCard("Planner Output", ctx.planner_response));
        container.insertAdjacentHTML('beforeend', makeCard("Last Response", ctx.final_response));
        container.insertAdjacentHTML('beforeend', makeCard("Permissions", ctx.permission_context));
        container.insertAdjacentHTML('beforeend', makeCard("System Details", ctx.system_context));
    } catch(e) {}
}
