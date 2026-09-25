/**
 * RECONSTRUCT — RECOVERY RESULTS DASHBOARD CONTROLLER (Chunk 2/5)
 * Handles table filtering, sorting, sidebar collapsing, and triage state transitions.
 */

// Forensic Recovery Dataset
const FORENSIC_ITEMS = [
  {
    id: "REC-001",
    filename: "evidence_vault.db",
    meta: "SQLite 3 format 3 (WAL mode active)",
    type: "database",
    typeName: "Database",
    typeIcon: "database",
    confidence: 99.4,
    status: "high",
    statusLabel: "99.4% Confident",
    statusBadgeClass: "badge-status-high",
    blockCount: 1420,
    hash: "3a8f102c91b8..."
  },
  {
    id: "REC-002",
    filename: "incident_report_2026_q3.pdf",
    meta: "Adobe PDF v1.7 (xref reconstructed)",
    type: "document",
    typeName: "Document",
    typeIcon: "fileText",
    confidence: 96.8,
    status: "high",
    statusLabel: "96.8% Confident",
    statusBadgeClass: "badge-status-high",
    blockCount: 852,
    hash: "7f4c01e92d8a..."
  },
  {
    id: "REC-003",
    filename: "$MFT_Mirror_Fragment.bin",
    meta: "NTFS MFT mirror segment (8 records)",
    type: "binary",
    typeName: "Binary",
    typeIcon: "fileCode",
    confidence: 94.1,
    status: "high",
    statusLabel: "94.1% Confident",
    statusBadgeClass: "badge-status-high",
    blockCount: 320,
    hash: "91b4c73a110f..."
  },
  {
    id: "REC-004",
    filename: "frame_capture_cam04.jpg",
    meta: "JFIF JPEG (valid SOI/EOI bounds)",
    type: "image",
    typeName: "Image",
    typeIcon: "fileImage",
    confidence: 78.5,
    status: "medium",
    statusLabel: "78.5% Review",
    statusBadgeClass: "badge-status-medium",
    blockCount: 540,
    hash: "45a89df2001c..."
  },
  {
    id: "REC-005",
    filename: "corporate_seal_fragment.png",
    meta: "PNG chunk sequence (missing IEND)",
    type: "image",
    typeName: "Image",
    typeIcon: "fileImage",
    confidence: 68.2,
    status: "medium",
    statusLabel: "68.2% Review",
    statusBadgeClass: "badge-status-medium",
    blockCount: 216,
    hash: "12d8a90bb4c1..."
  },
  {
    id: "REC-006",
    filename: "auth_audit.log",
    meta: "UTF-8 Syslog stream (neural carved)",
    type: "document",
    typeName: "Document",
    typeIcon: "fileText",
    confidence: 61.9,
    status: "medium",
    statusLabel: "61.9% Review",
    statusBadgeClass: "badge-status-medium",
    blockCount: 184,
    hash: "88cc401f993e..."
  },
  {
    id: "REC-007",
    filename: "backup_keys_enc.tar.gz",
    meta: "GZIP archive (truncated CRC32 trailer)",
    type: "archive",
    typeName: "Archive",
    typeIcon: "archive",
    confidence: 54.0,
    status: "medium",
    statusLabel: "54.0% Review",
    statusBadgeClass: "badge-status-medium",
    blockCount: 960,
    hash: "e5401188ba92..."
  },
  {
    id: "REC-008",
    filename: "malware_dropper.elf",
    meta: "ELF 64-bit LSB (section headers wiped)",
    type: "binary",
    typeName: "Binary",
    typeIcon: "fileCode",
    confidence: 24.5,
    status: "low",
    statusLabel: "24.5% Corrupted",
    statusBadgeClass: "badge-status-low",
    blockCount: 410,
    hash: "00fa9912bc87..."
  },
  {
    id: "REC-009",
    filename: "unallocated_sector_slack.raw",
    meta: "Zero-filled slack space cluster run",
    type: "binary",
    typeName: "Binary",
    typeIcon: "fileCode",
    confidence: 0.0,
    status: "low",
    statusLabel: "0.0% Corrupted",
    statusBadgeClass: "badge-status-low",
    blockCount: 1024,
    hash: "000000000000..."
  },
  {
    id: "REC-010",
    filename: "fve_metadata_block.bin",
    meta: "BitLocker metadata block (unreadable)",
    type: "binary",
    typeName: "Binary",
    typeIcon: "fileCode",
    confidence: 18.2,
    status: "low",
    statusLabel: "18.2% Corrupted",
    statusBadgeClass: "badge-status-low",
    blockCount: 64,
    hash: "c4118809aa1e..."
  }
];

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const tableBody = document.getElementById('triage-table-body');
  const searchInput = document.getElementById('search-input');
  const typeFilter = document.getElementById('type-filter');
  const statusFilter = document.getElementById('status-filter');
  const sortSelect = document.getElementById('sort-select');
  const rowCountDisplay = document.getElementById('row-count-display');
  const sidebar = document.getElementById('app-sidebar');
  const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
  const sidebarToggleIcon = document.getElementById('sidebar-toggle-icon');
  
  // State Containers
  const tableContainer = document.getElementById('table-wrapper');
  const emptyStateContainer = document.getElementById('empty-state-wrapper');
  const scanningStateContainer = document.getElementById('scanning-state-wrapper');
  const scanProgressStrip = document.getElementById('scan-progress-strip');
  const activeScanIndicator = document.getElementById('active-scan-indicator');

  // Stats Counters
  const statTotal = document.getElementById('stat-total');
  const statHigh = document.getElementById('stat-high');
  const statMedium = document.getElementById('stat-medium');
  const statLow = document.getElementById('stat-low');

  // Sidebar Collapse / Expand
  if (sidebarToggleBtn && sidebar) {
    sidebarToggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      const isCollapsed = sidebar.classList.contains('collapsed');
      if (sidebarToggleIcon) {
        sidebarToggleIcon.setAttribute('data-icon', isCollapsed ? 'panelLeftOpen' : 'panelLeftClose');
      }
      if (typeof renderIcons === 'function') {
        renderIcons();
      }
    });
  }

  // Triage View Switcher (Populated / Scanning / Empty)
  const stateBtns = document.querySelectorAll('.state-btn');
  stateBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      stateBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const targetState = btn.getAttribute('data-state');
      setDashboardState(targetState);
    });
  });

  function setDashboardState(state) {
    if (state === 'empty') {
      tableContainer.style.display = 'none';
      scanningStateContainer.style.display = 'none';
      emptyStateContainer.style.display = 'block';
      scanProgressStrip.classList.remove('active');
      activeScanIndicator.style.display = 'none';
      updateStatsCounters(0, 0, 0, 0);
    } else if (state === 'scanning') {
      tableContainer.style.display = 'none';
      emptyStateContainer.style.display = 'none';
      scanningStateContainer.style.display = 'block';
      scanProgressStrip.classList.add('active');
      activeScanIndicator.style.display = 'inline-flex';
      updateStatsCounters('...', '...', '...', '...');
    } else {
      // Populated default
      emptyStateContainer.style.display = 'none';
      scanningStateContainer.style.display = 'none';
      tableContainer.style.display = 'block';
      scanProgressStrip.classList.remove('active');
      activeScanIndicator.style.display = 'inline-flex';
      renderTable();
    }
    if (typeof renderIcons === 'function') {
      renderIcons();
    }
  }

  function updateStatsCounters(total, high, medium, low) {
    if (statTotal) statTotal.textContent = total;
    if (statHigh) statHigh.textContent = high;
    if (statMedium) statMedium.textContent = medium;
    if (statLow) statLow.textContent = low;
  }

  // Render Table with strict column alignment:
  // Col 1: Filename -> Left-aligned
  // Col 2: Type -> Left-aligned
  // Col 3: Confidence Score -> Right-aligned
  // Col 4: Status Badge -> Center-aligned
  // Col 5: Block Count -> Right-aligned
  // Col 6: Action -> Center-aligned
  function renderTable() {
    if (!tableBody) return;

    let items = [...FORENSIC_ITEMS];

    // Filter by Search Query
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
    if (query) {
      items = items.filter(item => 
        item.filename.toLowerCase().includes(query) ||
        item.meta.toLowerCase().includes(query) ||
        item.id.toLowerCase().includes(query)
      );
    }

    // Filter by Type
    const selectedType = typeFilter ? typeFilter.value : 'all';
    if (selectedType !== 'all') {
      items = items.filter(item => item.type === selectedType);
    }

    // Filter by Status
    const selectedStatus = statusFilter ? statusFilter.value : 'all';
    if (selectedStatus !== 'all') {
      items = items.filter(item => item.status === selectedStatus);
    }

    // Sort
    const sortVal = sortSelect ? sortSelect.value : 'confidence-desc';
    if (sortVal === 'confidence-desc') {
      items.sort((a, b) => b.confidence - a.confidence);
    } else if (sortVal === 'confidence-asc') {
      items.sort((a, b) => a.confidence - b.confidence);
    } else if (sortVal === 'filename-asc') {
      items.sort((a, b) => a.filename.localeCompare(b.filename));
    } else if (sortVal === 'blocks-desc') {
      items.sort((a, b) => b.blockCount - a.blockCount);
    }

    // Update Summary Stats with original totals
    const totalCount = FORENSIC_ITEMS.length;
    const highCount = FORENSIC_ITEMS.filter(i => i.status === 'high').length;
    const mediumCount = FORENSIC_ITEMS.filter(i => i.status === 'medium').length;
    const lowCount = FORENSIC_ITEMS.filter(i => i.status === 'low').length;
    updateStatsCounters(totalCount, highCount, mediumCount, lowCount);

    if (rowCountDisplay) {
      rowCountDisplay.textContent = `Showing ${items.length} of ${totalCount} recovered items`;
    }

    if (items.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; padding: var(--space-32); color: var(--text-muted);">
            No matching forensic items found for the active filter query.
          </td>
        </tr>
      `;
      return;
    }

    // Generate table rows
    tableBody.innerHTML = items.map(item => {
      const barClass = item.status === 'high' 
        ? 'confidence-bar-high' 
        : item.status === 'medium' 
          ? 'confidence-bar-medium' 
          : 'confidence-bar-low';

      return `
        <tr tabindex="0" data-item-id="${item.id}">
          <!-- Col 1: Filename (Left-aligned) -->
          <td class="col-filename">
            <div class="filename-cell">
              <span class="filename-text">${item.filename}</span>
              <span class="filename-meta">${item.meta} • <span style="color: var(--accent-ai);">${item.id}</span></span>
            </div>
          </td>

          <!-- Col 2: Type (Left-aligned) -->
          <td class="col-type">
            <span class="type-cell">
              <span data-icon="${item.typeIcon}" data-icon-size="16"></span>
              <span>${item.typeName}</span>
            </span>
          </td>

          <!-- Col 3: Confidence Score (Right-aligned) -->
          <td class="col-confidence">
            <div class="confidence-cell">
              <div class="confidence-bar-track">
                <div class="confidence-bar-fill ${barClass}" style="width: ${item.confidence}%;"></div>
              </div>
              <span class="confidence-pct">${item.confidence.toFixed(1)}%</span>
            </div>
          </td>

          <!-- Col 4: Status Badge (Center-aligned) -->
          <td class="col-status">
            <div class="status-badge-cell">
              <span class="badge ${item.statusBadgeClass}">
                ${item.status === 'high' ? '<span class="pulse-indicator" style="background-color: var(--status-high);"></span>' : ''}
                ${item.status === 'medium' ? '<span class="pulse-indicator" style="background-color: var(--status-medium);"></span>' : ''}
                ${item.status === 'low' ? '<span class="pulse-indicator" style="background-color: var(--status-low);"></span>' : ''}
                ${item.statusLabel}
              </span>
            </div>
          </td>

          <!-- Col 5: Block Count (Right-aligned) -->
          <td class="col-blocks">
            <span class="block-count-cell">${item.blockCount.toLocaleString()} BLKS</span>
          </td>

          <!-- Col 6: Action (Center-aligned) -->
          <td class="col-action">
            <button class="action-btn" data-detail-id="${item.id}">
              <span>View Detail</span>
              <span data-icon="arrowRight" data-icon-size="16"></span>
            </button>
          </td>
        </tr>
      `;
    }).join('');

    // Re-render icons
    if (typeof renderIcons === 'function') {
      renderIcons();
    }

    // Attach row click & button listeners
    tableBody.querySelectorAll('[data-detail-id]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const id = btn.getAttribute('data-detail-id');
        triggerDetailView(id);
      });
    });

    tableBody.querySelectorAll('tr[data-item-id]').forEach(row => {
      row.addEventListener('click', () => {
        const id = row.getAttribute('data-item-id');
        triggerDetailView(id);
      });
    });
  }

  // Toast / Detail notification (Chunk 3 handover)
  function triggerDetailView(id) {
    const item = FORENSIC_ITEMS.find(i => i.id === id);
    const itemName = item ? item.filename : id;
    if (typeof showToast === 'function') {
      showToast(`Selected: ${itemName} (Detail view builds in Chunk 3)`);
    } else {
      const toast = document.getElementById('toast');
      if (toast) {
        toast.textContent = `Selected: ${itemName} (Detail view builds in Chunk 3)`;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 2500);
      }
    }
  }

  // Event Listeners for Filters & Sorting
  if (searchInput) searchInput.addEventListener('input', renderTable);
  if (typeFilter) typeFilter.addEventListener('change', renderTable);
  if (statusFilter) statusFilter.addEventListener('change', renderTable);
  if (sortSelect) sortSelect.addEventListener('change', renderTable);

  // Initial Table Render
  renderTable();

  // Reset Filters button
  const resetBtn = document.getElementById('reset-filters-btn');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      if (searchInput) searchInput.value = '';
      if (typeFilter) typeFilter.value = 'all';
      if (statusFilter) statusFilter.value = 'all';
      if (sortSelect) sortSelect.value = 'confidence-desc';
      renderTable();
    });
  }

  // Start a Scan CTA Button (In Empty State)
  const startScanBtn = document.getElementById('start-scan-btn');
  if (startScanBtn) {
    startScanBtn.addEventListener('click', () => {
      // Transition to scanning state then populated state
      const scanBtn = document.querySelector('.state-btn[data-state="scanning"]');
      if (scanBtn) scanBtn.click();
      setTimeout(() => {
        const popBtn = document.querySelector('.state-btn[data-state="populated"]');
        if (popBtn) popBtn.click();
      }, 2500);
    });
  }
});
