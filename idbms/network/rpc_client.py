"""
RPC Client for inter-node communication, supporting in-process simulation
and network simulation hooks.
"""

import json
from typing import Dict, Any, List, Optional
from idbms.network.network_simulator import NetworkSimulator
from idbms.common.models import DataOperation

class RPCClient:
    """
    Handles RPC dispatch between coordinator and branch nodes.
    Supports in-memory routing with network latency and partition simulation.
    """
    def __init__(self, net_sim: NetworkSimulator):
        self.net_sim = net_sim
        self.node_registry: Dict[str, Any] = {} # node_id -> BranchNode instance

    def register_node_instance(self, node_id: str, node_instance: Any):
        self.node_registry[node_id] = node_instance

    def call_read(self, from_node: str, to_node: str, table: str, pk_value: Any, tx_id: Optional[str] = None, read_timestamp: Optional[float] = None) -> Optional[Dict[str, Any]]:
        self.net_sim.simulate_transit(from_node, to_node, payload_size_bytes=64)
        if to_node not in self.node_registry:
            raise ConnectionError(f"Node {to_node} is not registered in RPC client.")
        target = self.node_registry[to_node]
        res = target.handle_read(table, pk_value, tx_id=tx_id, read_timestamp=read_timestamp)
        payload_bytes = len(json.dumps(res)) if res else 32
        self.net_sim.simulate_transit(to_node, from_node, payload_size_bytes=payload_bytes)
        return res

    def call_scan(self, from_node: str, to_node: str, table: str, tx_id: Optional[str] = None) -> List[Dict[str, Any]]:
        self.net_sim.simulate_transit(from_node, to_node, payload_size_bytes=64)
        if to_node not in self.node_registry:
            raise ConnectionError(f"Node {to_node} is not registered in RPC client.")
        target = self.node_registry[to_node]
        rows = target.handle_scan(table, tx_id=tx_id)
        payload_bytes = len(json.dumps(rows)) if rows else 32
        self.net_sim.simulate_transit(to_node, from_node, payload_size_bytes=payload_bytes)
        return rows

    def call_execute_op(self, from_node: str, to_node: str, tx_id: str, op: DataOperation, tx_timestamp: float) -> Dict[str, Any]:
        req_bytes = len(json.dumps(op.model_dump()))
        self.net_sim.simulate_transit(from_node, to_node, payload_size_bytes=req_bytes)
        if to_node not in self.node_registry:
            raise ConnectionError(f"Node {to_node} is not registered in RPC client.")
        target = self.node_registry[to_node]
        res = target.execute_tx_operation(tx_id, op, tx_timestamp)
        self.net_sim.simulate_transit(to_node, from_node, payload_size_bytes=64)
        return res

    def call_prepare(self, from_node: str, to_node: str, tx_id: str) -> Dict[str, Any]:
        self.net_sim.simulate_transit(from_node, to_node, payload_size_bytes=48)
        if to_node not in self.node_registry:
            raise ConnectionError(f"Node {to_node} is not registered in RPC client.")
        target = self.node_registry[to_node]
        res = target.prepare(tx_id)
        self.net_sim.simulate_transit(to_node, from_node, payload_size_bytes=48)
        return res

    def call_commit(self, from_node: str, to_node: str, tx_id: str) -> Dict[str, Any]:
        self.net_sim.simulate_transit(from_node, to_node, payload_size_bytes=48)
        if to_node not in self.node_registry:
            raise ConnectionError(f"Node {to_node} is not registered in RPC client.")
        target = self.node_registry[to_node]
        res = target.commit(tx_id)
        self.net_sim.simulate_transit(to_node, from_node, payload_size_bytes=48)
        return res

    def call_abort(self, from_node: str, to_node: str, tx_id: str, reason: str = "") -> Dict[str, Any]:
        self.net_sim.simulate_transit(from_node, to_node, payload_size_bytes=48)
        if to_node not in self.node_registry:
            raise ConnectionError(f"Node {to_node} is not registered in RPC client.")
        target = self.node_registry[to_node]
        res = target.abort(tx_id, reason)
        self.net_sim.simulate_transit(to_node, from_node, payload_size_bytes=48)
        return res
