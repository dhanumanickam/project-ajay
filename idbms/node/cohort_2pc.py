"""
Two-Phase Commit (2PC) Cohort / Participant implementation.
Manages voting, WAL logging, crash recovery, and transaction state transitions.
"""

import threading
import time
from typing import Dict, Any, Tuple
from idbms.common.models import TwoPhaseVote, TwoPhaseDecision, TransactionStatus
from idbms.common.wal import WALManager
from idbms.node.storage_engine import StorageEngine
from idbms.node.lock_manager import LockManager

class Cohort2PC:
    """
    Participates in distributed 2PC transactions orchestrated by the Coordinator.
    Preserves ACID guarantees across node boundaries.
    """
    def __init__(self, node_id: str, storage: StorageEngine, lock_mgr: LockManager, wal: WALManager):
        self.node_id = node_id
        self.storage = storage
        self.lock_mgr = lock_mgr
        self.wal = wal
        self._lock = threading.RLock()
        self.cohort_tx_status: Dict[str, TransactionStatus] = {}

    def prepare(self, tx_id: str) -> Tuple[TwoPhaseVote, str]:
        """
        Phase 1: Voting Phase.
        Validates integrity, writes PREPARE to WAL, and guarantees it can commit.
        """
        with self._lock:
            # 1. Validate data constraints in storage engine
            is_valid, error_msg = self.storage.validate_workspace(tx_id)
            if not is_valid:
                # Vote Abort
                self.wal.append(tx_id=tx_id, rec_type="ABORT", table=None, key_value=None)
                self.cohort_tx_status[tx_id] = TransactionStatus.ABORTED
                self.storage.abort_workspace(tx_id)
                self.lock_mgr.release_locks_for_transaction(tx_id)
                return TwoPhaseVote.VOTE_ABORT, f"Cohort {self.node_id} abort: {error_msg}"

            # 2. Append PREPARE record to WAL (Durability barrier)
            self.wal.append(tx_id=tx_id, rec_type="PREPARE", table=None, key_value=None)
            self.cohort_tx_status[tx_id] = TransactionStatus.PREPARED
            return TwoPhaseVote.VOTE_COMMIT, f"Cohort {self.node_id} prepared successfully"

    def commit(self, tx_id: str) -> bool:
        """
        Phase 2: Decision Phase (Commit).
        Writes COMMIT to WAL, applies staged modifications to permanent store, releases locks.
        """
        with self._lock:
            # Durability log
            self.wal.append(tx_id=tx_id, rec_type="COMMIT", table=None, key_value=None)
            # Apply changes
            self.storage.commit_workspace(tx_id)
            # Release 2PL locks
            self.lock_mgr.release_locks_for_transaction(tx_id)
            self.cohort_tx_status[tx_id] = TransactionStatus.COMMITTED
            return True

    def abort(self, tx_id: str, reason: str = "") -> bool:
        """
        Phase 2: Decision Phase (Abort).
        Writes ABORT to WAL, discards staged changes, releases locks.
        """
        with self._lock:
            self.wal.append(tx_id=tx_id, rec_type="ABORT", table=None, key_value=None)
            self.storage.abort_workspace(tx_id)
            self.lock_mgr.release_locks_for_transaction(tx_id)
            self.cohort_tx_status[tx_id] = TransactionStatus.ABORTED
            return True

    def recover_in_doubt_transactions(self) -> Dict[str, Any]:
        """
        Crash recovery scan upon node reboot.
        Identifies transactions that are in PREPARED state (in-doubt)
        and must consult coordinator or peers to resolve.
        """
        analysis = self.wal.analyze_recovery_state()
        in_doubt = analysis["in_doubt_tx_ids"]
        for tx in in_doubt:
            self.cohort_tx_status[tx] = TransactionStatus.PREPARED
        return {
            "node_id": self.node_id,
            "in_doubt_transactions": in_doubt,
            "committed_count": len(analysis["committed_tx_ids"]),
            "unprepared_count": len(analysis["active_unprepared_tx_ids"])
        }
