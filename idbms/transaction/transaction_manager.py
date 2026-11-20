"""
Distributed Transaction Manager (DTM).
Coordinates multi-node transactions, enforces ACID semantics, routes operations,
and interfaces with the 2PC Coordinator and Deadlock Detector.
"""

import uuid
import time
import threading
from typing import Dict, Any, List, Optional, Set
from idbms.common.models import (
    IsolationLevel, TransactionStatus, OperationType, DataOperation
)
from idbms.common.exceptions import TransactionException, TwoPhaseCommitAbortException
from idbms.catalog.global_catalog import GlobalCatalog
from idbms.network.rpc_client import RPCClient
from idbms.transaction.coordinator_2pc import Coordinator2PC
from idbms.transaction.deadlock_detector import DistributedDeadlockDetector

class DistributedTransaction:
    def __init__(self, tx_id: str, timestamp: float, isolation_level: IsolationLevel):
        self.tx_id = tx_id
        self.timestamp = timestamp
        self.isolation_level = isolation_level
        self.status = TransactionStatus.ACTIVE
        self.participants: Set[str] = set()
        self.operations: List[DataOperation] = []
        self.created_at = time.time()
        self.finished_at: Optional[float] = None
        self.trace: List[Dict[str, Any]] = []

class DistributedTransactionManager:
    """
    Enterprise Distributed Transaction Manager.
    Coordinates distributed operations across multi-branch nodes.
    """
    def __init__(self, coordinator_node_id: str, catalog: GlobalCatalog, rpc_client: RPCClient, coordinator_2pc: Coordinator2PC):
        self.coordinator_node_id = coordinator_node_id
        self.catalog = catalog
        self.rpc_client = rpc_client
        self.coordinator_2pc = coordinator_2pc
        self.deadlock_detector = DistributedDeadlockDetector()
        self._lock = threading.RLock()
        self.active_transactions: Dict[str, DistributedTransaction] = {}
        self.completed_transactions: Dict[str, DistributedTransaction] = {}

    def begin_transaction(self, isolation_level: IsolationLevel = IsolationLevel.SERIALIZABLE) -> str:
        with self._lock:
            tx_id = f"tx_{uuid.uuid4().hex[:8]}"
            tx = DistributedTransaction(
                tx_id=tx_id,
                timestamp=time.time(),
                isolation_level=isolation_level
            )
            self.active_transactions[tx_id] = tx
            return tx_id

    def execute_operation(self, tx_id: str, op: DataOperation) -> Dict[str, Any]:
        """Routes a single data operation to its appropriate branch node(s) based on catalog fragmentation."""
        with self._lock:
            if tx_id not in self.active_transactions:
                raise TransactionException(f"Transaction {tx_id} is not active or has expired.")
            tx = self.active_transactions[tx_id]

        # Determine target node(s)
        target_slices = []
        if op.op_type == OperationType.INSERT:
            target_slices = self.catalog.get_target_nodes_for_insert(op.table, op.data or {})
        elif op.op_type in (OperationType.UPDATE, OperationType.DELETE, OperationType.READ):
            if op.target_node:
                target_slices = [(op.target_node, "direct", op.data)]
            else:
                # Find which node hosts this record by primary key or scan
                found_node = self._locate_record_node(op.table, op.key_value)
                target_node = found_node or "NODE_HQ"
                target_slices = [(target_node, "direct", op.data)]

        results = []
        for node_id, frag_id, slice_data in target_slices:
            with self._lock:
                tx.participants.add(node_id)
            node_op = DataOperation(
                op_type=op.op_type,
                table=op.table,
                key_field=op.key_field,
                key_value=op.key_value,
                data=slice_data,
                target_node=node_id
            )
            with self._lock:
                tx.operations.append(node_op)

            res = self.rpc_client.call_execute_op(
                from_node=self.coordinator_node_id,
                to_node=node_id,
                tx_id=tx_id,
                op=node_op,
                tx_timestamp=tx.timestamp
            )
            results.append({"node_id": node_id, "result": res})

        return {"status": "SUCCESS", "targets": results}

    def _locate_record_node(self, table: str, pk_value: Any) -> Optional[str]:
        """Locates which branch node hosts the record with given primary key."""
        table = table.lower()
        # Probe nodes that host fragments of this table
        nodes_to_check = [n.node_id for n in self.catalog.nodes.values() if n.status == "ONLINE"]
        for nid in nodes_to_check:
            try:
                rec = self.rpc_client.call_read(self.coordinator_node_id, nid, table, pk_value)
                if rec is not None:
                    return nid
            except Exception:
                continue
        return None

    def commit_transaction(self, tx_id: str) -> Dict[str, Any]:
        """Commits the distributed transaction using Two-Phase Commit."""
        with self._lock:
            if tx_id not in self.active_transactions:
                raise TransactionException(f"Transaction {tx_id} is not active.")
            tx = self.active_transactions[tx_id]
            tx.status = TransactionStatus.PREPARING

        participants = tx.participants.copy()
        try:
            success, msg, trace = self.coordinator_2pc.execute_2pc(tx_id, participants)
            with self._lock:
                tx.status = TransactionStatus.COMMITTED
                tx.finished_at = time.time()
                tx.trace = trace
                self.completed_transactions[tx_id] = tx
                del self.active_transactions[tx_id]
            return {
                "tx_id": tx_id,
                "status": "COMMITTED",
                "message": msg,
                "participants": list(participants),
                "trace": trace
            }
        except TwoPhaseCommitAbortException as abort_err:
            with self._lock:
                tx.status = TransactionStatus.ABORTED
                tx.finished_at = time.time()
                tx.trace = self.coordinator_2pc.get_transaction_trace(tx_id)
                self.completed_transactions[tx_id] = tx
                del self.active_transactions[tx_id]
            raise abort_err

    def abort_transaction(self, tx_id: str, reason: str = "User initiated abort") -> Dict[str, Any]:
        """Explicitly aborts the active transaction."""
        with self._lock:
            if tx_id not in self.active_transactions:
                return {"status": "ALREADY_CLOSED"}
            tx = self.active_transactions[tx_id]
            tx.status = TransactionStatus.ABORTED

        for participant in tx.participants:
            try:
                self.rpc_client.call_abort(self.coordinator_node_id, participant, tx_id, reason)
            except Exception:
                pass

        with self._lock:
            tx.finished_at = time.time()
            self.completed_transactions[tx_id] = tx
            del self.active_transactions[tx_id]

        return {"tx_id": tx_id, "status": "ABORTED", "reason": reason}

    def execute_cross_branch_transfer(self, from_acc: str, to_acc: str, amount: float) -> Dict[str, Any]:
        """
        High-level business transaction:
        Deducts amount from from_acc at one branch, adds amount to to_acc at another branch,
        logs the transaction record, and commits with 2PC across branches!
        """
        if amount <= 0:
            raise TransactionException("Transfer amount must be positive.")

        tx_id = self.begin_transaction(IsolationLevel.SERIALIZABLE)
        try:
            # 1. Locate nodes
            from_node = self._locate_record_node("accounts", from_acc)
            if not from_node:
                raise TransactionException(f"Source account {from_acc} not found at any branch node.")
            to_node = self._locate_record_node("accounts", to_acc)
            if not to_node:
                raise TransactionException(f"Destination account {to_acc} not found at any branch node.")

            # 2. Canonical lock ordering (prevent cyclic deadlocks across branches)
            first_is_debit = (from_acc <= to_acc)
            first_acc, first_node, first_delta = (from_acc, from_node, -amount) if first_is_debit else (to_acc, to_node, amount)
            second_acc, second_node, second_delta = (to_acc, to_node, amount) if first_is_debit else (from_acc, from_node, -amount)

            # Stage first update with balance_delta
            self.execute_operation(tx_id, DataOperation(
                op_type=OperationType.UPDATE,
                table="accounts",
                key_value=first_acc,
                data={"balance_delta": first_delta},
                target_node=first_node
            ))

            # Stage second update with balance_delta
            self.execute_operation(tx_id, DataOperation(
                op_type=OperationType.UPDATE,
                table="accounts",
                key_value=second_acc,
                data={"balance_delta": second_delta},
                target_node=second_node
            ))

            # 3. Insert audit transaction record
            trans_rec = {
                "tx_id": f"rec_{tx_id}",
                "from_account": from_acc,
                "to_account": to_acc,
                "branch_id": from_node,
                "amount": amount,
                "tx_type": "TRANSFER",
                "timestamp": time.time(),
                "status": "SUCCESS"
            }
            self.execute_operation(tx_id, DataOperation(
                op_type=OperationType.INSERT,
                table="transactions",
                key_value=trans_rec["tx_id"],
                data=trans_rec
            ))

            # 4. Execute Two-Phase Commit
            commit_res = self.commit_transaction(tx_id)
            commit_res["from_account"] = {"id": from_acc, "node": from_node}
            commit_res["to_account"] = {"id": to_acc, "node": to_node}
            commit_res["amount"] = amount
            return commit_res

        except Exception as e:
            self.abort_transaction(tx_id, str(e))
            raise e

    def run_deadlock_detection_cycle(self) -> List[Dict[str, Any]]:
        """Collects lock state from all branch nodes, identifies deadlocks, and aborts victims."""
        local_wfgs = []
        node_instances = list(self.rpc_client.node_registry.values())
        for node in node_instances:
            wfg = node.lock_mgr.get_wait_for_graph()
            if wfg:
                local_wfgs.append(wfg)

        global_wfg = self.deadlock_detector.build_global_wfg(local_wfgs)
        cycles = self.deadlock_detector.detect_cycles(global_wfg)

        resolutions = []
        if cycles:
            with self._lock:
                timestamps = {tx_id: tx.timestamp for tx_id, tx in self.active_transactions.items()}

            for cycle in cycles:
                victim_tx = self.deadlock_detector.select_victim(cycle, timestamps)
                if victim_tx:
                    self.abort_transaction(victim_tx, reason=f"Aborted by Distributed Deadlock Detector to break cycle: {' -> '.join(cycle)}")
                    resolutions.append({
                        "cycle": cycle,
                        "victim_aborted": victim_tx
                    })
        return resolutions
