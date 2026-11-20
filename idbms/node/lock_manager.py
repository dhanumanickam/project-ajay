"""
Local Lock Manager implementing Strict 2-Phase Locking (SS2PL),
with Wound-Wait and Wait-Die deadlock prevention algorithms.
"""

import threading
import time
from typing import Dict, Set, Optional, List, Tuple, Any
from idbms.common.models import LockMode
from idbms.common.exceptions import LockTimeoutException, DeadlockException

class LockEntry:
    def __init__(self, resource_key: str):
        self.resource_key = resource_key
        self.shared_holders: Set[str] = set()       # Set of tx_ids holding Shared lock
        self.exclusive_holder: Optional[str] = None # tx_id holding Exclusive lock
        self.wait_queue: List[Tuple[str, LockMode, float, threading.Event]] = [] # [(tx_id, mode, timestamp, event)]

class LockManager:
    """
    Strict Two-Phase Locking (SS2PL) Manager.
    All locks acquired during transaction execution are retained until Commit or Abort.
    Deadlock handling: Supports both Wound-Wait and Wait-Die timestamp schemes.
    """
    def __init__(self, node_id: str, deadlock_strategy: str = "WOUND_WAIT", lock_timeout_sec: float = 3.0):
        self.node_id = node_id
        self.deadlock_strategy = deadlock_strategy  # "WOUND_WAIT", "WAIT_DIE", or "TIMEOUT"
        self.lock_timeout_sec = lock_timeout_sec
        self._lock = threading.RLock()
        self.locks: Dict[str, LockEntry] = {}       # resource_key (table:id) -> LockEntry
        self.tx_locks: Dict[str, Set[str]] = {}     # tx_id -> set of resource_keys
        self.tx_timestamps: Dict[str, float] = {}   # tx_id -> transaction start timestamp
        self.wait_for_graph: Dict[str, Set[str]] = {} # tx_id -> set of tx_ids it is waiting for

    def register_transaction(self, tx_id: str, timestamp: float):
        with self._lock:
            self.tx_timestamps[tx_id] = timestamp
            if tx_id not in self.tx_locks:
                self.tx_locks[tx_id] = set()
            if tx_id not in self.wait_for_graph:
                self.wait_for_graph[tx_id] = set()

    def acquire_lock(self, tx_id: str, table: str, key_val: str, mode: LockMode) -> bool:
        resource_key = f"{table.lower()}:{str(key_val)}"
        req_ts = self.tx_timestamps.get(tx_id, time.time())

        event = threading.Event()
        with self._lock:
            if tx_id not in self.tx_locks:
                self.tx_locks[tx_id] = set()
            if resource_key not in self.locks:
                self.locks[resource_key] = LockEntry(resource_key)

            entry = self.locks[resource_key]

            # Fast path: already has required lock
            if mode == LockMode.SHARED:
                if tx_id in entry.shared_holders or entry.exclusive_holder == tx_id:
                    self.tx_locks[tx_id].add(resource_key)
                    return True
                # Can grant shared lock if no exclusive holder and no exclusive waiter ahead
                if entry.exclusive_holder is None and not any(m == LockMode.EXCLUSIVE for _, m, _, _ in entry.wait_queue):
                    entry.shared_holders.add(tx_id)
                    self.tx_locks[tx_id].add(resource_key)
                    return True
            elif mode == LockMode.EXCLUSIVE:
                if entry.exclusive_holder == tx_id:
                    return True
                # Upgrade shared to exclusive if tx is sole shared holder
                if entry.exclusive_holder is None and entry.shared_holders == {tx_id}:
                    entry.shared_holders.remove(tx_id)
                    entry.exclusive_holder = tx_id
                    self.tx_locks[tx_id].add(resource_key)
                    return True
                if entry.exclusive_holder is None and len(entry.shared_holders) == 0:
                    entry.exclusive_holder = tx_id
                    self.tx_locks[tx_id].add(resource_key)
                    return True

            # Conflict exists - determine conflicting transactions
            conflicting_txs = set()
            if entry.exclusive_holder and entry.exclusive_holder != tx_id:
                conflicting_txs.add(entry.exclusive_holder)
            if mode == LockMode.EXCLUSIVE:
                conflicting_txs.update({h for h in entry.shared_holders if h != tx_id})

            # Deadlock Handling Scheme
            for holder_tx in list(conflicting_txs):
                holder_ts = self.tx_timestamps.get(holder_tx, time.time())
                if self.deadlock_strategy == "WOUND_WAIT":
                    # Older transaction wounds (aborts) younger transaction
                    if req_ts < holder_ts:
                        # Requester is older! Wound the younger holder
                        raise DeadlockException(
                            f"[Wound-Wait] Older Tx {tx_id} wounded younger Tx {holder_tx} on {resource_key}",
                            victim_tx_id=holder_tx
                        )
                    else:
                        # Requester is younger: requester waits
                        pass
                elif self.deadlock_strategy == "WAIT_DIE":
                    # Older transaction waits, younger transaction dies immediately
                    if req_ts < holder_ts:
                        # Requester is older: allowed to wait
                        pass
                    else:
                        # Requester is younger: dies!
                        raise DeadlockException(
                            f"[Wait-Die] Younger Tx {tx_id} died waiting for older Tx {holder_tx} on {resource_key}",
                            victim_tx_id=tx_id
                        )

            # Record wait-for dependency
            self.wait_for_graph[tx_id] = conflicting_txs.copy()
            entry.wait_queue.append((tx_id, mode, req_ts, event))

        # Wait on event outside global lock
        acquired = event.wait(timeout=self.lock_timeout_sec)
        with self._lock:
            if tx_id in self.wait_for_graph:
                self.wait_for_graph[tx_id].clear()

            if not acquired:
                # Remove from wait queue
                if resource_key in self.locks:
                    self.locks[resource_key].wait_queue = [
                        item for item in self.locks[resource_key].wait_queue if item[0] != tx_id
                    ]
                raise LockTimeoutException(f"Tx {tx_id} timed out acquiring {mode.value} lock on {resource_key}")

            self.tx_locks[tx_id].add(resource_key)
            return True

    def release_locks_for_transaction(self, tx_id: str):
        """Strict 2PL: Releases all locks held by transaction at commit or abort."""
        with self._lock:
            held_resources = self.tx_locks.pop(tx_id, set())
            self.tx_timestamps.pop(tx_id, None)
            self.wait_for_graph.pop(tx_id, None)

            # Also remove tx_id from other wait graphs
            for waiting_tx, holders in self.wait_for_graph.items():
                holders.discard(tx_id)

            for resource_key in held_resources:
                if resource_key not in self.locks:
                    continue
                entry = self.locks[resource_key]
                if entry.exclusive_holder == tx_id:
                    entry.exclusive_holder = None
                entry.shared_holders.discard(tx_id)

                # Wake up eligible waiters in FIFO / Timestamp order
                self._wake_next_waiters(entry)

                if not entry.shared_holders and entry.exclusive_holder is None and not entry.wait_queue:
                    del self.locks[resource_key]

    def _wake_next_waiters(self, entry: LockEntry):
        if not entry.wait_queue:
            return

        # Check if head of queue can acquire
        head_tx_id, head_mode, _, head_event = entry.wait_queue[0]

        if head_mode == LockMode.EXCLUSIVE:
            if not entry.shared_holders and entry.exclusive_holder is None:
                entry.wait_queue.pop(0)
                entry.exclusive_holder = head_tx_id
                head_event.set()
        elif head_mode == LockMode.SHARED:
            if entry.exclusive_holder is None:
                # Wake all contiguous shared lock waiters
                while entry.wait_queue and entry.wait_queue[0][1] == LockMode.SHARED:
                    tx_id, _, _, event = entry.wait_queue.pop(0)
                    entry.shared_holders.add(tx_id)
                    event.set()

    def get_lock_table_snapshot(self) -> List[Dict[str, Any]]:
        """Returns snapshot of current active locks and waiters for monitoring dashboard."""
        snapshot = []
        with self._lock:
            for res_key, entry in self.locks.items():
                snapshot.append({
                    "resource": res_key,
                    "exclusive_holder": entry.exclusive_holder,
                    "shared_holders": list(entry.shared_holders),
                    "waiters": [{"tx_id": w[0], "mode": w[1].value} for w in entry.wait_queue]
                })
        return snapshot

    def get_wait_for_graph(self) -> Dict[str, List[str]]:
        with self._lock:
            return {tx: list(holders) for tx, holders in self.wait_for_graph.items() if holders}
