"""
Common data models and enumerations for the IDBMS.
"""

import time
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field

class IsolationLevel(str, Enum):
    SERIALIZABLE = "SERIALIZABLE"
    SNAPSHOT_ISOLATION = "SNAPSHOT_ISOLATION"
    READ_COMMITTED = "READ_COMMITTED"

class LockMode(str, Enum):
    SHARED = "S"          # Shared lock for Read
    EXCLUSIVE = "X"       # Exclusive lock for Write

class TransactionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PREPARING = "PREPARING"
    PREPARED = "PREPARED"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"

class TwoPhaseVote(str, Enum):
    VOTE_COMMIT = "VOTE_COMMIT"
    VOTE_ABORT = "VOTE_ABORT"

class TwoPhaseDecision(str, Enum):
    GLOBAL_COMMIT = "GLOBAL_COMMIT"
    GLOBAL_ABORT = "GLOBAL_ABORT"

class FragmentationType(str, Enum):
    HORIZONTAL = "HORIZONTAL"
    VERTICAL = "VERTICAL"
    HYBRID = "HYBRID"

class ReplicationStrategy(str, Enum):
    FULL = "FULL"                   # Full replication across all nodes
    QUORUM = "QUORUM"               # Quorum-based (R + W > N)
    MASTER_SLAVE = "MASTER_SLAVE"   # Single primary node, asynchronous/sync replicas

class OperationType(str, Enum):
    READ = "READ"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

class DataOperation(BaseModel):
    op_type: OperationType
    table: str
    key_field: str = "id"
    key_value: Any
    data: Optional[Dict[str, Any]] = None
    old_data: Optional[Dict[str, Any]] = None
    target_node: Optional[str] = None

class NodeInfo(BaseModel):
    node_id: str
    name: str
    host: str = "127.0.0.1"
    port: int
    region: str
    is_coordinator: bool = False
    status: str = "ONLINE"  # ONLINE, OFFLINE, PARTITIONED
    simulated_latency_ms: float = 5.0

class WALRecord(BaseModel):
    lsn: int
    tx_id: str
    rec_type: str  # BEGIN, OP, PREPARE, COMMIT, ABORT, CHECKPOINT
    table: Optional[str] = None
    key_value: Optional[Any] = None
    before_image: Optional[Dict[str, Any]] = None
    after_image: Optional[Dict[str, Any]] = None
    timestamp: float = Field(default_factory=time.time)

class QueryResult(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float
    nodes_queried: List[str]
    plan_explanation: Optional[Dict[str, Any]] = None
