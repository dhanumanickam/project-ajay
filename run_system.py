"""
IDBMS Application Launcher.
Bootstraps the cluster and launches the FastAPI Web Management Console on http://127.0.0.1:8000
"""

import uvicorn
import webbrowser
import time
import threading

def open_browser():
    time.sleep(1.5)
    print("\n[+] Opening IDBMS Web Management Console at http://127.0.0.1:8000 ...")
    try:
        webbrowser.open("http://127.0.0.1:8000")
    except Exception:
        pass

if __name__ == "__main__":
    print("=" * 80)
    print("  INTELLIGENT DISTRIBUTED DATABASE MANAGEMENT SYSTEM (IDBMS) v2.0")
    print("  Enterprise Multi-Branch Cluster Orchestrator")
    print("=" * 80)
    print("  - Topology: HQ (New York), London, Tokyo, Singapore")
    print("  - Concurrency: Strict 2PL (SS2PL) + Wound-Wait / Wait-Die")
    print("  - Atomic Transactions: Distributed Two-Phase Commit (2PC) + WAL")
    print("  - Query Engine: Cost-Based Optimizer, Fragment Pruning, Semi-Joins")
    print("  - Replication: Full & Quorum (R + W > N) with Vector Clocks")
    print("=" * 80)

    # Launch browser thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Start FastAPI server
    uvicorn.run("server.api:app", host="127.0.0.1", port=8000, log_level="info")
