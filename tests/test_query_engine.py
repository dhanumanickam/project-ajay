"""
Unit tests for Distributed Query Engine: parsing, localization,
Semi-Join optimization, and distributed joins.
"""

import unittest
from idbms.system import DistributedDatabaseCluster
from idbms.query.sql_parser import SQLParser

class TestQueryEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cluster = DistributedDatabaseCluster(reset_data=True)

    def test_sql_parser_select_with_join_and_where(self):
        sql = "SELECT accounts.account_id, balance FROM accounts JOIN branches ON accounts.branch_id = branches.branch_id WHERE branch_id = 'BRANCH_LON' ORDER BY balance DESC"
        parsed = SQLParser.parse(sql)

        self.assertEqual(parsed.command, "SELECT")
        self.assertEqual(parsed.table, "accounts")
        self.assertEqual(parsed.join_table, "branches")
        self.assertEqual(parsed.where_clause.get("branch_id"), "BRANCH_LON")
        self.assertEqual(parsed.order_by, "balance")
        self.assertEqual(parsed.order_direction, "DESC")

    def test_distributed_cross_table_join(self):
        """Cross-table distributed join between accounts and branches."""
        sql = "SELECT account_id, branch_name, balance, currency FROM accounts JOIN branches ON accounts.branch_id = branches.branch_id WHERE branch_id = 'BRANCH_LON'"
        res = self.cluster.query_executor.execute_sql(sql)

        self.assertGreater(len(res.rows), 0)
        sample = res.rows[0]
        self.assertIn("branch_name", sample)
        self.assertIn("currency", sample)
        self.assertEqual(sample["currency"], "GBP")

    def test_distributed_aggregations(self):
        """Distributed COUNT and SUM grouped by branch_id."""
        sql = "SELECT branch_id, COUNT(account_id), SUM(balance) FROM accounts GROUP BY branch_id ORDER BY branch_id ASC"
        res = self.cluster.query_executor.execute_sql(sql)

        self.assertEqual(len(res.rows), 4) # 4 branches: HQ, LON, TYO, SGP
        branches = [r["branch_id"] for r in res.rows]
        self.assertIn("BRANCH_HQ", branches)
        self.assertIn("BRANCH_LON", branches)

    def test_semijoin_cost_optimizer(self):
        """Verify cost optimizer selects semi-join or broadcast strategy appropriately."""
        parsed = SQLParser.parse("SELECT * FROM accounts JOIN branches ON accounts.branch_id = branches.branch_id")
        decomposed = self.cluster.query_executor.decomposer.decompose(parsed)
        opt_plan = self.cluster.query_executor.optimizer.optimize_plan(decomposed, {"accounts": 1000, "branches": 4})

        # Since branches is fully replicated, Broadcast Join should be chosen
        self.assertEqual(opt_plan["join_strategy"], "BROADCAST_JOIN")
        broadcast_step = next(s for s in opt_plan["plan_steps"] if s["type"] == "BROADCAST_JOIN")
        self.assertEqual(broadcast_step["network_bytes"], 0)

if __name__ == "__main__":
    unittest.main()
