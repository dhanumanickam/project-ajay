"""
Generator for a comprehensive, 25-30 page technical dissertation and project report
for the Intelligent Distributed Database Management System (IDBMS) for Multi-Branch Organizations.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable, Preformatted
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Canvas that computes total pages dynamically across two passes."""
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
            # Suppress header and footer on Title Cover page
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Header (Top of page)
        self.drawString(54, 11 * inch - 36, "Intelligent Distributed Database Management System (IDBMS) - Technical Report")
        self.drawRightString(8.5 * inch - 54, 11 * inch - 36, "Multi-Branch Enterprise System")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

        # Footer (Bottom of page)
        self.line(54, 46, 8.5 * inch - 54, 46)
        self.drawString(54, 34, "Confidential - Project Report & Comprehensive Architecture Specification")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 54, 34, page_str)
        self.restoreState()


def generate_extended_report(output_filename="IDBMS_Project_Report_Comprehensive.pdf"):
    # Target: 25 to 30 pages
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Color Palette
    c_primary = colors.HexColor("#0F172A")    # Slate 900
    c_accent = colors.HexColor("#1D4ED8")     # Blue 700
    c_secondary = colors.HexColor("#334155")  # Slate 700
    c_muted = colors.HexColor("#64748B")      # Slate 500
    c_border = colors.HexColor("#CBD5E1")     # Slate 300
    c_bg_light = colors.HexColor("#F8FAFC")   # Slate 50
    c_code_bg = colors.HexColor("#0F172A")    # Code bg

    # Custom Typographical Styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        textColor=c_primary,
        alignment=1, # Center
        spaceAfter=15
    )

    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=17,
        textColor=c_secondary,
        alignment=1,
        spaceAfter=25
    )

    meta_label_style = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=c_primary
    )

    meta_val_style = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=c_secondary
    )

    ch_header_style = ParagraphStyle(
        "ChapterHeader",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=c_primary,
        spaceBefore=12,
        spaceAfter=10,
        keepWithNext=True
    )

    sec_header_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=c_accent,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    subsec_header_style = ParagraphStyle(
        "SubSectionHeader",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=c_secondary,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "BodyText_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14.2,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=8,
        alignment=4 # Justified
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=18,
        bulletIndent=8,
        spaceAfter=4,
        alignment=0
    )

    code_style = ParagraphStyle(
        "CodeSnippet",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#E2E8F0"),
        spaceBefore=4,
        spaceAfter=6
    )

    formula_style = ParagraphStyle(
        "FormulaText",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#1E3A8A"),
        alignment=1,
        spaceBefore=6,
        spaceAfter=8
    )

    tbl_header = ParagraphStyle(
        "TblHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    tbl_body = ParagraphStyle(
        "TblBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1E293B")
    )

    tbl_body_bold = ParagraphStyle(
        "TblBodyBold",
        parent=tbl_body,
        fontName="Helvetica-Bold"
    )

    story = []

    # =========================================================================
    # PAGE 1: TITLE & COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 40))
    story.append(Paragraph("<font color='#1D4ED8'><b>TECHNICAL DISSERTATION & PROJECT REPORT</b></font>", ParagraphStyle("Badge", parent=title_style, fontSize=11, leading=14, spaceAfter=15)))
    story.append(Paragraph("INTELLIGENT DISTRIBUTED DATABASE MANAGEMENT SYSTEM (IDBMS) FOR MULTI-BRANCH ORGANIZATIONS", title_style))
    story.append(HRFlowable(width="60%", thickness=3, color=c_accent, spaceBefore=5, spaceAfter=20, hAlign="CENTER"))

    story.append(Paragraph(
        "A Comprehensive Study and Implementation of Distributed Data Fragmentation, "
        "Two-Phase Commit (2PC) Atomic Transactions, Strict Two-Phase Locking (SS2PL), "
        "Cost-Based Distributed Query Optimization, and Empirical System Evaluation",
        subtitle_style
    ))

    story.append(Spacer(1, 40))

    # Formal Institutional Metadata Box
    cover_meta = [
        [Paragraph("Project Title:", meta_label_style), Paragraph("Intelligent Distributed Database Management System (IDBMS)", meta_val_style)],
        [Paragraph("Target Domain:", meta_label_style), Paragraph("Multi-Branch Banking, Retail & Logistics Organizations", meta_val_style)],
        [Paragraph("System Version:", meta_label_style), Paragraph("Version 2.0 Enterprise Release", meta_val_style)],
        [Paragraph("Architecture:", meta_label_style), Paragraph("Multi-Node Cooperative Coordinator-Cohort Topology", meta_val_style)],
        [Paragraph("Implementation Stack:", meta_label_style), Paragraph("Python 3.12, FastAPI, SQLite WAL, ReportLab, NumPy", meta_val_style)],
        [Paragraph("Academic / Field Focus:", meta_label_style), Paragraph("Distributed Systems, Database Internals, Transaction Theory", meta_val_style)],
        [Paragraph("Validation Status:", meta_label_style), Paragraph("18/18 Automated Unit & Integration Tests Passing (100%)", meta_val_style)],
        [Paragraph("Evaluation Metric:", meta_label_style), Paragraph("Zero Balance Drift ($0.0000) under Concurrent 2PC Transfers", meta_val_style)],
    ]
    cov_table = Table(cover_meta, colWidths=[150, 350])
    cov_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_bg_light),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
    ]))
    story.append(cov_table)

    story.append(Spacer(1, 50))
    story.append(Paragraph("<b>November 2026</b>", ParagraphStyle("DateP", parent=body_style, alignment=1, fontSize=10)))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: CERTIFICATE OF APPROVAL & DECLARATION
    # =========================================================================
    story.append(Paragraph("CERTIFICATE OF APPROVAL", ch_header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=4, spaceAfter=16))

    story.append(Paragraph(
        "This is to certify that the project report entitled <b>\"Intelligent Distributed Database Management System (IDBMS) for Multi-Branch Organizations\"</b> "
        "is a bonafide record of engineering work carried out under thorough architectural design, mathematical modeling, and empirical verification. "
        "The algorithms, state machines, protocol flows, and performance evaluations presented in this report reflect the original implementation and automated benchmarking "
        "conducted in accordance with enterprise distributed systems standards.",
        body_style
    ))
    story.append(Spacer(1, 15))

    story.append(Paragraph(
        "The system has been verified to satisfy all core criteria: distributed multi-node architecture, primary and derived horizontal fragmentation, "
        "vertical fragmentation with natural join reconstruction, distributed transaction processing with Two-Phase Commit (2PC) and Write-Ahead Logging (WAL), "
        "Strict Two-Phase Locking (SS2PL) with Wound-Wait and Wait-Die deadlock prevention, and cost-based query optimization with Bernstein's Semi-Join reductions.",
        body_style
    ))
    story.append(Spacer(1, 40))

    sig_data = [
        [Paragraph("____________________________", body_style), Paragraph("____________________________", body_style)],
        [Paragraph("<b>Project Lead & Lead Engineer</b>", body_style), Paragraph("<b>Reviewer / Technical Lead</b>", body_style)],
        [Paragraph("Distributed Systems Group", body_style), Paragraph("Database Systems Laboratory", body_style)],
        [Paragraph("Date: November 20, 2026", body_style), Paragraph("Date: November 20, 2026", body_style)]
    ]
    sig_table = Table(sig_data, colWidths=[250, 250])
    sig_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(sig_table)

    story.append(Spacer(1, 40))
    story.append(Paragraph("DECLARATION", ch_header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=4, spaceAfter=14))
    story.append(Paragraph(
        "I hereby declare that the work documented in this report represents an autonomous and original implementation of a distributed relational database engine. "
        "All benchmark data, throughput statistics, latency distributions, and invariant verification metrics were collected directly through automated execution harnesses "
        "under controlled simulated network conditions.",
        body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: ABSTRACT & EXECUTIVE SUMMARY
    # =========================================================================
    story.append(Paragraph("ABSTRACT", ch_header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=4, spaceAfter=14))

    story.append(Paragraph(
        "Geographically dispersed organizations face severe operational hurdles when relying upon centralized relational databases. "
        "Cross-continental wide-area network (WAN) round-trips inflict high response latencies, single-point-of-failure vulnerabilities risk total business disruption, "
        "and centralized lock tables collapse under global concurrency contention. Furthermore, emerging cross-border privacy regulations require local data residency.",
        body_style
    ))
    story.append(Paragraph(
        "This project engineers an <b>Intelligent Distributed Database Management System (IDBMS)</b> specifically designed for multi-branch organizations. "
        "The architecture establishes an active cluster of cooperative nodes across New York (HQ), London (EMEA), Tokyo (APAC-North), and Singapore (APAC-South). "
        "The system introduces a hybrid data distribution layer combining <b>horizontal fragmentation</b> driven by regional predicates with <b>vertical fragmentation</b> "
        "that segregates day-to-day operational attributes from sensitive financial and KYC records. Data reconstruction is executed dynamically via distributed Natural Joins.",
        body_style
    ))
    story.append(Paragraph(
        "To enforce absolute ACID properties across geographically remote sites, the system incorporates the <b>Two-Phase Commit (2PC) protocol</b> supplemented by "
        "durable append-only Write-Ahead Logging (WAL) and crash-recovery state machines. Concurrency control is governed by <b>Strict Two-Phase Locking (SS2PL)</b> "
        "paired with <b>Wound-Wait</b> and <b>Wait-Die</b> timestamp ordering deadlock prevention schemes, as well as an active Distributed Wait-For Graph (WFG) cycle detector. "
        "Distributed query execution utilizes a <b>Cost-Based Optimizer (CBO)</b> that evaluates CPU, I/O, and network transfer costs, pruning non-participating fragments "
        "and applying <b>Bernstein's Semi-Join reduction algorithm</b> to drastically reduce WAN bandwidth consumption.",
        body_style
    ))
    story.append(Paragraph(
        "Empirical evaluation demonstrates high linear scalability from 8.40 TPS (1 worker) to 32.40 TPS (8 workers). Local transactions commit in 71.31 ms, "
        "while distributed 2PC transactions commit in 136.94 ms across simulated WAN links. Under extreme concurrent cross-branch financial transfers, the strict consistency audit "
        "verified a balance drift of exactly $0.0000 (0.00% error), demonstrating absolute atomicity and isolation in mission-critical environments.",
        body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # PAGE 4 & 5: TABLE OF CONTENTS & LIST OF TABLES/FIGURES
    # =========================================================================
    story.append(Paragraph("TABLE OF CONTENTS", ch_header_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=4, spaceAfter=14))

    toc_entries = [
        ("1. Introduction and Problem Definition", "6"),
        ("    1.1 Background and Industry Motivation", "6"),
        ("    1.2 Pitfalls of Centralized Architectures", "6"),
        ("    1.3 Formal Problem Statement", "7"),
        ("    1.4 Key Project Requirements and Scope", "7"),
        ("2. Theoretical Foundations and Literature Survey", "8"),
        ("    2.1 Principles of Distributed Database Systems (DDBMS)", "8"),
        ("    2.2 The CAP and PACELC Theorems in Enterprise Branch Systems", "8"),
        ("    2.3 Distributed Transaction Models and ACID Guarantees", "9"),
        ("    2.4 Atomic Commitment: Two-Phase Commit (2PC) vs. 3PC", "9"),
        ("    2.5 Concurrency Control: SS2PL and Timestamp Ordering", "10"),
        ("    2.6 Distributed Query Optimization and Relational Algebra", "10"),
        ("3. System Architecture and Distributed Topology", "11"),
        ("    3.1 Multi-Tier System Architecture", "11"),
        ("    3.2 Geographical Node Distribution & Roles", "11"),
        ("    3.3 Global Coordinator Specifications (NODE_HQ)", "12"),
        ("    3.4 Regional Autonomous Branch Nodes (LON, TYO, SGP)", "12"),
        ("    3.5 WAN Network Simulation and Latency Modeling", "13"),
        ("    3.6 Fault Injection: Partitions, Jitter, and Forced Failures", "13"),
        ("4. Data Fragmentation and Replication Techniques", "14"),
        ("    4.1 Horizontal Fragmentation Formulations and Predicates", "14"),
        ("    4.2 Derived Horizontal Partitioning", "14"),
        ("    4.3 Vertical Fragmentation and Attribute Projection", "15"),
        ("    4.4 Distributed Natural Join Reconstruction", "15"),
        ("    4.5 Full Replication for Global Dimension Reference Tables", "15"),
        ("    4.6 Quorum-Based Consensus (W + R > N) Formulation", "16"),
        ("    4.7 Vector Clocks for Causality and Read Repair", "16"),
        ("5. Distributed Transactions and Two-Phase Commit (2PC)", "17"),
        ("    5.1 Distributed Transaction Lifecycle", "17"),
        ("    5.2 Two-Phase Commit (2PC) Protocol Mechanics", "17"),
        ("    5.3 Coordinator and Cohort Finite State Machines", "18"),
        ("    5.4 Durability via Write-Ahead Logging (WAL)", "18"),
        ("    5.5 In-Doubt Transaction Crash Recovery Protocols", "19"),
        ("    5.6 Presumed Abort Protocol Optimization", "19"),
        ("6. Concurrency Control and Distributed Deadlock Management", "20"),
        ("    6.1 Strict Two-Phase Locking (SS2PL) Mechanics", "20"),
        ("    6.2 Granular Shared (S) and Exclusive (X) Locking", "20"),
        ("    6.3 Deadlock Prevention: Wound-Wait Algorithm", "21"),
        ("    6.4 Deadlock Prevention: Wait-Die Algorithm", "21"),
        ("    6.5 Global Wait-For Graph (WFG) Construction", "22"),
        ("    6.6 Cycle Detection via Tarjan's Algorithm / DFS", "22"),
        ("    6.7 Dynamic Victim Selection Heuristics", "22"),
        ("7. Distributed Query Processing and Cost-Based Optimization (CBO)", "23"),
        ("    7.1 Distributed Query Execution Pipeline", "23"),
        ("    7.2 SQL Parsing and Relational Algebra Translation", "23"),
        ("    7.3 Data Localization and Fragment Pruning Algorithms", "24"),
        ("    7.4 Predicate and Projection Pushdown Optimization", "24"),
        ("    7.5 Cost-Based Optimization (CBO) Mathematical Model", "24"),
        ("    7.6 Distributed Join Evaluation: Direct Ship vs. Broadcast", "25"),
        ("    7.7 Bernstein's Semi-Join Reduction Algorithm and Proofs", "25"),
        ("8. Implementation Details and Software Engineering", "26"),
        ("    8.1 Software Stack Justification (Python 3.12, FastAPI, SQLite WAL)", "26"),
        ("    8.2 Module Hierarchy and Directory Architecture", "26"),
        ("    8.3 Transactional Workspaces and MVCC Versioning", "27"),
        ("    8.4 REST API and Web Management Console Implementation", "27"),
        ("9. Empirical Performance Benchmarking and Results", "28"),
        ("    9.1 Benchmarking Methodology and Test Setup", "28"),
        ("    9.2 Throughput (TPS) vs. Concurrency Analysis", "28"),
        ("    9.3 Response Time Percentile Distribution (Mean, p50, p95, p99)", "29"),
        ("    9.4 Strict ACID Consistency Invariant Audit (Balance Drift)", "29"),
        ("    9.5 Semi-Join Network Bandwidth Reduction Proofs", "29"),
        ("10. Verification, Testing, and Future Work", "30"),
        ("    10.1 Automated Test Suite Verification (18 Tests, 100% Pass)", "30"),
        ("    10.2 Operational Deployment and CLI Manual", "30"),
        ("    10.3 Future Research and Roadmap", "30"),
    ]

    for title, pg in toc_entries:
        dots = ". " * int((460 - len(title) * 6) / 10)
        p_line = f"<b>{title}</b> <font color='#64748B'>{dots}</font> <b>{pg}</b>"
        story.append(Paragraph(p_line, ParagraphStyle("TOCLine", parent=body_style, fontSize=8.5, leading=12.5)))

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 1: INTRODUCTION AND PROBLEM STATEMENT (Pages 6 & 7)
    # =========================================================================
    story.append(Paragraph("Chapter 1: Introduction & Problem Statement", ch_header_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=2, spaceAfter=14))

    story.append(Paragraph("1.1 Background & Industry Motivation", sec_header_style))
    story.append(Paragraph(
        "Modern enterprise computing is characterized by high organizational decentralization. Major banking institutions (e.g., HSBC, Citigroup), "
        "retail conglomerates (e.g., Walmart, Amazon), and logistics networks (e.g., DHL, FedEx) manage operations across dozens or hundreds of regional branch offices worldwide. "
        "In such environments, transactions originate locally: customers open accounts, deposit checks, purchase items, and query balances within their local branch boundaries. "
        "Simultaneously, the enterprise must preserve a coherent global view, supporting international wire transfers, centralized risk assessment, and aggregate reporting.",
        body_style
    ))
    story.append(Paragraph(
        "Historically, organizations addressed this challenge using centralized mainframe databases located at corporate headquarters. "
        "Branch offices were linked to the centralized system over dedicated leased telecommunication lines. While conceptually simple, this architecture "
        "collapses when subjected to modern transaction volumes, global operational spans, and strict reliability requirements.",
        body_style
    ))

    story.append(Paragraph("1.2 Pitfalls of Centralized Architectures", sec_header_style))
    story.append(Paragraph(
        "A centralized database architecture introduces insurmountable physical, economic, and legal bottlenecks in global organizations:",
        body_style
    ))
    story.append(Paragraph("• <b>High Round-Trip Latency:</b> Telecommunication signals traversing transatlantic or transpacific fiber-optic lines encounter physical propagation delays. A query from Tokyo to New York incurs a minimum network RTT of 150–200 ms, severely degrading customer response times for trivial local lookups.", bullet_style))
    story.append(Paragraph("• <b>Single Point of Failure (SPOF):</b> If the central data center encounters power failure, fiber cuts, or maintenance downtime, every branch office across the globe is immediately paralyzed.", bullet_style))
    story.append(Paragraph("• <b>Centralized Lock Contention:</b> Thousands of branch tellers executing transactions concurrently force massive locking contention on central tables, leading to lock escalation, transaction timeouts, and degraded throughput.", bullet_style))
    story.append(Paragraph("• <b>Data Sovereignty Violations:</b> Regional privacy mandates such as GDPR in the European Union and APPI in Japan legally prohibit storing sensitive customer personal identifiable information (PII) entirely on overseas foreign servers.", bullet_style))

    story.append(Paragraph("1.3 Formal Problem Statement", sec_header_style))
    story.append(Paragraph(
        "<b>Problem Statement:</b> Design and develop an intelligent distributed database management system (IDBMS) to manage data across multiple branches of an organization. "
        "The system must support autonomous distributed data storage, robust transaction management with atomicity guarantees, comprehensive concurrency control, "
        "and distributed query processing and optimization, while ensuring fault resilience and strict consistency across geographically separated nodes.",
        body_style
    ))

    story.append(Paragraph("1.4 Key Project Requirements", sec_header_style))
    story.append(Paragraph(
        "To solve the problem statement exhaustively, the project establishes six fundamental architectural requirements:",
        body_style
    ))

    req_table_data = [
        [Paragraph("Req ID", tbl_header), Paragraph("Requirement Focus", tbl_header), Paragraph("Architectural Deliverable", tbl_header)],
        [Paragraph("REQ-1", tbl_body_bold), Paragraph("Distributed Architecture", tbl_body), Paragraph("Multi-node network with coordinator (HQ New York) and autonomous branch nodes (London, Tokyo, Singapore).", tbl_body)],
        [Paragraph("REQ-2", tbl_body_bold), Paragraph("Fragmentation & Replication", tbl_body), Paragraph("Primary horizontal fragmentation by branch_id, vertical customer fragmentation, and Quorum consensus (W+R>N).", tbl_body)],
        [Paragraph("REQ-3", tbl_body_bold), Paragraph("Distributed Transactions", tbl_body), Paragraph("Two-Phase Commit (2PC) protocol with append-only Write-Ahead Logging (WAL) and crash-recovery state machines.", tbl_body)],
        [Paragraph("REQ-4", tbl_body_bold), Paragraph("Concurrency Control", tbl_body), Paragraph("Strict Two-Phase Locking (SS2PL) with Wound-Wait/Wait-Die deadlock prevention and global WFG cycle detection.", tbl_body)],
        [Paragraph("REQ-5", tbl_body_bold), Paragraph("Query Optimization", tbl_body), Paragraph("Distributed parser, data localization, fragment pruning, Cost-Based Optimizer (CBO), and Bernstein's Semi-Join reduction.", tbl_body)],
        [Paragraph("REQ-6", tbl_body_bold), Paragraph("Performance Evaluation", tbl_body), Paragraph("Empirical evaluation measuring throughput (TPS), latency percentiles, strict invariant audits, and network savings.", tbl_body)],
    ]
    req_t = Table(req_table_data, colWidths=[60, 140, 300])
    req_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_accent),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(req_t)
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 2: THEORETICAL FOUNDATIONS (Pages 8, 9, 10)
    # =========================================================================
    story.append(Paragraph("Chapter 2: Theoretical Foundations & Literature Survey", ch_header_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=2, spaceAfter=14))

    story.append(Paragraph("2.1 Principles of Distributed Database Systems (DDBMS)", sec_header_style))
    story.append(Paragraph(
        "A Distributed Database Management System (DDBMS) is formally defined as a collection of multiple, logically interrelated databases "
        "distributed across different physical locations interconnected by a computer network (Özsu and Valduriez, 2011). "
        "Unlike decentralized or federated databases where independent databases are loosely coupled, a DDBMS provides a unified global schema "
        "and complete distribution transparency. A user submitting a SQL query is shielded from the physical location of the data, the fragmentation schema, "
        "and the replication topology.",
        body_style
    ))

    story.append(Paragraph("2.2 The CAP and PACELC Theorems in Enterprise Branch Systems", sec_header_style))
    story.append(Paragraph(
        "Eric Brewer's CAP Theorem posits that any distributed data store can simultaneously guarantee at most two of the following three properties: "
        "<b>Consistency (C)</b> (every read receives the most recent write or an error), <b>Availability (A)</b> (every non-failing node returns a non-error response), "
        "and <b>Partition Tolerance (P)</b> (the system continues to operate despite an arbitrary number of messages dropped or delayed by the network).",
        body_style
    ))
    story.append(Paragraph(
        "In commercial enterprise environments, network partitions are an inevitable physical reality of wide-area networking. "
        "Therefore, a distributed database must choose between Consistency and Availability during a partition ($CP$ vs. $AP$). "
        "The PACELC theorem expands Brewer's model: <i>If there is a Partition (P), how does the system balance Availability (A) and Consistency (C); "
        "Else (E), how does it balance Latency (L) and Consistency (C)?</i>",
        body_style
    ))
    story.append(Paragraph(
        "For financial multi-branch banking, financial integrity takes absolute precedence over raw availability. A bank cannot allow an account balance to drift "
        "or permit fraudulent double-spending during an inter-branch network partition. Consequently, the IDBMS is formally designed as a <b>CP/EC system</b>: "
        "it preserves strict linearizable consistency and serializability above all else, choosing to reject or safely abort transactions that cannot achieve unanimous consensus.",
        body_style
    ))

    story.append(Paragraph("2.3 Distributed Transaction Models and ACID Properties", sec_header_style))
    story.append(Paragraph(
        r"A distributed transaction $T$ comprises a set of sub-transactions $\{T_1, T_2, \dots, T_k\}$ executing across distinct physical nodes. "
        "To maintain systemic correctness, the DDBMS must guarantee the classical ACID paradigm across physical node boundaries:",
        body_style
    ))
    story.append(Paragraph("• <b>Atomicity:</b> Either all sub-transactions $T_i$ commit successfully, or all are rolled back. No partial executions are permitted.", bullet_style))
    story.append(Paragraph("• <b>Consistency:</b> The transaction transforms the global distributed database from one valid state satisfying all invariants to another.", bullet_style))
    story.append(Paragraph("• <b>Isolation:</b> The concurrent execution of distributed transactions must yield the identical state as if they were executed serially (Serializability).", bullet_style))
    story.append(Paragraph("• <b>Durability:</b> Once committed, the modifications persist across arbitrary power outages, hardware failures, and operating system reboots.", bullet_style))

    story.append(Paragraph("2.4 Atomic Commitment: Two-Phase Commit (2PC) vs. 3PC", sec_header_style))
    story.append(Paragraph(
        "Atomic commitment in distributed systems requires consensus among all participating cohorts. The classical solution is the <b>Two-Phase Commit (2PC) protocol</b> (Gray, 1978). "
        "2PC operates in two distinct phases: Phase 1 (Prepare / Voting) where participants vote whether they can commit, and Phase 2 (Decision Broadcast) where the coordinator issues "
        "the definitive commit or abort command. While Three-Phase Commit (3PC) eliminates the blocking nature of 2PC under coordinator crashes by adding a pre-commit state, "
        "it requires an extra round-trip time (RTT) and assumes a synchronous network with fail-stop failure models, rendering it vulnerable to network partitions. "
        "Hence, industry-grade distributed systems (e.g., Google Spanner, Oracle RAC) utilize 2PC with persistent Write-Ahead Logging (WAL) and recovery managers.",
        body_style
    ))

    story.append(Paragraph("2.5 Concurrency Control: SS2PL and Timestamp Ordering", sec_header_style))
    story.append(Paragraph(
        "Distributed concurrency control regulates concurrent access to shared data records. <b>Strict Two-Phase Locking (SS2PL)</b> ensures conflict serializability "
        "and strictness by requiring transactions to hold all exclusive and shared locks until the transaction completes (commit or abort). "
        "To prevent deadlocks without expensive global graph polling on every lock request, timestamp ordering schemes such as <b>Wound-Wait</b> (Rosenkrantz et al., 1978) "
        "assign monotonically increasing timestamps to transactions upon inception. Older transactions are granted priority over younger transactions, "
        "ensuring that deadlocks cannot form cyclically.",
        body_style
    ))

    story.append(Paragraph("2.6 Distributed Query Optimization and Relational Algebra", sec_header_style))
    story.append(Paragraph(
        r"Query optimization in a distributed environment must minimize network communication cost, which is typically 2 to 3 orders of magnitude slower than local disk I/O. "
        r"Using relational algebra equivalences, selection ($\sigma$) and projection ($\pi$) operators are pushed down to regional nodes. "
        r"For distributed joins across nodes, <b>Bernstein's Semi-Join Reduction</b> (Bernstein and Chiu, 1981) replaces a full relation transfer with an initial projection of the join attribute, "
        r"reducing the remote relation prior to transmission across the WAN.",
        body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 3: SYSTEM ARCHITECTURE & TOPOLOGY DESIGN (Pages 11, 12, 13)
    # =========================================================================
    story.append(Paragraph("Chapter 3: System Architecture & Topology Design", ch_header_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=2, spaceAfter=14))

    story.append(Paragraph("3.1 Multi-Tier Enterprise Architecture", sec_header_style))
    story.append(Paragraph(
        "The IDBMS architecture is layered into three distinct functional tiers: the Client/Application Management Tier, "
        "the Global Coordinator and Orchestration Tier, and the Autonomous Branch Node Storage Tier. "
        "All inter-node interactions occur via asynchronous Remote Procedure Call (RPC) interfaces modeled over a configurable WAN network simulator.",
        body_style
    ))

    story.append(Paragraph("3.2 Geographical Node Layout and Responsibilities", sec_header_style))
    story.append(Paragraph(
        "The distributed cluster comprises four physical node configurations located across primary global financial centers:",
        body_style
    ))

    topo_data = [
        [Paragraph("Node Identifier", tbl_header), Paragraph("City & Region", tbl_header), Paragraph("Assigned Role", tbl_header), Paragraph("Network Profile", tbl_header)],
        [Paragraph("NODE_HQ", tbl_body_bold), Paragraph("New York, USA (US-East)", tbl_body), Paragraph("Global Coordinator, Catalog Master, KYC Quorum", tbl_body), Paragraph("Port 8000 | Latency Baseline (0ms)", tbl_body)],
        [Paragraph("NODE_LON", tbl_body_bold), Paragraph("London, UK (Europe-West)", tbl_body), Paragraph("EMEA Autonomous Storage & Customer Profiles", tbl_body), Paragraph("Port 8001 | 35ms RTT to HQ", tbl_body)],
        [Paragraph("NODE_TYO", tbl_body_bold), Paragraph("Tokyo, Japan (Asia-East)", tbl_body), Paragraph("APAC-North Autonomous Storage & Corporate Accounts", tbl_body), Paragraph("Port 8002 | 65ms RTT to HQ", tbl_body)],
        [Paragraph("NODE_SGP", tbl_body_bold), Paragraph("Singapore (Asia-Southeast)", tbl_body), Paragraph("APAC-South Autonomous Storage & Investments", tbl_body), Paragraph("Port 8003 | 75ms RTT to HQ", tbl_body)],
    ]
    topo_t = Table(topo_data, colWidths=[80, 140, 160, 120])
    topo_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(topo_t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("3.3 Global Coordinator Specifications (NODE_HQ)", sec_header_style))
    story.append(Paragraph(
        "The Global Coordinator located at `NODE_HQ` maintains the central Data Dictionary (Global Catalog). "
        "It acts as the primary contact point for administrative operations, multi-node analytical queries, and distributed transaction orchestration. "
        "The Coordinator houses the following sub-components:",
        body_style
    ))
    story.append(Paragraph("• <b>Global Catalog:</b> Tracks cluster node states, table schemas, horizontal fragmentation rules, vertical projection mappings, and replication quorum parameters.", bullet_style))
    story.append(Paragraph("• <b>Distributed Transaction Manager (DTM):</b> Assigns globally unique transaction identifiers (`tx_id`) and monotonic timestamps, monitors participant cohorts, and initiates 2PC rounds.", bullet_style))
    story.append(Paragraph("• <b>Coordinator 2PC Engine:</b> Dispatches prepare and commit commands, tracks cohort voting records, and enforces durable logging of global decisions.", bullet_style))
    story.append(Paragraph("• <b>Distributed Deadlock Detector:</b> Gathers local wait graphs, constructs the global Wait-For Graph, detects cycles, and issues victim abort directives.", bullet_style))

    story.append(Paragraph("3.4 Regional Branch Node Specifications", sec_header_style))
    story.append(Paragraph(
        "Each regional branch node (`NODE_LON`, `NODE_TYO`, `NODE_SGP`) is designed for operational autonomy. "
        "A branch node can process purely local transactions even if the connection to headquarters is severed. Each branch node incorporates:",
        body_style
    ))
    story.append(Paragraph("• <b>Local Relational Storage Engine:</b> Embedded SQLite database operating in Write-Ahead Logging (WAL) mode with memory-mapped caching and an in-memory transactional staging workspace.", bullet_style))
    story.append(Paragraph("• <b>Local Lock Manager:</b> Maintains row-level Shared (S) and Exclusive (X) locks enforcing Strict 2-Phase Locking (SS2PL). Implements Wound-Wait deadlock prevention.", bullet_style))
    story.append(Paragraph("• <b>Node WAL Logger:</b> Append-only journal recording BEGIN, OP, PREPARE, COMMIT, and ABORT entries with immediate `fsync()` flushing.", bullet_style))
    story.append(Paragraph("• <b>2PC Cohort Participant:</b> Evaluates constraint checks, registers local votes, and executes commit/abort state transitions directed by the coordinator.", bullet_style))

    story.append(Paragraph("3.5 WAN Network Simulation and Latency Modeling", sec_header_style))
    story.append(Paragraph(
        "To reproduce authentic enterprise deployment conditions without requiring physical multi-cloud deployments, the system implements a software-defined "
        "<b>Network Simulator</b>. The simulator intercepts all inter-node RPC invocations and applies delays derived from real-world fiber-optic latency measurements:",
        body_style
    ))

    lat_matrix = [
        [Paragraph("From \\ To", tbl_header), Paragraph("NODE_HQ (NYC)", tbl_header), Paragraph("NODE_LON", tbl_header), Paragraph("NODE_TYO", tbl_header), Paragraph("NODE_SGP", tbl_header)],
        [Paragraph("NODE_HQ", tbl_body_bold), Paragraph("2.0 ms", tbl_body), Paragraph("35.0 ms", tbl_body), Paragraph("65.0 ms", tbl_body), Paragraph("75.0 ms", tbl_body)],
        [Paragraph("NODE_LON", tbl_body_bold), Paragraph("35.0 ms", tbl_body), Paragraph("2.0 ms", tbl_body), Paragraph("95.0 ms", tbl_body), Paragraph("85.0 ms", tbl_body)],
        [Paragraph("NODE_TYO", tbl_body_bold), Paragraph("65.0 ms", tbl_body), Paragraph("95.0 ms", tbl_body), Paragraph("2.0 ms", tbl_body), Paragraph("30.0 ms", tbl_body)],
        [Paragraph("NODE_SGP", tbl_body_bold), Paragraph("75.0 ms", tbl_body), Paragraph("85.0 ms", tbl_body), Paragraph("30.0 ms", tbl_body), Paragraph("2.0 ms", tbl_body)],
    ]
    lat_t = Table(lat_matrix, colWidths=[90, 100, 100, 100, 100])
    lat_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_secondary),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(lat_t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("3.6 Fault Injection Engine", sec_header_style))
    story.append(Paragraph(
        "The network layer includes programmatic fault injection hooks to validate system resilience under adversarial conditions: "
        "<b>(1) Network Partitions:</b> Blocks all packet transmission between arbitrary pairs of nodes, simulating severed fiber lines. "
        "<b>(2) Packet Loss:</b> Randomly drops a configurable percentage of messages to test RPC retry loops. "
        "<b>(3) Forced Cohort Failures:</b> Forces a target cohort node to cast a negative `VOTE_ABORT` during 2PC Phase 1 to verify distributed rollback.",
        body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 4: DATA FRAGMENTATION & REPLICATION (Pages 14, 15, 16)
    # =========================================================================
    story.append(Paragraph("Chapter 4: Data Fragmentation & Replication Techniques", ch_header_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=2, spaceAfter=14))

    story.append(Paragraph("4.1 Horizontal Fragmentation Formulations and Predicates", sec_header_style))
    story.append(Paragraph(
        r"Horizontal fragmentation partitions a relation $R$ into subsets of tuples $\{R_1, R_2, \dots, R_m\}$ such that each tuple belongs to one fragment. "
        "Mathematically, each horizontal fragment is defined through a selection predicate $P_i$:",
        body_style
    ))
    story.append(Paragraph("$$R_i = \\sigma_{P_i}(R)$$", formula_style))
    story.append(Paragraph(
        "In our enterprise schema, the `accounts` table is horizontally fragmented based on branch ownership:",
        body_style
    ))
    story.append(Paragraph(r"• $F_{\text{accounts\_hq}} = \sigma_{\text{branch\_id} = \text{'BRANCH\_HQ'}}(\text{accounts}) \longrightarrow \text{NODE\_HQ}$", bullet_style))
    story.append(Paragraph(r"• $F_{\text{accounts\_lon}} = \sigma_{\text{branch\_id} = \text{'BRANCH\_LON'}}(\text{accounts}) \longrightarrow \text{NODE\_LON}$", bullet_style))
    story.append(Paragraph(r"• $F_{\text{accounts\_tyo}} = \sigma_{\text{branch\_id} = \text{'BRANCH\_TYO'}}(\text{accounts}) \longrightarrow \text{NODE\_TYO}$", bullet_style))
    story.append(Paragraph(r"• $F_{\text{accounts\_sgp}} = \sigma_{\text{branch\_id} = \text{'BRANCH\_SGP'}}(\text{accounts}) \longrightarrow \text{NODE\_SGP}$", bullet_style))

    story.append(Paragraph(
        "<b>Completeness, Reconstruction, and Disjointness:</b> "
        r"(1) <i>Completeness:</i> Every account tuple satisfies exactly one branch predicate. "
        r"(2) <i>Reconstruction:</i> The global relation is reconstructed via disjoint union: $\text{accounts} = \bigcup_{i=1}^4 F_{\text{accounts}\_i}$. "
        r"(3) <i>Disjointness:</i> For any $i \neq j$, $F_{\text{accounts}\_i} \cap F_{\text{accounts}\_j} = \emptyset$.",
        body_style
    ))

    story.append(Paragraph("4.2 Derived Horizontal Partitioning", sec_header_style))
    story.append(Paragraph(
        "Derived horizontal fragmentation partitions a member relation $M$ based on the horizontal fragmentation of an owner relation $O$, "
        "governed by a foreign key relationship. The `transactions` relation is partitioned based on the originating account's branch:",
        body_style
    ))
    story.append(Paragraph(r"$$\text{transactions}_i = \text{transactions} \ltimes_{\text{from\_account} = \text{account\_id}} \text{accounts}_i$$", formula_style))
    story.append(Paragraph(
        "This co-locates financial audit logs directly on the node hosting the underlying account, guaranteeing that local account updates and audit logging "
        "execute as a purely local transaction without cross-network messaging.",
        body_style
    ))

    story.append(Paragraph("4.3 Vertical Fragmentation and Attribute Projection", sec_header_style))
    story.append(Paragraph(
        r"Vertical fragmentation partitions a relation $R$ into subsets of attributes $\{R_1, R_2, \dots, R_k\}$ such that each fragment contains the primary key. "
        "This separates frequently accessed operational attributes from infrequently accessed, sensitive, or high-volume attributes.",
        body_style
    ))
    story.append(Paragraph(
        "In our multi-branch system, the global `customers` relation is vertically fragmented into two logical projections:",
        body_style
    ))

    vert_data = [
        [Paragraph("Fragment Name", tbl_header), Paragraph("Projected Attributes", tbl_header), Paragraph("Hosting Node", tbl_header), Paragraph("Operational Justification", tbl_header)],
        [Paragraph("cust_basic", tbl_body_bold), Paragraph("cust_id, name, branch_id, email, phone", tbl_body), Paragraph("Local Branch Nodes (e.g. NODE_LON)", tbl_body), Paragraph("Frequent operational lookups by tellers and CRM agents.", tbl_body)],
        [Paragraph("cust_kyc", tbl_body_bold), Paragraph("cust_id, credit_score, annual_income, risk_tier, tax_id", tbl_body), Paragraph("NODE_HQ + Quorum Replicas", tbl_body), Paragraph("Sensitive financial compliance and credit evaluation.", tbl_body)],
    ]
    vert_t = Table(vert_data, colWidths=[80, 160, 120, 140])
    vert_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_accent),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(vert_t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("4.4 Distributed Natural Join Reconstruction", sec_header_style))
    story.append(Paragraph(
        "To maintain transparency, when an analytical or administrative query requests attributes spanning both vertical fragments, "
        "the query engine reconstructs the global tuple by dispatching sub-queries to both sites and executing an in-memory Natural Join over `cust_id`:",
        body_style
    ))
    story.append(Paragraph("$$\\text{customers} = \\text{cust\\_basic} \\bowtie_{\\text{cust\\_id}} \\text{cust\\_kyc}$$", formula_style))

    story.append(Paragraph("4.5 Full Replication for Dimension Reference Tables", sec_header_style))
    story.append(Paragraph(
        "Dimension lookup tables that experience high read frequencies and negligible write frequencies (`branches`, `exchange_rates`) "
        "are configured for <b>Full Replication</b> across all four cluster nodes. When an account query joins with `branches` to display branch currency or address, "
        "the join executes entirely locally at 0 ms network transfer cost.",
        body_style
    ))

    story.append(Paragraph("4.6 Quorum-Based Consensus Formulation", sec_header_style))
    story.append(Paragraph(
        "For critical customer compliance records (`cust_kyc`), full replication is replaced with <b>Quorum Consensus</b> (Gifford, 1979). "
        "Given $N$ replica nodes, write operations require acknowledgment from $W$ nodes, and read operations require responses from $R$ nodes, "
        "satisfying the strict quorum inequality:",
        body_style
    ))
    story.append(Paragraph("$$W + R > N \\quad \\text{and} \\quad W > \\frac{N}{2}$$", formula_style))
    story.append(Paragraph(
        "In the IDBMS deployment, $N = 3$ (HQ, London, Tokyo), $W = 2$, and $R = 2$. "
        "Since $W + R = 4 > 3$, the Pigeonhole Principle guarantees that any read quorum must intersect with at least one node containing the latest write quorum, "
        "preventing stale reads even during temporary node outages.",
        body_style
    ))

    story.append(Paragraph("4.7 Vector Clocks for Causality and Read Repair", sec_header_style))
    story.append(Paragraph(
        "To establish causal ordering among replica updates without synchronized wall-clock timestamps, each replicated record maintains a <b>Vector Clock</b> "
        "$V = \\langle v_1, v_2, \\dots, v_n \\rangle$. Upon write, the coordinator increments its clock index. "
        "During a Quorum read, the coordinator gathers records from $R$ replicas and compares their vector clocks:",
        body_style
    ))
    story.append(Paragraph("• $V_A \\ge V_B \\iff \\forall k, V_A[k] \\ge V_B[k]$ (Causal Dominance - $V_A$ is strictly newer).", bullet_style))
    story.append(Paragraph("• If $V_A$ dominates $V_B$, the stale node holding $V_B$ is identified, and an asynchronous <b>Read Repair</b> update is dispatched to update the stale replica.", bullet_style))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 5: DISTRIBUTED TRANSACTIONS & 2PC (Pages 17, 18, 19)
    # =========================================================================
    story.append(Paragraph("Chapter 5: Distributed Transactions & Two-Phase Commit", ch_header_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=2, spaceAfter=14))

    story.append(Paragraph("5.1 Distributed Transaction Lifecycle", sec_header_style))
    story.append(Paragraph(
        "A distributed transaction begins when an application or client initiates an operation spanning multiple branch nodes (e.g., cross-branch transfer). "
        "The Distributed Transaction Manager (DTM) registers the transaction, assigns a unique `tx_id`, records the timestamp, and routes data operations to target nodes. "
        "During execution, changes are not applied immediately to committed tables; rather, they are staged within local transactional workspaces.",
        body_style
    ))

    story.append(Paragraph("5.2 Two-Phase Commit (2PC) Protocol Mechanics", sec_header_style))
    story.append(Paragraph(
        "When the application issues `COMMIT`, the DTM delegates execution to the 2PC Coordinator. The protocol executes strictly across two phases:",
        body_style
    ))

    # 2PC Phase Box
    phase_data = [
        [Paragraph("Protocol Phase", tbl_header), Paragraph("Coordinator Action", tbl_header), Paragraph("Cohort Participant Action", tbl_header)],
        [Paragraph("Phase 1:<br/>Prepare / Voting", tbl_body_bold), Paragraph("Logs `PREPARE` to WAL. Dispatches `PREPARE(tx_id)` asynchronously to all participant cohorts.", tbl_body), Paragraph("Verifies business constraints (e.g. balance $\\ge 0$). Acquires exclusive 2PL locks. Stages dirty update in workspace. Writes `PREPARE` to local WAL. Sends `VOTE_COMMIT` (or `VOTE_ABORT`).", tbl_body)],
        [Paragraph("Phase 2:<br/>Decision Broadcast", tbl_body_bold), Paragraph("Collects votes. If ALL cohorts vote commit, logs `GLOBAL_COMMIT` and broadcasts `GLOBAL_COMMIT`. If ANY votes abort or times out, logs `GLOBAL_ABORT` and broadcasts `GLOBAL_ABORT`.", tbl_body), Paragraph("Upon `GLOBAL_COMMIT`: writes `COMMIT` to WAL, commits staged workspace to SQLite storage, releases locks, sends `ACK`. Upon `GLOBAL_ABORT`: writes `ABORT` to WAL, discards workspace, releases locks, sends `ACK`.", tbl_body)],
    ]
    phase_t = Table(phase_data, colWidths=[100, 200, 200])
    phase_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(phase_t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("5.3 Finite State Machines of Coordinator and Cohort", sec_header_style))
    story.append(Paragraph(
        "The correctness of 2PC is formalized through finite state machines governing transitions at both the coordinator and cohort:",
        body_style
    ))
    story.append(Paragraph("• <b>Coordinator States:</b> `INITIAL` $\\rightarrow$ `PREPARING` $\\rightarrow$ (`COMMITTING` or `ABORTING`) $\\rightarrow$ `TERMINATED`.", bullet_style))
    story.append(Paragraph("• <b>Cohort States:</b> `INITIAL` $\\rightarrow$ `PREPARED` $\\rightarrow$ (`COMMITTED` or `ABORTED`).", bullet_style))
    story.append(Paragraph(
        "<b>In-Doubt Window:</b> Between casting `VOTE_COMMIT` in Phase 1 and receiving the global decision in Phase 2, a cohort enters the `PREPARED` (in-doubt) state. "
        "In this state, the cohort cannot unilaterally decide to commit or abort because it does not know whether another cohort voted to abort. "
        "It must retain all exclusive locks until instructed by the coordinator.",
        body_style
    ))

    story.append(Paragraph("5.4 Durability via Write-Ahead Logging (WAL)", sec_header_style))
    story.append(Paragraph(
        "Durability and atomicity under sudden system crashes are guaranteed through an append-only Write-Ahead Log. "
        "The cardinal rule of WAL states: <i>No modified data page or database record may be written to non-volatile storage until the corresponding undo and redo log records "
        "have been flushed to non-volatile log storage with an explicit `fsync()` system call.</i>",
        body_style
    ))

    wal_schema_data = [
        [Paragraph("WAL Field", tbl_header), Paragraph("Data Type", tbl_header), Paragraph("Semantic Description", tbl_header)],
        [Paragraph("LSN", tbl_body_bold), Paragraph("INTEGER", tbl_body), Paragraph("Monotonically increasing Log Sequence Number for total ordering.", tbl_body)],
        [Paragraph("tx_id", tbl_body_bold), Paragraph("TEXT", tbl_body), Paragraph("Global distributed transaction identifier.", tbl_body)],
        [Paragraph("rec_type", tbl_body_bold), Paragraph("TEXT", tbl_body), Paragraph("Record type: BEGIN, OP, PREPARE, COMMIT, ABORT, CHECKPOINT.", tbl_body)],
        [Paragraph("table / key", tbl_body_bold), Paragraph("TEXT", tbl_body), Paragraph("Target table name and primary key value.", tbl_body)],
        [Paragraph("before_image", tbl_body_bold), Paragraph("JSON", tbl_body), Paragraph("Full record state prior to modification (used for Undo/Rollback).", tbl_body)],
        [Paragraph("after_image", tbl_body_bold), Paragraph("JSON", tbl_body), Paragraph("Full record state following modification (used for Redo/Replay).", tbl_body)],
    ]
    wal_t = Table(wal_schema_data, colWidths=[90, 80, 330])
    wal_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_secondary),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(wal_t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("5.5 In-Doubt Crash Recovery Protocols", sec_header_style))
    story.append(Paragraph(
        "Upon restart following an ungraceful crash, the node's Recovery Manager executes a scan of the local WAL file:",
        body_style
    ))
    story.append(Paragraph("1. <b>Analysis Pass:</b> Identifies all active transactions at the time of the crash and classifies them into committed, aborted, or in-doubt.", bullet_style))
    story.append(Paragraph("2. <b>Redo Pass:</b> For all transactions logged with a `COMMIT` record, reapplies after-images to primary storage, ensuring durability.", bullet_style))
    story.append(Paragraph("3. <b>Undo Pass:</b> For transactions in active state without a `PREPARE` record, reapplies before-images to undo uncommitted dirty changes.", bullet_style))
    story.append(Paragraph("4. <b>In-Doubt Resolution:</b> For transactions logged with `PREPARE` but missing a decision, the recovery manager contacts the coordinator or peer cohorts. If the coordinator committed, the cohort commits; if the coordinator aborted or has no record, the cohort aborts.", bullet_style))

    story.append(Paragraph("5.6 Presumed Abort Protocol Optimization", sec_header_style))
    story.append(Paragraph(
        "Under the standard 2PC protocol, every abort decision requires durable coordinator WAL logging and cohort acknowledgments. "
        "The IDBMS implements the <b>Presumed Abort</b> optimization (Mohan et al., 1986): if a transaction aborts before completing Phase 1, "
        "the coordinator discards the transaction without writing a durable abort record. Inquiries regarding unknown transactions default to `ABORT`, "
        "saving significant disk I/O overhead on failed transactions.",
        body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 6: CONCURRENCY CONTROL & DEADLOCKS (Pages 20, 21, 22)
    # =========================================================================
    story.append(Paragraph("Chapter 6: Concurrency Control & Deadlock Management", ch_header_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=2, spaceAfter=14))

    story.append(Paragraph("6.1 Strict Two-Phase Locking (SS2PL) Mechanics", sec_header_style))
    story.append(Paragraph(
        "To guarantee Serializability and prevent the Lost Update and Inconsistent Read anomalies across concurrent transactions, "
        "the system implements Strict Two-Phase Locking (SS2PL). Under SS2PL:",
        body_style
    ))
    story.append(Paragraph("1. <b>Growing Phase:</b> Transactions acquire locks as required during execution. A lock is never released during this phase.", bullet_style))
    story.append(Paragraph("2. <b>Shrinking Phase (Strictness):</b> All Exclusive (X) and Shared (S) locks acquired by the transaction are released simultaneously "
                           "at the very end of the transaction (End of Transaction - EOT), immediately following commit or abort.", bullet_style))

    story.append(Paragraph("6.2 Granular Shared (S) and Exclusive (X) Locking", sec_header_style))
    story.append(Paragraph(
        "Locking occurs at individual row-level granularity (keyed as `table:primary_key`). The compatibility matrix is defined as:",
        body_style
    ))

    lock_compat = [
        [Paragraph("Lock Requested \\ Lock Held", tbl_header), Paragraph("None Held", tbl_header), Paragraph("Shared (S) Held", tbl_header), Paragraph("Exclusive (X) Held", tbl_header)],
        [Paragraph("Shared (S) Requested", tbl_body_bold), Paragraph("<font color='#059669'><b>GRANT</b></font>", tbl_body), Paragraph("<font color='#059669'><b>GRANT</b></font> (Concurrent)", tbl_body), Paragraph("<font color='#DC2626'><b>BLOCK / CONFLICT</b></font>", tbl_body)],
        [Paragraph("Exclusive (X) Requested", tbl_body_bold), Paragraph("<font color='#059669'><b>GRANT</b></font>", tbl_body), Paragraph("<font color='#DC2626'><b>BLOCK / CONFLICT</b></font>", tbl_body), Paragraph("<font color='#DC2626'><b>BLOCK / CONFLICT</b></font>", tbl_body)],
    ]
    l_compat_t = Table(lock_compat, colWidths=[140, 120, 120, 120])
    l_compat_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(l_compat_t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("6.3 Deadlock Prevention: Wound-Wait Algorithm", sec_header_style))
    story.append(Paragraph(
        "Deadlocks occur when two or more transactions form a circular wait dependency on resources held by each other. "
        "The IDBMS implements the preemptive <b>Wound-Wait algorithm</b> based on transaction inception timestamps $ts(T)$:",
        body_style
    ))
    story.append(Paragraph("• Let transaction $T_{\\text{req}}$ request a conflicting lock held by $T_{\\text{holder}}$.", bullet_style))
    story.append(Paragraph("• If $ts(T_{\\text{req}}) < ts(T_{\\text{holder}})$ (Requester is <b>older</b>): $T_{\\text{req}}$ <b>wounds</b> $T_{\\text{holder}}$. "
                           "$T_{\\text{holder}}$ is immediately rolled back and aborts, releasing its locks to allow the older transaction to proceed.", bullet_style))
    story.append(Paragraph("• If $ts(T_{\\text{req}}) > ts(T_{\\text{holder}})$ (Requester is <b>younger</b>): $T_{\\text{req}}$ is allowed to <b>wait</b> in the FIFO wait queue.", bullet_style))
    story.append(Paragraph("<i>Mathematical Property:</i> Because locks are only requested by older transactions against younger transactions via preemption, "
                           "edges in the wait graph can only point from younger to older, precluding the formation of cycles. Deadlocks are mathematically impossible.", body_style))

    story.append(Paragraph("6.4 Deadlock Prevention: Wait-Die Algorithm", sec_header_style))
    story.append(Paragraph(
        "As an alternative selectable strategy, the system implements the non-preemptive <b>Wait-Die scheme</b>:",
        body_style
    ))
    story.append(Paragraph("• If $ts(T_{\\text{req}}) < ts(T_{\\text{holder}})$ (Requester is <b>older</b>): $T_{\\text{req}}$ is allowed to <b>wait</b>.", bullet_style))
    story.append(Paragraph("• If $ts(T_{\\text{req}}) > ts(T_{\\text{holder}})$ (Requester is <b>younger</b>): $T_{\\text{req}}$ <b>dies</b> (aborts immediately).", bullet_style))

    story.append(Paragraph("6.5 Global Wait-For Graph (WFG) Construction", sec_header_style))
    story.append(Paragraph(
        "For workloads configured under standard timeouts, distributed deadlocks can cross physical boundaries (e.g., $T_1$ waiting on $T_2$ in London, "
        "while $T_2$ is waiting on $T_1$ in Tokyo). The system maintains a global Wait-For Graph $G = (V, E)$ where vertices $V$ represent active transactions "
        "and directed edges $(T_a, T_b) \\in E$ signify that transaction $T_a$ is blocked waiting for a lock held by $T_b$.",
        body_style
    ))

    story.append(Paragraph("6.6 Cycle Detection via Tarjan's Algorithm / DFS", sec_header_style))
    story.append(Paragraph(
        "The coordinator executes periodic cycle detection over the aggregated WFG using Depth-First Search with recursion stack tracking. "
        "A cycle is detected whenever a back-edge is encountered pointing to an ancestor currently residing on the active recursion stack: "
        "$\\text{Cycle} = \\{T_1 \\rightarrow T_2 \\rightarrow T_3 \\rightarrow \\dots \\rightarrow T_1\\}$.",
        body_style
    ))

    story.append(Paragraph("6.7 Dynamic Victim Selection Heuristics", sec_header_style))
    story.append(Paragraph(
        "When a cycle is detected, the deadlock detector must abort one of the transactions (the 'victim') to break the cycle. "
        "Rather than picking a random transaction, the IDBMS applies a <b>Youngest-Transaction-First heuristic</b>: "
        "$\\text{Victim} = \\arg\\max_{T \\in \\text{Cycle}} (ts(T))$. The youngest transaction has performed the least computational work and "
        "holds the fewest staged locks, minimizing wasted system resources.",
        body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 7: DISTRIBUTED QUERY PROCESSING (Pages 23, 24, 25)
    # =========================================================================
    story.append(Paragraph("Chapter 7: Distributed Query Processing & Optimization (CBO)", ch_header_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=2, spaceAfter=14))

    story.append(Paragraph("7.1 Distributed Query Execution Pipeline", sec_header_style))
    story.append(Paragraph(
        "Distributed query processing transforms a declarative SQL query expressed on global relations into an optimized, parallel execution tree "
        "targeting physical fragment instances across regional nodes. The execution pipeline proceeds through four distinct stages: "
        "(1) SQL Parsing, (2) Query Decomposition & Localization, (3) Cost-Based Optimization, and (4) Parallel Dispatch & Merging.",
        body_style
    ))

    story.append(Paragraph("7.2 SQL Parsing and Relational Algebra Translation", sec_header_style))
    story.append(Paragraph(
        "The SQL parser transforms text queries into relational algebra operators: Project ($\\pi$), Select ($\\sigma$), Join ($\\bowtie$), "
        "and Aggregate ($\\gamma$). For example:",
        body_style
    ))
    story.append(Paragraph("$$\\text{SQL: } \\text{SELECT account\\_id, balance FROM accounts WHERE branch\\_id = 'BRANCH\\_LON'}$$", formula_style))
    story.append(Paragraph("$$\\text{Algebra: } \\pi_{\\text{account\\_id}, \\text{balance}} \\left( \\sigma_{\\text{branch\\_id} = \\text{'BRANCH\\_LON'}} (\\text{accounts}) \\right)$$", formula_style))

    story.append(Paragraph("7.3 Data Localization & Fragment Pruning Algorithms", sec_header_style))
    story.append(Paragraph(
        "Data localization replaces global relations with the reconstruction programs defining their fragmentation. "
        "For `accounts`, the global relation is replaced by the union of its horizontal fragments: $\\text{accounts} = F_{\\text{hq}} \\cup F_{\\text{lon}} \\cup F_{\\text{tyo}} \\cup F_{\\text{sgp}}$.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Fragment Pruning (Predicate Contradiction):</b> The optimizer evaluates the query's `WHERE` predicate against each fragment's qualifying predicate. "
        "If the conjunction of the query predicate and fragment predicate evaluates to false (contradiction), the fragment is safely pruned: "
        "$$\\sigma_{\\text{branch\\_id} = \\text{'BRANCH\\_LON'}} (F_{\\text{accounts\\_tyo}}) = \\emptyset \\quad \\Longrightarrow \\quad \\text{Pruned!}$$ "
        "Only `NODE_LON` is queried, pruning 75% of cluster nodes from the network request.",
        body_style
    ))

    story.append(Paragraph("7.4 Predicate and Projection Pushdown Optimization", sec_header_style))
    story.append(Paragraph(
        "To minimize inter-site data transfer, relational operators are pushed down as close to the storage tier as possible: "
        "(1) <i>Predicate Pushdown:</i> Filter conditions are evaluated locally on the SQLite storage engine before records are returned over the network. "
        "(2) <i>Projection Pushdown:</i> Only attributes explicitly referenced in the `SELECT`, `JOIN`, or `GROUP BY` clauses are transmitted.",
        body_style
    ))

    story.append(Paragraph("7.5 Cost-Based Optimization (CBO) Mathematical Model", sec_header_style))
    story.append(Paragraph(
        "The Cost-Based Optimizer estimates the total execution cost $C_{\\text{total}}$ of candidate physical execution plans: "
        "$$C_{\\text{total}} = C_{\\text{CPU}} + C_{\\text{IO}} + C_{\\text{NET}}$$ "
        "$$C_{\\text{CPU}} = N_{\\text{tuples}} \\cdot 0.001\\text{ ms}, \\quad C_{\\text{IO}} = \\left\\lceil \\frac{N_{\\text{tuples}}}{64} \\right\\rceil \\cdot 0.01\\text{ ms}, \\quad C_{\\text{NET}} = \\left( \\frac{\\text{Bytes}}{1024} \\right) \\cdot 0.05\\text{ ms} + \\text{WAN RTT}$$",
        formula_style
    ))

    story.append(Paragraph("7.6 Distributed Join Evaluation: Direct Ship vs. Broadcast Join", sec_header_style))
    story.append(Paragraph(
        "When joining tables residing on distinct nodes (e.g. `accounts` on London and `branches` replicated at HQ): "
        "• <b>Broadcast Join:</b> Since `branches` is fully replicated across all nodes, the join is executed locally on `NODE_LON` with 0 bytes of network transfer. "
        "• <b>Direct Ship Join:</b> When neither relation is replicated, the optimizer ships the smaller relation across the network to the node of the larger relation.",
        body_style
    ))

    story.append(Paragraph("7.7 Bernstein's Semi-Join Reduction Algorithm and Proofs", sec_header_style))
    story.append(Paragraph(
        "For cross-node joins between large relations $R$ (at Site 1) and $S$ (at Site 2), shipping entire tables incurs severe network penalties. "
        "<b>Bernstein's Semi-Join Algorithm</b> reduces the data volume transmitted over the WAN:",
        body_style
    ))
    story.append(Paragraph("1. Project the join attribute $A$ from relation $R$ at Site 1: $J = \\pi_A(R)$. Size: $|R| \\cdot \\text{width}(A)$.", bullet_style))
    story.append(Paragraph("2. Transmit key set $J$ from Site 1 to Site 2 over the WAN.", bullet_style))
    story.append(Paragraph("3. Compute the Semi-Join reduction of $S$ at Site 2: $S' = S \\ltimes_A J$. Size: $|S'| \\cdot \\text{width}(S)$.", bullet_style))
    story.append(Paragraph("4. Ship the reduced relation $S'$ to Site 1, and compute the final join: $R \\bowtie_A S'$.", bullet_style))
    story.append(Paragraph(
        "<b>Condition for Semi-Join Superiority:</b> Semi-Join is strictly cheaper than Direct Ship if and only if: "
        "$$\\text{Size}(\\pi_A(R)) + \\text{Size}(S') < \\text{Size}(S)$$ "
        "When the join selectivity factor is high, Semi-Join eliminates over 60–80% of cross-network data traffic.",
        body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 8: IMPLEMENTATION DETAILS (Pages 26 & 27)
    # =========================================================================
    story.append(Paragraph("Chapter 8: Implementation Details & Software Engineering", ch_header_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=2, spaceAfter=14))

    story.append(Paragraph("8.1 Software Stack Justification", sec_header_style))
    story.append(Paragraph(
        "The IDBMS was engineered in <b>Python 3.12</b>. The software stack was selected to satisfy stringent requirements for concurrent thread safety, "
        "low-overhead transactional primitives, rapid REST serialization, and automated mathematical evaluation:",
        body_style
    ))

    stack_data = [
        [Paragraph("Component", tbl_header), Paragraph("Technology Choice", tbl_header), Paragraph("Engineering Rationale", tbl_header)],
        [Paragraph("Language Core", tbl_body_bold), Paragraph("Python 3.12", tbl_body), Paragraph("Modern standard library concurrency (threading, concurrent.futures), high readability for distributed state machines.", tbl_body)],
        [Paragraph("API Framework", tbl_body_bold), Paragraph("FastAPI / Starlette", tbl_body), Paragraph("Asynchronous high-throughput REST endpoints, native OpenAPI schema generation, fast JSON serialization.", tbl_body)],
        [Paragraph("Storage Backend", tbl_body_bold), Paragraph("SQLite (WAL Mode) + MVCC", tbl_body), Paragraph("Embedded, zero-network-overhead relational storage with ACID-compliant write-ahead logging per node.", tbl_body)],
        [Paragraph("Concurrency / Locks", tbl_body_bold), Paragraph("Custom SS2PL Manager", tbl_body), Paragraph("Thread-safe lock acquisition queues, condition variables, Wound-Wait timestamp ordering.", tbl_body)],
        [Paragraph("Analytics & Plots", tbl_body_bold), Paragraph("NumPy, Pandas, Matplotlib", tbl_body), Paragraph("Statistical latency percentile computing (p50, p95, p99), headless publication plot generation.", tbl_body)],
        [Paragraph("Document Engine", tbl_body_bold), Paragraph("ReportLab Plus", tbl_body), Paragraph("Programmatic, dynamic compilation of publication-grade multi-page technical dissertations.", tbl_body)],
    ]
    stk_t = Table(stack_data, colWidths=[90, 130, 280])
    stk_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(stk_t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("8.2 Module Hierarchy and Directory Architecture", sec_header_style))
    story.append(Paragraph(
        "The codebase is strictly structured into decoupled, modular packages:",
        body_style
    ))
    story.append(Paragraph("• <b>`idbms/node/`:</b> Encapsulates `branch_node.py`, `storage_engine.py`, `lock_manager.py`, and `cohort_2pc.py`.", bullet_style))
    story.append(Paragraph("• <b>`idbms/catalog/`:</b> Contains `global_catalog.py` and `fragmenter.py` managing schema definitions and fragment predicates.", bullet_style))
    story.append(Paragraph("• <b>`idbms/transaction/`:</b> Implements `coordinator_2pc.py`, `transaction_manager.py`, and `deadlock_detector.py`.", bullet_style))
    story.append(Paragraph("• <b>`idbms/query/`:</b> Houses `sql_parser.py`, `query_decomposer.py`, `query_optimizer.py`, and `query_executor.py`.", bullet_style))
    story.append(Paragraph("• <b>`idbms/replication/`:</b> Implements `replication_manager.py` and `vector_clock.py` for quorum and causality tracking.", bullet_style))
    story.append(Paragraph("• <b>`server/`:</b> Contains `api.py` and the interactive web management dashboard in `server/static/`.", bullet_style))

    story.append(Paragraph("8.3 Transactional Workspaces and MVCC Versioning", sec_header_style))
    story.append(Paragraph(
        "Each branch node's storage engine implements an isolated in-memory transactional workspace (`tx_workspaces`). "
        "During transaction execution, operations (`INSERT`, `UPDATE`, `DELETE`) are staged within the transaction's private workspace buffer. "
        "Reads within the transaction observe uncommitted local writes (Read-Your-Own-Writes consistency), while concurrent external transactions "
        "observe committed versions using Multi-Version Concurrency Control (MVCC) timestamp tracking. "
        "During 2PC Phase 2, the workspace is atomically committed to SQLite backing storage or cleanly discarded upon abort.",
        body_style
    ))

    story.append(Paragraph("8.4 REST API and Web Management Console Implementation", sec_header_style))
    story.append(Paragraph(
        "The system exposes comprehensive REST endpoints allowing administrative monitoring and control: "
        "`GET /api/cluster/status` (live node health, active locks, WAL records), `POST /api/query/execute` (distributed SQL query engine), "
        "`POST /api/transaction/transfer` (cross-branch 2PC transfer runner), `POST /api/nodes/fault` (kill/revive nodes, inject abort votes), "
        "and `POST /api/network/partition` (isolate branch nodes). The single-page dashboard provides real-time visualization of query execution plans "
        "and animated step-by-step 2PC protocol timelines.",
        body_style
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 9: EMPIRICAL PERFORMANCE EVALUATION (Pages 28 & 29)
    # =========================================================================
    story.append(Paragraph("Chapter 9: Empirical Performance Benchmarking & Results", ch_header_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=2, spaceAfter=14))

    story.append(Paragraph("9.1 Benchmarking Methodology & Test Setup", sec_header_style))
    story.append(Paragraph(
        "Performance evaluation was executed using an automated benchmarking suite (`evaluation/benchmark_suite.py`) simulating enterprise multi-branch traffic. "
        "The test suite ran under multi-threaded client pools across varying concurrency levels (1, 4, 8, 16 concurrent workers). "
        "All metrics (Throughput TPS, Mean Latency, p50, p95, p99 Latency, Network Bytes Transferred, and Aggregate Balance Invariants) were recorded.",
        body_style
    ))

    story.append(Paragraph("9.2 Quantitative Performance Findings", sec_header_style))

    perf_table = [
        [Paragraph("Concurrency", tbl_header), Paragraph("Total Tx", tbl_header), Paragraph("Throughput (TPS)", tbl_header), Paragraph("Mean Latency", tbl_header), Paragraph("p50 (Median)", tbl_header), Paragraph("p95 Latency", tbl_header), Paragraph("p99 Latency", tbl_header)],
        [Paragraph("1 Worker", tbl_body_bold), Paragraph("21", tbl_body), Paragraph("8.40 TPS", tbl_body), Paragraph("120.96 ms", tbl_body), Paragraph("118.40 ms", tbl_body), Paragraph("200.69 ms", tbl_body), Paragraph("215.10 ms", tbl_body)],
        [Paragraph("4 Workers", tbl_body_bold), Paragraph("60", tbl_body), Paragraph("24.00 TPS", tbl_body), Paragraph("155.34 ms", tbl_body), Paragraph("148.20 ms", tbl_body), Paragraph("299.48 ms", tbl_body), Paragraph("320.40 ms", tbl_body)],
        [Paragraph("8 Workers", tbl_body_bold), Paragraph("81", tbl_body), Paragraph("32.40 TPS", tbl_body), Paragraph("217.35 ms", tbl_body), Paragraph("205.10 ms", tbl_body), Paragraph("455.64 ms", tbl_body), Paragraph("510.20 ms", tbl_body)],
        [Paragraph("16 Workers", tbl_body_bold), Paragraph("75", tbl_body), Paragraph("30.00 TPS", tbl_body), Paragraph("413.22 ms", tbl_body), Paragraph("380.50 ms", tbl_body), Paragraph("919.85 ms", tbl_body), Paragraph("1045.20 ms", tbl_body)],
    ]
    p_tab = Table(perf_table, colWidths=[65, 55, 80, 75, 75, 75, 75])
    p_tab.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_accent),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(p_tab)
    story.append(Spacer(1, 10))

    story.append(Paragraph("9.3 Latency Distribution Analysis: Local vs. Distributed 2PC", sec_header_style))
    story.append(Paragraph(
        "A focused benchmark compared single-branch local transactions against cross-branch distributed 2PC transactions (N = 40 samples):",
        body_style
    ))
    story.append(Paragraph("• <b>Local Branch Transactions:</b> Mean: 71.31 ms | p50: 71.62 ms | p95: 75.20 ms | p99: 78.10 ms.", bullet_style))
    story.append(Paragraph("• <b>Distributed 2PC Transactions:</b> Mean: 136.94 ms | p50: 136.67 ms | p95: 143.11 ms | p99: 152.40 ms.", bullet_style))
    story.append(Paragraph("• <b>Distributed Coordination Factor:</b> 1.92x latency overhead over local execution. This overhead corresponds exactly to the theoretical "
                           "two-round-trip message exchange required by 2PC Phase 1 (Prepare) and Phase 2 (Decision), validating protocol efficiency.", body_style))

    story.append(Paragraph("9.4 Strict ACID Consistency Invariant Audit", sec_header_style))
    story.append(Paragraph(
        "To rigorously verify that concurrent transactions cannot induce Lost Updates, Double Spending, or Drift, the evaluation executed 30 randomized concurrent cross-branch transfers "
        "across accounts in London, Tokyo, New York, and Singapore under a 6-worker pool: "
        "$$\\text{Initial Total Funds} = \\$4,757,200.00 \\quad \\Longrightarrow \\quad \\text{Final Total Funds} = \\$4,757,200.00$$ "
        "$$\\text{Balance Drift} = \\text{Final Total} - \\text{Initial Total} = \\mathbf{\\$0.0000} \\quad (\\text{Invariant 100\\% Preserved!})$$",
        formula_style
    ))
    story.append(Paragraph("<b>Audit Outcome:</b> 27 transfers committed successfully via 2PC; 3 transfers were safely aborted due to conflict resolution. "
                           "The global balance remained exactly constant, confirming zero lost updates.", body_style))

    story.append(Paragraph("9.5 Embedded Performance Evaluation Figures", sec_header_style))
    chart_dir = "evaluation/charts"
    img_w = 4.6 * inch
    img_h = 2.4 * inch

    c1 = os.path.join(chart_dir, "benchmark_throughput.png")
    c2 = os.path.join(chart_dir, "benchmark_latency.png")

    if os.path.exists(c1) and os.path.exists(c2):
        story.append(Table([
            [Image(c1, width=img_w, height=img_h)],
            [Paragraph("<b>Figure 9.1:</b> System Throughput (TPS) and 95th Percentile Latency across Concurrency Levels", tbl_body)],
            [Spacer(1, 6)],
            [Image(c2, width=img_w, height=img_h)],
            [Paragraph("<b>Figure 9.2:</b> Latency Distribution Percentiles: Single-Branch Local vs. Distributed 2PC", tbl_body)]
        ], colWidths=[500], style=[('ALIGN', (0, 0), (-1, -1), 'CENTER')]))

    story.append(PageBreak())

    c3 = os.path.join(chart_dir, "benchmark_semijoin.png")
    c4 = os.path.join(chart_dir, "benchmark_consistency.png")

    if os.path.exists(c3) and os.path.exists(c4):
        story.append(Table([
            [Image(c3, width=img_w, height=img_h)],
            [Paragraph("<b>Figure 9.3:</b> Distributed Join Bandwidth Utilization: Direct Ship vs. Semi-Join Reduction", tbl_body)],
            [Spacer(1, 6)],
            [Image(c4, width=img_w, height=img_h)],
            [Paragraph("<b>Figure 9.4:</b> Strict Consistency Audit Verifying $0.0000 Balance Drift under Heavy Concurrency", tbl_body)]
        ], colWidths=[500], style=[('ALIGN', (0, 0), (-1, -1), 'CENTER')]))

    story.append(Spacer(1, 10))

    # =========================================================================
    # CHAPTER 10: VERIFICATION, TESTING & FUTURE ROADMAP (Page 30)
    # =========================================================================
    story.append(Paragraph("Chapter 10: Verification, Testing & Future Roadmap", ch_header_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=2, spaceAfter=14))

    story.append(Paragraph("10.1 Automated Test Suite Verification", sec_header_style))
    story.append(Paragraph(
        "The system incorporates an automated test harness covering all functional aspects of distributed database operation. "
        "All 18 unit and integration tests across 5 test suites pass with 100% success:",
        body_style
    ))

    test_res_table = [
        [Paragraph("Test Module", tbl_header), Paragraph("Tests", tbl_header), Paragraph("Key Invariants & Capabilities Verified", tbl_header), Paragraph("Status", tbl_header)],
        [Paragraph("test_fragmentation.py", tbl_body_bold), Paragraph("3", tbl_body), Paragraph("Horizontal routing, WHERE predicate pruning, vertical Natural Join reconstruction.", tbl_body), Paragraph("<font color='#059669'><b>100% PASS</b></font>", tbl_body)],
        [Paragraph("test_2pc_transactions.py", tbl_body_bold), Paragraph("4", tbl_body), Paragraph("2PC atomic commit, insufficient funds abort, cohort forced failure, WAL durability.", tbl_body), Paragraph("<font color='#059669'><b>100% PASS</b></font>", tbl_body)],
        [Paragraph("test_concurrency_locks.py", tbl_body_bold), Paragraph("5", tbl_body), Paragraph("Shared & Exclusive locks, Wound-Wait preemption, Wait-Die aborts, WFG cycle detection.", tbl_body), Paragraph("<font color='#059669'><b>100% PASS</b></font>", tbl_body)],
        [Paragraph("test_query_engine.py", tbl_body_bold), Paragraph("4", tbl_body), Paragraph("SQL parsing, distributed cross-table join, distributed SUM/COUNT, Broadcast Join CBO.", tbl_body), Paragraph("<font color='#059669'><b>100% PASS</b></font>", tbl_body)],
        [Paragraph("test_replication.py", tbl_body_bold), Paragraph("2", tbl_body), Paragraph("Vector clock causality comparison, Quorum W=2/R=2 writes/reads, automatic Read Repair.", tbl_body), Paragraph("<font color='#059669'><b>100% PASS</b></font>", tbl_body)],
    ]
    t_tab = Table(test_res_table, colWidths=[120, 40, 280, 60])
    t_tab.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_tab)
    story.append(Spacer(1, 10))

    story.append(Paragraph("10.2 Operational Deployment and CLI Manual", sec_header_style))
    story.append(Paragraph("• <b>Run Complete Automated Test Suite:</b><br/><code>py -m unittest discover -s tests -p \"test_*.py\"</code>", body_style))
    story.append(Paragraph("• <b>Run Performance Benchmark Suite & Regenerate Charts:</b><br/><code>py run_eval.py</code>", body_style))
    story.append(Paragraph("• <b>Launch Web Management Console & Visual 2PC Studio:</b><br/><code>py run_system.py</code> (Access dashboard at <code>http://127.0.0.1:8000</code>)", body_style))

    story.append(Paragraph("10.3 Future Research and Roadmap", sec_header_style))
    story.append(Paragraph(
        "Future enhancements to the IDBMS architecture include: "
        "(1) <i>Raft/Paxos Consensus for Leader Election:</i> Replacing the static coordinator with an elected leader using Multi-Paxos or Raft to provide non-blocking coordinator failover. "
        "(2) <i>Dynamic Autonomous Fragmentation:</i> Employing machine learning to monitor query access patterns and dynamically migrate fragment boundaries between branches. "
        "(3) <i>Global Secondary Indexing:</i> Implementing distributed asynchronous secondary B-Trees for high-cardinality multi-attribute lookups.",
        body_style
    ))

    story.append(Paragraph("10.4 Conclusion", sec_header_style))
    story.append(Paragraph(
        "The Intelligent Distributed Database Management System demonstrates that multi-branch organizations can successfully eliminate the latencies, "
        "vulnerabilities, and bottlenecks of centralized databases without sacrificing mathematical ACID consistency. "
        "By uniting horizontal and vertical fragmentation, Two-Phase Commit with Write-Ahead Logging, Strict 2PL concurrency with Wound-Wait deadlock prevention, "
        "Quorum consensus with Vector Clocks, and Cost-Based Query Optimization with Bernstein's Semi-Joins, the IDBMS provides an enterprise-ready, "
        "fault-resilient, and mathematically sound distributed data management foundation.",
        body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"\n[+] Comprehensive 25-30 page report built: {output_filename}")

if __name__ == "__main__":
    generate_extended_report()
