"""
Local storage engine supporting relational storage, transaction workspace,
MVCC row versioning, and SQLite file persistence.
"""

import sqlite3
import os
import threading
import time
from typing import Dict, Any, List, Optional, Tuple
from idbms.common.models import OperationType, DataOperation
from idbms.common.exceptions import DataIntegrityException

class StorageEngine:
    """
    Local storage engine for a branch node.
    Provides in-memory row store with MVCC version history and SQLite backing.
    Manages uncommitted workspaces for 2PC atomic commits.
    """
    def __init__(self, node_id: str, data_dir: str):
        self.node_id = node_id
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.db_path = os.path.join(self.data_dir, f"{node_id}.sqlite3")
        self._lock = threading.RLock()

        # In-memory primary store: table -> {pk: {data, _version, _tx_id, _created_at}}
        self.tables: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # MVCC History: table -> {pk: [list of historical row versions]}
        self.mvcc_history: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

        # Active transaction staging buffers: tx_id -> {table: {pk: {'op': op_type, 'data': dict, 'old_data': dict}}}
        self.tx_workspaces: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]] = {}

        self._init_sqlite()

    def _init_sqlite(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL;")
            cur.execute("PRAGMA synchronous=NORMAL;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS kv_records (
                    table_name TEXT,
                    pk_value TEXT,
                    record_json TEXT,
                    version INTEGER,
                    updated_at REAL,
                    PRIMARY KEY (table_name, pk_value)
                );
            """)
            conn.commit()
            # Preload into memory
            cur.execute("SELECT table_name, pk_value, record_json, version, updated_at FROM kv_records")
            import json
            for t_name, pk, r_json, ver, u_at in cur.fetchall():
                if t_name not in self.tables:
                    self.tables[t_name] = {}
                    self.mvcc_history[t_name] = {}
                row = json.loads(r_json)
                row["_version"] = ver
                row["_created_at"] = u_at
                self.tables[t_name][str(pk)] = row
                self.mvcc_history[t_name][str(pk)] = [row.copy()]

    def ensure_table(self, table_name: str):
        t = table_name.lower()
        with self._lock:
            if t not in self.tables:
                self.tables[t] = {}
                self.mvcc_history[t] = {}

    def get_record(self, table_name: str, pk_value: Any, tx_id: Optional[str] = None, read_timestamp: Optional[float] = None) -> Optional[Dict[str, Any]]:
        t = table_name.lower()
        pk = str(pk_value)
        with self._lock:
            # 1. Read uncommitted write within the same transaction workspace
            if tx_id and tx_id in self.tx_workspaces:
                ws = self.tx_workspaces[tx_id]
                if t in ws and pk in ws[t]:
                    staged = ws[t][pk]
                    if staged["op"] == OperationType.DELETE:
                        return None
                    return staged["data"].copy()

            # 2. Snapshot Isolation / MVCC read by timestamp
            if read_timestamp is not None and t in self.mvcc_history and pk in self.mvcc_history[t]:
                history = self.mvcc_history[t][pk]
                # Walk backward to find the version that was committed before or at read_timestamp
                for version_rec in reversed(history):
                    if version_rec.get("_created_at", 0) <= read_timestamp:
                        return version_rec.copy()

            # 3. Read current committed version
            if t in self.tables and pk in self.tables[t]:
                return self.tables[t][pk].copy()

            return None

    def scan_table(self, table_name: str, tx_id: Optional[str] = None) -> List[Dict[str, Any]]:
        t = table_name.lower()
        with self._lock:
            self.ensure_table(t)
            current_dict = {k: v.copy() for k, v in self.tables[t].items()}

            # Overlay tx workspace if present
            if tx_id and tx_id in self.tx_workspaces:
                ws = self.tx_workspaces[tx_id].get(t, {})
                for pk, staged in ws.items():
                    if staged["op"] == OperationType.DELETE:
                        current_dict.pop(pk, None)
                    else:
                        current_dict[pk] = staged["data"].copy()

            return list(current_dict.values())

    def stage_operation(self, tx_id: str, op: DataOperation):
        """Stages an operation into the transaction workspace without committing it yet."""
        t = op.table.lower()
        pk = str(op.key_value)
        with self._lock:
            self.ensure_table(t)
            if tx_id not in self.tx_workspaces:
                self.tx_workspaces[tx_id] = {}
            if t not in self.tx_workspaces[tx_id]:
                self.tx_workspaces[tx_id][t] = {}

            current = self.get_record(t, pk, tx_id=tx_id)

            if op.op_type == OperationType.INSERT:
                if current is not None:
                    raise DataIntegrityException(f"Record with PK {pk} already exists in {t}")
                record_data = op.data.copy() if op.data else {}
                record_data[op.key_field] = op.key_value
                self.tx_workspaces[tx_id][t][pk] = {
                    "op": OperationType.INSERT,
                    "data": record_data,
                    "old_data": None
                }

            elif op.op_type == OperationType.UPDATE:
                if current is None:
                    raise DataIntegrityException(f"Record with PK {pk} does not exist in {t}")
                updated = current.copy()
                if op.data:
                    if "balance_delta" in op.data:
                        updated["balance"] = round(updated.get("balance", 0.0) + float(op.data["balance_delta"]), 2)
                    else:
                        updated.update(op.data)
                # Validation checks (e.g., negative balance check)
                if "balance" in updated and updated["balance"] < 0:
                    raise DataIntegrityException(f"Insufficient funds: Balance cannot be negative ({updated['balance']})")

                self.tx_workspaces[tx_id][t][pk] = {
                    "op": OperationType.UPDATE,
                    "data": updated,
                    "old_data": current
                }

            elif op.op_type == OperationType.DELETE:
                if current is None:
                    raise DataIntegrityException(f"Record with PK {pk} does not exist in {t}")
                self.tx_workspaces[tx_id][t][pk] = {
                    "op": OperationType.DELETE,
                    "data": None,
                    "old_data": current
                }

    def validate_workspace(self, tx_id: str) -> Tuple[bool, Optional[str]]:
        """Validates all staged operations for integrity constraints before voting commit."""
        with self._lock:
            if tx_id not in self.tx_workspaces:
                return True, None
            ws = self.tx_workspaces[tx_id]
            for t_name, rows in ws.items():
                for pk, staged in rows.items():
                    data = staged["data"]
                    if data and "balance" in data:
                        if data["balance"] < 0:
                            return False, f"Constraint violation: Negative balance {data['balance']} on {t_name}:{pk}"
            return True, None

    def commit_workspace(self, tx_id: str) -> List[Dict[str, Any]]:
        """Applies all staged updates atomically to memory and SQLite backing store."""
        import json
        applied_ops = []
        with self._lock:
            if tx_id not in self.tx_workspaces:
                return applied_ops

            ws = self.tx_workspaces.pop(tx_id)
            now = time.time()

            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                for t_name, rows in ws.items():
                    self.ensure_table(t_name)
                    for pk, staged in rows.items():
                        op = staged["op"]
                        data = staged["data"]
                        old = staged["old_data"]

                        if op in (OperationType.INSERT, OperationType.UPDATE):
                            new_version = (old.get("_version", 0) + 1) if old else 1
                            data["_version"] = new_version
                            data["_created_at"] = now
                            data["_last_tx"] = tx_id
                            self.tables[t_name][pk] = data

                            if pk not in self.mvcc_history[t_name]:
                                self.mvcc_history[t_name][pk] = []
                            self.mvcc_history[t_name][pk].append(data.copy())

                            cur.execute("""
                                INSERT OR REPLACE INTO kv_records (table_name, pk_value, record_json, version, updated_at)
                                VALUES (?, ?, ?, ?, ?)
                            """, (t_name, pk, json.dumps(data), new_version, now))

                        elif op == OperationType.DELETE:
                            self.tables[t_name].pop(pk, None)
                            cur.execute("DELETE FROM kv_records WHERE table_name = ? AND pk_value = ?", (t_name, pk))

                        applied_ops.append({
                            "table": t_name,
                            "pk": pk,
                            "op": op.value,
                            "data": data
                        })

                conn.commit()

        return applied_ops

    def abort_workspace(self, tx_id: str):
        """Discards staged operations without touching committed storage."""
        with self._lock:
            self.tx_workspaces.pop(tx_id, None)

    def get_table_stats(self) -> Dict[str, int]:
        with self._lock:
            return {t: len(records) for t, records in self.tables.items()}

    def clear(self):
        with self._lock:
            self.tables.clear()
            self.mvcc_history.clear()
            self.tx_workspaces.clear()
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM kv_records;")
                    conn.commit()
            except Exception:
                pass

