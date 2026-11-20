"""
Vector Clock implementation for distributed causality tracking and conflict detection.
"""

from typing import Dict, Any

class VectorClock:
    """
    Vector Clock maintaining per-node sequence counters for causal consistency.
    """
    def __init__(self, clock_dict: Dict[str, int] = None):
        self.clock: Dict[str, int] = clock_dict.copy() if clock_dict else {}

    def increment(self, node_id: str):
        self.clock[node_id] = self.clock.get(node_id, 0) + 1

    def merge(self, other: "VectorClock") -> "VectorClock":
        merged = {}
        all_keys = set(self.clock.keys()).union(set(other.clock.keys()))
        for k in all_keys:
            merged[k] = max(self.clock.get(k, 0), other.clock.get(k, 0))
        return VectorClock(merged)

    def compare(self, other: "VectorClock") -> str:
        """
        Compares this clock with another.
        Returns: 'EQUAL', 'DOMINATES' (greater), 'DOMINATED' (lesser), or 'CONCURRENT' (conflict).
        """
        all_keys = set(self.clock.keys()).union(set(other.clock.keys()))
        greater = False
        lesser = False

        for k in all_keys:
            v1 = self.clock.get(k, 0)
            v2 = other.clock.get(k, 0)
            if v1 > v2:
                greater = True
            elif v1 < v2:
                lesser = True

        if greater and not lesser:
            return "DOMINATES"
        elif lesser and not greater:
            return "DOMINATED"
        elif not greater and not lesser:
            return "EQUAL"
        else:
            return "CONCURRENT"

    def to_dict(self) -> Dict[str, int]:
        return self.clock.copy()
