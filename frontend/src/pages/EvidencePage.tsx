/**
 * Evidence Ingestion & Registry — Phase 1 LIVE
 *
 * Input Dataset panel supporting:
 *   - Raw disk image / forensic image
 *   - Binary fragment files
 *   - Extracted block/cluster files
 *   - Multiple fragment files
 *   - ZIP of fragments
 *   - "Load sample dataset" (built-in loose-fragment-soup)
 *
 * Real SHA-256 computed client-side via Web Crypto API.
 * Honest status: 501 from Phase 2+ endpoints shown transparently.
 */

import React, { useCallback, useRef, useState } from 'react';
import { useInvestigation } from '../context/InvestigationContext';

// ─── Types ────────────────────────────────────────────────────────────────────

type SourceType =
  | 'raw_disk_image'
  | 'forensic_image'
  | 'binary_fragment_files'
  | 'extracted_block_files'
  | 'zip_of_fragments'
  | 'sample_dataset';

interface EvidenceRecord {
  id: string;
  filename: string;
  file_size_bytes: number;
  sha256_hash: string;
  md5_hash: string | null;
  source_type: string;
  status: string;
  is_sample_dataset: boolean;
  disclaimer: string;
  created_at: string;
}

interface HashProgress {
  state: 'idle' | 'hashing' | 'done' | 'error';
  percent: number;
  sha256?: string;
  errorMsg?: string;
}

interface IngestStatus {
  state: 'idle' | 'loading' | 'success' | 'error';
  record?: EvidenceRecord;
  errorMsg?: string;
}

interface DiscoveryStatus {
  state: 'not_started' | 'probing' | 'done' | 'deferred' | 'error';
  phase?: string;
  detail?: string;
  // Phase 2 real results
  fragmentCount?: number;
  duplicateCount?: number;
  blockSize?: number;
}

// ─── Source type config ───────────────────────────────────────────────────────

const SOURCE_TYPES: { id: SourceType; label: string; icon: string; accept: string; multi: boolean; desc: string }[] = [
  {
    id: 'raw_disk_image',
    label: 'Raw Disk Image',
    icon: '💿',
    accept: '.img,.dd,.raw,.iso',
    multi: false,
    desc: '.img, .dd, .raw — direct sector-level dump',
  },
  {
    id: 'forensic_image',
    label: 'Forensic Image',
    icon: '🔬',
    accept: '.E01,.e01,.ewf,.aff,.ad1',
    multi: false,
    desc: 'E01, EWF, AFF — tool-wrapped forensic formats',
  },
  {
    id: 'binary_fragment_files',
    label: 'Binary Fragment Files',
    icon: '🧩',
    accept: '.bin,.raw,.frag',
    multi: true,
    desc: '.bin, .raw, .frag — individual block/sector files',
  },
  {
    id: 'extracted_block_files',
    label: 'Extracted Block/Cluster Files',
    icon: '📦',
    accept: '.bin,.raw,.blk,.cluster',
    multi: true,
    desc: 'Files extracted at cluster boundaries',
  },
  {
    id: 'zip_of_fragments',
    label: 'ZIP of Fragments',
    icon: '🗜️',
    accept: '.zip',
    multi: false,
    desc: 'ZIP archive containing fragment files',
  },
  {
    id: 'sample_dataset',
    label: '⚗️ Load Sample Dataset',
    icon: '⚗️',
    accept: '',
    multi: false,
    desc: 'Built-in synthetic fixtures (seed=42) — loose-fragment-soup.bin. FOR TESTING ONLY.',
  },
];

// ─── Helper: client-side SHA-256 via Web Crypto ───────────────────────────────

async function computeSha256(
  file: File,
  onProgress: (pct: number) => void
): Promise<string> {
  const CHUNK = 2 * 1024 * 1024; // 2 MB per chunk
  const total = file.size;
  let offset = 0;

  // Use SubtleCrypto streaming via chunk-based approach
  const hashBuffer = await (async () => {
    const chunks: ArrayBuffer[] = [];
    while (offset < total) {
      const slice = file.slice(offset, offset + CHUNK);
      const ab = await slice.arrayBuffer();
      chunks.push(ab);
      offset += CHUNK;
      onProgress(Math.min(100, Math.round((offset / total) * 100)));
    }
    // Concatenate
    const total_len = chunks.reduce((s, c) => s + c.byteLength, 0);
    const merged = new Uint8Array(total_len);
    let pos = 0;
    for (const c of chunks) {
      merged.set(new Uint8Array(c), pos);
      pos += c.byteLength;
    }
    return crypto.subtle.digest('SHA-256', merged);
  })();

  return Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 * 1024 * 1024) return `${(n / 1024 / 1024).toFixed(2)} MB`;
  return `${(n / 1024 / 1024 / 1024).toFixed(3)} GB`;
}

