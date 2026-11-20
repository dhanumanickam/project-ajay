"""
Branch Node service encapsulating local storage, lock management, WAL, and 2PC cohort.
"""

import os
import time
from typing import Dict, Any, List, Optional
from idbms.common.models import NodeInfo, LockMode, OperationType, DataOperation, TwoPhaseVote
from idbms.common.wal import WALManager
from idbms.node.storage_engine import StorageEngine
from idbms.node.lock_manager import LockManager
from idbms.node.cohort_2pc import Cohort2PC

class BranchNode:
    """
    Represents an autonomous database node located at an organizational branch or HQ.
    """
    def __init__(self, node_info: NodeInfo, base_data_dir: str = "data/nodes"):
        self.node_info = node_info
        self.node_id = node_info.node_id
        self.node_dir = os.path.join(base_data_dir, self.node_id)
        os.makedirs(self.node_dir, exist_ok=True)

        self.wal = WALManager(log_dir=self.node_dir, node_id=self.node_id)
        self.storage = StorageEngine(node_id=self.node_id, data_dir=self.node_dir)
        self.lock_mgr = LockManager(node_id=self.node_id, deadlock_strategy="WOUND_WAIT")
        self.cohort = Cohort2PC(node_id=self.node_id, storage=self.storage, lock_mgr=self.lock_mgr, wal=self.wal)

        # Fault injection flags
        self.is_offline = False
        self.simulate_abort_vote = False

    def handle_read(self, table: str, pk_value: Any, tx_id: Optional[str] = None, read_timestamp: Optional[float] = None) -> Optional[Dict[str, Any]]:
        if self.is_offline:
            raise ConnectionError(f"Node {self.node_id} is currently offline.")
        return self.storage.get_record(table, pk_value, tx_id=tx_id, read_timestamp=read_timestamp)

    def handle_scan(self, table: str, tx_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.is_offline:
            raise ConnectionError(f"Node {self.node_id} is currently offline.")
        return self.storage.scan_table(table, tx_id=tx_id)

    def execute_tx_operation(self, tx_id: str, op: DataOperation, tx_timestamp: float) -> Dict[str, Any]:
        """
        Executes a data operation within a distributed transaction:
        1. Registers tx with lock manager
        2. Acquires appropriate 2PL lock (S for read, X for write)
        3. Appends BEGIN / OP to WAL log
        4. Stages change into local storage engine workspace
        """
        if self.is_offline:
            raise ConnectionError(f"Node {self.node_id} is currently offline.")

        self.lock_mgr.register_transaction(tx_id, tx_timestamp)

        pk = str(op.key_value)
        # Determine lock mode
        if op.op_type == OperationType.READ:
            self.lock_mgr.acquire_lock(tx_id, op.table, pk, LockMode.SHARED)
            record = self.storage.get_record(op.table, pk, tx_id=tx_id)
            return {"status": "SUCCESS", "record": record}
        else:
            # Exclusive lock for Insert, Update, Delete
            self.lock_mgr.acquire_lock(tx_id, op.table, pk, LockMode.EXCLUSIVE)
            # Log to WAL
            self.wal.append(
                tx_id=tx_id,
                rec_type="OP",
                table=op.table,
                key_value=pk,
                before_image=self.storage.get_record(op.table, pk, tx_id=tx_id),
                after_image=op.data
            )
            # Stage into workspace
            self.storage.stage_operation(tx_id, op)
            return {"status": "STAGED", "node_id": self.node_id, "table": op.table, "key": pk}

    def prepare(self, tx_id: str) -> Dict[str, Any]:
        if self.is_offline:
            return {"vote": TwoPhaseVote.VOTE_ABORT.value, "reason": f"Node {self.node_id} is offline"}
        if self.simulate_abort_vote:
            return {"vote": TwoPhaseVote.VOTE_ABORT.value, "reason": f"Node {self.node_id} forced failure injection"}

        vote, reason = self.cohort.prepare(tx_id)
        return {"vote": vote.value, "reason": reason, "node_id": self.node_id}

    def commit(self, tx_id: str) -> Dict[str, Any]:
        if self.is_offline:
            raise ConnectionError(f"Node {self.node_id} offline during commit")
        success = self.cohort.commit(tx_id)
        return {"status": "COMMITTED" if success else "FAILED", "node_id": self.node_id}

    def abort(self, tx_id: str, reason: str = "") -> Dict[str, Any]:
        success = self.cohort.abort(tx_id, reason)
        return {"status": "ABORTED" if success else "FAILED", "node_id": self.node_id}

    def get_status(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "name": self.node_info.name,
            "region": self.node_info.region,
            "status": "OFFLINE" if self.is_offline else self.node_info.status,
            "active_locks": self.lock_mgr.get_lock_table_snapshot(),
            "table_stats": self.storage.get_table_stats(),
            "wal_records": len(self.wal.read_all_records())
        }
