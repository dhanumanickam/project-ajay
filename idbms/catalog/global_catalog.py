"""
Global Catalog (Data Dictionary) managing distributed schemas, fragmentation rules,
replica mappings, and cluster node directory.
"""

import threading
from typing import Dict, Any, List, Optional, Tuple
from idbms.common.models import NodeInfo, FragmentationType, ReplicationStrategy
from idbms.catalog.fragmenter import FragmentRule

class GlobalCatalog:
    """
    Central or replicated metadata directory of the distributed database system.
    Maintains schemas, fragment directories, replica locations, and node statuses.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self.nodes: Dict[str, NodeInfo] = {}
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.fragment_rules: Dict[str, List[FragmentRule]] = {}
        self.replica_mappings: Dict[str, Dict[str, Any]] = {}  # table/fragment -> {strategy, replica_nodes, quorum}
        self._init_default_cluster()

    def _init_default_cluster(self):
        """Initializes default multi-branch enterprise topology."""
        # 1. Register Multi-Branch Nodes: HQ (New York), London, Tokyo, Singapore
        self.register_node(NodeInfo(
            node_id="NODE_HQ",
            name="HQ Data Center (New York)",
            host="127.0.0.1",
            port=8000,
            region="US-East",
            is_coordinator=True,
            simulated_latency_ms=2.0
        ))
        self.register_node(NodeInfo(
            node_id="NODE_LON",
            name="London Branch",
            host="127.0.0.1",
            port=8001,
            region="Europe-West",
            simulated_latency_ms=35.0
        ))
        self.register_node(NodeInfo(
            node_id="NODE_TYO",
            name="Tokyo Branch",
            host="127.0.0.1",
            port=8002,
            region="Asia-East",
            simulated_latency_ms=65.0
        ))
        self.register_node(NodeInfo(
            node_id="NODE_SGP",
            name="Singapore Branch",
            host="127.0.0.1",
            port=8003,
            region="Asia-Southeast",
            simulated_latency_ms=75.0
        ))

        # 2. Table Schemas
        # Dimension table: branches (Fully replicated)
        self.register_table("branches", {
            "primary_key": "branch_id",
            "columns": {
                "branch_id": "TEXT",
                "branch_name": "TEXT",
                "city": "TEXT",
                "country": "TEXT",
                "currency": "TEXT"
            }
        })
        self.set_replication_strategy("branches", ReplicationStrategy.FULL, ["NODE_HQ", "NODE_LON", "NODE_TYO", "NODE_SGP"])

        # Reference table: exchange_rates (Fully replicated)
        self.register_table("exchange_rates", {
            "primary_key": "currency_code",
            "columns": {
                "currency_code": "TEXT",
                "usd_rate": "REAL",
                "last_updated": "TEXT"
            }
        })
        self.set_replication_strategy("exchange_rates", ReplicationStrategy.FULL, ["NODE_HQ", "NODE_LON", "NODE_TYO", "NODE_SGP"])

        # Operational Table: accounts (Horizontal Fragmentation by branch_id)
        self.register_table("accounts", {
            "primary_key": "account_id",
            "columns": {
                "account_id": "TEXT",
                "cust_id": "TEXT",
                "branch_id": "TEXT",
                "account_type": "TEXT",
                "balance": "REAL",
                "status": "TEXT"
            }
        })
        # Horizontal fragments for accounts
        self.add_fragment_rule(FragmentRule(
            table_name="accounts",
            frag_type=FragmentationType.HORIZONTAL,
            frag_id="accounts_hq",
            assigned_node="NODE_HQ",
            predicate={"branch_id": "BRANCH_HQ"}
        ))
        self.add_fragment_rule(FragmentRule(
            table_name="accounts",
            frag_type=FragmentationType.HORIZONTAL,
            frag_id="accounts_lon",
            assigned_node="NODE_LON",
            predicate={"branch_id": "BRANCH_LON"}
        ))
        self.add_fragment_rule(FragmentRule(
            table_name="accounts",
            frag_type=FragmentationType.HORIZONTAL,
            frag_id="accounts_tyo",
            assigned_node="NODE_TYO",
            predicate={"branch_id": "BRANCH_TYO"}
        ))
        self.add_fragment_rule(FragmentRule(
            table_name="accounts",
            frag_type=FragmentationType.HORIZONTAL,
            frag_id="accounts_sgp",
            assigned_node="NODE_SGP",
            predicate={"branch_id": "BRANCH_SGP"}
        ))

        # Operational Table: transactions (Derived horizontal fragmentation by branch_id)
        self.register_table("transactions", {
            "primary_key": "tx_id",
            "columns": {
                "tx_id": "TEXT",
                "from_account": "TEXT",
                "to_account": "TEXT",
                "branch_id": "TEXT",
                "amount": "REAL",
                "tx_type": "TEXT",
                "timestamp": "REAL",
                "status": "TEXT"
            }
        })
        self.add_fragment_rule(FragmentRule(
            table_name="transactions",
            frag_type=FragmentationType.HORIZONTAL,
            frag_id="trans_hq",
            assigned_node="NODE_HQ",
            predicate={"branch_id": "BRANCH_HQ"}
        ))
        self.add_fragment_rule(FragmentRule(
            table_name="transactions",
            frag_type=FragmentationType.HORIZONTAL,
            frag_id="trans_lon",
            assigned_node="NODE_LON",
            predicate={"branch_id": "BRANCH_LON"}
        ))
        self.add_fragment_rule(FragmentRule(
            table_name="transactions",
            frag_type=FragmentationType.HORIZONTAL,
            frag_id="trans_tyo",
            assigned_node="NODE_TYO",
            predicate={"branch_id": "BRANCH_TYO"}
        ))
        self.add_fragment_rule(FragmentRule(
            table_name="transactions",
            frag_type=FragmentationType.HORIZONTAL,
            frag_id="trans_sgp",
            assigned_node="NODE_SGP",
            predicate={"branch_id": "BRANCH_SGP"}
        ))

        # Vertical Fragmentation: customers -> basic profile on local branch, KYC/financial on HQ with Quorum replication
        self.register_table("customers", {
            "primary_key": "cust_id",
            "columns": {
                "cust_id": "TEXT",
                "name": "TEXT",
                "branch_id": "TEXT",
                "email": "TEXT",
                "phone": "TEXT",
                "credit_score": "INTEGER",
                "annual_income": "REAL",
                "risk_tier": "TEXT",
                "tax_id": "TEXT"
            }
        })
        # Customer basic attributes
        self.add_fragment_rule(FragmentRule(
            table_name="customers",
            frag_type=FragmentationType.VERTICAL,
            frag_id="cust_basic",
            assigned_node="NODE_LON", # Also on other nodes
            attributes=["cust_id", "name", "branch_id", "email", "phone"]
        ))
        # Customer KYC and credit profile
        self.add_fragment_rule(FragmentRule(
            table_name="customers",
            frag_type=FragmentationType.VERTICAL,
            frag_id="cust_kyc",
            assigned_node="NODE_HQ",
            attributes=["cust_id", "credit_score", "annual_income", "risk_tier", "tax_id"]
        ))
        # Quorum replication on cust_kyc across HQ, LON, TYO
        self.set_replication_strategy("cust_kyc", ReplicationStrategy.QUORUM, ["NODE_HQ", "NODE_LON", "NODE_TYO"], quorum_n=3, quorum_r=2, quorum_w=2)

    def register_node(self, node: NodeInfo):
        with self._lock:
            self.nodes[node.node_id] = node

    def update_node_status(self, node_id: str, status: str):
        with self._lock:
            if node_id in self.nodes:
                self.nodes[node_id].status = status

    def register_table(self, table_name: str, schema: Dict[str, Any]):
        with self._lock:
            self.schemas[table_name.lower()] = schema

    def add_fragment_rule(self, rule: FragmentRule):
        with self._lock:
            t = rule.table_name.lower()
            if t not in self.fragment_rules:
                self.fragment_rules[t] = []
            self.fragment_rules[t].append(rule)

    def set_replication_strategy(self, target_name: str, strategy: ReplicationStrategy,
                                 replica_nodes: List[str], quorum_n: int = 1, quorum_r: int = 1, quorum_w: int = 1):
        with self._lock:
            self.replica_mappings[target_name.lower()] = {
                "strategy": strategy.value,
                "nodes": replica_nodes,
                "n": quorum_n or len(replica_nodes),
                "r": quorum_r,
                "w": quorum_w
            }

    def get_target_nodes_for_insert(self, table_name: str, record: Dict[str, Any]) -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Determines which node(s) and fragment(s) an inserted record should be routed to,
        along with the projected record attributes for vertical/hybrid fragments.
        Returns: List of (node_id, fragment_id, record_slice)
        """
        table_name = table_name.lower()
        results = []

        # Check full replication
        if table_name in self.replica_mappings and self.replica_mappings[table_name]["strategy"] == ReplicationStrategy.FULL.value:
            for nid in self.replica_mappings[table_name]["nodes"]:
                results.append((nid, f"{table_name}_full", record))
            return results

        rules = self.fragment_rules.get(table_name, [])
        if not rules:
            # Default to coordinator node
            return [("NODE_HQ", f"{table_name}_default", record)]

        pk_field = self.schemas.get(table_name, {}).get("primary_key", "id")

        for rule in rules:
            if rule.frag_type == FragmentationType.HORIZONTAL:
                if rule.matches_horizontal_predicate(record):
                    results.append((rule.assigned_node, rule.frag_id, record))
            elif rule.frag_type == FragmentationType.VERTICAL:
                sliced = rule.project_vertical_attributes(record, pk_field)
                results.append((rule.assigned_node, rule.frag_id, sliced))
            elif rule.frag_type == FragmentationType.HYBRID:
                if rule.matches_horizontal_predicate(record):
                    sliced = rule.project_vertical_attributes(record, pk_field)
                    results.append((rule.assigned_node, rule.frag_id, sliced))

        return results

    def get_pruned_nodes_for_query(self, table_name: str, where_clause: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Data Localization & Pruning:
        Determines which nodes must be contacted to satisfy a query on table_name with WHERE conditions.
        If where_clause filters on partitioning attribute (e.g. branch_id = 'BRANCH_LON'),
        all other branch fragments are safely pruned!
        """
        table_name = table_name.lower()

        # If table is fully replicated, query the nearest online node (or local HQ)
        if table_name in self.replica_mappings and self.replica_mappings[table_name]["strategy"] == ReplicationStrategy.FULL.value:
            for nid in ["NODE_HQ", "NODE_LON", "NODE_TYO", "NODE_SGP"]:
                if nid in self.nodes and self.nodes[nid].status == "ONLINE":
                    return [nid]

        rules = self.fragment_rules.get(table_name, [])
        if not rules:
            return ["NODE_HQ"]

        matched_nodes = set()
        where_clause = where_clause or {}

        for rule in rules:
            if rule.frag_type == FragmentationType.HORIZONTAL:
                if not where_clause:
                    matched_nodes.add(rule.assigned_node)
                else:
                    # Check predicate overlap
                    conflict = False
                    for pred_key, pred_val in rule.predicate.items():
                        if pred_key in where_clause:
                            query_val = where_clause[pred_key]
                            if str(query_val) != str(pred_val):
                                conflict = True
                                break
                    if not conflict:
                        matched_nodes.add(rule.assigned_node)
            elif rule.frag_type == FragmentationType.VERTICAL:
                # Vertical fragments must be joined to reconstruct full record unless projection is subset
                matched_nodes.add(rule.assigned_node)
            elif rule.frag_type == FragmentationType.HYBRID:
                matched_nodes.add(rule.assigned_node)

        return list(matched_nodes)

    def get_catalog_summary(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "nodes": {nid: n.model_dump() for nid, n in self.nodes.items()},
                "schemas": self.schemas,
                "fragments": {
                    t: [r.to_dict() for r in rules]
                    for t, rules in self.fragment_rules.items()
                },
                "replication": self.replica_mappings
            }