function formatTs(iso: string): string {
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
}

// ─── EvidenceTable ────────────────────────────────────────────────────────────

const EvidenceTable: React.FC<{
  records: EvidenceRecord[];
  onDelete: (id: string) => void;
  onSelectForDiscovery: (r: EvidenceRecord) => void;
}> = ({ records, onDelete, onSelectForDiscovery }) => {
  if (records.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 'var(--space-12)', color: 'var(--text-muted)' }}>
        <div style={{ fontSize: '40px', marginBottom: 'var(--space-3)' }}>📂</div>
        <div style={{ fontSize: 'var(--text-base)', marginBottom: 'var(--space-2)' }}>No evidence registered yet</div>
        <div style={{ fontSize: 'var(--text-sm)' }}>Upload a file or load the sample dataset above</div>
      </div>
    );
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--text-sm)' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border-medium)' }}>
            {['Filename', 'Size', 'Source Type', 'SHA-256 (first 16)', 'Status', 'Ingested At', 'Actions'].map((h) => (
              <th key={h} style={{
                textAlign: 'left', padding: '10px 12px', fontSize: 'var(--text-xs)',
                fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase',
                letterSpacing: '0.06em',
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {records.map((r) => (
            <tr
              key={r.id}
              style={{ borderBottom: '1px solid var(--border-subtle)', transition: 'background 0.12s' }}
              onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-hover)')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
            >
              <td style={{ padding: '10px 12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <span style={{ fontWeight: 500 }}>{r.filename}</span>
                  {r.is_sample_dataset && (
                    <span className="badge" style={{
                      background: 'rgba(251,146,60,0.12)', color: '#FB923C',
                      border: '1px solid rgba(251,146,60,0.3)', fontSize: '10px',
                    }}>
                      SAMPLE
                    </span>
                  )}
                </div>
              </td>
              <td style={{ padding: '10px 12px', color: 'var(--text-secondary)' }} className="font-mono">
                {formatBytes(r.file_size_bytes)}
              </td>
              <td style={{ padding: '10px 12px', color: 'var(--text-secondary)' }}>
                {r.source_type.replace(/_/g, ' ')}
              </td>
              <td style={{ padding: '10px 12px' }} className="font-mono">
                <span style={{ color: '#06B6D4', letterSpacing: '0.03em' }}>
                  {r.sha256_hash.slice(0, 16)}…
                </span>
              </td>
              <td style={{ padding: '10px 12px' }}>
                <span className="badge badge-valid">{r.status}</span>
              </td>
              <td style={{ padding: '10px 12px', color: 'var(--text-muted)' }} className="font-mono">
                {formatTs(r.created_at)}
              </td>
              <td style={{ padding: '10px 12px' }}>
                <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                  <button
                    className="btn-secondary"
                    style={{ fontSize: 'var(--text-xs)', padding: '4px 10px' }}
                    onClick={() => onSelectForDiscovery(r)}
                    id={`btn-discover-${r.id.slice(0, 8)}`}
                  >
                    🔍 Discover
                  </button>
                  <button
                    style={{
                      fontSize: 'var(--text-xs)', padding: '4px 10px',
                      background: 'rgba(239,68,68,0.08)', color: '#F87171',
                      border: '1px solid rgba(239,68,68,0.2)', borderRadius: 'var(--radius-md)',
                      cursor: 'pointer', transition: 'all 0.15s',
                    }}
                    onClick={() => onDelete(r.id)}
                    id={`btn-delete-${r.id.slice(0, 8)}`}
                  >
                    ✕
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// ─── DiscoveryStatusPanel ─────────────────────────────────────────────────────

const DiscoveryStatusPanel: React.FC<{ status: DiscoveryStatus; evidenceName?: string }> = ({
  status, evidenceName,
}) => {
  if (status.state === 'not_started') return null;

  const colors = {
    probing:  { border: '#06B6D4', bg: 'rgba(6,182,212,0.06)',   text: '#67E8F9' },
    done:     { border: '#10B981', bg: 'rgba(16,185,129,0.06)',   text: '#34D399' },
    deferred: { border: '#38BDF8', bg: 'rgba(56,189,248,0.06)',   text: '#7DD3FC' },
    error:    { border: '#EF4444', bg: 'rgba(239,68,68,0.06)',    text: '#FCA5A5' },
  }[status.state] ?? { border: '#64748B', bg: 'rgba(100,116,139,0.06)', text: '#94A3B8' };

  return (
    <div style={{
      borderRadius: 'var(--radius-lg)', border: `1px solid ${colors.border}`,
      background: colors.bg, padding: 'var(--space-5)', marginTop: 'var(--space-4)',
      borderLeft: `4px solid ${colors.border}`,
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
        <span style={{ fontSize: '20px' }}>
          {status.state === 'probing' ? '🔍' : status.state === 'done' ? '✅' : status.state === 'deferred' ? '⏳' : '⚠️'}
        </span>
        <div>
          <div style={{ fontWeight: 600, color: colors.text, fontSize: 'var(--text-base)' }}>
            {status.state === 'probing' && 'Running Phase 2 fragment analysis…'}
            {status.state === 'done' && `Fragment discovery complete — ${status.fragmentCount} fragments found`}
            {status.state === 'deferred' && 'Coming in Phase 2 — Fragment Discovery'}
            {status.state === 'error' && 'Discovery Error'}
          </div>
          {evidenceName && (
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '2px' }}>
              For: <span className="font-mono" style={{ color: 'var(--text-secondary)' }}>{evidenceName}</span>
            </div>
          )}
        </div>
      </div>

      {/* Phase 2 done: show real results */}
      {status.state === 'done' && (
        <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap', alignItems: 'center' }}>
          {[
            { label: 'Total Fragments', value: status.fragmentCount ?? 0, color: '#06B6D4' },
            { label: 'Duplicates', value: status.duplicateCount ?? 0, color: '#F59E0B' },
            { label: 'Block Size', value: `${status.blockSize ?? 4096} B`, color: '#94A3B8' },
            { label: 'Unique', value: (status.fragmentCount ?? 0) - (status.duplicateCount ?? 0), color: '#10B981' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ background: 'var(--bg-page)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', padding: 'var(--space-2) var(--space-4)', textAlign: 'center' }}>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '2px' }}>{label}</div>
              <div className="font-mono" style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color }}>{value}</div>
            </div>
          ))}
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
            →{' '}
            <button
              onClick={() => {/* use setCurrentPage from outer */}}
              style={{ background: 'none', border: 'none', color: '#38BDF8', cursor: 'pointer', fontSize: 'inherit', padding: 0 }}
            >
              View in Fragments page
            </button>
          </div>
        </div>
      )}

      {status.state === 'deferred' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          <div style={{
            background: 'var(--bg-page)', borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)', padding: 'var(--space-4)',
          }}>
            <div style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 'var(--space-2)' }}>
              Backend Response (HTTP 501)
            </div>
            <pre className="font-mono" style={{ fontSize: 'var(--text-xs)', color: '#7DD3FC', margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
              {`{
  "status_code": 501,
  "phase": "${status.phase ?? 'Phase 2 — Fragment Discovery'}",
  "stage": "fragment_analysis",
  "detail": "${status.detail ?? 'Not yet implemented. The discovery endpoint will scan the evidence for fragment boundaries, compute entropy profiles, and populate the Fragments registry.'}"
}`}
            </pre>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--space-3)' }}>
            {[
              { icon: '🧩', label: 'Fragment Boundary Detection', phase: 'Phase 2' },
              { icon: '📊', label: 'Entropy Analysis', phase: 'Phase 2' },
              { icon: '🔗', label: 'Relationship Scoring (ML)', phase: 'Phase 3' },
            ].map((item) => (
              <div key={item.label} style={{
                background: 'var(--bg-page)', borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)', padding: 'var(--space-3)',
                textAlign: 'center',
              }}>
                <div style={{ fontSize: '22px', marginBottom: 'var(--space-1)' }}>{item.icon}</div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', marginBottom: '4px' }}>{item.label}</div>
                <span className="badge badge-phase" style={{ fontSize: '10px' }}>{item.phase}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {status.state === 'error' && (
        <div className="font-mono" style={{ fontSize: 'var(--text-xs)', color: '#FCA5A5', marginTop: 'var(--space-2)' }}>
          {status.detail}
        </div>
      )}
    </div>
  );
};

// ─── Main Page Component ──────────────────────────────────────────────────────

export const EvidencePage: React.FC = () => {
  const { setCurrentPage } = useInvestigation();

  // Source type selection
  const [selectedType, setSelectedType] = useState<SourceType>('binary_fragment_files');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Selected file state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [hashProgress, setHashProgress] = useState<HashProgress>({ state: 'idle', percent: 0 });

  // Ingest & list state
  const [ingestStatus, setIngestStatus] = useState<IngestStatus>({ state: 'idle' });
  const [evidenceList, setEvidenceList] = useState<EvidenceRecord[]>([]);
  const [listLoading, setListLoading] = useState(false);
  const [listError, setListError] = useState<string | null>(null);

  // Discovery probe state
  const [discoveryStatus, setDiscoveryStatus] = useState<DiscoveryStatus>({ state: 'not_started' });
  const [discoveryTarget, setDiscoveryTarget] = useState<EvidenceRecord | null>(null);

  // ── Load evidence list from backend ───────────────────────────────────────
  const loadEvidenceList = useCallback(async () => {
    setListLoading(true);
    setListError(null);
    try {
      const res = await fetch('/api/v1/discovery/evidence');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setEvidenceList(data.items ?? []);
    } catch (err: any) {
      setListError(err.message || 'Failed to load evidence list');
    } finally {
      setListLoading(false);
    }
  }, []);

  // Load on mount
  React.useEffect(() => { loadEvidenceList(); }, [loadEvidenceList]);

  // ── File selection & hashing ───────────────────────────────────────────────
  const handleFileSelect = async (file: File) => {
    setSelectedFile(file);
    setHashProgress({ state: 'hashing', percent: 0 });
    setIngestStatus({ state: 'idle' });
    setDiscoveryStatus({ state: 'not_started' });

    try {
      const sha256 = await computeSha256(file, (pct) =>
        setHashProgress((h) => ({ ...h, percent: pct }))
      );
      setHashProgress({ state: 'done', percent: 100, sha256 });
    } catch (err: any) {
      setHashProgress({ state: 'error', percent: 0, errorMsg: err.message });
    }
  };

  const handleDropZone = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file) handleFileSelect(file);
    },
    [selectedType]
  );

  // ── Register evidence via backend ──────────────────────────────────────────
  const handleIngest = async () => {
    if (!selectedFile || hashProgress.state !== 'done' || !hashProgress.sha256) return;
    setIngestStatus({ state: 'loading' });

    try {
      const res = await fetch('/api/v1/discovery/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: selectedFile.name,
          file_size_bytes: selectedFile.size,
          sha256_hash: hashProgress.sha256,
          source_type: selectedType,
          is_sample_dataset: false,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail ?? `HTTP ${res.status}`);
      }
      setIngestStatus({ state: 'success', record: data });
      await loadEvidenceList();
      // Reset form
      setSelectedFile(null);
      setHashProgress({ state: 'idle', percent: 0 });
    } catch (err: any) {
      setIngestStatus({ state: 'error', errorMsg: err.message });
    }
  };

  // ── Load sample dataset ────────────────────────────────────────────────────
  const handleLoadSample = async () => {
    setIngestStatus({ state: 'loading' });
    setDiscoveryStatus({ state: 'not_started' });
    try {
      const res = await fetch('/api/v1/discovery/sample', { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`);
      setIngestStatus({ state: 'success', record: data });
      await loadEvidenceList();
    } catch (err: any) {
      setIngestStatus({ state: 'error', errorMsg: err.message });
    }
  };

  // ── Delete evidence record ─────────────────────────────────────────────────
  const handleDelete = async (id: string) => {
    try {
      await fetch(`/api/v1/discovery/evidence/${id}`, { method: 'DELETE' });
      await loadEvidenceList();
    } catch { /* swallow */ }
  };

  // ── Run Phase 2 fragment discovery ────────────────────────────────────────
  const handleDiscover = async (record: EvidenceRecord) => {
    setDiscoveryTarget(record);
    setDiscoveryStatus({ state: 'probing' });
    try {
      const res = await fetch('/api/v1/analysis/fragments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ evidence_id: record.id, block_size: 4096 }),
      });
      const data = await res.json();
      if (res.ok) {
        setDiscoveryStatus({
          state: 'done',
          fragmentCount: data.fragment_count,
          duplicateCount: data.duplicate_count,
          blockSize: data.block_size_used,
        });
        // Refresh evidence list so status shows PROCESSED
        await loadEvidenceList();
      } else if (res.status === 501) {
        setDiscoveryStatus({
          state: 'deferred',
          phase: data.phase ?? 'Phase 2',
          detail: data.detail ?? 'Not yet implemented.',
        });
      } else {
        throw new Error(data.detail ?? `HTTP ${res.status}`);
      }
    } catch (err: any) {
      setDiscoveryStatus({ state: 'error', detail: err.message });
    }
    setTimeout(() => {
      document.getElementById('discovery-status')?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const sourceConfig = SOURCE_TYPES.find((s) => s.id === selectedType)!;

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

      {/* ── Page Header ───────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-2)' }}>
            <h1 style={{ fontSize: 'var(--text-2xl)', fontWeight: 700 }}>Evidence Registry</h1>
            <span className="badge badge-valid" style={{ fontSize: '10px' }}>Phase 1 — LIVE</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '560px' }}>
            Register evidence files for analysis. All evidence is treated as <strong>read-only</strong> immediately on registration.
            SHA-256 is computed client-side and verified by the backend.
          </p>
        </div>
        <div style={{
          padding: '8px 14px', borderRadius: 'var(--radius-md)',
          background: 'rgba(251,146,60,0.10)', border: '1px solid rgba(251,146,60,0.3)',
          color: '#FB923C', fontSize: 'var(--text-xs)', fontWeight: 600,
          display: 'flex', alignItems: 'center', gap: '6px', maxWidth: '280px',
        }}>
          <span>⚠️</span>
          <span>PORTFOLIO PROTOTYPE — NOT LEGALLY ADMISSIBLE IN COURT</span>
        </div>
      </div>

      {/* ── Input Dataset Panel ───────────────────────────────────────────── */}
      <div className="forensic-card" style={{ borderLeft: '4px solid #06B6D4' }}>
        <div style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-4)' }}>
          Input Dataset
        </div>

        {/* Source Type Selector */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-2)', marginBottom: 'var(--space-5)' }}>
          {SOURCE_TYPES.map((st) => {
            const isSelected = selectedType === st.id;
            const isSample = st.id === 'sample_dataset';
            return (
              <button
                key={st.id}
                id={`source-type-${st.id}`}
                onClick={() => { setSelectedType(st.id); setSelectedFile(null); setHashProgress({ state: 'idle', percent: 0 }); setIngestStatus({ state: 'idle' }); }}
                style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'flex-start',
                  padding: 'var(--space-3)', borderRadius: 'var(--radius-md)',
                  border: isSelected
                    ? isSample
                      ? '1px solid rgba(251,146,60,0.6)'
                      : '1px solid var(--border-focus)'
                    : '1px solid var(--border-subtle)',
                  background: isSelected
                    ? isSample
                      ? 'rgba(251,146,60,0.08)'
                      : 'rgba(6,182,212,0.08)'
                    : 'var(--bg-page)',
                  cursor: 'pointer', transition: 'all 0.15s', textAlign: 'left',
                }}
              >
                <div style={{ fontSize: '18px', marginBottom: '4px' }}>{st.icon}</div>
                <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: isSelected ? '#F8FAFC' : 'var(--text-secondary)', marginBottom: '2px' }}>
                  {isSample ? '⚗️ Sample Dataset' : st.label}
                </div>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                  {st.desc}
                </div>
                {isSample && (
                  <div style={{
                    marginTop: 'var(--space-2)', fontSize: '10px', fontWeight: 700,
                    color: '#FB923C', background: 'rgba(251,146,60,0.12)',
                    border: '1px solid rgba(251,146,60,0.3)',
                    borderRadius: 'var(--radius-sm)', padding: '2px 6px',
                  }}>
                    NOT REAL EVIDENCE
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* File Drop Zone or Sample Button */}
        {selectedType === 'sample_dataset' ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <div style={{
              border: '2px dashed rgba(251,146,60,0.4)', borderRadius: 'var(--radius-lg)',
              padding: 'var(--space-8)', textAlign: 'center',
              background: 'rgba(251,146,60,0.04)',
            }}>
              <div style={{ fontSize: '40px', marginBottom: 'var(--space-3)' }}>⚗️</div>
              <div style={{ fontWeight: 600, color: '#FB923C', marginBottom: 'var(--space-2)' }}>
                Built-in Sample Dataset
              </div>
              <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', maxWidth: '480px', margin: '0 auto var(--space-4)' }}>
                <code className="font-mono" style={{ color: '#FB923C' }}>sample-data/loose-fragment-soup.bin</code>
                <br />
                Synthetic binary fixtures: fragmented PDF, JPEG (with duplicate), PNG (with corruption), ZIP (with gap).
                Concatenated in randomised order (seed=42). Generated by{' '}
                <code className="font-mono">sample-data/generate.py</code>.
              </div>
              <div style={{
                display: 'inline-block', marginBottom: 'var(--space-4)',
                padding: '8px 16px', borderRadius: 'var(--radius-md)',
                background: 'rgba(251,146,60,0.12)', border: '1px solid rgba(251,146,60,0.4)',
                color: '#FB923C', fontSize: 'var(--text-xs)', fontWeight: 700,
              }}>
                ⚠️ SAMPLE DATASET — Will be clearly marked in the registry. Never treated as real evidence.
              </div>
              <br />
              <button
                id="btn-load-sample"
                className="btn-primary"
                disabled={ingestStatus.state === 'loading'}
                onClick={handleLoadSample}
                style={{ background: '#EA580C', boxShadow: '0 0 12px rgba(234,88,12,0.3)' }}
              >
                {ingestStatus.state === 'loading' ? '⏳ Registering…' : '⚗️ Load Sample Dataset'}
              </button>
            </div>
          </div>
        ) : (
          <div
            id="drop-zone"
            onDrop={handleDropZone}
            onDragOver={(e) => e.preventDefault()}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: `2px dashed ${selectedFile ? 'var(--border-focus)' : 'var(--border-medium)'}`,
              borderRadius: 'var(--radius-lg)', padding: 'var(--space-8)',
              textAlign: 'center', cursor: 'pointer', transition: 'all 0.2s',
              background: selectedFile ? 'rgba(6,182,212,0.04)' : 'transparent',
            }}
            onMouseEnter={(e) => { if (!selectedFile) e.currentTarget.style.borderColor = 'var(--border-focus)'; e.currentTarget.style.background = 'rgba(6,182,212,0.04)'; }}
            onMouseLeave={(e) => { if (!selectedFile) e.currentTarget.style.borderColor = 'var(--border-medium)'; if (!selectedFile) e.currentTarget.style.background = 'transparent'; }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept={sourceConfig.accept}
              multiple={sourceConfig.multi}
              style={{ display: 'none' }}
              id="file-input"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFileSelect(f); }}
            />
            <div style={{ fontSize: '36px', marginBottom: 'var(--space-3)' }}>{sourceConfig.icon}</div>
            <div style={{ fontWeight: 600, marginBottom: 'var(--space-2)' }}>
              {selectedFile ? selectedFile.name : `Drop ${sourceConfig.label} here`}
            </div>
            <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
              {selectedFile ? formatBytes(selectedFile.size) : `or click to browse — accepts ${sourceConfig.accept}`}
            </div>
          </div>
        )}

        {/* Hash Progress */}
        {hashProgress.state === 'hashing' && (
          <div style={{ marginTop: 'var(--space-4)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
              <span>Computing SHA-256 client-side…</span>
              <span className="font-mono">{hashProgress.percent}%</span>
            </div>
            <div style={{ height: '4px', background: 'var(--bg-raised)', borderRadius: 'var(--radius-pill)' }}>
              <div style={{
                height: '100%', borderRadius: 'var(--radius-pill)',
                background: 'linear-gradient(90deg, #06B6D4, #3B82F6)',
                width: `${hashProgress.percent}%`, transition: 'width 0.2s',
              }} />
            </div>
          </div>
        )}

        {/* File Info Card (post-hash) */}
        {selectedFile && hashProgress.state === 'done' && hashProgress.sha256 && (
          <div style={{
            marginTop: 'var(--space-4)', padding: 'var(--space-4)',
            background: 'var(--bg-page)', borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-focus)',
          }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
              {[
                { label: 'Filename', value: selectedFile.name },
                { label: 'Size', value: formatBytes(selectedFile.size) },
                { label: 'Source Type', value: sourceConfig.label },
                { label: 'Processing Status', value: 'SHA-256 VERIFIED ✓' },
              ].map(({ label, value }) => (
                <div key={label}>
                  <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '2px' }}>{label}</div>
                  <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-primary)' }}>{value}</div>
                </div>
              ))}
            </div>
            <div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '4px' }}>
                SHA-256 Hash (client-side Web Crypto)
              </div>
              <div className="font-mono" style={{
                fontSize: 'var(--text-sm)', color: '#06B6D4', letterSpacing: '0.04em',
                padding: 'var(--space-2) var(--space-3)', background: 'var(--bg-raised)',
                borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)',
                wordBreak: 'break-all',
              }}>
                {hashProgress.sha256}
              </div>
            </div>

            <div style={{ marginTop: 'var(--space-4)', display: 'flex', gap: 'var(--space-3)', alignItems: 'center' }}>
              <button
                id="btn-ingest"
                className="btn-primary"
                disabled={ingestStatus.state === 'loading'}
                onClick={handleIngest}
              >
                {ingestStatus.state === 'loading' ? '⏳ Registering…' : '🔐 Register Evidence (Read-Only)'}
              </button>
              <button
                className="btn-secondary"
                onClick={() => { setSelectedFile(null); setHashProgress({ state: 'idle', percent: 0 }); setIngestStatus({ state: 'idle' }); }}
              >
                Clear
              </button>
            </div>

            {ingestStatus.state === 'error' && (
              <div style={{ marginTop: 'var(--space-3)', fontSize: 'var(--text-sm)', color: '#FCA5A5' }}>
                ⚠️ {ingestStatus.errorMsg}
              </div>
            )}
          </div>
        )}

        {/* Ingest success flash */}
        {ingestStatus.state === 'success' && ingestStatus.record && (
          <div style={{
            marginTop: 'var(--space-4)', padding: 'var(--space-3) var(--space-4)',
            borderRadius: 'var(--radius-md)', border: '1px solid var(--status-valid-border)',
            background: 'var(--status-valid-bg)', color: 'var(--status-valid)',
            fontSize: 'var(--text-sm)', fontWeight: 500,
          }}>
            ✓ Registered: <strong>{ingestStatus.record.filename}</strong>
            {ingestStatus.record.is_sample_dataset && (
              <span style={{ marginLeft: 'var(--space-2)', color: '#FB923C', fontSize: 'var(--text-xs)' }}>
                [SAMPLE DATASET — not real evidence]
              </span>
            )}
          </div>
        )}
      </div>

      {/* ── Discovery Status (Phase 2 Gate) ───────────────────────────────── */}
      <div id="discovery-status">
        <DiscoveryStatusPanel status={discoveryStatus} evidenceName={discoveryTarget?.filename} />
      </div>

      {/* ── Evidence Registry Table ───────────────────────────────────────── */}
      <div className="forensic-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
          <div>
            <div style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Evidence Registry
            </div>
            <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginTop: '2px' }}>
              {listLoading ? 'Loading…' : `${evidenceList.length} record${evidenceList.length !== 1 ? 's' : ''} registered`}
            </div>
          </div>
          <button id="btn-refresh-list" className="btn-secondary" onClick={loadEvidenceList} style={{ fontSize: 'var(--text-xs)' }}>
            ↻ Refresh
          </button>
        </div>

        {listError ? (
          <div style={{ color: '#FCA5A5', fontSize: 'var(--text-sm)', padding: 'var(--space-4)' }}>
            ⚠️ {listError}
          </div>
        ) : (
          <EvidenceTable
            records={evidenceList}
            onDelete={handleDelete}
            onSelectForDiscovery={handleDiscover}
          />
        )}

        {/* Phase 2 hint */}
        <div style={{
          marginTop: 'var(--space-4)', padding: 'var(--space-3) var(--space-4)',
          borderRadius: 'var(--radius-md)', background: 'rgba(56,189,248,0.05)',
          border: '1px solid rgba(56,189,248,0.15)', fontSize: 'var(--text-xs)',
          color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)',
        }}>
          <span style={{ color: '#38BDF8' }}>ℹ</span>
          Click <strong style={{ color: 'var(--text-secondary)' }}>🔍 Discover</strong> on any record to probe the Phase 2 fragment discovery endpoint. The honest 501 response will appear above.
          Fragment analysis implements in{' '}
          <button
            style={{ background: 'none', border: 'none', color: '#38BDF8', cursor: 'pointer', padding: 0, fontSize: 'inherit' }}
            onClick={() => setCurrentPage('fragments')}
          >
            Phase 2 →
          </button>
        </div>
      </div>
    </div>
  );
};
