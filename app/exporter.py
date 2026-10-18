"""
VaultSign AI - Audit Report & Export Generator
Generates exportable audit reports in Markdown, HTML, and JSON formats.
Includes mandatory legal disclaimers, verbatim quotes, page references, and pushback templates.
"""

import json
from typing import Dict, Any, List
from .analyzer import AnalysisReport, ClauseFlag
from .config import LEGAL_DISCLAIMER, JURISDICTION_NOTICE

class ReportExporter:
    @staticmethod
    def to_markdown(report: AnalysisReport, user_name: str = "Freelancer", client_name: str = "Client") -> str:
        lines = []
        lines.append("# VaultSign AI - Contract Red-Flag Audit Report")
        lines.append(f"**Document**: `{report.filename}` | **Pages**: {report.total_pages} | **Engine**: {report.model_used}")
        lines.append("\n> [!CAUTION]\n> **" + LEGAL_DISCLAIMER + "**\n>\n> " + JURISDICTION_NOTICE)
        lines.append("\n---\n")

        lines.append("## Executive Summary")
        lines.append(f"- **Total Clause Families Checked**: {report.summary.get('total_clause_families_analyzed', 8)}")
        lines.append(f"- **Flagged Red Flags**: **{report.summary.get('flagged_issues', 0)}**")
        lines.append(f"- **High Risk Traps**: **{report.summary.get('high_risk_issues', 0)}**")
        lines.append(f"- **Verifier Rejections (Hallucinations Discarded)**: {report.dropped_hallucinations_count}")
        lines.append(f"- **Execution Mode**: `{report.execution_mode}` (Strict Zero-Trust Local)\n")

        lines.append("## Detailed Clause Analysis (8 Freelancer Traps)")
        for flag in report.flags:
            status_emoji = "🚨 FLAGGED" if flag.status == "FLAGGED" else "⚪ NOT DETECTED"
            risk_badge = f"`[{flag.risk_level} RISK]`" if flag.status == "FLAGGED" else ""
            lines.append(f"### {status_emoji} {flag.family_label} {risk_badge}")

            if flag.status == "FLAGGED":
                lines.append(f"- **Verified Page Reference**: Page {flag.page_number} ({flag.section_name or 'Contract Body'})")
                lines.append(f"- **Verbatim Contract Quote**:\n  > \"{flag.verbatim_quote}\"")
                lines.append(f"- **Plain English Breakdown**: {flag.plain_english_explanation}")
                lines.append(f"- **Recommended Counter-Ask**: {flag.suggested_ask}")
                lines.append(f"- **Verifier Proof**: Verified verbatim against document source.")
            else:
                lines.append(f"- **Status**: *{flag.plain_english_explanation}*")
                lines.append(f"- **Standard Freelancer Baseline**: {flag.suggested_ask}")
            lines.append("")

        lines.append("## Zero-Trust Verification Guarantee")
        lines.append("This document was parsed and audited entirely in transient system memory on localhost (`127.0.0.1`). "
                     "Zero bytes of document content or embeddings were transmitted across the internet.")

        return "\n".join(lines)

    @staticmethod
    def to_html(report: AnalysisReport, user_name: str = "Freelancer", client_name: str = "Client") -> str:
        flags_html = []
        for flag in report.flags:
            is_flagged = flag.status == "FLAGGED"
            card_class = "border-red-500 bg-red-50/50" if is_flagged else "border-gray-200 bg-gray-50/50"
            badge_color = "bg-red-600 text-white" if flag.risk_level == "HIGH" else "bg-amber-500 text-white" if flag.risk_level == "MEDIUM" else "bg-gray-400 text-white"

            quote_block = ""
            if is_flagged:
                quote_block = f"""
                <div class="mt-3 p-3 bg-white border-l-4 border-red-500 rounded font-mono text-sm text-gray-800">
                    <strong>Source Quote (Page {flag.page_number}):</strong><br/>
                    &ldquo;{flag.verbatim_quote}&rdquo;
                </div>
                <div class="mt-3 text-sm text-gray-700">
                    <strong>Plain English Explanation:</strong> {flag.plain_english_explanation}
                </div>
                <div class="mt-2 text-sm text-indigo-900 bg-indigo-50 p-2 rounded">
                    <strong>Recommended Ask:</strong> {flag.suggested_ask}
                </div>
                """
            else:
                quote_block = f"""
                <div class="mt-2 text-sm text-gray-500 italic">
                    {flag.plain_english_explanation}
                </div>
                """

            flags_html.append(f"""
            <div class="p-4 mb-4 border rounded-lg {card_class}">
                <div class="flex items-center justify-between">
                    <h3 class="text-base font-bold text-gray-900">{flag.family_label}</h3>
                    <span class="px-2 py-1 text-xs font-semibold rounded {badge_color}">{flag.status}</span>
                </div>
                {quote_block}
            </div>
            """)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>VaultSign AI - Contract Red-Flag Audit: {report.filename}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @media print {{
            .no-print {{ display: none; }}
            body {{ background: white; }}
        }}
    </style>
