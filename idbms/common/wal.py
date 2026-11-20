"""
Write-Ahead Logging (WAL) system for local node durability and 2PC crash recovery.
"""

import json
import os
import threading
import time
from typing import List, Dict, Any, Optional
from idbms.common.models import WALRecord

class WALManager:
    """
    Append-only Write-Ahead Log for transaction recovery, atomicity, and durability.
    Maintains a sequential LSN (Log Sequence Number) and provides crash recovery scan.
    """
    def __init__(self, log_dir: str, node_id: str):
        self.node_id = node_id
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, f"wal_{node_id}.log")
        self._lock = threading.Lock()
        self._current_lsn = self._init_lsn()

    def _init_lsn(self) -> int:
        if not os.path.exists(self.log_file):
            return 0
        last_lsn = 0
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        last_lsn = max(last_lsn, record.get("lsn", 0))
        except Exception:
            pass
        return last_lsn

    def append(self, tx_id: str, rec_type: str, table: Optional[str] = None,
               key_value: Optional[Any] = None, before_image: Optional[Dict[str, Any]] = None,
               after_image: Optional[Dict[str, Any]] = None) -> int:
        with self._lock:
            self._current_lsn += 1
            rec = WALRecord(
                lsn=self._current_lsn,
                tx_id=tx_id,
                rec_type=rec_type,
                table=table,
                key_value=key_value,
                before_image=before_image,
                after_image=after_image,
                timestamp=time.time()
            )
            line = json.dumps(rec.model_dump()) + "\n"
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
            return self._current_lsn

    def read_all_records(self) -> List[WALRecord]:
        records = []
        if not os.path.exists(self.log_file):
            return records
        with self._lock:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            records.append(WALRecord(**data))
                        except Exception:
                            continue
        return records

    def analyze_recovery_state(self) -> Dict[str, Any]:
        """
        Analyzes the log to determine:
        1. Prepared transactions awaiting decision (in-doubt).
        2. Committed transactions needing redo.
        3. Aborted / uncommitted active transactions needing undo.
        """
        records = self.read_all_records()
        tx_states: Dict[str, str] = {}
        tx_ops: Dict[str, List[WALRecord]] = {}

        for rec in records:
            tx_id = rec.tx_id
            if tx_id not in tx_ops:
                tx_ops[tx_id] = []
            tx_ops[tx_id].append(rec)

            if rec.rec_type == "BEGIN":
                tx_states[tx_id] = "ACTIVE"
            elif rec.rec_type == "PREPARE":
                tx_states[tx_id] = "PREPARED"
            elif rec.rec_type == "COMMIT":
                tx_states[tx_id] = "COMMITTED"
            elif rec.rec_type == "ABORT":
                tx_states[tx_id] = "ABORTED"

        in_doubt = [tx for tx, st in tx_states.items() if st == "PREPARED"]
        active_unprepared = [tx for tx, st in tx_states.items() if st == "ACTIVE"]
        committed = [tx for tx, st in tx_states.items() if st == "COMMITTED"]

        return {
            "tx_states": tx_states,
            "in_doubt_tx_ids": in_doubt,
            "active_unprepared_tx_ids": active_unprepared,
            "committed_tx_ids": committed,
            "tx_operations": tx_ops
        }

    def clear(self):
        with self._lock:
            if os.path.exists(self.log_file):
                os.remove(self.log_file)
            self._current_lsn = 0
