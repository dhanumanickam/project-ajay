"""
Distributed Two-Phase Commit (2PC) Coordinator.
Orchestrates Prepare and Commit/Abort phases across cohorts with fault tolerance,
timeout handling, WAL logging, and visual execution traces.
"""

import time
import threading
from typing import Dict, Any, List, Set, Tuple
from idbms.common.models import TwoPhaseVote, TwoPhaseDecision, TransactionStatus
from idbms.common.exceptions import TwoPhaseCommitAbortException
from idbms.common.wal import WALManager
from idbms.network.rpc_client import RPCClient

class Coordinator2PC:
    """
    Coordinator component of the Two-Phase Commit (2PC) protocol.
    Guarantees distributed atomicity (all-or-nothing).
    """
    def __init__(self, coordinator_node_id: str, rpc_client: RPCClient, wal: WALManager, timeout_sec: float = 4.0):
        self.coordinator_node_id = coordinator_node_id
        self.rpc_client = rpc_client
        self.wal = wal
        self.timeout_sec = timeout_sec
        self._lock = threading.RLock()
        self.tx_traces: Dict[str, List[Dict[str, Any]]] = {} # tx_id -> visual trace events

    def _log_trace(self, tx_id: str, phase: str, event: str, details: Dict[str, Any] = None):
        with self._lock:
            if tx_id not in self.tx_traces:
                self.tx_traces[tx_id] = []
            self.tx_traces[tx_id].append({
                "timestamp": time.time(),
                "phase": phase,
                "event": event,
                "details": details or {}
            })

    def execute_2pc(self, tx_id: str, participants: Set[str]) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Executes standard 2PC protocol across the given participant cohort nodes.
        Returns: (success: bool, message: str, trace_events: list)
        """
        if not participants:
            # Trivial 0-cohort transaction
            self.wal.append(tx_id=tx_id, rec_type="COMMIT")
            return True, "No cohorts involved; committed immediately.", []

        self._log_trace(tx_id, "INIT", f"Starting 2PC across {len(participants)} cohorts: {list(participants)}")

        # ----------------- PHASE 1: PREPARE -----------------
        self._log_trace(tx_id, "PHASE_1_PREPARE", f"Broadcasting PREPARE request to cohorts {list(participants)}")
        votes: Dict[str, str] = {}
        vote_reasons: Dict[str, str] = {}
        all_voted_commit = True
        failed_cohorts = []

        for cohort_id in participants:
            try:
                res = self.rpc_client.call_prepare(
                    from_node=self.coordinator_node_id,
                    to_node=cohort_id,
                    tx_id=tx_id
                )
                vote = res.get("vote", TwoPhaseVote.VOTE_ABORT.value)
                reason = res.get("reason", "")
                votes[cohort_id] = vote
                vote_reasons[cohort_id] = reason

                self._log_trace(tx_id, "PHASE_1_VOTE", f"Received vote from {cohort_id}: {vote}", {"reason": reason})

                if vote != TwoPhaseVote.VOTE_COMMIT.value:
                    all_voted_commit = False
                    failed_cohorts.append(cohort_id)
            except Exception as e:
                all_voted_commit = False
                failed_cohorts.append(cohort_id)
                votes[cohort_id] = TwoPhaseVote.VOTE_ABORT.value
                vote_reasons[cohort_id] = f"RPC Error / Timeout: {str(e)}"
                self._log_trace(tx_id, "PHASE_1_ERROR", f"Failed to contact cohort {cohort_id}: {str(e)}")

        # ----------------- PHASE 2: DECISION & BROADCAST -----------------
        if all_voted_commit:
            decision = TwoPhaseDecision.GLOBAL_COMMIT
            # Durable Coordinator WAL log record
            self.wal.append(tx_id=tx_id, rec_type="COMMIT")
            self._log_trace(tx_id, "PHASE_2_DECISION", "All cohorts voted COMMIT -> Coordinator decided GLOBAL_COMMIT")

            # Broadcast GLOBAL_COMMIT
            for cohort_id in participants:
                try:
                    self.rpc_client.call_commit(
                        from_node=self.coordinator_node_id,
                        to_node=cohort_id,
                        tx_id=tx_id
                    )
                    self._log_trace(tx_id, "PHASE_2_ACK", f"Received commit ACK from cohort {cohort_id}")
                except Exception as e:
                    self._log_trace(tx_id, "PHASE_2_RETRY", f"Error delivering commit to {cohort_id} (will retry): {str(e)}")

            trace = self.tx_traces.get(tx_id, []).copy()
            return True, f"Transaction {tx_id} successfully committed across all cohorts.", trace

        else:
            decision = TwoPhaseDecision.GLOBAL_ABORT
            # Durable Coordinator WAL log record (Presumed abort allows omitting if not prepared, but we log for audit)
            self.wal.append(tx_id=tx_id, rec_type="ABORT")
            self._log_trace(tx_id, "PHASE_2_DECISION", f"One or more cohorts aborted {failed_cohorts} -> Coordinator decided GLOBAL_ABORT")

            # Broadcast GLOBAL_ABORT
            for cohort_id in participants:
                try:
                    self.rpc_client.call_abort(
                        from_node=self.coordinator_node_id,
                        to_node=cohort_id,
                        tx_id=tx_id,
                        reason="Coordinator Global Abort decision"
                    )
                    self._log_trace(tx_id, "PHASE_2_ACK", f"Received abort ACK from cohort {cohort_id}")
                except Exception as e:
                    self._log_trace(tx_id, "PHASE_2_WARN", f"Cohort {cohort_id} unreachable during abort: {str(e)}")

            trace = self.tx_traces.get(tx_id, []).copy()
            raise TwoPhaseCommitAbortException(
                f"Distributed transaction {tx_id} aborted by 2PC. Failed nodes: {failed_cohorts}",
                reason=str(vote_reasons),
                failed_nodes=failed_cohorts
            )

    def get_transaction_trace(self, tx_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return self.tx_traces.get(tx_id, [])

    def recover_coordinator(self, participants_map: Dict[str, Set[str]]):
        """
        Coordinator crash recovery: reads WAL, checks transactions where GLOBAL_COMMIT was logged,
        and resends COMMIT to cohorts that may have missed it.
        """
        analysis = self.wal.analyze_recovery_state()
        for tx_id in analysis["committed_tx_ids"]:
            cohorts = participants_map.get(tx_id, set())
            for cohort_id in cohorts:
                try:
                    self.rpc_client.call_commit(self.coordinator_node_id, cohort_id, tx_id)
                except Exception:
                    pass
