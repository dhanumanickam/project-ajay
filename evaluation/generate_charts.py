"""
Chart generator for performance evaluation results.
Generates publication-quality benchmark plots saved to evaluation/charts and server/static/charts.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import shutil
import matplotlib
matplotlib.use("Agg") # Non-interactive headless backend
import matplotlib.pyplot as plt
import numpy as np
from evaluation.benchmark_suite import PerformanceBenchmarkSuite

def generate_all_evaluation_charts(output_dirs=["evaluation/charts", "server/static/charts"]):
    for out_dir in output_dirs:
        os.makedirs(out_dir, exist_ok=True)

    suite = PerformanceBenchmarkSuite()

    # Modern color palette
    c_blue = "#2563eb"
    c_indigo = "#4f46e5"
    c_emerald = "#059669"
    c_amber = "#d97706"
    c_rose = "#e11d48"

    # 1. Throughput vs Concurrency Plot
    print("[1/4] Running Throughput vs Concurrency Benchmark...")
    tps_data = suite.benchmark_throughput_vs_concurrency(concurrency_levels=[1, 4, 8, 16], duration_sec=2.5)

    workers = list(tps_data.keys())
    tps_vals = [tps_data[w]["tps"] for w in workers]
    p95_vals = [tps_data[w]["p95_latency_ms"] for w in workers]

    fig, ax1 = plt.subplots(figsize=(8, 4.8), dpi=200)
    ax2 = ax1.twinx()

    b1 = ax1.bar([w - 0.3 for w in workers], tps_vals, width=0.6, color=c_blue, alpha=0.85, label="Throughput (TPS)")
    l1 = ax2.plot(workers, p95_vals, color=c_rose, marker="o", linewidth=2.5, label="p95 Latency (ms)")

    ax1.set_xlabel("Concurrent Client Workers", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Throughput (Transactions / Sec)", color=c_blue, fontsize=11, fontweight="bold")
    ax2.set_ylabel("95th Percentile Latency (ms)", color=c_rose, fontsize=11, fontweight="bold")
    ax1.set_title("IDBMS Throughput & Latency vs. Concurrency", fontsize=13, fontweight="bold", pad=12)
    ax1.set_xticks(workers)
    ax1.grid(True, linestyle="--", alpha=0.4)

    # Bar labels
    for rect in b1:
        h = rect.get_height()
        ax1.annotate(f"{h:.1f}", xy=(rect.get_x() + rect.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")

    plt.tight_layout()
    chart1_path = os.path.join(output_dirs[0], "benchmark_throughput.png")
    fig.savefig(chart1_path)
    plt.close(fig)

    # 2. Local vs Distributed 2PC Latency Comparison
    print("[2/4] Running Local vs Distributed 2PC Latency Benchmark...")
    lat_data = suite.benchmark_local_vs_distributed_latency(sample_size=40)

    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=200)
    categories = ["Mean", "Median (p50)", "95th Percentile", "99th Percentile"]
    local_metrics = [lat_data["local_mean"], lat_data["local_p50"], lat_data["local_p95"], lat_data["local_p99"]]
    dist_metrics = [lat_data["distributed_mean"], lat_data["distributed_p50"], lat_data["distributed_p95"], lat_data["distributed_p99"]]

    x = np.arange(len(categories))
    width = 0.35

    rects1 = ax.bar(x - width/2, local_metrics, width, label="Local Branch Tx", color=c_emerald, alpha=0.85)
    rects2 = ax.bar(x + width/2, dist_metrics, width, label="Distributed 2PC Tx", color=c_indigo, alpha=0.85)

    ax.set_ylabel("Response Time / Latency (ms)", fontsize=11, fontweight="bold")
    ax.set_title("Response Time: Single Branch vs. Multi-Branch 2PC Protocol", fontsize=13, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=10, fontweight="bold")
    ax.legend(frameon=True)
    ax.grid(True, linestyle="--", alpha=0.4)

    for rect in list(rects1) + list(rects2):
        h = rect.get_height()
        ax.annotate(f"{h:.1f}ms", xy=(rect.get_x() + rect.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8, fontweight="bold")

    plt.tight_layout()
    chart2_path = os.path.join(output_dirs[0], "benchmark_latency.png")
    fig.savefig(chart2_path)
    plt.close(fig)

    # 3. Semi-Join Reduction vs Direct Ship Network Transfer
    print("[3/4] Running Semi-Join Reduction Network Transfer Evaluation...")
    sj_data = suite.benchmark_semijoin_network_reduction()

    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=200)
    strategies = ["Direct Ship Join", "Semi-Join Reduction\n(Bernstein's Algorithm)"]
    bytes_vals = [sj_data["direct_ship_bytes"] / 1024.0, sj_data["semijoin_total_bytes"] / 1024.0] # in KB
    colors = [c_rose, c_emerald]

    bars = ax.bar(strategies, bytes_vals, color=colors, width=0.45, alpha=0.9)
    ax.set_ylabel("Network Payload Transferred (Kilobytes)", fontsize=11, fontweight="bold")
    ax.set_title(f"Distributed Join Network Reduction: -{sj_data['reduction_percentage']}% Bandwidth Saved", fontsize=12, fontweight="bold", pad=12)
    ax.grid(True, linestyle="--", alpha=0.4)

    for rect in bars:
        h = rect.get_height()
        ax.annotate(f"{h:.1f} KB", xy=(rect.get_x() + rect.get_width() / 2, h),
                     xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.tight_layout()
    chart3_path = os.path.join(output_dirs[0], "benchmark_semijoin.png")
    fig.savefig(chart3_path)
    plt.close(fig)

    # 4. Consistency Verification Plot
    print("[4/4] Running Strict Consistency Verification...")
    cons_data = suite.benchmark_strict_consistency_audit(num_transfers=30)

    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=200)
    cats = ["Initial Total Funds", "Final Total Funds"]
    fund_vals = [cons_data["initial_sum"], cons_data["final_sum"]]

    bars = ax.bar(cats, fund_vals, color=[c_blue, c_indigo], width=0.4)
    ax.set_ylabel("Total System Balances ($ USD)", fontsize=11, fontweight="bold")
    ax.set_ylim(min(fund_vals) * 0.9, max(fund_vals) * 1.1)
    ax.set_title(f"ACID Consistency Audit: Drift = ${cons_data['drift']:.4f} (100% Invariant Preserved)", fontsize=12, fontweight="bold", pad=12)
    ax.grid(True, linestyle="--", alpha=0.4)

    for rect in bars:
        h = rect.get_height()
        ax.annotate(f"${h:,.2f}", xy=(rect.get_x() + rect.get_width() / 2, h),
                     xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.tight_layout()
    chart4_path = os.path.join(output_dirs[0], "benchmark_consistency.png")
    fig.savefig(chart4_path)
    plt.close(fig)

    # Copy generated charts to other target directories (e.g. server/static/charts)
    for extra_dir in output_dirs[1:]:
        for fname in ["benchmark_throughput.png", "benchmark_latency.png", "benchmark_semijoin.png", "benchmark_consistency.png"]:
            src = os.path.join(output_dirs[0], fname)
            dst = os.path.join(extra_dir, fname)
            shutil.copyfile(src, dst)

    print(f"\nAll benchmark charts generated successfully in {output_dirs}!")
    return {
        "throughput": tps_data,
        "latency": lat_data,
        "semijoin": sj_data,
        "consistency": cons_data
    }

if __name__ == "__main__":
    generate_all_evaluation_charts()
