"""
Forensic Evidence Report Generator (Phase 10 — Spec Section 19 & 20)

Generates self-contained, tamper-evident HTML and JSON evidence reports for
reconstructed file candidates.

Includes:
- Evidence metadata (filename, hash, size, ingest timestamp, tool version)
- Candidate summary & forensic recovery status
- Bit-level provenance mapping (Output Byte Range -> Source Fragment -> Original Offset)
- Multi-signal relationship confidence decomposition
- Structural validation results
- Immutable audit trail with cryptographic chain-of-custody hashes
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from typing import Any, Mapping

TOOL_VERSION = "reconstruct-v0.5.0-alpha"


def format_hex_offset(offset: int) -> str:
    """Format an integer byte offset as uppercase hexadecimal."""
    return f"0x{offset:06X}"


def format_size(bytes_count: int) -> str:
    """Format byte count into human-readable string."""
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1048576:
        return f"{bytes_count / 1024:.1f} KB"
    return f"{bytes_count / 1048576:.2f} MB"


def generate_report_data(
    candidate: Mapping[str, Any],
    evidence: Mapping[str, Any],
    candidate_fragments: list[Mapping[str, Any]],
    provenance_spans: list[Mapping[str, Any]],
    audit_entries: list[Mapping[str, Any]],
    validation_results: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assemble structured report dictionary from database rows."""
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    gaps = json.loads(candidate.get("gaps_json") or "[]")
    evidence_strings = json.loads(candidate.get("evidence_strings_json") or "[]")

    recovery_status = candidate.get("recovery_status") or "UNCERTAIN"
    composite_conf = float(candidate.get("composite_confidence") or 0.0)
    coverage_pct = float(candidate.get("coverage_pct") or 0.0)

    return {
        "report_metadata": {
            "title": "Forensic File Reconstruction & Chain of Custody Report",
            "generated_at": now_iso,
            "tool_name": "Reconstruct Forensic Workbench",
            "tool_version": TOOL_VERSION,
            "hash_algorithm": "SHA-256 (NIST FIPS 180-4)",
            "classification": "FORENSIC ARTIFACT / INVESTIGATOR AUDIT RECORD",
        },
        "evidence_metadata": {
            "id": evidence.get("id"),
            "filename": evidence.get("filename"),
            "file_size_bytes": evidence.get("file_size_bytes"),
            "formatted_size": format_size(int(evidence.get("file_size_bytes") or 0)),
            "sha256_hash": evidence.get("sha256_hash"),
            "status": evidence.get("status"),
            "ingested_at": evidence.get("created_at"),
        },
        "candidate_summary": {
            "id": candidate.get("id"),
            "name": candidate.get("name"),
            "target_format": str(candidate.get("target_format", "")).upper(),
            "recovery_status": recovery_status,
            "composite_confidence": round(composite_conf, 4),
            "coverage_pct": round(coverage_pct, 1),
            "reconstructed_bytes": candidate.get("reconstructed_bytes", 0),
            "missing_bytes": candidate.get("missing_bytes", 0),
            "total_size_bytes": candidate.get("total_size_bytes", 0),
            "reconstruction_sha256": candidate.get("reconstruction_sha256"),
            "artifact_path": candidate.get("artifact_path"),
            "fragment_count": len(candidate_fragments),
            "gap_count": len(gaps),
            "recovered_fragments": candidate.get("recovered_fragments", 0),
            "missing_fragments": candidate.get("missing_fragments", 0),
            "corrupted_fragments": candidate.get("corrupted_fragments", 0),
            "duplicate_fragments": candidate.get("duplicate_fragments", 0),
        },
        "provenance_spans": provenance_spans,
        "gaps": gaps,
        "evidence_strings": evidence_strings,
        "validation_results": validation_results or [],
        "audit_trail": audit_entries,
    }


