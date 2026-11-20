"""
Unit tests for Concurrency Control: Strict 2PL, Wound-Wait, Wait-Die,
and Distributed Deadlock Detection.
"""

import unittest
import time
import threading
from idbms.node.lock_manager import LockManager
from idbms.common.models import LockMode
from idbms.common.exceptions import DeadlockException, LockTimeoutException
from idbms.transaction.deadlock_detector import DistributedDeadlockDetector

class TestConcurrencyControl(unittest.TestCase):
    def test_shared_locks_concurrent_access(self):
        """Multiple transactions can acquire Shared (S) locks concurrently on the same resource."""
        lm = LockManager(node_id="NODE_LON")
        lm.register_transaction("tx_read_1", time.time())
        lm.register_transaction("tx_read_2", time.time())

        # Both acquire S lock on same account
        granted_1 = lm.acquire_lock("tx_read_1", "accounts", "ACC_001", LockMode.SHARED)
        granted_2 = lm.acquire_lock("tx_read_2", "accounts", "ACC_001", LockMode.SHARED)

        self.assertTrue(granted_1)
        self.assertTrue(granted_2)

        snapshot = lm.get_lock_table_snapshot()
        self.assertEqual(len(snapshot), 1)
        self.assertIn("tx_read_1", snapshot[0]["shared_holders"])
        self.assertIn("tx_read_2", snapshot[0]["shared_holders"])

        # Release
        lm.release_locks_for_transaction("tx_read_1")
        lm.release_locks_for_transaction("tx_read_2")
        self.assertEqual(len(lm.get_lock_table_snapshot()), 0)

    def test_exclusive_lock_mutual_exclusion(self):
        """Exclusive (X) lock excludes concurrent readers and writers."""
        lm = LockManager(node_id="NODE_LON", lock_timeout_sec=0.5)
        lm.register_transaction("tx_write", time.time())
        lm.acquire_lock("tx_write", "accounts", "ACC_001", LockMode.EXCLUSIVE)

        # Another transaction attempting to read should time out
        lm.register_transaction("tx_read", time.time())
        with self.assertRaises(LockTimeoutException):
            lm.acquire_lock("tx_read", "accounts", "ACC_001", LockMode.SHARED)

        lm.release_locks_for_transaction("tx_write")
        lm.release_locks_for_transaction("tx_read")

    def test_wound_wait_deadlock_prevention(self):
        """Wound-Wait: Older transaction wounds (aborts) younger transaction holding conflicting lock."""
        lm = LockManager(node_id="NODE_LON", deadlock_strategy="WOUND_WAIT")
        # Tx1 is younger (started at t=100)
        lm.register_transaction("tx_younger", timestamp=100.0)
        lm.acquire_lock("tx_younger", "accounts", "ACC_001", LockMode.EXCLUSIVE)

        # Tx2 is older (started at t=50)
        lm.register_transaction("tx_older", timestamp=50.0)

        # Older transaction attempts to acquire X lock on same item -> should WOUND younger tx!
        with self.assertRaises(DeadlockException) as ctx:
            lm.acquire_lock("tx_older", "accounts", "ACC_001", LockMode.EXCLUSIVE)

        self.assertEqual(ctx.exception.victim_tx_id, "tx_younger")

    def test_wait_die_deadlock_prevention(self):
        """Wait-Die: Younger transaction dies when attempting to acquire lock held by older transaction."""
        lm = LockManager(node_id="NODE_LON", deadlock_strategy="WAIT_DIE")
        # Tx1 is older (t=50)
        lm.register_transaction("tx_older", timestamp=50.0)
        lm.acquire_lock("tx_older", "accounts", "ACC_001", LockMode.EXCLUSIVE)

        # Tx2 is younger (t=100)
        lm.register_transaction("tx_younger", timestamp=100.0)

        # Younger attempts to acquire -> dies immediately!
        with self.assertRaises(DeadlockException) as ctx:
            lm.acquire_lock("tx_younger", "accounts", "ACC_001", LockMode.EXCLUSIVE)

        self.assertEqual(ctx.exception.victim_tx_id, "tx_younger")

    def test_distributed_deadlock_cycle_detection(self):
        """Distributed WFG cycle detection: T1 -> T2 and T2 -> T1 across nodes."""
        detector = DistributedDeadlockDetector()

        # Node 1 WFG: T1 is waiting for T2
        node1_wfg = {"tx_1": ["tx_2"]}
        # Node 2 WFG: T2 is waiting for T1
        node2_wfg = {"tx_2": ["tx_1"]}

        global_wfg = detector.build_global_wfg([node1_wfg, node2_wfg])
        cycles = detector.detect_cycles(global_wfg)

        self.assertGreater(len(cycles), 0)
        # Verify cycle contains both tx_1 and tx_2
        cycle_txs = set(cycles[0])
        self.assertIn("tx_1", cycle_txs)
        self.assertIn("tx_2", cycle_txs)

        # Verify victim selection picks the youngest transaction
        timestamps = {"tx_1": 10.0, "tx_2": 25.0}
        victim = detector.select_victim(cycles[0], timestamps)
        self.assertEqual(victim, "tx_2")

if __name__ == "__main__":
    unittest.main()
