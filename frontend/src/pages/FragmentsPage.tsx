/**
 * Fragments Page — Phase 3 LIVE
 *
 * Left panel: real fragment list with detected file type, role classification (FILE_START,
 * CONTINUATION, POSSIBLE_END), confidence score, entropy profile, and duplicate/corruption flags.
 * Right panel:
 *   - Tab 1: Hex Inspector — real bytes, offset navigation, search within fragment,
 *            and matched magic-byte range highlighting.
 *   - Tab 2: Binary / Header Analysis view (spec section 6 format) — File Type, Magic Bytes,
 *            Offset, Header Validity, Expected Structure, and Match Confidence.
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';

// ─── Types ────────────────────────────────────────────────────────────────────

interface EvidenceSummary {
  id: string;
  filename: string;
  file_size_bytes: number;
  sha256_hash: string;
  status: string;
  is_sample_dataset: boolean;
}

interface FragmentRecord {
  id: string;
  evidence_id: string;
  offset_start: number;
  offset_end: number;
  size_bytes: number;
  sha256_hash: string;
  entropy: number;
  status: string;
  entropy_class: string;
  content_class: string;
  hex_preview: string;
  flags: string[];
  inferred_format: string | null;
  role_guess: string;
  signature_confidence: number;
  matched_magic_hex: string | null;
  matched_magic_offset: number;
  matched_magic_length: number;
  structural_notes: string;
  created_at: string;
}

interface HexRow {
  offset: number;
  offset_hex: string;
  hex: string;
  ascii: string;
}

interface HexDump {
  fragment_id: string;
  evidence_filename: string;
  offset_start: number;
  size_bytes: number;
  bytes_returned: number;
  truncated: boolean;
  rows: HexRow[];
  inferred_format?: string | null;
  role_guess?: string;
  signature_confidence?: number;
  matched_magic_hex?: string | null;
  matched_magic_offset?: number;
  matched_magic_length?: number;
  structural_notes?: string;
}

interface AnalysisResult {
  evidence_id: string;
  evidence_filename: string;
  fragment_count: number;
  duplicate_count: number;
  block_size_used: number;
  fragments: FragmentRecord[];
  disclaimer: string;
}

interface SignatureDefinition {
  format_id: string;
  name: string;
  extension: string;
  category: string;
  magic_hex: string;
  header_offset: number;
  trailer_hex: string | null;
  description: string;
  expected_structural_notes: string;
  typical_entropy_range: number[];
  confidence_base: number;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const formatBytes = (n: number) => {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(2)} MB`;
};

const entropyColor = (ent: number) => {
  if (ent >= 7.2) return '#F87171';
  if (ent >= 5.0) return '#FB923C';
  if (ent >= 2.5) return '#FBBF24';
  return '#34D399';
};

const formatBadgeColor = (fmt: string | null): { bg: string; text: string; border: string } => {
  switch (fmt?.toLowerCase()) {
    case 'pdf':
      return { bg: 'rgba(239, 68, 68, 0.12)', text: '#F87171', border: 'rgba(239, 68, 68, 0.3)' };
    case 'jpeg':
    case 'jpg':
      return { bg: 'rgba(245, 158, 11, 0.12)', text: '#FBBF24', border: 'rgba(245, 158, 11, 0.3)' };
    case 'png':
      return { bg: 'rgba(16, 185, 129, 0.12)', text: '#34D399', border: 'rgba(16, 185, 129, 0.3)' };
    case 'zip':
      return { bg: 'rgba(6, 182, 212, 0.12)', text: '#38BDF8', border: 'rgba(6, 182, 212, 0.3)' };
    default:
      return { bg: 'rgba(100, 116, 139, 0.12)', text: '#94A3B8', border: 'rgba(100, 116, 139, 0.25)' };
  }
};

const roleBadgeColor = (role: string): { bg: string; text: string } => {
  switch (role) {
    case 'FILE_START':
      return { bg: 'rgba(16, 185, 129, 0.15)', text: '#10B981' };
    case 'POSSIBLE_END':
      return { bg: 'rgba(168, 85, 247, 0.15)', text: '#C084FC' };
    case 'CONTINUATION':
      return { bg: 'rgba(56, 189, 248, 0.12)', text: '#38BDF8' };
    default:
      return { bg: 'rgba(100, 116, 139, 0.12)', text: '#64748B' };
  }
};

const statusStyle = (status: string): React.CSSProperties => {
  const map: Record<string, [string, string, string]> = {
    UNCERTAIN:  ['var(--status-uncertain)',  'var(--status-uncertain-bg)',  'var(--status-uncertain-border)'],
    DUPLICATE:  ['var(--status-duplicate)',  'var(--status-duplicate-bg)',  'var(--status-duplicate-border)'],
    CONFIRMED:  ['var(--status-valid)',      'var(--status-valid-bg)',      'var(--status-valid-border)'],
    CORRUPTED:  ['var(--status-corrupted)',  'var(--status-corrupted-bg)',  'var(--status-corrupted-border)'],
    MISSING:    ['var(--status-missing)',    'var(--status-missing-bg)',    'var(--status-missing-border)'],
    INFERRED:   ['var(--status-recovered)',  'var(--status-recovered-bg)',  'var(--status-recovered-border)'],
  };
  const [color, bg, border] = map[status] ?? ['#94A3B8', 'rgba(100,116,139,0.1)', 'rgba(100,116,139,0.25)'];
  return { color, background: bg, border: `1px solid ${border}` };
};

// ─── EntropyBar ───────────────────────────────────────────────────────────────

const EntropyBar: React.FC<{ value: number }> = ({ value }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', minWidth: 0 }}>
    <div style={{
      flex: 1, height: '6px', background: 'var(--bg-raised)',
      borderRadius: 'var(--radius-pill)', overflow: 'hidden',
    }}>
      <div style={{
        height: '100%', width: `${(value / 8.0) * 100}%`,
        background: entropyColor(value), borderRadius: 'var(--radius-pill)',
        transition: 'width 0.3s ease',
      }} />
    </div>
    <span className="font-mono" style={{ fontSize: '10px', color: entropyColor(value), flexShrink: 0, width: '34px', textAlign: 'right' }}>
      {value.toFixed(2)}
    </span>
  </div>
);

// ─── HexInspector & HeaderAnalysis Component ─────────────────────────────────

const HexInspector: React.FC<{
  fragment: FragmentRecord | null;
  dump: HexDump | null;
  loading: boolean;
  signatures: SignatureDefinition[];
}> = ({ fragment, dump, loading, signatures }) => {
  const [activeTab, setActiveTab] = useState<'hex' | 'header'>('hex');
  const [hoveredRow, setHoveredRow] = useState<number | null>(null);
  const [hexFilter, setHexFilter] = useState<string>('');
  const [jumpOffset, setJumpOffset] = useState<string>('');
  const rowsRef = useRef<HTMLDivElement>(null);

  const matchedFormatSig = useMemo(() => {
    if (!fragment?.inferred_format) return null;
    return signatures.find(s => s.format_id.toLowerCase() === fragment.inferred_format?.toLowerCase()) || null;
  }, [fragment, signatures]);

  if (!fragment) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', gap: 'var(--space-3)' }}>
        <div style={{ fontSize: '36px' }}>🔬</div>
        <div style={{ fontSize: 'var(--text-base)', fontWeight: 600 }}>Select a fragment to inspect</div>
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-disabled)' }}>Hex · ASCII · Magic Byte Highlighting · Header Analysis</div>
      </div>
    );
  }

  // Determine if a byte in a row is part of the matched magic range
  const isByteInMagicRange = (rowByteOffset: number): boolean => {
    if (!fragment.matched_magic_length || fragment.matched_magic_length <= 0) return false;
    const magicStart = fragment.offset_start + (fragment.matched_magic_offset || 0);
    const magicEnd = magicStart + fragment.matched_magic_length;
    return rowByteOffset >= magicStart && rowByteOffset < magicEnd;
  };

  const filteredRows = useMemo(() => {
    if (!dump?.rows) return [];
    if (!hexFilter.trim()) return dump.rows;
    const q = hexFilter.trim().toUpperCase();
    return dump.rows.filter(r => r.hex.includes(q) || r.ascii.toUpperCase().includes(q) || r.offset_hex.includes(q));
  }, [dump, hexFilter]);

  const handleJump = () => {
    if (!jumpOffset.trim() || !rowsRef.current) return;
    const target = parseInt(jumpOffset.replace(/^0x/i, ''), 16);
    if (isNaN(target)) return;
    const el = document.getElementById(`hex-row-${target}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 'var(--space-3)' }}>
      {/* Fragment Header & Tab Bar */}
      <div style={{ padding: 'var(--space-3)', background: 'var(--bg-raised)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', flexShrink: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '2px' }}>
              Selected Fragment
            </div>
            <div className="font-mono" style={{ fontSize: 'var(--text-xs)', color: '#06B6D4', letterSpacing: '0.03em', fontWeight: 600 }}>
              {fragment.id}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap' }}>
            {[
              ['Offset', `0x${fragment.offset_start.toString(16).toUpperCase().padStart(8, '0')}`],
              ['Size', formatBytes(fragment.size_bytes)],
              ['Entropy', fragment.entropy.toFixed(4)],
              ['Confidence', `${Math.round(fragment.signature_confidence * 100)}%`],
            ].map(([label, val]) => (
              <div key={label} style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>{label}</div>
                <div className="font-mono" style={{ fontSize: 'var(--text-xs)', color: 'var(--text-primary)', fontWeight: 600 }}>{val}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Badges & Phase 3 Attributes */}
        <div style={{ marginTop: 'var(--space-2)', display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap', alignItems: 'center' }}>
          <span className="badge" style={{ ...statusStyle(fragment.status), fontSize: '10px' }}>{fragment.status}</span>

          {fragment.inferred_format ? (
            <span className="badge font-mono" style={{
              background: formatBadgeColor(fragment.inferred_format).bg,
              color: formatBadgeColor(fragment.inferred_format).text,
              border: `1px solid ${formatBadgeColor(fragment.inferred_format).border}`,
              fontSize: '11px', fontWeight: 700,
            }}>
              FORMAT: {fragment.inferred_format.toUpperCase()}
            </span>
          ) : (
            <span className="badge font-mono" style={{ background: 'rgba(100,116,139,0.1)', color: '#94A3B8', fontSize: '10px' }}>
              FORMAT: UNKNOWN
            </span>
          )}

          <span className="badge font-mono" style={{
            background: roleBadgeColor(fragment.role_guess).bg,
            color: roleBadgeColor(fragment.role_guess).text,
            fontSize: '10px', fontWeight: 600,
          }}>
            ROLE: {fragment.role_guess}
          </span>

          {fragment.matched_magic_hex && (
            <span className="badge font-mono" style={{
              background: 'rgba(245, 158, 11, 0.15)', color: '#FCD34D',
              border: '1px solid rgba(245, 158, 11, 0.3)', fontSize: '10px',
            }}>
              MAGIC: {fragment.matched_magic_hex}
            </span>
          )}

          {fragment.flags.map((f) => (
            <span key={f} className="badge" style={{ background: 'rgba(239,68,68,0.12)', color: '#FCA5A5', border: '1px solid rgba(239,68,68,0.25)', fontSize: '10px' }}>
              {f.split(':')[0]}
            </span>
          ))}
        </div>

        {/* Structural Notes Banner */}
        {fragment.structural_notes && (
          <div style={{
            marginTop: 'var(--space-2)', padding: '6px 10px', borderRadius: 'var(--radius-sm)',
            background: 'rgba(6,182,212,0.05)', border: '1px solid rgba(6,182,212,0.15)',
            fontSize: '11px', color: '#67E8F9', lineHeight: 1.4,
          }}>
            <strong>Structure:</strong> {fragment.structural_notes}
          </div>
        )}

        {/* View Tabs */}
        <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-3)' }}>
          <button
            onClick={() => setActiveTab('hex')}
            style={{
              padding: '4px 12px', fontSize: 'var(--text-xs)', fontWeight: 600,
              borderRadius: 'var(--radius-sm)', border: 'none', cursor: 'pointer',
              background: activeTab === 'hex' ? 'var(--border-focus)' : 'var(--bg-page)',
              color: activeTab === 'hex' ? '#041016' : 'var(--text-muted)',
            }}
          >
            🔬 Hex &amp; ASCII Inspector
          </button>
          <button
            onClick={() => setActiveTab('header')}
            style={{
              padding: '4px 12px', fontSize: 'var(--text-xs)', fontWeight: 600,
              borderRadius: 'var(--radius-sm)', border: 'none', cursor: 'pointer',
              background: activeTab === 'header' ? 'var(--border-focus)' : 'var(--bg-page)',
              color: activeTab === 'header' ? '#041016' : 'var(--text-muted)',
            }}
          >
            📋 Binary / Header Analysis View
          </button>
        </div>
      </div>

      {/* Tab 1: Hex & ASCII Inspector */}
      {activeTab === 'hex' && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
          {/* Controls: Search & Jump */}
          <div style={{
            display: 'flex', gap: 'var(--space-2)', padding: '6px 8px',
            background: 'var(--bg-page)', borderBottom: '1px solid var(--border-subtle)',
            alignItems: 'center', flexWrap: 'wrap',
          }}>
            <input
              placeholder="Search Hex (e.g. 25 50) or ASCII..."
              value={hexFilter}
              onChange={(e) => setHexFilter(e.target.value)}
              style={{
                flex: 1, minWidth: '160px', background: 'var(--bg-surface)', color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)',
                padding: '4px 8px', fontSize: '11px', fontFamily: 'var(--font-mono)',
              }}
            />
            <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
              <input
                placeholder="Offset 0x..."
                value={jumpOffset}
                onChange={(e) => setJumpOffset(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleJump(); }}
                style={{
                  width: '90px', background: 'var(--bg-surface)', color: 'var(--text-primary)',
                  border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)',
                  padding: '4px 6px', fontSize: '11px', fontFamily: 'var(--font-mono)',
                }}
              />
              <button
                onClick={handleJump}
                className="btn-secondary"
                style={{ fontSize: '10px', padding: '4px 8px' }}
              >
                Go
              </button>
            </div>
            {fragment.matched_magic_hex && (
              <span className="font-mono" style={{ fontSize: '10px', color: '#FCD34D', padding: '2px 6px', background: 'rgba(245,158,11,0.1)', borderRadius: 'var(--radius-sm)' }}>
                ⭐ Magic range highlighted
              </span>
            )}
          </div>

          {/* Hex rows */}
          <div ref={rowsRef} style={{ flex: 1, overflow: 'auto', position: 'relative' }}>
            {loading ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', marginBottom: 'var(--space-2)' }}>⏳</div>
                  <div>Loading raw bytes…</div>
                </div>
              </div>
            ) : dump ? (
              <>
                <div className="font-mono" style={{
                  display: 'grid', gridTemplateColumns: '90px 1fr 140px',
                  gap: '12px', padding: '6px 8px',
                  fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600,
                  borderBottom: '1px solid var(--border-subtle)', position: 'sticky', top: 0,
                  background: 'var(--bg-page)', zIndex: 2,
                }}>
                  <span>OFFSET</span>
                  <span>00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F</span>
                  <span>ASCII</span>
                </div>

                {filteredRows.map((row, idx) => {
                  const bytesInRow = row.hex.split(' ');
                  const rowHasMagic = bytesInRow.some((_, bIdx) => isByteInMagicRange(row.offset + bIdx));

                  return (
                    <div
                      key={row.offset}
                      id={`hex-row-${row.offset}`}
                      onMouseEnter={() => setHoveredRow(idx)}
                      onMouseLeave={() => setHoveredRow(null)}
                      className="font-mono"
                      style={{
                        display: 'grid', gridTemplateColumns: '90px 1fr 140px',
                        gap: '12px', padding: '2px 8px',
                        fontSize: '11px', lineHeight: 1.8,
                        background: rowHasMagic
                          ? 'rgba(245, 158, 11, 0.08)'
                          : hoveredRow === idx ? 'rgba(6,182,212,0.06)' : 'transparent',
                        borderLeft: rowHasMagic ? '2px solid #F59E0B' : '2px solid transparent',
                        transition: 'background 0.1s',
                        cursor: 'default',
                      }}
                    >
                      <span style={{ color: '#64748B' }}>{row.offset_hex}</span>
                      <div style={{ display: 'flex', gap: '5px' }}>
                        {bytesInRow.map((byteHex, bIdx) => {
                          const isMagic = isByteInMagicRange(row.offset + bIdx);
                          return (
                            <span
                              key={bIdx}
                              style={{
                                color: isMagic ? '#FCD34D' : '#CBD5E1',
                                background: isMagic ? 'rgba(245, 158, 11, 0.25)' : 'transparent',
                                padding: isMagic ? '0 2px' : '0',
                                borderRadius: isMagic ? '2px' : '0',
                                fontWeight: isMagic ? 700 : 400,
                              }}
                              title={isMagic ? `Matched Signature Byte: ${byteHex}` : undefined}
                            >
                              {byteHex}
                            </span>
                          );
                        })}
                      </div>
                      <span style={{ color: rowHasMagic ? '#FCD34D' : '#4B6B8A', letterSpacing: '0.05em' }}>
                        {row.ascii}
                      </span>
                    </div>
                  );
                })}
              </>
            ) : null}
          </div>
        </div>
      )}

      {/* Tab 2: Binary / Header Analysis View (Spec Section 6 Format) */}
      {activeTab === 'header' && (
        <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-2)' }}>
          <div style={{
            background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-subtle)', padding: 'var(--space-4)',
          }}>
            <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 700, marginBottom: 'var(--space-3)', color: 'var(--text-primary)' }}>
              Binary &amp; Header Signature Analysis
            </h3>

            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--text-xs)' }}>
              <tbody>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 600, color: 'var(--text-muted)', width: '160px' }}>Detected File Type</td>
                  <td style={{ padding: '8px 12px' }}>
                    {fragment.inferred_format ? (
                      <span className="badge font-mono" style={{
                        background: formatBadgeColor(fragment.inferred_format).bg,
                        color: formatBadgeColor(fragment.inferred_format).text,
                        fontWeight: 700,
                      }}>
                        {matchedFormatSig?.name ?? fragment.inferred_format.toUpperCase()} (.{fragment.inferred_format})
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>No definitive signature matched</span>
                    )}
                  </td>
                </tr>

                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 600, color: 'var(--text-muted)' }}>Role Guess</td>
                  <td style={{ padding: '8px 12px' }}>
                    <span className="badge font-mono" style={{ ...roleBadgeColor(fragment.role_guess), fontWeight: 600 }}>
                      {fragment.role_guess}
                    </span>
                  </td>
                </tr>

                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 600, color: 'var(--text-muted)' }}>Magic Bytes (Hex)</td>
                  <td style={{ padding: '8px 12px' }} className="font-mono">
                    {fragment.matched_magic_hex ? (
                      <span style={{ color: '#FCD34D', fontWeight: 700, background: 'rgba(245,158,11,0.15)', padding: '2px 6px', borderRadius: '3px' }}>
                        {fragment.matched_magic_hex}
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>None matched</span>
                    )}
                  </td>
                </tr>

                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 600, color: 'var(--text-muted)' }}>Header Offset</td>
                  <td style={{ padding: '8px 12px', color: '#67E8F9' }} className="font-mono">
                    0x{(fragment.matched_magic_offset || 0).toString(16).toUpperCase().padStart(4, '0')}
                    <span style={{ color: 'var(--text-muted)', marginLeft: '8px' }}>
                      (Global offset: 0x{(fragment.offset_start + (fragment.matched_magic_offset || 0)).toString(16).toUpperCase().padStart(8, '0')})
                    </span>
                  </td>
                </tr>

                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 600, color: 'var(--text-muted)' }}>Header Validity</td>
                  <td style={{ padding: '8px 12px' }}>
                    {fragment.status === 'CORRUPTED' ? (
                      <span style={{ color: '#EF4444', fontWeight: 600 }}>❌ CORRUPTED / STRUCTURAL ANOMALY DETECTED</span>
                    ) : fragment.role_guess === 'FILE_START' ? (
                      <span style={{ color: '#10B981', fontWeight: 600 }}>✅ VALID EXACT MAGIC HEADER</span>
                    ) : fragment.inferred_format ? (
                      <span style={{ color: '#06B6D4', fontWeight: 600 }}>ℹ STRUCTURAL MARKERS INFERRED</span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>UNCERTAIN</span>
                    )}
                  </td>
                </tr>

                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 600, color: 'var(--text-muted)' }}>Expected Structure</td>
                  <td style={{ padding: '8px 12px', lineHeight: 1.5, color: 'var(--text-primary)' }}>
                    {matchedFormatSig?.expected_structural_notes || fragment.structural_notes || 'Standard binary/data sequence.'}
                  </td>
                </tr>

                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 600, color: 'var(--text-muted)' }}>Match Confidence</td>
                  <td style={{ padding: '8px 12px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                      <div style={{ width: '120px', height: '8px', background: 'var(--bg-raised)', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{
                          height: '100%', width: `${Math.round(fragment.signature_confidence * 100)}%`,
                          background: fragment.signature_confidence > 0.7 ? '#10B981' : '#F59E0B',
                        }} />
                      </div>
                      <span className="font-mono" style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                        {Math.round(fragment.signature_confidence * 100)}%
                      </span>
                    </div>
                  </td>
                </tr>

                <tr>
                  <td style={{ padding: '8px 12px', fontWeight: 600, color: 'var(--text-muted)' }}>Entropy Consistency</td>
                  <td style={{ padding: '8px 12px' }} className="font-mono">
                    Fragment entropy: {fragment.entropy.toFixed(4)} bits/byte
                    {matchedFormatSig && (
                      <span style={{ color: 'var(--text-muted)', marginLeft: '8px' }}>
                        (Typical for {matchedFormatSig.name}: {matchedFormatSig.typical_entropy_range[0]} - {matchedFormatSig.typical_entropy_range[1]})
                      </span>
                    )}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Main FragmentsPage Component ─────────────────────────────────────────────

