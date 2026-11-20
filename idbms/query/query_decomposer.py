"""
Distributed Query Decomposer.
Performs data localization, fragment pruning based on predicates,
and predicate pushdown optimization.
"""

from typing import Dict, Any, List, Optional
from idbms.catalog.global_catalog import GlobalCatalog
from idbms.catalog.fragmenter import FragmentRule
from idbms.common.models import FragmentationType
from idbms.query.sql_parser import ParsedQuery

class SubQueryTask:
    def __init__(self, node_id: str, fragment_id: str, table: str, columns: List[str], where_clause: Dict[str, Any], is_vertical: bool = False):
        self.node_id = node_id
        self.fragment_id = fragment_id
        self.table = table
        self.columns = columns
        self.where_clause = where_clause
        self.is_vertical = is_vertical

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "fragment_id": self.fragment_id,
            "table": self.table,
            "columns": self.columns,
            "where_clause": self.where_clause,
            "is_vertical": self.is_vertical
        }

class QueryDecomposer:
    """Decomposes global SQL queries into localized sub-queries targeted at specific branch nodes."""

    def __init__(self, catalog: GlobalCatalog):
        self.catalog = catalog

    def decompose(self, query: ParsedQuery) -> Dict[str, Any]:
        """
        Decomposes global query into subquery tasks with fragment pruning and localization.
        """
        needed_base_cols = list(query.columns)
        if query.join_condition and "*" not in needed_base_cols:
            left_col = query.join_condition[0].split(".")[-1]
            if left_col not in needed_base_cols:
                needed_base_cols.append(left_col)

        base_tasks = self._localize_table(query.table, needed_base_cols, query.where_clause)
        join_tasks = []
        if query.join_table:
            join_tasks = self._localize_table(query.join_table, ["*"], query.where_clause)

        all_target_nodes = list(set([t.node_id for t in base_tasks + join_tasks]))
        pruned_nodes = [nid for nid in self.catalog.nodes.keys() if nid not in all_target_nodes]

        return {
            "base_table": query.table,
            "base_tasks": base_tasks,
            "join_table": query.join_table,
            "join_tasks": join_tasks,
            "join_condition": query.join_condition,
            "target_nodes": all_target_nodes,
            "pruned_nodes": pruned_nodes,
            "has_vertical_fragments": any(t.is_vertical for t in base_tasks),
            "group_by": query.group_by,
            "order_by": query.order_by,
            "order_direction": query.order_direction
        }

    def _localize_table(self, table_name: str, requested_columns: List[str], where_clause: Dict[str, Any]) -> List[SubQueryTask]:
        t = table_name.lower()
        rules = self.catalog.fragment_rules.get(t, [])

        # Fully replicated table: send to local HQ node or single available node
        if t in self.catalog.replica_mappings and self.catalog.replica_mappings[t]["strategy"] == "FULL":
            return [SubQueryTask(
                node_id="NODE_HQ",
                fragment_id=f"{t}_replicated",
                table=t,
                columns=requested_columns,
                where_clause=where_clause
            )]

        if not rules:
            # Unfragmented default
            return [SubQueryTask(
                node_id="NODE_HQ",
                fragment_id=f"{t}_default",
                table=t,
                columns=requested_columns,
                where_clause=where_clause
            )]

        tasks = []
        for rule in rules:
            if rule.frag_type == FragmentationType.HORIZONTAL:
                # Prune if WHERE clause contradicts horizontal predicate
                if self._can_prune_horizontal(rule.predicate, where_clause):
                    continue
                tasks.append(SubQueryTask(
                    node_id=rule.assigned_node,
                    fragment_id=rule.frag_id,
                    table=t,
                    columns=requested_columns,
                    where_clause=where_clause
                ))

            elif rule.frag_type == FragmentationType.VERTICAL:
                # Vertical fragment includes primary key plus projected columns
                pk = self.catalog.schemas.get(t, {}).get("primary_key", "id")
                # Check if this vertical fragment holds any requested column
                has_requested_col = False
                if "*" in requested_columns:
                    has_requested_col = True
                else:
                    needed = set(requested_columns).union(set(where_clause.keys()))
                    has_requested_col = bool(needed.intersection(set(rule.attributes)))

                if has_requested_col:
                    tasks.append(SubQueryTask(
                        node_id=rule.assigned_node,
                        fragment_id=rule.frag_id,
                        table=t,
                        columns=rule.attributes if "*" in requested_columns else [c for c in requested_columns if c in rule.attributes] + [pk],
                        where_clause={k: v for k, v in where_clause.items() if k in rule.attributes},
                        is_vertical=True
                    ))

            elif rule.frag_type == FragmentationType.HYBRID:
                if not self._can_prune_horizontal(rule.predicate, where_clause):
                    tasks.append(SubQueryTask(
                        node_id=rule.assigned_node,
                        fragment_id=rule.frag_id,
                        table=t,
                        columns=requested_columns,
                        where_clause=where_clause,
                        is_vertical=False
                    ))

        return tasks

    def _can_prune_horizontal(self, frag_predicate: Dict[str, Any], query_where: Dict[str, Any]) -> bool:
        """Returns True if the fragment's predicate conflicts with the query's WHERE clause."""
        if not frag_predicate or not query_where:
            return False
        for k, frag_val in frag_predicate.items():
            if k in query_where:
                query_val = query_where[k]
                if str(frag_val) != str(query_val):
                    return True # Fragment pruned!
        return False
