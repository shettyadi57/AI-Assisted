import { describe, it, expect } from 'vitest';
import { FORENSIC_STATUS_COLORS, TYPOGRAPHY, ELEVATIONS } from '../tokens';

describe('Forensic Design Tokens', () => {
  it('trivial baseline test passes', () => {
    expect(true).toBe(true);
  });

  it('contains all 6 required forensic status colors', () => {
    const requiredKeys = ['valid', 'recovered', 'missing', 'corrupted', 'duplicate', 'uncertain'] as const;
    requiredKeys.forEach((key) => {
      expect(FORENSIC_STATUS_COLORS[key]).toBeDefined();
      expect(FORENSIC_STATUS_COLORS[key].color).toMatch(/^#[0-9A-Fa-f]{6}$/);
      expect(FORENSIC_STATUS_COLORS[key].bg).toContain('rgba(');
      expect(FORENSIC_STATUS_COLORS[key].border).toContain('rgba(');
      expect(FORENSIC_STATUS_COLORS[key].label).toBeTruthy();
    });
  });

  it('defines forensic monospace and sans-serif typography fonts', () => {
    expect(TYPOGRAPHY.fonts.mono).toContain('JetBrains Mono');
    expect(TYPOGRAPHY.fonts.sans).toContain('Inter');
  });

  it('defines dark forensic elevation palette', () => {
    expect(ELEVATIONS.bgPage).toBe('#0B0F17');
    expect(ELEVATIONS.bgSurface).toBe('#121824');
    expect(ELEVATIONS.bgRaised).toBe('#1A2234');
  });
});
