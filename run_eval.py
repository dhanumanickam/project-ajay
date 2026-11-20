"""
Standalone Evaluation Runner.
Executes the comprehensive performance benchmark suite and outputs performance metrics and plots.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from evaluation.generate_charts import generate_all_evaluation_charts

if __name__ == "__main__":
    print("=" * 80)
    print("  RUNNING IDBMS PERFORMANCE EVALUATION SUITE")
    print("=" * 80)
    metrics = generate_all_evaluation_charts()
    print("=" * 80)
    print("  EVALUATION SUMMARY COMPLETE")
    print("=" * 80)
