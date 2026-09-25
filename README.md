# Reconstruct // AI-Assisted Digital Forensics Dashboard

> **Cybersecurity Hackathon Specification — Complete 5-Chunk Implementation**  
> Visual rigor inspired by Wireshark, Splunk, and CrowdStrike Falcon dashboards.

---

## 🛡️ Executive Architecture Overview

**Reconstruct** is an investigator-grade digital forensics workbench designed to triage, evaluate, and inspect file fragments carved from damaged, deleted, and slack storage media. Built with pixel-level discipline, strict 4px modular geometry, a high-contrast forensic dark theme, and dual typography split.

---

## 📐 Chunk-by-Chunk Implementation

### Chunk 1: Role, Project Context & Design System (`tokens.css`, `components.css`, `showcase.html`)
- **Spacing Scale:** Strict 4px modular progression (`4, 8, 12, 16, 24, 32, 48, 64px`). Zero arbitrary pixel values.
- **Vertical Rhythm:** 16px between form fields, 24px between sections, 32px between major page regions.
- **12-Column Responsive Grid:** 24px desktop gutters, 16px tablet gutters, 8px mobile gutters.
- **Forensic Dark Theme:** Three distinct near-black charcoal elevations:
  - Page Background: `#0B0F17` (Layer 0)
  - Card Surface: `#121824` (Layer 1)
  - Raised Elements: `#1A2234` (Layer 2)
  - *Light Mode Toggle supported with high-contrast daytime tuning.*
- **Strict Dual Typography:**
  - **UI Sans-Serif (`Inter`):** All interface chrome, prose, labels, and navigation.
  - **Forensic Monospace (`JetBrains Mono`):** Exclusively for technical values (SHA-256 hashes, block IDs, byte offsets, hex previews, timestamps, file sizes, and block counts).
- **Semantic Status & AI Accent System:**
  - `--status-high` (`#10B981` Emerald) + 12% opacity background tint.
  - `--status-medium` (`#F59E0B` Amber) + 12% opacity background tint.
  - `--status-low` (`#EF4444` Crimson) + 12% opacity background tint.
  - `--accent-ai` (`#06B6D4` Cyan) + 12% opacity background tint.
- **Component Geometry:** 4px radius for small chips, 6px radius for buttons/inputs/badges, 12px radius for cards; 1px uniform border width; zero shadows in dark mode.
- **Outline Icons:** Lucide icon set strictly restricted to two sizes: 16px (`--icon-dense`) and 20px (`--icon-ui`).

---

### Chunk 2: Main Dashboard & Recovery Results Triage (`dashboard.css`, `dashboard.js`, `index.html`)
- **Top Bar (64px fixed):** Left-aligned brand logo, center-right active scan status indicator (with cyan pulse and evaluated block counter), user profile icon, and dark/light mode toggle sharing a strict vertical-center axis.
- **Left Sidebar (240px collapsible to 64px):** Dashboard, Scans, Reports, Tokens, and Settings with 20px icons and 12px label gaps.
- **Summary Stat Row:** 4 equal-width, equal-height cards with status token accents (Total Items, High Confidence, Needs Review, Unrecoverable).
- **Filter & Sort Toolbar:** Single row, uniform 36px height (min 44px on mobile), spaced via flexbox `gap: 12px` without manual margins. Real-time search, type filtering, status filtering, and multi-field sorting.
- **Strict Column Alignment:**
  1. `Filename (inferred)`: **Left-aligned**
  2. `Artifact Type`: **Left-aligned** (with 16px icon)
  3. `AI Confidence Score`: **Right-aligned** (colored track + monospace %)
  4. `Status Badge`: **Center-aligned** (pixel-identical 24px height, 6px radius, paired 12% tint)
  5. `Block Count`: **Right-aligned** (monospace format)
  6. `Action Button`: **Center-aligned** (`View Detail →`)
- **Interactive State Toggles:** Populated (10 items), In-Progress scanning strip, and Centered Empty State.

---

### Chunk 3: Fragment Detail & Relationship View (`detail.css`, `index.html`)
- **Header Row:** Standard Chunk 1 back button (`Back to Recovery Results`), left-aligned filename with type icon, and pixel-identical Chunk 2 status badge.
- **Two-Column 60/40 Responsive Split:**
  - **Left Column (60%):** Bounded content preview (never overflows card). Monospace text/JSON for logs, inline vector render for images, and structured table/schema metadata with WAL frame telemetry for databases.
  - **Right Column (40%):** **Fragment Chain** — ordered vertical sequence of block chips (`#01` to `#N`) connected by 2px vertical sequence lines. Every chip has identical height (44px), uniform width (100%), 4px radius, monospace block ID, condition status dot, and interactive hover tooltip revealing raw byte offsets and block sizes.
- **Full-Width Confidence Breakdown:** Left-aligned list of 3-4 score-influencing factors (magic signature match, pointer continuity, sector corruption audit) using 16px outline status icons.

---

### Chunk 4: Scan Trigger, Progress & Upload Screen (`scan.css`, `scan.js`)
- **Single Centered Card (max-width 480px):** Smoothly transitions across three phases without dimension jitter:
  1. **Idle/Setup State:** Dashed drop zone (12px radius, dragover turns border to `--accent-ai`), fallback image path input with sample shortcut button, collapsible advanced sector options (4,096 B block size), and disabled-by-default primary CTA (≥44px touch target).
  2. **In-Progress State:** `--accent-ai` horizontal progress bar, live monospace counter (`1,842 / 3,000 blocks processed`), and an auto-scrolling telemetry feed logging timestamps, status dots, and sector discoveries.
  3. **Complete State:** Success summary with a 2x2 grid that **strictly reuses the Chunk 2 stat-card pattern**, followed by a primary CTA to navigate to Chunk 2 full results.

---

### Chunk 5: Responsive Pass, Interaction States & Accessibility
- **Responsive Architecture:**
  - **Mobile (375px):** Sidebar collapses to an **ergonomic bottom navigation tab bar** (justification: field forensics investigators require immediate, single-handed thumb access between primary views without hiding tools in multi-tap menus). Triage table features contained horizontal scrolling (`min-width: 680px`), stat cards stack into a clean grid, and touch targets meet the ≥44px requirement.
  - **Tablet (768px):** 16px grid gutters, 2-column stat grid, stacked 60/40 detail columns.
  - **Desktop (1280px+):** 24px grid gutters, 12-column grid layout, 60/40 split.
- **Interaction States Audit:** All buttons, table rows, fragment chips, drop zone, filters, and nav items feature defined `:hover`, `:active` (`transform: scale(0.98)`), `:focus-visible`, and `:disabled` states with consistent 150ms ease transitions.
- **Accessibility & Colorblind Compliance:** High-visibility focus ring (`outline: 2px solid var(--border-focus) !important; outline-offset: 2px; box-shadow: 0 0 0 3px var(--accent-ai-glow);`). Color is **never** the sole indicator of status — every status pill, dot, and badge is paired with explicit text labels and distinct outline icons.

---

## 🚀 How to Run Locally

```bash
# Start the zero-dependency local Node server
npm start
# or
node server.js
```

Open your browser to:
- **Main Triage Dashboard (Chunks 2, 3, 4, 5):** `http://localhost:3000`
- **Design Tokens Specification Showcase (Chunk 1):** `http://localhost:3000/showcase.html`
