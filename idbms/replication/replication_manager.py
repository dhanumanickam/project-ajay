"""
Replication Manager supporting Full Replication, Quorum consensus (R + W > N),
Vector Clock versioning, and asynchronous/synchronous Read Repair.
"""

import time
import threading
from typing import Dict, Any, List, Optional, Tuple
from idbms.common.models import ReplicationStrategy, DataOperation, OperationType
from idbms.catalog.global_catalog import GlobalCatalog
from idbms.network.rpc_client import RPCClient
from idbms.replication.vector_clock import VectorClock

class ReplicationManager:
    """
    Manages replica consistency across multi-branch nodes.
    Guarantees strict or eventual consistency with Quorum (W + R > N) and Read Repair.
    """
    def __init__(self, coordinator_id: str, catalog: GlobalCatalog, rpc_client: RPCClient):
        self.coordinator_id = coordinator_id
        self.catalog = catalog
        self.rpc_client = rpc_client
        self._lock = threading.RLock()
        # Track vector clocks per table:pk
        self.vector_clocks: Dict[str, VectorClock] = {}

    def get_clock(self, table: str, pk: str) -> VectorClock:
        key = f"{table.lower()}:{str(pk)}"
        with self._lock:
            if key not in self.vector_clocks:
                self.vector_clocks[key] = VectorClock()
            return self.vector_clocks[key]

    def write_quorum(self, table: str, pk_value: Any, record_data: Dict[str, Any], n_nodes: List[str], w: int) -> Dict[str, Any]:
        """
        Executes a Quorum write across replica nodes.
        Requires at least W successful acknowledgments out of N nodes.
        """
        key = f"{table.lower()}:{str(pk_value)}"
        with self._lock:
            clock = self.get_clock(table, str(pk_value))
            clock.increment(self.coordinator_id)
            updated_clock_dict = clock.to_dict()

        data_with_clock = record_data.copy()
        data_with_clock["_vclock"] = updated_clock_dict

        ack_count = 0
        ack_nodes = []
        errors = []

        op = DataOperation(
            op_type=OperationType.INSERT if "_version" not in record_data else OperationType.UPDATE,
            table=table,
            key_value=pk_value,
            data=data_with_clock
        )

        for nid in n_nodes:
            try:
                rep_tx_id = f"rep_{nid}_{int(time.time()*1000)}"
                # Use a lightweight direct operation or 2PC
                res = self.rpc_client.call_execute_op(
                    from_node=self.coordinator_id,
                    to_node=nid,
                    tx_id=rep_tx_id,
                    op=op,
                    tx_timestamp=time.time()
                )
                # Commit immediately for replica record
                self.rpc_client.call_commit(self.coordinator_id, nid, rep_tx_id)
                ack_count += 1
                ack_nodes.append(nid)
            except Exception as e:
                errors.append(f"{nid}: {str(e)}")

        if ack_count < w:
            raise ConnectionError(f"Quorum Write Failed: Required W={w}, only received {ack_count} ACKs. Errors: {errors}")

        return {
            "status": "SUCCESS",
            "quorum_w": w,
            "ack_count": ack_count,
            "ack_nodes": ack_nodes,
            "vclock": updated_clock_dict
        }

    def read_quorum(self, table: str, pk_value: Any, n_nodes: List[str], r: int) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """
        Executes a Quorum read across replica nodes.
        Collects from R replicas, resolves to newest vector clock, and triggers Read Repair on stale nodes.
        """
        responses = []
        errors = []

        for nid in n_nodes:
            try:
                rec = self.rpc_client.call_read(self.coordinator_id, nid, table, pk_value)
                if rec:
                    responses.append((nid, rec))
            except Exception as e:
                errors.append(f"{nid}: {str(e)}")

            if len(responses) >= r:
                break

        if len(responses) < r:
            raise ConnectionError(f"Quorum Read Failed: Required R={r}, only received {len(responses)} responses. Errors: {errors}")

        # Find newest version by comparing Vector Clocks
        latest_rec = None
        latest_clock = None
        latest_node = None
        stale_nodes = []

        for nid, rec in responses:
            rec_clock = VectorClock(rec.get("_vclock", {}))
            if latest_clock is None:
                latest_clock = rec_clock
                latest_rec = rec
                latest_node = nid
            else:
                comp = rec_clock.compare(latest_clock)
                if comp == "DOMINATES":
                    stale_nodes.append(latest_node)
                    latest_clock = rec_clock
                    latest_rec = rec
                    latest_node = nid
                elif comp == "DOMINATED":
                    stale_nodes.append(nid)

        # Trigger Read Repair on stale nodes asynchronously
        read_repair_performed = []
        if stale_nodes and latest_rec:
            for stale_node in stale_nodes:
                try:
                    repair_op = DataOperation(
                        op_type=OperationType.UPDATE,
                        table=table,
                        key_value=pk_value,
                        data=latest_rec
                    )
                    self.rpc_client.call_execute_op(self.coordinator_id, stale_node, "repair_tx", repair_op, time.time())
                    self.rpc_client.call_commit(self.coordinator_id, stale_node, "repair_tx")
                    read_repair_performed.append(stale_node)
                except Exception:
                    pass

        return latest_rec, {
            "quorum_r": r,
            "received_count": len(responses),
            "stale_nodes_found": stale_nodes,
            "read_repair_performed": read_repair_performed,
            "vclock": latest_clock.to_dict() if latest_clock else {}
        }