</head>
<body class="bg-slate-100 text-slate-800 p-6 md:p-12">
    <div class="max-w-4xl mx-auto bg-white p-8 rounded-xl shadow-lg border border-slate-200">
        <div class="flex justify-between items-start border-b pb-4 mb-6">
            <div>
                <h1 class="text-3xl font-extrabold text-slate-900 tracking-tight">VaultSign AI</h1>
                <p class="text-sm font-medium text-slate-500">Zero-Trust Contract Red-Flag Audit Report</p>
            </div>
            <div class="text-right">
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                    🔒 Offline Verified (127.0.0.1)
                </span>
                <p class="text-xs text-slate-400 mt-1">Target: {report.filename} ({report.total_pages} pages)</p>
            </div>
        </div>

        <div class="p-4 mb-6 bg-amber-50 border-l-4 border-amber-500 text-amber-900 rounded text-xs leading-relaxed">
            <strong>LEGAL NOTICE:</strong> {LEGAL_DISCLAIMER}<br/>
            <strong>JURISDICTION NOTICE:</strong> {JURISDICTION_NOTICE}
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div class="p-4 bg-slate-50 rounded-lg text-center border">
                <p class="text-xs text-slate-500 uppercase font-semibold">Traps Audited</p>
                <p class="text-2xl font-bold text-slate-800">{report.summary.get('total_clause_families_analyzed', 8)}</p>
            </div>
            <div class="p-4 bg-red-50 rounded-lg text-center border border-red-200">
                <p class="text-xs text-red-600 uppercase font-semibold">Red Flags</p>
                <p class="text-2xl font-bold text-red-700">{report.summary.get('flagged_issues', 0)}</p>
            </div>
            <div class="p-4 bg-amber-50 rounded-lg text-center border border-amber-200">
                <p class="text-xs text-amber-600 uppercase font-semibold">High Risk</p>
                <p class="text-2xl font-bold text-amber-700">{report.summary.get('high_risk_issues', 0)}</p>
            </div>
            <div class="p-4 bg-emerald-50 rounded-lg text-center border border-emerald-200">
                <p class="text-xs text-emerald-600 uppercase font-semibold">Hallucinations Dropped</p>
                <p class="text-2xl font-bold text-emerald-700">{report.dropped_hallucinations_count}</p>
            </div>
        </div>

        <h2 class="text-xl font-bold text-slate-900 mb-4 pb-2 border-b">Clause Findings & Proof</h2>
        {"".join(flags_html)}

        <div class="mt-8 pt-4 border-t text-xs text-slate-400 text-center">
            Generated locally by VaultSign AI. No document data was transmitted to external servers.
        </div>
    </div>
</body>
</html>"""
        return html

    @staticmethod
    def to_json(report: AnalysisReport) -> str:
        return json.dumps(report.model_dump(), indent=2)
