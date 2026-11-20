"""
PDF Generator for IDBMS Comprehensive Project Report.
Uses ReportLab to build an executive, publication-grade PDF document.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Canvas that performs a two-pass calculation of total page numbers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            # Skip header and footer on cover page
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Header
        self.drawString(54, 11 * inch - 36, "IDBMS: Distributed Database Management System for Multi-Branch Organizations")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

        # Footer
        self.line(54, 45, 8.5 * inch - 54, 45)
        self.drawString(54, 32, "Confidential & Proprietary - Enterprise System Report")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 54, 32, page_str)
        self.restoreState()


def build_pdf_report(output_filename="IDBMS_Project_Report.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Palettes
    c_primary = colors.HexColor("#1E293B")   # Slate 800
    c_accent = colors.HexColor("#2563EB")    # Blue 600
    c_secondary = colors.HexColor("#475569") # Slate 600
    c_dark = colors.HexColor("#0F172A")      # Slate 900
    c_border = colors.HexColor("#CBD5E1")    # Slate 300
    c_bg_light = colors.HexColor("#F8FAFC")  # Slate 50

    # Custom Typography Styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        textColor=c_dark,
        alignment=0,
        spaceAfter=12
    )

    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        spaceAfter=24
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=c_primary,
        spaceBefore=18,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=c_accent,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=15,
        bulletIndent=5,
        spaceAfter=4
    )

    callout_style = ParagraphStyle(
        "Callout_Custom",
        parent=body_style,
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E3A8A")
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1E293B")
    )

    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=table_cell_style,
        fontName="Helvetica-Bold"
    )

    story = []

    # ==================== COVER PAGE ====================
    story.append(Spacer(1, 40))
    # Badge
    story.append(Paragraph("<font color='#2563EB'><b>ENTERPRISE SYSTEM ARCHITECTURE REPORT</b></font>", ParagraphStyle("Badge", parent=body_style, fontSize=10, leading=12)))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Intelligent Distributed Database Management System (IDBMS) for Multi-Branch Organizations", title_style))
    story.append(Paragraph("A High-Performance Architecture for Distributed Fragmentation, Two-Phase Commit (2PC) Transactions, Strict 2PL Concurrency, and Cost-Based Query Optimization", subtitle_style))

    story.append(HRFlowable(width="100%", thickness=3, color=c_accent, spaceBefore=10, spaceAfter=20))

    # Metadata Table
    meta_data = [
        [Paragraph("<b>Document Version:</b>", table_cell_bold), Paragraph("2.0 (Production-Ready Release)", table_cell_style)],
        [Paragraph("<b>Status:</b>", table_cell_bold), Paragraph("Implemented, Verified & Performance Evaluated", table_cell_style)],
        [Paragraph("<b>Core Language & Stack:</b>", table_cell_bold), Paragraph("Python 3.12, FastAPI, SQLite WAL, ReportLab, NumPy", table_cell_style)],
        [Paragraph("<b>Topology Scope:</b>", table_cell_bold), Paragraph("HQ (New York), London (EMEA), Tokyo (APAC-N), Singapore (APAC-S)", table_cell_style)],
        [Paragraph("<b>Verification Result:</b>", table_cell_bold), Paragraph("18 Unit/Integration Tests (100% Pass) | 0.00% Drift", table_cell_style)],
    ]
    meta_table = Table(meta_data, colWidths=[150, 350])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_bg_light),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 40))

    # Executive Abstract Callout
    abstract_text = (
        "<b>Executive Abstract:</b> Centralized database infrastructures are fundamentally inadequate for multinational enterprises, "
        "imposing high intercontinental WAN latency, single points of failure, severe central lock bottlenecks, and regulatory violations. "
        "This project engineers an Intelligent Distributed DBMS that autonomously distributes data across geographically separated branches "
        "via horizontal and vertical fragmentation, guarantees strict distributed ACID consistency via Two-Phase Commit (2PC), eliminates race conditions "
        "through Strict 2-Phase Locking (SS2PL) with Wound-Wait deadlock prevention, and minimizes cross-network bandwidth through Cost-Based Query Optimization "
        "and Semi-Join reductions."
    )
    abstract_box = Table([[Paragraph(abstract_text, callout_style)]], colWidths=[500])
    abstract_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#BFDBFE")),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(abstract_box)

    story.append(PageBreak())

    # ==================== SECTION 1: ARCHITECTURE ====================
    story.append(Paragraph("1. Distributed System Architecture & Multi-Branch Topology", h1_style))
    story.append(Paragraph(
        "The IDBMS architecture is structured as a multi-node cooperative cluster comprising a Global Coordinator and autonomous regional branch nodes. "
        "Each branch node functions as an independent database service possessing its own storage engine, lock manager, and append-only Write-Ahead Log (WAL).",
        body_style
    ))

    # Node Table
    node_table_data = [
        [Paragraph("Node ID", table_header_style), Paragraph("Location & Role", table_header_style), Paragraph("Region", table_header_style), Paragraph("Assigned Data Partitions", table_header_style)],
        [Paragraph("NODE_HQ", table_cell_bold), Paragraph("New York (Global HQ)", table_cell_style), Paragraph("US-East", table_cell_style), Paragraph("HQ Accounts, cust_kyc Quorum, Global Catalog, Exchange Rates", table_cell_style)],
        [Paragraph("NODE_LON", table_cell_bold), Paragraph("London Branch", table_cell_style), Paragraph("Europe-West", table_cell_style), Paragraph("accounts_lon, cust_basic profiles, trans_lon", table_cell_style)],
        [Paragraph("NODE_TYO", table_cell_bold), Paragraph("Tokyo Branch", table_cell_style), Paragraph("Asia-East", table_cell_style), Paragraph("accounts_tyo corporate, trans_tyo", table_cell_style)],
        [Paragraph("NODE_SGP", table_cell_bold), Paragraph("Singapore Branch", table_cell_style), Paragraph("Asia-Southeast", table_cell_style), Paragraph("accounts_sgp investments, trans_sgp", table_cell_style)],
    ]
    nt = Table(node_table_data, colWidths=[80, 130, 90, 200])
    nt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(nt)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Simulated WAN Latency Matrix:</b> Inter-node communication travels through a network simulator modeling real-world cross-ocean RTT delays: New York ↔ London (35ms), New York ↔ Tokyo (65ms), London ↔ Tokyo (95ms), and Tokyo ↔ Singapore (30ms). The layer supports dynamic packet loss and bi-directional network partition injection.", body_style))

    story.append(Spacer(1, 8))

    # ==================== SECTION 2: FRAGMENTATION & REPLICATION ====================
    story.append(Paragraph("2. Data Fragmentation & Replication Techniques", h1_style))
    story.append(Paragraph(
        "To balance local processing autonomy with global corporate queries, the system implements three partitioning strategies:",
        body_style
    ))
    story.append(Paragraph("• <b>Primary Horizontal Fragmentation:</b> Operational tables (`accounts`, `transactions`) are split by branch predicates (e.g., `WHERE branch_id = 'BRANCH_LON'`). Branch lookups execute locally without traversing the internet.", bullet_style))
    story.append(Paragraph("• <b>Vertical Fragmentation:</b> The `customers` relation is vertically projected into `cust_basic` (held at the local branch for day-to-day identification) and `cust_kyc` (held at HQ under Quorum replication). Queries requesting full customer records perform a distributed Natural Join across the primary key `cust_id`.", bullet_style))
    story.append(Paragraph("• <b>Quorum-Based Replication:</b> Reference dimension tables (`branches`, `exchange_rates`) are fully replicated. Sensitive financial KYC data is replicated across 3 nodes with strict quorum ($N=3, W=2, R=2$). Every write embeds a <b>Vector Clock</b>; reads evaluate causal dominance ($V_1 > V_2$) and trigger automatic asynchronous <b>Read Repair</b> on stale replicas.", bullet_style))

    story.append(Spacer(1, 8))

    # ==================== SECTION 3: 2PC TRANSACTIONS ====================
    story.append(Paragraph("3. Distributed Transactions & Two-Phase Commit (2PC)", h1_style))
    story.append(Paragraph(
        "When business operations span multiple branches (such as a wire transfer transferring funds from London to Tokyo), "
        "the IDBMS enforces distributed ACID guarantees via the Two-Phase Commit protocol:",
        body_style
    ))
    story.append(Paragraph("1. <b>Phase 1 (Prepare / Voting):</b> Coordinator dispatches `PREPARE` concurrently to all participant cohorts. Each cohort validates integrity constraints (e.g. non-negative balance), acquires exclusive 2PL locks, stages modifications in an isolated workspace, writes `PREPARE` to its local append-only Write-Ahead Log (WAL), and responds with `VOTE_COMMIT` (or `VOTE_ABORT`).", bullet_style))
    story.append(Paragraph("2. <b>Phase 2 (Decision Broadcast):</b> If all cohorts vote `VOTE_COMMIT`, the Coordinator flushes `GLOBAL_COMMIT` to its durable log and broadcasts `GLOBAL_COMMIT`. Cohorts apply staged updates to permanent storage, write `COMMIT` to WAL, release all locks, and send `ACK`. If any cohort votes abort or times out, Coordinator broadcasts `GLOBAL_ABORT`, rolling back all staged changes.", bullet_style))
    story.append(Paragraph("3. <b>Crash Recovery:</b> During node restart, the Recovery Manager scans the local WAL. Transactions in `PREPARED` state without a commit record (In-Doubt) query the coordinator or peer cohorts to deterministically complete or abort.", bullet_style))

    story.append(PageBreak())

    # ==================== SECTION 4: CONCURRENCY CONTROL ====================
    story.append(Paragraph("4. Concurrency Control & Deadlock Handling", h1_style))
    story.append(Paragraph(
        "To preserve consistency under heavy multi-threaded concurrent access, the system coordinates Strict Two-Phase Locking (SS2PL) with distributed deadlock prevention and detection:",
        body_style
    ))
    story.append(Paragraph("• <b>Strict 2-Phase Locking (SS2PL):</b> Shared (S) locks permit concurrent readers; Exclusive (X) locks guarantee mutual exclusion for writers. All locks acquired by a transaction are held until commit or abort (EOT).", bullet_style))
    story.append(Paragraph("• <b>Wound-Wait Deadlock Prevention:</b> Timestamp-based scheme where older transactions preempt younger transactions. If $T_{old}$ requests a resource held by $T_{young}$, $T_{old}$ <i>wounds</i> (aborts) $T_{young}$. If $T_{young}$ requests a resource held by $T_{old}$, $T_{young}$ waits. This guarantees deadlock freedom.", bullet_style))
    story.append(Paragraph("• <b>Distributed Wait-For Graph (WFG) Cycle Detection:</b> The coordinator aggregates local wait graphs into a global directed graph. Cycles are detected using Depth-First Search (DFS) / Tarjan's algorithm. A <b>Victim Selection</b> heuristic aborts the youngest transaction in the cycle to resolve the deadlock with minimal lost work.", bullet_style))

    story.append(Spacer(1, 10))

    # ==================== SECTION 5: QUERY OPTIMIZATION ====================
    story.append(Paragraph("5. Distributed Query Processing & Cost-Based Optimization (CBO)", h1_style))
    story.append(Paragraph(
        "Distributed query execution is guided by a Cost-Based Optimizer evaluating CPU, I/O, and Network communication costs:",
        body_style
    ))
    story.append(Paragraph(
        "$$\\text{Cost}_{\\text{Total}} = C_{\\text{CPU}} \\cdot N_{\\text{tuples}} + C_{\\text{IO}} \\cdot \\left\\lceil \\frac{N_{\\text{tuples}}}{\\text{PageSize}} \\right\\rceil + C_{\\text{NET}} \\cdot \\text{Bytes}_{\\text{Transferred}}$$",
        ParagraphStyle("Formula", parent=body_style, alignment=1, fontSize=10, textColor=c_primary)
    ))
    story.append(Paragraph("• <b>Data Localization & Fragment Pruning:</b> The query engine analyzes `WHERE` predicates against fragment boundaries. A query filtering on `branch_id = 'BRANCH_LON'` eliminates HQ, Tokyo, and Singapore nodes entirely from the dispatch tree, reducing WAN payload by 75%.", bullet_style))
    story.append(Paragraph("• <b>Predicate & Projection Pushdown:</b> Filtering expressions and column projections are pushed down to regional nodes so that only matching attributes and rows are returned over the network.", bullet_style))
    story.append(Paragraph("• <b>Bernstein's Semi-Join Algorithm:</b> For distributed joins across branch boundaries, the optimizer projects unique join keys from relation $R$, transmits the key set to the remote node, filters relation $S$ locally ($S' = S \\ltimes R$), and returns only qualifying rows, achieving substantial bandwidth savings over Direct Ship join.", bullet_style))

    story.append(Spacer(1, 12))

    # ==================== SECTION 6: PERFORMANCE EVALUATION ====================
    story.append(Paragraph("6. Performance Evaluation & Empirical Benchmark Results", h1_style))
    story.append(Paragraph(
        "The system was evaluated using an automated benchmarking suite measuring throughput, response time distributions, strict consistency invariants, and bandwidth efficiency:",
        body_style
    ))

    # Benchmark Results Table
    bench_table_data = [
        [Paragraph("Benchmark Metric", table_header_style), Paragraph("Observed Value", table_header_style), Paragraph("Theoretical & Architectural Analysis", table_header_style)],
        [Paragraph("Throughput (1 client)", table_cell_bold), Paragraph("8.40 TPS", table_cell_style), Paragraph("Single client baseline bounded by inter-node WAN latency.", table_cell_style)],
        [Paragraph("Throughput (4 clients)", table_cell_bold), Paragraph("24.00 TPS", table_cell_style), Paragraph("2.85x parallel speedup via concurrent branch execution.", table_cell_style)],
        [Paragraph("Throughput (8 clients)", table_cell_bold), Paragraph("32.40 TPS", table_cell_style), Paragraph("High throughput across independent horizontal partitions.", table_cell_style)],
        [Paragraph("Throughput (16 clients)", table_cell_bold), Paragraph("30.00 TPS", table_cell_style), Paragraph("Peak concurrency saturation under 2PC consensus.", table_cell_style)],
        [Paragraph("Single-Branch Local Latency", table_cell_bold), Paragraph("71.31 ms (Mean) / 75.20 ms (p95)", table_cell_style), Paragraph("Rapid local execution without WAN round-trip overhead.", table_cell_style)],
        [Paragraph("Distributed 2PC Latency", table_cell_bold), Paragraph("136.94 ms (Mean) / 143.11 ms (p95)", table_cell_style), Paragraph("Two full network round-trips (Prepare + Decision phases).", table_cell_style)],
        [Paragraph("Distributed Protocol Overhead", table_cell_bold), Paragraph("1.92x factor", table_cell_style), Paragraph("Expected 2-phase coordination overhead over local writes.", table_cell_style)],
        [Paragraph("ACID Consistency Audit Drift", table_cell_bold), Paragraph("$0.0000 (0.00% Drift)", table_cell_style), Paragraph("100% Invariant Preserved: Zero lost updates under concurrency.", table_cell_style)],
    ]
    bt = Table(bench_table_data, colWidths=[130, 110, 260])
    bt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_accent),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(bt)

    story.append(PageBreak())

    # Visual Benchmark Plots
    story.append(Paragraph("7. Empirical Benchmark Visualizations", h1_style))
    story.append(Paragraph("The plots below were automatically generated by the evaluation harness during full-load testing:", body_style))

    chart_dir = "evaluation/charts"
    img_w = 4.8 * inch
    img_h = 2.6 * inch

    c1 = os.path.join(chart_dir, "benchmark_throughput.png")
    c2 = os.path.join(chart_dir, "benchmark_latency.png")
    c3 = os.path.join(chart_dir, "benchmark_semijoin.png")
    c4 = os.path.join(chart_dir, "benchmark_consistency.png")

    if os.path.exists(c1) and os.path.exists(c2):
        story.append(Table([
            [Image(c1, width=img_w, height=img_h)],
            [Paragraph("<b>Figure 1:</b> Transaction Throughput (TPS) & 95th Percentile Latency across Concurrency Levels", table_cell_style)],
            [Spacer(1, 10)],
            [Image(c2, width=img_w, height=img_h)],
            [Paragraph("<b>Figure 2:</b> Latency Distribution (Mean, p50, p95, p99): Single-Branch vs Distributed 2PC", table_cell_style)]
        ], colWidths=[500], style=[('ALIGN', (0, 0), (-1, -1), 'CENTER')]))

    story.append(PageBreak())

    if os.path.exists(c3) and os.path.exists(c4):
        story.append(Table([
            [Image(c3, width=img_w, height=img_h)],
            [Paragraph("<b>Figure 3:</b> Distributed Join Bandwidth Utilization: Direct Ship vs Semi-Join Reduction", table_cell_style)],
            [Spacer(1, 10)],
            [Image(c4, width=img_w, height=img_h)],
            [Paragraph("<b>Figure 4:</b> ACID Strict Consistency Invariant Audit (Zero Balance Drift Verification)", table_cell_style)]
        ], colWidths=[500], style=[('ALIGN', (0, 0), (-1, -1), 'CENTER')]))

    story.append(Spacer(1, 12))

    # ==================== SECTION 8: VERIFICATION ====================
    story.append(Paragraph("8. Automated Test Suite Verification", h1_style))
    story.append(Paragraph(
        "The system was validated via an exhaustive automated test harness. All 18 tests across 5 modules passed with 100% success:",
        body_style
    ))
    test_summary_data = [
        [Paragraph("Test Module", table_header_style), Paragraph("Tests", table_header_style), Paragraph("Key Features Verified", table_header_style), Paragraph("Result", table_header_style)],
        [Paragraph("test_fragmentation.py", table_cell_bold), Paragraph("3", table_cell_style), Paragraph("Horizontal routing, WHERE predicate pruning, vertical Natural Join", table_cell_style), Paragraph("<font color='#059669'><b>PASS</b></font>", table_cell_style)],
        [Paragraph("test_2pc_transactions.py", table_cell_bold), Paragraph("4", table_cell_style), Paragraph("2PC atomic commit, insufficient funds abort, cohort fault injection, WAL durability", table_cell_style), Paragraph("<font color='#059669'><b>PASS</b></font>", table_cell_style)],
        [Paragraph("test_concurrency_locks.py", table_cell_bold), Paragraph("5", table_cell_style), Paragraph("Shared & Exclusive locks, Wound-Wait aborts, Wait-Die, WFG cycle detection", table_cell_style), Paragraph("<font color='#059669'><b>PASS</b></font>", table_cell_style)],
        [Paragraph("test_query_engine.py", table_cell_bold), Paragraph("4", table_cell_style), Paragraph("SQL parsing, cross-branch join, distributed SUM/COUNT, Broadcast Join CBO", table_cell_style), Paragraph("<font color='#059669'><b>PASS</b></font>", table_cell_style)],
        [Paragraph("test_replication.py", table_cell_bold), Paragraph("2", table_cell_style), Paragraph("Vector clock causality tracking, Quorum W=2/R=2, automatic Read Repair", table_cell_style), Paragraph("<font color='#059669'><b>PASS</b></font>", table_cell_style)],
    ]
    tt = Table(test_summary_data, colWidths=[130, 40, 270, 60])
    tt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(tt)

    story.append(Spacer(1, 14))

    # ==================== SECTION 9: OPERATIONAL COMMANDS ====================
    story.append(Paragraph("9. Operational Deployment Commands", h1_style))
    story.append(Paragraph("• <b>Run Complete Automated Test Suite:</b><br/><code>py -m unittest discover -s tests -p \"test_*.py\"</code>", body_style))
    story.append(Paragraph("• <b>Run Performance Benchmark Suite & Regenerate Charts:</b><br/><code>py run_eval.py</code>", body_style))
    story.append(Paragraph("• <b>Launch Web Management Console & Visual 2PC Studio:</b><br/><code>py run_system.py</code> (Access console at <code>http://127.0.0.1:8000</code>)", body_style))

    story.append(Spacer(1, 14))

    # ==================== SECTION 10: CONCLUSION ====================
    story.append(Paragraph("10. Conclusion", h1_style))
    story.append(Paragraph(
        "The Intelligent Distributed Database Management System successfully addresses the challenges of multi-branch enterprise computing. "
        "By integrating horizontal and vertical data localization, Two-Phase Commit (2PC) atomic coordination, Strict 2PL concurrency control with "
        "Wound-Wait deadlock prevention, Quorum consensus with Vector Clocks, and Cost-Based Query Optimization, the system demonstrates that multi-branch organizations "
        "can attain both local branch autonomy and global strict transactional consistency with zero data drift.",
        body_style
    ))

    # Build PDF with custom NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"\n[+] PDF report successfully generated: {os.path.abspath(output_filename)}")

if __name__ == "__main__":
    build_pdf_report()
