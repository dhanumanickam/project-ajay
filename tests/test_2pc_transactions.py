"""
Unit tests for Distributed Transactions and Two-Phase Commit (2PC) Protocol.
"""

import unittest
from idbms.system import DistributedDatabaseCluster
from idbms.common.exceptions import TransactionException, TwoPhaseCommitAbortException

class TestTwoPhaseCommit(unittest.TestCase):
    def setUp(self):
        self.cluster = DistributedDatabaseCluster(reset_data=True)

    def test_successful_2pc_distributed_transfer(self):
        """Cross-branch transfer from London to Tokyo should commit atomically via 2PC."""
        from_acc = "ACC_LON_01"
        to_acc = "ACC_TYO_01"

        lon_node = self.cluster.nodes["NODE_LON"]
        tyo_node = self.cluster.nodes["NODE_TYO"]

        init_lon_bal = lon_node.storage.get_record("accounts", from_acc)["balance"]
        init_tyo_bal = tyo_node.storage.get_record("accounts", to_acc)["balance"]

        transfer_amt = 1000.0
        res = self.cluster.tx_mgr.execute_cross_branch_transfer(from_acc, to_acc, transfer_amt)

        self.assertEqual(res["status"], "COMMITTED")
        self.assertIn("NODE_LON", res["participants"])
        self.assertIn("NODE_TYO", res["participants"])

        # Check balances
        new_lon_bal = lon_node.storage.get_record("accounts", from_acc)["balance"]
        new_tyo_bal = tyo_node.storage.get_record("accounts", to_acc)["balance"]

        self.assertEqual(new_lon_bal, init_lon_bal - transfer_amt)
        self.assertEqual(new_tyo_bal, init_tyo_bal + transfer_amt)

        # Check 2PC execution trace events
        trace_phases = [t["phase"] for t in res["trace"]]
        self.assertIn("PHASE_1_PREPARE", trace_phases)
        self.assertIn("PHASE_1_VOTE", trace_phases)
        self.assertIn("PHASE_2_DECISION", trace_phases)
        self.assertIn("PHASE_2_ACK", trace_phases)

    def test_2pc_abort_insufficient_funds(self):
        """Transaction should abort when an integrity constraint is violated."""
        from_acc = "ACC_LON_01"
        to_acc = "ACC_TYO_01"

        lon_node = self.cluster.nodes["NODE_LON"]
        tyo_node = self.cluster.nodes["NODE_TYO"]

        init_lon_bal = lon_node.storage.get_record("accounts", from_acc)["balance"]
        init_tyo_bal = tyo_node.storage.get_record("accounts", to_acc)["balance"]

        # Attempt to transfer amount greater than balance
        with self.assertRaises(TransactionException):
            self.cluster.tx_mgr.execute_cross_branch_transfer(from_acc, to_acc, 99999999.0)

        # Balances must be unaltered (Atomicity)
        curr_lon_bal = lon_node.storage.get_record("accounts", from_acc)["balance"]
        curr_tyo_bal = tyo_node.storage.get_record("accounts", to_acc)["balance"]
        self.assertEqual(curr_lon_bal, init_lon_bal)
        self.assertEqual(curr_tyo_bal, init_tyo_bal)

    def test_2pc_abort_cohort_forced_failure(self):
        """Simulate a cohort failure or negative vote during Phase 1."""
        tyo_node = self.cluster.nodes["NODE_TYO"]
        tyo_node.simulate_abort_vote = True # Fault injection

        from_acc = "ACC_LON_01"
        to_acc = "ACC_TYO_01"
        lon_node = self.cluster.nodes["NODE_LON"]
        init_lon_bal = lon_node.storage.get_record("accounts", from_acc)["balance"]

        with self.assertRaises(TwoPhaseCommitAbortException):
            self.cluster.tx_mgr.execute_cross_branch_transfer(from_acc, to_acc, 200.0)

        # Ensure London balance was not modified (Atomicity preserved!)
        curr_lon_bal = lon_node.storage.get_record("accounts", from_acc)["balance"]
        self.assertEqual(curr_lon_bal, init_lon_bal)

        tyo_node.simulate_abort_vote = False

    def test_wal_durability_and_recovery_scan(self):
        """Verify that WAL log contains prepared and committed records for audit and recovery."""
        from_acc = "ACC_LON_01"
        to_acc = "ACC_TYO_01"
        self.cluster.tx_mgr.execute_cross_branch_transfer(from_acc, to_acc, 300.0)

        lon_wal = self.cluster.nodes["NODE_LON"].wal
        analysis = lon_wal.analyze_recovery_state()

        self.assertGreater(len(analysis["committed_tx_ids"]), 0)
        self.assertEqual(len(analysis["in_doubt_tx_ids"]), 0)

if __name__ == "__main__":
    unittest.main()
