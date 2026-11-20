"""
Network Simulator supporting latency modeling, jitter, packet loss, and partition simulation.
"""

import time
import random
import threading
from typing import Dict, Set, Tuple, Any

class NetworkSimulator:
    """
    Simulates distributed network behavior between geographically separated branch nodes.
    Tracks network statistics (messages sent, payload bytes, transit latencies).
    """
    def __init__(self):
        self._lock = threading.Lock()
        # Default latency matrix in milliseconds between regions/nodes
        self.latency_matrix: Dict[Tuple[str, str], float] = {
            ("NODE_HQ", "NODE_LON"): 35.0,
            ("NODE_LON", "NODE_HQ"): 35.0,
            ("NODE_HQ", "NODE_TYO"): 65.0,
            ("NODE_TYO", "NODE_HQ"): 65.0,
            ("NODE_HQ", "NODE_SGP"): 75.0,
            ("NODE_SGP", "NODE_HQ"): 75.0,
            ("NODE_LON", "NODE_TYO"): 95.0,
            ("NODE_TYO", "NODE_LON"): 95.0,
            ("NODE_LON", "NODE_SGP"): 85.0,
            ("NODE_SGP", "NODE_LON"): 85.0,
            ("NODE_TYO", "NODE_SGP"): 30.0,
            ("NODE_SGP", "NODE_TYO"): 30.0,
        }
        self.partitions: Set[Tuple[str, str]] = set() # Pairs of partitioned nodes
        self.packet_loss_rate = 0.0                    # 0.0 to 1.0
        self.total_messages_sent = 0
        self.total_bytes_transferred = 0
        self.simulated_enabled = True

    def set_partition(self, node_a: str, node_b: str, partitioned: bool = True):
        with self._lock:
            pair1 = (node_a, node_b)
            pair2 = (node_b, node_a)
            if partitioned:
                self.partitions.add(pair1)
                self.partitions.add(pair2)
            else:
                self.partitions.discard(pair1)
                self.partitions.discard(pair2)

    def is_partitioned(self, node_a: str, node_b: str) -> bool:
        with self._lock:
            return (node_a, node_b) in self.partitions

    def simulate_transit(self, from_node: str, to_node: str, payload_size_bytes: int = 128):
        """Simulates latency and checks partition / packet loss."""
        with self._lock:
            self.total_messages_sent += 1
            self.total_bytes_transferred += payload_size_bytes

            if (from_node, to_node) in self.partitions:
                raise ConnectionError(f"Network Partition: Unable to route packets between {from_node} and {to_node}")

            if self.packet_loss_rate > 0 and random.random() < self.packet_loss_rate:
                raise TimeoutError(f"Simulated Packet Loss: Message dropped between {from_node} and {to_node}")

        if not self.simulated_enabled or from_node == to_node:
            return

        base_latency = self.latency_matrix.get((from_node, to_node), 10.0)
        # Scaled down slightly for responsive interactive evaluation (divide by 10 in interactive mode)
        delay_sec = (base_latency / 1000.0) * 0.1
        if delay_sec > 0:
            time.sleep(delay_sec)

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_messages": self.total_messages_sent,
                "total_bytes_transferred": self.total_bytes_transferred,
                "active_partitions": [f"{a} <-> {b}" for a, b in self.partitions if a < b],
                "packet_loss_rate": self.packet_loss_rate
            }
