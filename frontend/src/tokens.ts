/**
 * Reconstruct Design System Tokens
 *
 * Implements strict forensic aesthetics:
 * - Forensic status states: valid, recovered, missing, corrupted, duplicate, uncertain
 * - High-contrast dark elevations
 * - Strict typography scale
 * - Monospace font for hex previews, byte offsets, and SHA-256 hashes
 */

export const FORENSIC_STATUS_COLORS = {
  valid: {
    color: '#10B981',
    bg: 'rgba(16, 185, 129, 0.12)',
    border: 'rgba(16, 185, 129, 0.35)',
    label: 'Valid',
    description: 'Header, structural integrity, and checksum verified',
  },
  recovered: {
    color: '#06B6D4',
    bg: 'rgba(6, 182, 212, 0.12)',
    border: 'rgba(6, 182, 212, 0.35)',
    label: 'Recovered',
    description: 'Successfully assembled and reconstructed',
  },
  missing: {
    color: '#64748B',
    bg: 'rgba(100, 116, 139, 0.12)',
    border: 'rgba(100, 116, 139, 0.35)',
    label: 'Missing',
    description: 'Expected sector or fragment boundary unallocated',
  },
  corrupted: {
    color: '#EF4444',
    bg: 'rgba(239, 68, 68, 0.12)',
    border: 'rgba(239, 68, 68, 0.35)',
    label: 'Corrupted',
    description: 'Checksum failure or conflicting magic markers',
  },
  duplicate: {
    color: '#F59E0B',
    bg: 'rgba(245, 158, 11, 0.12)',
    border: 'rgba(245, 158, 11, 0.35)',
    label: 'Duplicate',
    description: 'Identical SHA-256 hash or duplicate logical sector',
  },
  uncertain: {
    color: '#8B5CF6',
    bg: 'rgba(139, 92, 246, 0.12)',
    border: 'rgba(139, 92, 246, 0.35)',
    label: 'Uncertain',
    description: 'Weak relationship confidence (<0.70) requiring review',
  },
} as const;

export type ForensicStatusKey = keyof typeof FORENSIC_STATUS_COLORS;

export const TYPOGRAPHY = {
  fonts: {
    sans: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: '"JetBrains Mono", "SF Mono", Consolas, "Fira Code", Menlo, monospace',
  },
  scale: {
    'text-xs': '11px',
    'text-sm': '12px',
    'text-base': '14px',
    'text-lg': '16px',
    'text-xl': '20px',
    'text-2xl': '24px',
    'text-3xl': '30px',
  },
  weights: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeights: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
} as const;

export const ELEVATIONS = {
  bgPage: '#0B0F17',       // Layer 0: Page canvas
  bgSurface: '#121824',    // Layer 1: Forensic cards, panels, sidebars
  bgRaised: '#1A2234',     // Layer 2: Raised interactive chips, active buttons
  bgHover: '#232D42',      // Hover state elevation
  borderSubtle: '#1E293B', // 1px borders
  borderMedium: '#334155',
  borderFocus: '#06B6D4',  // Cyan focus highlight
} as const;

export const SPACING = {
  xs: '4px',
  sm: '8px',
  md: '12px',
  lg: '16px',
  xl: '24px',
  '2xl': '32px',
  '3xl': '48px',
} as const;