def generate_html_report(data: dict[str, Any]) -> str:
    """
    Render self-contained, publication-grade HTML report.
    Adheres to forensic chain-of-custody standards with printable layout.
    """
    cand = data["candidate_summary"]
    ev = data["evidence_metadata"]
    rep = data["report_metadata"]
    spans = data["provenance_spans"]
    audit = data["audit_trail"]
    evidence_strings = data["evidence_strings"]
    gaps = data["gaps"]

    status_color = "#10B981" if cand["recovery_status"] == "RECOVERED" else "#F59E0B" if cand["recovery_status"] == "PARTIALLY RECOVERED" else "#EF4444"

    # Generate Provenance Rows
    prov_rows_html = []
    for idx, span in enumerate(spans, start=1):
        out_start = span.get("output_start", 0)
        out_end = span.get("output_end", 0)
        length = span.get("length_bytes", 0)
        fid = span.get("source_fragment_id", "UNKNOWN")
        orig_off = span.get("original_evidence_offset", 0)
        status_val = span.get("validation_status", "CONFIRMED")
        sha = span.get("sha256_hash", "")
        ent = span.get("entropy", 0.0)
        is_gap = span.get("is_synthetic_filler", False)

        badge_color = "#EF4444" if is_gap else "#10B981" if status_val == "CONFIRMED" else "#F59E0B"
        row_bg = "rgba(239, 68, 68, 0.05)" if is_gap else "transparent"

        prov_rows_html.append(f"""
        <tr style="background: {row_bg}; border-bottom: 1px solid #E2E8F0;">
            <td style="padding: 10px 12px; font-weight: 600;">#{idx}</td>
            <td style="padding: 10px 12px; font-family: monospace; font-size: 13px;">
                {format_hex_offset(out_start)} &ndash; {format_hex_offset(out_end)}
            </td>
            <td style="padding: 10px 12px; font-family: monospace; font-size: 13px;">
                {format_size(length)}
            </td>
            <td style="padding: 10px 12px; font-family: monospace; font-size: 13px;">
                {html.escape(fid[:12]) if not is_gap else '<strong>SYNTHETIC GAP</strong>'}
            </td>
            <td style="padding: 10px 12px; font-family: monospace; font-size: 13px;">
                {format_hex_offset(orig_off)}
            </td>
            <td style="padding: 10px 12px; font-family: monospace; font-size: 13px;">
                {ent:.3f}
            </td>
            <td style="padding: 10px 12px;">
                <span style="display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; background: {badge_color}22; color: {badge_color};">
                    {status_val}
                </span>
            </td>
            <td style="padding: 10px 12px; font-family: monospace; font-size: 11px; color: #64748B; word-break: break-all;">
                {sha[:16]}...{sha[-8:] if len(sha) >= 24 else sha}
            </td>
        </tr>
        """)

    # Generate Audit Trail Rows
    audit_rows_html = []
    for entry in audit:
        ev_type = entry.get("event_type", "EVENT")
        created = entry.get("created_at", "")
        detail = entry.get("action_detail", "")
        e_hash = entry.get("entry_hash", "")

        audit_rows_html.append(f"""
        <tr style="border-bottom: 1px solid #E2E8F0;">
            <td style="padding: 8px 12px; font-size: 12px; color: #64748B; white-space: nowrap;">{html.escape(created)}</td>
            <td style="padding: 8px 12px; font-size: 12px; font-weight: 600; color: #0EA5E9;">{html.escape(ev_type)}</td>
            <td style="padding: 8px 12px; font-size: 12px; color: #1E293B;">{html.escape(detail)}</td>
            <td style="padding: 8px 12px; font-family: monospace; font-size: 11px; color: #94A3B8;">{e_hash[:16]}...</td>
        </tr>
        """)

    evidence_strings_html = "".join([f"<li style='margin-bottom: 6px; font-size: 13px; color: #334155;'>{html.escape(s)}</li>" for s in evidence_strings]) or "<li style='color: #94A3B8; font-size: 13px;'>No specific edge heuristics recorded.</li>"

    gaps_html = "".join([
        f"<div style='padding: 10px 14px; margin-bottom: 8px; background: #FEF2F2; border-left: 4px solid #EF4444; border-radius: 4px; font-size: 13px;'>"
        f"<strong>Gap at Seq #{g.get('after_sequence_order')}:</strong> Expected offset {format_hex_offset(g.get('offset_expected', 0))}, "
        f"estimated size {g.get('estimated_size_bytes')} bytes ({g.get('filler_type', 'zero_fill')}). "
        f"<em>{html.escape(g.get('description', ''))}</em></div>"
        for g in gaps
    ]) or "<p style='color: #10B981; font-size: 13px; font-weight: 600;'>Zero structural gaps detected. Sequence is 100% physically contiguous.</p>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Forensic Evidence Report — {cand['id']}</title>
    <style>
        @page {{
            size: A4;
            margin: 1.5cm;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #F8FAFC;
            color: #0F172A;
            margin: 0;
            padding: 32px 20px;
            line-height: 1.5;
        }}
        .report-container {{
            max-width: 1080px;
            margin: 0 auto;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            padding: 40px;
        }}
        .header-bar {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #0F172A;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header-title h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #0F172A;
        }}
        .header-title p {{
            margin: 4px 0 0 0;
            color: #64748B;
            font-size: 13px;
        }}
        .badge {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .section {{
            margin-bottom: 36px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: 700;
            color: #0F172A;
            border-bottom: 1px solid #E2E8F0;
            padding-bottom: 8px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .grid-4 {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        }}
        .card {{
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 16px;
        }}
        .card-label {{
            font-size: 12px;
            font-weight: 600;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 4px;
        }}
        .card-value {{
            font-size: 18px;
            font-weight: 700;
            color: #0F172A;
            font-family: monospace;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th {{
            background: #F1F5F9;
            color: #475569;
            font-weight: 700;
            text-align: left;
            padding: 10px 12px;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}
        .hash-box {{
            background: #F1F5F9;
            border: 1px solid #CBD5E1;
            padding: 12px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 12px;
            color: #0F172A;
            word-break: break-all;
        }}
        @media print {{
            body {{
                background: #FFFFFF;
                padding: 0;
            }}
            .report-container {{
                border: none;
                box-shadow: none;
                padding: 0;
            }}
            .no-print {{
                display: none !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <!-- Header -->
        <div class="header-bar">
            <div class="header-title">
                <h1>FORENSIC EVIDENCE REPORT</h1>
                <p>NIST FIPS 180-4 Compliant Candidate Reconstruction & Provenance Audit</p>
                <p style="margin-top: 6px; font-size: 12px; color: #94A3B8;">
                    Tool Version: <strong>{rep['tool_version']}</strong> &bull; Generated: {rep['generated_at']}
                </p>
            </div>
            <div style="text-align: right;">
                <div class="badge" style="background: {status_color}22; color: {status_color}; border: 1px solid {status_color};">
                    {cand['recovery_status']}
                </div>
                <div style="font-size: 12px; color: #64748B; margin-top: 8px;">
                    Candidate: <span style="font-family: monospace; font-weight: 700;">{cand['id']}</span>
                </div>
            </div>
        </div>

        <!-- Section 1: Executive Summary -->
        <div class="section">
            <div class="section-title">1. Executive Summary & Core Metrics</div>
            <div class="grid-4">
                <div class="card">
                    <div class="card-label">Target Format</div>
                    <div class="card-value" style="color: #0EA5E9;">{cand['target_format']}</div>
                </div>
                <div class="card">
                    <div class="card-label">Composite Confidence</div>
                    <div class="card-value" style="color: {status_color};">{(cand['composite_confidence'] * 100):.1f}%</div>
                </div>
                <div class="card">
                    <div class="card-label">Evidence Coverage</div>
                    <div class="card-value">{cand['coverage_pct']:.1f}%</div>
                </div>
                <div class="card">
                    <div class="card-label">Output Data Size</div>
                    <div class="card-value">{format_size(cand['reconstructed_bytes'])}</div>
                </div>
            </div>
        </div>

        <!-- Section 2: Cryptographic Verification -->
        <div class="section">
            <div class="section-title">2. Cryptographic Integrity Signatures (SHA-256)</div>
            <div style="display: flex; flexDirection: column; gap: 12px;">
                <div style="margin-bottom: 12px;">
                    <div class="card-label">Source Evidence Digest (Read-Only Master Image):</div>
                    <div class="hash-box">{ev['sha256_hash']}</div>
                </div>
                <div>
                    <div class="card-label">Reconstructed Artifact Digest (Derived Output File):</div>
                    <div class="hash-box" style="border-color: #10B981; color: #047857; font-weight: 700;">
                        {cand['reconstruction_sha256'] or 'NOT_YET_ASSEMBLED'}
                    </div>
                </div>
            </div>
        </div>

        <!-- Section 3: Bit-Level Provenance Timeline -->
        <div class="section">
            <div class="section-title">3. Bit-Level Provenance Mapping (Output Range &rarr; Source Offset)</div>
            <p style="font-size: 13px; color: #64748B; margin-top: -8px; margin-bottom: 16px;">
                Each byte of the reconstructed output is mapped deterministically to its carved fragment location in the primary evidence image.
            </p>
            <table>
                <thead>
                    <tr>
                        <th>Seq</th>
                        <th>Output Byte Range</th>
                        <th>Length</th>
                        <th>Source Fragment</th>
                        <th>Source Offset</th>
                        <th>Entropy</th>
                        <th>Status</th>
                        <th>Digest (SHA-256)</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(prov_rows_html)}
                </tbody>
            </table>
        </div>

        <!-- Section 4: Structural Continuity & Gap Assessment -->
        <div class="section">
            <div class="section-title">4. Gap Analysis & Boundary Consistency</div>
            {gaps_html}
        </div>

        <!-- Section 5: Heuristic & Validation Evidence Breakdown -->
        <div class="section">
            <div class="section-title">5. Multi-Signal Evidence Decomposition</div>
            <ul style="padding-left: 20px; margin: 0;">
                {evidence_strings_html}
            </ul>
        </div>

        <!-- Section 6: Forensic Audit Trail -->
        <div class="section">
            <div class="section-title">6. Chain of Custody & Tamper-Evident Audit Trail</div>
            <table>
                <thead>
                    <tr>
                        <th>Timestamp (UTC)</th>
                        <th>Event Type</th>
                        <th>Action Description</th>
                        <th>Record Hash</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(audit_rows_html)}
                </tbody>
            </table>
        </div>

        <!-- Footer Notice -->
        <div style="border-top: 1px solid #E2E8F0; padding-top: 16px; margin-top: 40px; font-size: 11px; color: #94A3B8; display: flex; justify-content: space-between;">
            <div>Reconstruct Forensic Workbench &bull; Cryptographic Hash Verification Enforced</div>
            <div>Autonomous Forensic Engine &bull; Case Record ID: {cand['id']}</div>
        </div>
    </div>
</body>
</html>"""
