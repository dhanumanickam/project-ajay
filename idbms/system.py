"""
Cluster bootstrap and orchestration system for the IDBMS.
Instantiates multi-branch nodes, wires RPC, catalog, transaction manager, and query engine.
"""

import os
import shutil
from typing import Dict
from idbms.catalog.global_catalog import GlobalCatalog
from idbms.node.branch_node import BranchNode
from idbms.network.network_simulator import NetworkSimulator
from idbms.network.rpc_client import RPCClient
from idbms.common.wal import WALManager
from idbms.transaction.coordinator_2pc import Coordinator2PC
from idbms.transaction.transaction_manager import DistributedTransactionManager
from idbms.replication.replication_manager import ReplicationManager
from idbms.query.query_executor import DistributedQueryExecutor

class DistributedDatabaseCluster:
    """
    Main cluster coordinator holding references to all distributed components.
    """
    def __init__(self, data_root: str = "data/nodes", reset_data: bool = False):
        self.data_root = data_root
        os.makedirs(data_root, exist_ok=True)

        # 1. Global Catalog
        self.catalog = GlobalCatalog()

        # 2. Network Simulator & RPC Client
        self.net_sim = NetworkSimulator()
        self.rpc_client = RPCClient(self.net_sim)

        # 3. Instantiate Branch Nodes
        self.nodes: Dict[str, BranchNode] = {}
        for nid, info in self.catalog.nodes.items():
            node = BranchNode(node_info=info, base_data_dir=self.data_root)
            if reset_data:
                node.storage.clear()
                node.wal.clear()
            self.nodes[nid] = node
            self.rpc_client.register_node_instance(nid, node)

        # 4. Coordinator WAL & 2PC Coordinator
        coord_dir = os.path.join(self.data_root, "coordinator_hq")
        self.coord_wal = WALManager(log_dir=coord_dir, node_id="COORD_HQ")
        if reset_data:
            self.coord_wal.clear()
        self.coordinator_2pc = Coordinator2PC(
            coordinator_node_id="NODE_HQ",
            rpc_client=self.rpc_client,
            wal=self.coord_wal
        )

        # 5. Distributed Transaction Manager
        self.tx_mgr = DistributedTransactionManager(
            coordinator_node_id="NODE_HQ",
            catalog=self.catalog,
            rpc_client=self.rpc_client,
            coordinator_2pc=self.coordinator_2pc
        )

        # 6. Replication Manager
        self.replication_mgr = ReplicationManager(
            coordinator_id="NODE_HQ",
            catalog=self.catalog,
            rpc_client=self.rpc_client
        )

        # 7. Distributed Query Executor
        self.query_executor = DistributedQueryExecutor(
            coordinator_id="NODE_HQ",
            catalog=self.catalog,
            rpc_client=self.rpc_client,
            tx_mgr=self.tx_mgr
        )

        # 8. Seed sample data if empty
        self.seed_sample_enterprise_data()

    def seed_sample_enterprise_data(self):
        """Populates multi-branch enterprise initial datasets."""
        # Check if already seeded
        hq_node = self.nodes.get("NODE_HQ")
        if hq_node and hq_node.storage.get_record("branches", "BRANCH_HQ"):
            return

        # 1. Fully Replicated Branches Table
        branches_data = [
            {"branch_id": "BRANCH_HQ", "branch_name": "New York Global HQ", "city": "New York", "country": "USA", "currency": "USD"},
            {"branch_id": "BRANCH_LON", "branch_name": "London EMEA Branch", "city": "London", "country": "UK", "currency": "GBP"},
            {"branch_id": "BRANCH_TYO", "branch_name": "Tokyo APAC North", "city": "Tokyo", "country": "Japan", "currency": "JPY"},
            {"branch_id": "BRANCH_SGP", "branch_name": "Singapore APAC South", "city": "Singapore", "country": "Singapore", "currency": "SGD"},
        ]
        for b in branches_data:
            self.query_executor.execute_sql(
                f"INSERT INTO branches (branch_id, branch_name, city, country, currency) "
                f"VALUES ('{b['branch_id']}', '{b['branch_name']}', '{b['city']}', '{b['country']}', '{b['currency']}')"
            )

        # 2. Fully Replicated Exchange Rates Table
        rates = [
            {"currency_code": "USD", "usd_rate": 1.00, "last_updated": "2026-11-20"},
            {"currency_code": "GBP", "usd_rate": 1.30, "last_updated": "2026-11-20"},
            {"currency_code": "JPY", "usd_rate": 0.0067, "last_updated": "2026-11-20"},
            {"currency_code": "SGD", "usd_rate": 0.76, "last_updated": "2026-11-20"},
        ]
        for r in rates:
            self.query_executor.execute_sql(
                f"INSERT INTO exchange_rates (currency_code, usd_rate, last_updated) "
                f"VALUES ('{r['currency_code']}', {r['usd_rate']}, '{r['last_updated']}')"
            )

        # 3. Horizontally Partitioned Accounts
        accounts = [
            {"account_id": "ACC_HQ_01", "cust_id": "CUST_101", "branch_id": "BRANCH_HQ", "account_type": "CHECKING", "balance": 25000.0, "status": "ACTIVE"},
            {"account_id": "ACC_HQ_02", "cust_id": "CUST_102", "branch_id": "BRANCH_HQ", "account_type": "CORPORATE", "balance": 185000.0, "status": "ACTIVE"},
            {"account_id": "ACC_LON_01", "cust_id": "CUST_201", "branch_id": "BRANCH_LON", "account_type": "CHECKING", "balance": 14200.0, "status": "ACTIVE"},
            {"account_id": "ACC_LON_02", "cust_id": "CUST_202", "branch_id": "BRANCH_LON", "account_type": "SAVINGS", "balance": 46000.0, "status": "ACTIVE"},
            {"account_id": "ACC_TYO_01", "cust_id": "CUST_301", "branch_id": "BRANCH_TYO", "account_type": "CORPORATE", "balance": 3500000.0, "status": "ACTIVE"},
            {"account_id": "ACC_TYO_02", "cust_id": "CUST_302", "branch_id": "BRANCH_TYO", "account_type": "CHECKING", "balance": 820000.0, "status": "ACTIVE"},
            {"account_id": "ACC_SGP_01", "cust_id": "CUST_401", "branch_id": "BRANCH_SGP", "account_type": "CHECKING", "balance": 52000.0, "status": "ACTIVE"},
            {"account_id": "ACC_SGP_02", "cust_id": "CUST_402", "branch_id": "BRANCH_SGP", "account_type": "SAVINGS", "balance": 115000.0, "status": "ACTIVE"},
        ]
        for a in accounts:
            self.query_executor.execute_sql(
                f"INSERT INTO accounts (account_id, cust_id, branch_id, account_type, balance, status) "
                f"VALUES ('{a['account_id']}', '{a['cust_id']}', '{a['branch_id']}', '{a['account_type']}', {a['balance']}, '{a['status']}')"
            )

        # 4. Vertically Fragmented Customers (Basic profile + KYC)
        customers = [
            {"cust_id": "CUST_101", "name": "Alice Morgan", "branch_id": "BRANCH_HQ", "email": "alice@nycorp.com", "phone": "+1-212-555-0199", "credit_score": 780, "annual_income": 125000.0, "risk_tier": "LOW", "tax_id": "US-TAX-9821"},
            {"cust_id": "CUST_102", "name": "Sterling Capital", "branch_id": "BRANCH_HQ", "email": "finance@sterling.com", "phone": "+1-212-555-0811", "credit_score": 820, "annual_income": 2500000.0, "risk_tier": "LOW", "tax_id": "US-TAX-4412"},
            {"cust_id": "CUST_201", "name": "David Smith", "branch_id": "BRANCH_LON", "email": "david.smith@london.co.uk", "phone": "+44-20-7946-0912", "credit_score": 740, "annual_income": 85000.0, "risk_tier": "MEDIUM", "tax_id": "UK-NINO-771"},
            {"cust_id": "CUST_301", "name": "Kenji Sato", "branch_id": "BRANCH_TYO", "email": "kenji.sato@tokyo-tech.jp", "phone": "+81-3-5555-0143", "credit_score": 790, "annual_income": 9500000.0, "risk_tier": "LOW", "tax_id": "JP-MYNUM-331"},
            {"cust_id": "CUST_401", "name": "Mei Ling Tan", "branch_id": "BRANCH_SGP", "email": "meiling@sgp-invest.sg", "phone": "+65-6712-3344", "credit_score": 765, "annual_income": 140000.0, "risk_tier": "LOW", "tax_id": "SG-NRIC-S123"},
        ]
        for c in customers:
            self.query_executor.execute_sql(
                f"INSERT INTO customers (cust_id, name, branch_id, email, phone, credit_score, annual_income, risk_tier, tax_id) "
                f"VALUES ('{c['cust_id']}', '{c['name']}', '{c['branch_id']}', '{c['email']}', '{c['phone']}', {c['credit_score']}, {c['annual_income']}, '{c['risk_tier']}', '{c['tax_id']}')"
            )

    def get_cluster_status(self) -> Dict:
        return {
            "cluster_nodes": [n.get_status() for n in self.nodes.values()],
            "network_stats": self.net_sim.get_stats(),
            "active_transactions": len(self.tx_mgr.active_transactions),
            "completed_transactions": len(self.tx_mgr.completed_transactions),
            "catalog_summary": self.catalog.get_catalog_summary()
        }
