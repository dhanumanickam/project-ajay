"""
Custom exceptions for the Intelligent Distributed DBMS.
"""

class IDBMSException(Exception):
    """Base exception for IDBMS."""
    pass

class TransactionException(IDBMSException):
    """Base exception for transaction management."""
    pass

class LockTimeoutException(TransactionException):
    """Raised when a lock acquisition times out."""
    pass

class DeadlockException(TransactionException):
    """Raised when a deadlock cycle is detected or wound/die fires."""
    def __init__(self, message: str, victim_tx_id: str = None):
        super().__init__(message)
        self.victim_tx_id = victim_tx_id

class TwoPhaseCommitAbortException(TransactionException):
    """Raised when one or more cohorts vote to abort during 2PC."""
    def __init__(self, message: str, reason: str = None, failed_nodes: list = None):
        super().__init__(message)
        self.reason = reason
        self.failed_nodes = failed_nodes or []

class NodeUnavailableException(IDBMSException):
    """Raised when a target branch node cannot be reached."""
    pass

class DataIntegrityException(TransactionException):
    """Raised when data integrity or constraint check fails."""
    pass

class QueryParsingException(IDBMSException):
    """Raised when a distributed query cannot be parsed or optimized."""
    pass

class ReplicationConflictException(IDBMSException):
    """Raised when a replica conflict cannot be automatically reconciled."""
    pass
