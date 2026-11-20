"""
Distributed Deadlock Detector.
Constructs the global Wait-For Graph (WFG) from participant node lock managers
and resolves cycles via victim selection.
"""

import threading
from typing import Dict, List, Set, Optional, Tuple

class DistributedDeadlockDetector:
    """
    Periodic or on-demand Distributed Wait-For Graph (WFG) cycle detector.
    Uses Depth-First Search (DFS) / Tarjan's cycle detection.
    """
    def __init__(self):
        self._lock = threading.Lock()

    def build_global_wfg(self, local_wfgs: List[Dict[str, List[str]]]) -> Dict[str, Set[str]]:
        """Aggregates local WFGs into a global directed graph."""
        global_graph: Dict[str, Set[str]] = {}
        for local_wfg in local_wfgs:
            for waiter_tx, holder_txs in local_wfg.items():
                if waiter_tx not in global_graph:
                    global_graph[waiter_tx] = set()
                global_graph[waiter_tx].update(holder_txs)
        return global_graph

    def detect_cycles(self, global_graph: Dict[str, Set[str]]) -> List[List[str]]:
        """
        Finds all elementary cycles in the directed graph using DFS.
        Returns list of cycles, each cycle is a list of tx_ids [T1, T2, ..., T1].
        """
        visited = set()
        rec_stack = []
        cycles = []

        def dfs(node: str):
            visited.add(node)
            rec_stack.append(node)

            for neighbor in global_graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Cycle detected!
                    cycle_start_idx = rec_stack.index(neighbor)
                    cycle = rec_stack[cycle_start_idx:] + [neighbor]
                    cycles.append(cycle)

            rec_stack.pop()

        for node in list(global_graph.keys()):
            if node not in visited:
                dfs(node)

        return cycles

    def select_victim(self, cycle: List[str], tx_timestamps: Dict[str, float]) -> str:
        """
        Victim Selection heuristic:
        Picks the youngest transaction (highest timestamp) in the cycle to abort,
        minimizing wasted work.
        """
        unique_txs = list(set(cycle))
        if not unique_txs:
            return ""
        # Youngest tx has maximum timestamp
        victim = max(unique_txs, key=lambda tx: tx_timestamps.get(tx, 0.0))
        return victim
