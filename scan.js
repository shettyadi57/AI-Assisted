/**
 * RECONSTRUCT — SCAN TRIGGER & PROGRESS CONTROLLER (Chunk 4/5)
 * Manages the three states: Idle/Setup, In-Progress, and Complete.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Container & States
  const scanIdleState = document.getElementById('scan-idle-state');
  const scanProgressState = document.getElementById('scan-progress-state');
  const scanCompleteState = document.getElementById('scan-complete-state');

  // Idle State Controls
  const dropZone = document.getElementById('scan-drop-zone');
  const fileInput = document.getElementById('scan-file-input');
  const pathInput = document.getElementById('scan-path-input');
  const selectedFileDisplay = document.getElementById('drop-selected-file');
  const dropErrorMsg = document.getElementById('drop-error-msg');
  const scanCtaBtn = document.getElementById('scan-start-btn');
  const sampleTargetBtn = document.getElementById('sample-target-btn');

  // In-Progress State Controls
  const scanBarFill = document.getElementById('scan-bar-fill-live');
  const scanLiveCounter = document.getElementById('scan-live-counter-text');
  const scanPctBadge = document.getElementById('scan-pct-badge');
  const scanLogBox = document.getElementById('scan-live-log-box');

  // Complete State Controls
  const viewResultsBtn = document.getElementById('view-results-cta-btn');
  const rescanBtn = document.getElementById('scan-again-btn');

  let activeInterval = null;
  const VALID_EXTENSIONS = ['.dd', '.raw', '.img', '.bin', '.e01', '.iso', '.vmdk'];

  // ========================================================================
  // STATE 1: IDLE / SETUP CONTROLLER
  // ========================================================================

  function validateAndSelectFile(filename) {
    if (!filename) {
      if (selectedFileDisplay) selectedFileDisplay.style.display = 'none';
      if (dropErrorMsg) dropErrorMsg.classList.remove('active');
      if (dropZone) dropZone.classList.remove('error');
      if (scanCtaBtn) scanCtaBtn.disabled = true;
      return false;
    }

    const lower = filename.toLowerCase();
    const isValid = VALID_EXTENSIONS.some(ext => lower.endsWith(ext));

    if (isValid) {
      if (dropZone) dropZone.classList.remove('error');
      if (dropErrorMsg) dropErrorMsg.classList.remove('active');
      if (selectedFileDisplay) {
        selectedFileDisplay.textContent = `Selected: ${filename}`;
        selectedFileDisplay.style.display = 'inline-block';
      }
      if (scanCtaBtn) scanCtaBtn.disabled = false;
      return true;
    } else {
      if (dropZone) dropZone.classList.add('error');
      if (dropErrorMsg) {
        dropErrorMsg.textContent = `Invalid file type. Supported forensics targets: ${VALID_EXTENSIONS.join(', ')}`;
        dropErrorMsg.classList.add('active');
      }
      if (selectedFileDisplay) selectedFileDisplay.style.display = 'none';
      if (scanCtaBtn) scanCtaBtn.disabled = true;
      return false;
    }
  }

  // Drag and Drop Events
  if (dropZone && fileInput) {
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        fileInput.click();
      }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('drag-active');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('drag-active');
      });
    });

    dropZone.addEventListener('drop', (e) => {
      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        validateAndSelectFile(files[0].name);
        if (pathInput) pathInput.value = `/media/evidence/${files[0].name}`;
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (fileInput.files && fileInput.files.length > 0) {
        validateAndSelectFile(fileInput.files[0].name);
        if (pathInput) pathInput.value = `/media/evidence/${fileInput.files[0].name}`;
      }
    });
  }

  // Path Fallback Input
  if (pathInput) {
    pathInput.addEventListener('input', () => {
      validateAndSelectFile(pathInput.value.trim());
    });
  }

  // Quick Sample Target Button
  if (sampleTargetBtn && pathInput) {
    sampleTargetBtn.addEventListener('click', () => {
      const samplePath = '/mnt/evidence/drive_0xFD2.dd';
      pathInput.value = samplePath;
      validateAndSelectFile(samplePath);
    });
  }

  // ========================================================================
  // STATE TRANSITIONS: SETUP -> IN-PROGRESS -> COMPLETE
  // ========================================================================

  function showState(state) {
    if (!scanIdleState || !scanProgressState || !scanCompleteState) return;

    scanIdleState.style.display = state === 'idle' ? 'flex' : 'none';
    scanProgressState.style.display = state === 'progress' ? 'flex' : 'none';
    scanCompleteState.style.display = state === 'complete' ? 'flex' : 'none';

    if (typeof renderIcons === 'function') {
      renderIcons();
    }
  }

  // Start Recovery Scan
  if (scanCtaBtn) {
    scanCtaBtn.addEventListener('click', () => {
      startScanExecution();
    });
  }

  // Running telemetry logs data
  const TELEMETRY_EVENTS = [
    { pct: 5,  blocks: 150,  dot: 'var(--accent-ai)', text: 'Mounted disk target at physical sector offset <strong>0x00000000</strong>' },
    { pct: 18, blocks: 540,  dot: 'var(--status-high)', text: 'Found valid NTFS partition table & MFT mirror block' },
    { pct: 32, blocks: 960,  dot: 'var(--status-high)', text: 'Carved SQLite format 3 database header (BLK-0x004F:SEC-8192)' },
    { pct: 45, blocks: 1350, dot: 'var(--status-high)', text: 'Identified Adobe PDF v1.7 linearized catalog streams' },
    { pct: 60, blocks: 1800, dot: 'var(--status-medium)', text: 'Recovered fragmented JPEG surveillance frame (SOI marker)' },
    { pct: 72, blocks: 2160, dot: 'var(--status-medium)', text: 'Carved syslog UTF-8 records with 128-byte slack drift' },
    { pct: 85, blocks: 2550, dot: 'var(--status-low)', text: 'Detected corrupted ELF executable section table in cluster slack' },
    { pct: 95, blocks: 2850, dot: 'var(--status-low)', text: 'Identified zero-filled slack space cluster run (0.0% entropy)' },
    { pct: 100, blocks: 3000, dot: 'var(--status-high)', text: 'Deep carve finished: <strong>10 reconstructed items</strong> ready' }
  ];

  function getTimestamp() {
    const now = new Date();
    return now.toTimeString().split(' ')[0] + '.' + String(now.getMilliseconds()).padStart(3, '0').slice(0, 2);
  }

  function startScanExecution() {
    showState('progress');

    // Reset progress
    if (scanBarFill) scanBarFill.style.width = '0%';
    if (scanLiveCounter) scanLiveCounter.textContent = '0 / 3,000 blocks';
    if (scanPctBadge) scanPctBadge.textContent = '0.0%';
    if (scanLogBox) scanLogBox.innerHTML = '';

    let eventIndex = 0;
    const totalBlocks = 3000;

    if (activeInterval) clearInterval(activeInterval);

    activeInterval = setInterval(() => {
      if (eventIndex >= TELEMETRY_EVENTS.length) {
        clearInterval(activeInterval);
        setTimeout(() => {
          showState('complete');
        }, 500);
        return;
      }

      const evt = TELEMETRY_EVENTS[eventIndex];
      const curPct = evt.pct;
      const curBlocks = evt.blocks;

      // Update UI
      if (scanBarFill) scanBarFill.style.width = `${curPct}%`;
      if (scanLiveCounter) scanLiveCounter.textContent = `${curBlocks.toLocaleString()} / ${totalBlocks.toLocaleString()} blocks processed`;
      if (scanPctBadge) scanPctBadge.textContent = `${curPct.toFixed(1)}%`;

      // Append log entry
      if (scanLogBox) {
        const logLine = document.createElement('div');
        logLine.className = 'scan-log-line';
        logLine.innerHTML = `
          <span class="log-dot" style="background-color: ${evt.dot};"></span>
          <span class="log-time">[${getTimestamp()}]</span>
          <span class="log-text">${evt.text}</span>
        `;
        scanLogBox.appendChild(logLine);
        scanLogBox.scrollTop = scanLogBox.scrollHeight;
      }

      eventIndex++;
    }, 350);
  }

  // Complete State: View Full Results CTA -> Navigate to Chunk 2 Dashboard
  if (viewResultsBtn) {
    viewResultsBtn.addEventListener('click', () => {
      // Trigger navigation back to populated triage dashboard
      const navDashboard = document.querySelector('a.nav-item[href="index.html"]');
      const scanView = document.getElementById('scan-view-container');
      const triageView = document.getElementById('triage-view-container');
      const detailView = document.getElementById('detail-view-container');

      if (scanView) scanView.style.display = 'none';
      if (detailView) detailView.style.display = 'none';
      if (triageView) triageView.style.display = 'flex';

      // Set sidebar active state
      document.querySelectorAll('.sidebar-nav .nav-item').forEach(i => i.classList.remove('active'));
      if (navDashboard) navDashboard.classList.add('active');

      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // Rescan / Start Another Scan
  if (rescanBtn) {
    rescanBtn.addEventListener('click', () => {
      showState('idle');
    });
  }

  // Expose global function to switch to Scan View from anywhere
  window.openScanTriggerScreen = function() {
    const scanView = document.getElementById('scan-view-container');
    const triageView = document.getElementById('triage-view-container');
    const detailView = document.getElementById('detail-view-container');

    if (triageView) triageView.style.display = 'none';
    if (detailView) detailView.style.display = 'none';
    if (scanView) scanView.style.display = 'flex';

    showState('idle');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
});
