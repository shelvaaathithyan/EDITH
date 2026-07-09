const orb = document.getElementById('ai-orb');
const statusText = document.getElementById('status-text');
const subText = document.getElementById('sub-text');
const pulse = document.getElementById('pulse-ring');

const StateConfig = {
    'STARTING': { text: 'Starting', sub: 'Initializing core systems...', class: 'state-ready' },
    'INITIALIZING': { text: 'Initializing', sub: 'Loading AI models...', class: 'state-ready' },
    'READY': { text: 'Ready', sub: 'Waiting for "Hello EDITH"', class: 'state-ready' },
    'LISTENING': { text: 'Listening', sub: 'I am listening...', class: 'state-listening' },
    'UNDERSTANDING': { text: 'Understanding', sub: 'Processing speech...', class: 'state-understanding' },
    'PLANNING': { text: 'Planning', sub: 'Generating execution plan...', class: 'state-planning' },
    'EXECUTING': { text: 'Executing', sub: 'Running tools...', class: 'state-executing' },
    'RESPONDING': { text: 'Speaking', sub: '...', class: 'state-responding' },
    'IDLE': { text: 'Idle', sub: 'Waiting for "Hello EDITH"', class: 'state-ready' },
    'ERROR': { text: 'Error', sub: 'Something went wrong.', class: 'state-error' },
    'SHUTTING_DOWN': { text: 'Offline', sub: 'System is shutting down.', class: 'state-ready' }
};

// This function will be called by Python via pywebview
window.updateState = function(stateName) {
    console.log("State transition:", stateName);
    
    const config = StateConfig[stateName] || StateConfig['READY'];
    
    // Update Text
    statusText.innerText = config.text;
    subText.innerText = config.sub;
    
    // Reset classes
    orb.className = 'orb';
    orb.classList.add(config.class);
    
// Special handling for pulse animation
    if (stateName === 'LISTENING') {
        pulse.style.display = 'block';
    } else {
        pulse.style.display = 'none';
    }
    
    // Update debug panel state
    document.getElementById('debug-state').innerText = stateName;
    addTimelineEvent(stateName);
};

// Toggle Debug Panel with Ctrl+D
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key.toLowerCase() === 'd') {
        const panel = document.getElementById('debug-panel');
        if (panel.style.display === 'none') {
            panel.style.display = 'block';
        } else {
            panel.style.display = 'none';
        }
    }
});

// Received from Python via pywebview
window.updateDebug = function(payloadStr) {
    try {
        const payload = JSON.parse(payloadStr);
        if (payload.transcription) document.getElementById('debug-transcription').innerText = payload.transcription;
        if (payload.goal) document.getElementById('debug-goal').innerText = payload.goal;
        if (payload.type) document.getElementById('debug-type').innerText = payload.type;
        if (payload.confidence) document.getElementById('debug-confidence').innerText = payload.confidence;
        if (payload.latency) document.getElementById('debug-latency').innerText = payload.latency + 's';
        if (payload.pipeline_duration) document.getElementById('debug-pipeline-dur').innerText = payload.pipeline_duration + 's';
        if (payload.response) document.getElementById('debug-response').innerText = payload.response;
        if (payload.json_dump) document.getElementById('debug-json').innerText = payload.json_dump;
    } catch (e) {
        console.error("Failed to parse debug payload:", e);
    }
};

let timelineCount = 0;
function addTimelineEvent(eventName) {
    const tl = document.getElementById('debug-timeline');
    if (timelineCount > 0) {
        tl.innerHTML += ' <span>&rarr;</span> ';
    }
    tl.innerHTML += `<span>${eventName}</span>`;
    timelineCount++;
    if (timelineCount > 15) {
        tl.innerHTML = `<span>${eventName}</span>`;
        timelineCount = 1;
    }
}

// Initial state
window.updateState('READY');
