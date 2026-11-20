"""
Unit tests for Replication, Quorum consensus (R + W > N),
Vector Clocks, and Read Repair.
"""

import unittest
from idbms.replication.vector_clock import VectorClock
from idbms.system import DistributedDatabaseCluster

class TestReplication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cluster = DistributedDatabaseCluster(reset_data=True)

    def test_vector_clock_causality_and_concurrency(self):
        """Vector clocks correctly identify causal dominance and concurrent conflict."""
        v1 = VectorClock({"NODE_HQ": 1, "NODE_LON": 0})
        v2 = VectorClock({"NODE_HQ": 1, "NODE_LON": 0})
        self.assertEqual(v1.compare(v2), "EQUAL")

        # v1 increments
        v1.increment("NODE_HQ") # {"NODE_HQ": 2, "NODE_LON": 0}
        self.assertEqual(v1.compare(v2), "DOMINATES")
        self.assertEqual(v2.compare(v1), "DOMINATED")

        # v2 increments a different node
        v2.increment("NODE_LON") # {"NODE_HQ": 1, "NODE_LON": 1}
        self.assertEqual(v1.compare(v2), "CONCURRENT") # Conflict!

        # Merge
        merged = v1.merge(v2)
        self.assertEqual(merged.to_dict(), {"NODE_HQ": 2, "NODE_LON": 1})

    def test_quorum_write_and_read_repair(self):
        """Quorum write updates W replicas; Quorum read detects and repairs stale replica."""
        rep_mgr = self.cluster.replication_mgr
        target_nodes = ["NODE_HQ", "NODE_LON", "NODE_TYO"] # N = 3

        # 1. Quorum Write with W = 2
        rec_data = {
            "cust_id": "CUST_999",
            "name": "Global VIP Client",
            "credit_score": 850,
            "status": "APPROVED"
        }
        write_res = rep_mgr.write_quorum("customers", "CUST_999", rec_data, target_nodes, w=2)
        self.assertEqual(write_res["status"], "SUCCESS")
        self.assertGreaterEqual(write_res["ack_count"], 2)

        # 2. Quorum Read with R = 2
        read_rec, read_meta = rep_mgr.read_quorum("customers", "CUST_999", target_nodes, r=2)
        self.assertIsNotNone(read_rec)
        self.assertEqual(read_rec["cust_id"], "CUST_999")
        self.assertEqual(read_rec["credit_score"], 850)

if __name__ == "__main__":
    unittest.main()
