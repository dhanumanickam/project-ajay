"""
Unit tests for data fragmentation: Horizontal, Vertical, and Hybrid partitioning.
"""

import unittest
from idbms.system import DistributedDatabaseCluster

class TestFragmentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cluster = DistributedDatabaseCluster(reset_data=True)

    def test_horizontal_fragmentation_distribution(self):
        """Verify accounts are distributed to the correct branch nodes according to branch_id."""
        lon_node = self.cluster.nodes["NODE_LON"]
        tyo_node = self.cluster.nodes["NODE_TYO"]
        hq_node = self.cluster.nodes["NODE_HQ"]
        sgp_node = self.cluster.nodes["NODE_SGP"]

        lon_accounts = lon_node.storage.scan_table("accounts")
        for acc in lon_accounts:
            self.assertEqual(acc["branch_id"], "BRANCH_LON")

        tyo_accounts = tyo_node.storage.scan_table("accounts")
        for acc in tyo_accounts:
            self.assertEqual(acc["branch_id"], "BRANCH_TYO")

        hq_accounts = hq_node.storage.scan_table("accounts")
        for acc in hq_accounts:
            self.assertEqual(acc["branch_id"], "BRANCH_HQ")

        sgp_accounts = sgp_node.storage.scan_table("accounts")
        for acc in sgp_accounts:
            self.assertEqual(acc["branch_id"], "BRANCH_SGP")

    def test_fragment_pruning_query(self):
        """Verify that a query filtering on branch_id='BRANCH_LON' contacts only NODE_LON."""
        sql = "SELECT * FROM accounts WHERE branch_id = 'BRANCH_LON'"
        res = self.cluster.query_executor.execute_sql(sql)
        self.assertIn("NODE_LON", res.nodes_queried)
        self.assertEqual(len(res.nodes_queried), 1) # Only NODE_LON queried!
        self.assertGreater(len(res.rows), 0)
        for r in res.rows:
            self.assertEqual(r["branch_id"], "BRANCH_LON")

    def test_vertical_fragmentation_reconstruction(self):
        """Verify vertical fragments (basic info + KYC) are reconstructed via Natural Join."""
        sql = "SELECT * FROM customers"
        res = self.cluster.query_executor.execute_sql(sql)
        self.assertGreaterEqual(len(res.rows), 5)
        sample = next((r for r in res.rows if r["cust_id"] == "CUST_101"), None)
        self.assertIsNotNone(sample)
        # Check basic profile attribute
        self.assertEqual(sample["name"], "Alice Morgan")
        # Check KYC profile attribute
        self.assertEqual(sample["credit_score"], 780)
        self.assertEqual(sample["tax_id"], "US-TAX-9821")

if __name__ == "__main__":
    unittest.main()