export const FragmentsPage: React.FC = () => {
  const [evidenceList, setEvidenceList] = useState<EvidenceSummary[]>([]);
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceSummary | null>(null);

  const [analysisState, setAnalysisState] = useState<'idle' | 'running' | 'done' | 'error'>('idle');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [blockSize, setBlockSize] = useState<number>(4096);

  const [selectedFragment, setSelectedFragment] = useState<FragmentRecord | null>(null);
  const [hexDump, setHexDump] = useState<HexDump | null>(null);
  const [hexLoading, setHexLoading] = useState(false);

  const [signatures, setSignatures] = useState<SignatureDefinition[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [formatFilter, setFormatFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Load evidence and signatures on mount
  useEffect(() => {
    fetch('/api/v1/discovery/evidence')
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.items) {
          setEvidenceList(data.items);
          const sample = data.items.find((e: EvidenceSummary) => e.is_sample_dataset);
          setSelectedEvidence(sample ?? data.items[0] ?? null);
        }
      })
      .catch(console.error);

    fetch('/api/v1/analysis/signatures')
      .then((r) => (r.ok ? r.json() : []))
      .then((sigs) => setSignatures(sigs))
      .catch(console.error);
  }, []);

  const runAnalysis = useCallback(async (evId: string, force = false) => {
    setAnalysisState('running');
    setAnalysisError(null);
    try {
      const res = await fetch('/api/v1/analysis/fragments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          evidence_id: evId,
          block_size: blockSize,
          force_reanalyze: force,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Analysis failed' }));
        throw new Error(err.detail ?? 'Analysis failed');
      }
      const data: AnalysisResult = await res.json();
      setAnalysisResult(data);
      setAnalysisState('done');
      if (data.fragments.length > 0) {
        selectFragment(data.fragments[0]);
      }
    } catch (e: any) {
      setAnalysisError(e.message);
      setAnalysisState('error');
    }
  }, [blockSize]);

  useEffect(() => {
    if (selectedEvidence) {
      runAnalysis(selectedEvidence.id, false);
    }
  }, [selectedEvidence, runAnalysis]);

  const selectFragment = useCallback(async (frag: FragmentRecord) => {
    setSelectedFragment(frag);
    setHexLoading(true);
    try {
      const res = await fetch(`/api/v1/analysis/fragments/${frag.id}/hex?max_bytes=4096`);
      if (res.ok) {
        const dump: HexDump = await res.json();
        setHexDump(dump);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setHexLoading(false);
    }
  }, []);

  const filteredFragments = useMemo(() => {
    if (!analysisResult) return [];
    return analysisResult.fragments.filter((f) => {
      if (statusFilter !== 'ALL' && f.status !== statusFilter) return false;
      if (formatFilter !== 'ALL') {
        if (formatFilter === 'UNKNOWN' && f.inferred_format !== null) return false;
        if (formatFilter !== 'UNKNOWN' && f.inferred_format?.toUpperCase() !== formatFilter) return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          f.id.toLowerCase().includes(q) ||
          f.sha256_hash.toLowerCase().includes(q) ||
          (f.inferred_format && f.inferred_format.toLowerCase().includes(q)) ||
          f.role_guess.toLowerCase().includes(q) ||
          f.content_class.toLowerCase().includes(q) ||
          f.entropy_class.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [analysisResult, statusFilter, formatFilter, searchQuery]);

  const dupCount = useMemo(
    () => analysisResult?.fragments.filter((f) => f.status === 'DUPLICATE').length ?? 0,
    [analysisResult]
  );

  return (
    <div style={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
      {/* ── Page header ─────────────────────────────────────────────────── */}
      <div style={{ flexShrink: 0, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
        <div>
          <h1 style={{ fontSize: 'var(--text-xl)', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            Fragment Discovery &amp; Signature Detection
          </h1>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '2px' }}>
            Phase 3: Magic byte analysis, role classification, and hex inspector
          </div>
        </div>
        <div style={{
          padding: '4px 10px', borderRadius: 'var(--radius-md)',
          background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.25)',
          color: '#34D399', fontSize: '11px', fontWeight: 600,
        }}>
          ✓ Phase 3 Active — Extensible Signature Registry Live
        </div>
      </div>

      {/* ── Evidence selector + config bar ──────────────────────────────── */}
      <div style={{
        flexShrink: 0, display: 'flex', gap: 'var(--space-3)', alignItems: 'center',
        flexWrap: 'wrap', padding: 'var(--space-3) var(--space-4)',
        background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flex: 1, minWidth: '200px' }}>
          <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', flexShrink: 0 }}>
            Evidence
          </label>
          <select
            id="evidence-selector"
            value={selectedEvidence?.id ?? ''}
            onChange={(e) => {
              const ev = evidenceList.find((x) => x.id === e.target.value) ?? null;
              setSelectedEvidence(ev);
            }}
            style={{
              flex: 1, background: 'var(--bg-page)', color: 'var(--text-primary)',
              border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
              padding: '5px 8px', fontSize: 'var(--text-sm)', fontFamily: 'var(--font-sans)',
            }}
          >
            {evidenceList.length === 0 && <option value="">No evidence registered</option>}
            {evidenceList.map((ev) => (
              <option key={ev.id} value={ev.id}>
                {ev.filename} — {formatBytes(ev.file_size_bytes)}
                {ev.is_sample_dataset ? ' [SAMPLE]' : ''}
              </option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', flexShrink: 0 }}>
            Block Size
          </label>
          <select
            id="block-size-selector"
            value={blockSize}
            onChange={(e) => setBlockSize(Number(e.target.value))}
            style={{
              background: 'var(--bg-page)', color: 'var(--text-primary)',
              border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
              padding: '5px 8px', fontSize: 'var(--text-sm)', fontFamily: 'var(--font-mono)',
            }}
          >
            {[512, 1024, 2048, 4096, 8192].map((b) => (
              <option key={b} value={b}>{b.toLocaleString()} B</option>
            ))}
          </select>
        </div>

        <button
          id="btn-run-analysis"
          className="btn-primary"
          disabled={!selectedEvidence || analysisState === 'running'}
          onClick={() => selectedEvidence && runAnalysis(selectedEvidence.id, true)}
          style={{ fontSize: 'var(--text-xs)', padding: '6px 14px' }}
        >
          {analysisState === 'running' ? '⏳ Analyzing…' : '▶ Re-analyze'}
        </button>
      </div>

      {/* ── Stats bar ────────────────────────────────────────────────────── */}
      {analysisResult && (
        <div style={{
          flexShrink: 0, display: 'grid',
          gridTemplateColumns: 'repeat(5, 1fr)', gap: 'var(--space-3)',
        }}>
          {[
            { label: 'Total Fragments', value: analysisResult.fragment_count, color: '#06B6D4' },
            { label: 'Duplicates', value: dupCount, color: '#F59E0B' },
            { label: 'Signatures Detected', value: analysisResult.fragments.filter(f => f.inferred_format).length, color: '#10B981' },
            { label: 'Block Size', value: `${analysisResult.block_size_used.toLocaleString()} B`, color: '#94A3B8' },
            { label: 'Evidence Size', value: formatBytes(selectedEvidence?.file_size_bytes ?? 0), color: '#94A3B8' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{
              background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)', padding: 'var(--space-3)',
            }}>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '4px' }}>{label}</div>
              <div className="font-mono" style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color }}>{value}</div>
            </div>
          ))}
        </div>
      )}

      {/* ── Main split: fragment list + hex inspector ─────────────────────── */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '430px 1fr', gap: 'var(--space-4)', overflow: 'hidden', minHeight: 0 }}>

        {/* Left: Fragment List */}
        <div style={{
          background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-subtle)', display: 'flex',
          flexDirection: 'column', overflow: 'hidden',
        }}>
          {/* Filters & Search */}
          <div style={{ padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--border-subtle)', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {/* Status Filter */}
            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
              {['ALL', 'CONFIRMED', 'INFERRED', 'CORRUPTED', 'DUPLICATE', 'UNCERTAIN'].map((s) => (
                <button
                  key={s}
                  onClick={() => setStatusFilter(s)}
                  style={{
                    fontSize: '9px', fontWeight: 600, padding: '2px 6px',
                    borderRadius: 'var(--radius-sm)', border: 'none', cursor: 'pointer',
                    background: statusFilter === s ? 'var(--border-focus)' : 'var(--bg-raised)',
                    color: statusFilter === s ? '#041016' : 'var(--text-muted)',
                  }}
                >
                  {s}
                </button>
              ))}
            </div>

            {/* Format Filter */}
            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', alignItems: 'center' }}>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600 }}>TYPE:</span>
              {['ALL', 'PDF', 'JPEG', 'PNG', 'ZIP', 'UNKNOWN'].map((fmt) => (
                <button
                  key={fmt}
                  onClick={() => setFormatFilter(fmt)}
                  style={{
                    fontSize: '9px', fontWeight: 700, padding: '1px 5px',
                    borderRadius: 'var(--radius-sm)', border: 'none', cursor: 'pointer',
                    background: formatFilter === fmt ? '#38BDF8' : 'var(--bg-raised)',
                    color: formatFilter === fmt ? '#041016' : 'var(--text-muted)',
                  }}
                >
                  {fmt}
                </button>
              ))}
            </div>

            <input
              placeholder="Filter by ID, format, role, flags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%', background: 'var(--bg-page)', color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)',
                padding: '5px 8px', fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {/* Fragment Rows */}
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {analysisState === 'running' ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '200px', color: 'var(--text-muted)', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <div style={{ fontSize: '28px' }}>⏳</div>
                <div>Analyzing fragments &amp; scanning signatures…</div>
              </div>
            ) : analysisState === 'error' ? (
              <div style={{ padding: 'var(--space-4)', color: '#FCA5A5', fontSize: 'var(--text-sm)' }}>
                ⚠ {analysisError}
              </div>
            ) : filteredFragments.length === 0 ? (
              <div style={{ padding: 'var(--space-4)', color: 'var(--text-muted)', textAlign: 'center', fontSize: 'var(--text-sm)' }}>
                No fragments match the current filter
              </div>
            ) : (
              filteredFragments.map((frag) => {
                const isSelected = selectedFragment?.id === frag.id;
                const isDup = frag.status === 'DUPLICATE';

                return (
                  <div
                    key={frag.id}
                    id={`frag-${frag.id.slice(0, 8)}`}
                    onClick={() => selectFragment(frag)}
                    style={{
                      padding: 'var(--space-3) var(--space-4)',
                      borderBottom: '1px solid var(--border-subtle)',
                      cursor: 'pointer', transition: 'background 0.1s',
                      borderLeft: isSelected ? '3px solid var(--border-focus)' : '3px solid transparent',
                      background: isSelected ? 'rgba(6,182,212,0.06)' : 'transparent',
                    }}
                    onMouseEnter={(e) => { if (!isSelected) e.currentTarget.style.background = 'var(--bg-hover)'; }}
                    onMouseLeave={(e) => { if (!isSelected) e.currentTarget.style.background = 'transparent'; }}
                  >
                    {/* Row top: offset + status & format badges */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <span className="font-mono" style={{ fontSize: '11px', color: '#64748B', fontWeight: 600 }}>
                        0x{frag.offset_start.toString(16).toUpperCase().padStart(8, '0')}
                      </span>
                      <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                        {frag.inferred_format && (
                          <span className="badge font-mono" style={{
                            ...formatBadgeColor(frag.inferred_format),
                            fontSize: '9px', fontWeight: 700, padding: '1px 5px',
                          }}>
                            {frag.inferred_format.toUpperCase()}
                          </span>
                        )}
                        <span className="badge font-mono" style={{ ...roleBadgeColor(frag.role_guess), fontSize: '9px', padding: '1px 5px' }}>
                          {frag.role_guess}
                        </span>
                        <span className="badge" style={{ ...statusStyle(frag.status), fontSize: '9px', padding: '1px 5px' }}>
                          {frag.status}
                        </span>
                        {isDup && <span style={{ fontSize: '11px', color: '#F59E0B' }} title="Duplicate fragment">♦</span>}
                      </div>
                    </div>

                    {/* Fragment ID (shortened) */}
                    <div className="font-mono" style={{ fontSize: '11px', color: '#06B6D4', marginBottom: '4px', fontWeight: 600 }}>
                      {frag.id.slice(0, 8)}…
                    </div>

                    {/* Size + entropy + confidence */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
                      <span>{formatBytes(frag.size_bytes)} · {frag.content_class}</span>
                      <span className="font-mono" style={{ fontSize: '10px', color: '#34D399', fontWeight: 600 }}>
                        Conf: {Math.round(frag.signature_confidence * 100)}%
                      </span>
                    </div>

                    {/* Entropy preview bar */}
                    <EntropyBar value={frag.entropy} />

                    {/* Hex preview */}
                    <div className="font-mono" style={{
                      marginTop: '6px', fontSize: '10px', color: 'var(--text-disabled)',
                      letterSpacing: '0.04em', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>
                      {frag.hex_preview}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right: Hex Inspector & Header Analysis */}
        <div style={{
          background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-subtle)', overflow: 'hidden',
          display: 'flex', flexDirection: 'column',
        }}>
          <HexInspector
            fragment={selectedFragment}
            dump={hexDump}
            loading={hexLoading}
            signatures={signatures}
          />
        </div>

      </div>
    </div>
  );
};
