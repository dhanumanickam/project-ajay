"""
Distributed Cost-Based Query Optimizer (CBO) and Semi-Join Reducer.
Evaluates Direct Ship vs. Semi-Join (Bernstein's algorithm) vs. Broadcast Join strategies.
"""

from typing import Dict, Any, List, Optional, Tuple
from idbms.query.query_decomposer import SubQueryTask

class DistributedQueryOptimizer:
    """
    Cost-Based Optimizer evaluating CPU, I/O, and Network communication costs.
    Applies Semi-Join reductions when beneficial to minimize cross-site data shipping.
    """
    C_CPU = 0.001   # ms per tuple
    C_IO = 0.01     # ms per page
    C_NET_KB = 0.05 # ms per KB
    PAGE_SIZE = 64  # tuples per page

    def optimize_plan(self, decomposed_query: Dict[str, Any], table_cardinalities: Dict[str, int]) -> Dict[str, Any]:
        base_tasks: List[SubQueryTask] = decomposed_query["base_tasks"]
        join_tasks: List[SubQueryTask] = decomposed_query["join_tasks"]
        join_cond = decomposed_query.get("join_condition")

        plan_steps = []
        total_estimated_cost = 0.0
        total_estimated_net_bytes = 0

        # Step 1: Scan and filter local base fragments
        for task in base_tasks:
            est_rows = table_cardinalities.get(task.table, 50)
            if task.where_clause:
                est_rows = max(1, int(est_rows * 0.2)) # Predicate pushdown selectivity factor
            cpu_cost = est_rows * self.C_CPU
            io_cost = (est_rows / self.PAGE_SIZE) * self.C_IO
            row_size = len(task.columns) * 32
            net_bytes = est_rows * row_size
            net_cost = (net_bytes / 1024.0) * self.C_NET_KB
            step_cost = round(cpu_cost + io_cost + net_cost, 3)

            total_estimated_cost += step_cost
            total_estimated_net_bytes += net_bytes

            plan_steps.append({
                "step": f"FilterScan_{task.fragment_id}",
                "node": task.node_id,
                "table": task.table,
                "type": "LOCAL_SCAN_AND_FILTER",
                "predicates": task.where_clause,
                "projected_columns": task.columns,
                "estimated_rows": est_rows,
                "estimated_bytes": net_bytes,
                "cost_ms": step_cost
            })

        # Step 2: Distributed Join Optimization (if JOIN is present)
        join_strategy = "NONE"
        if join_tasks and join_cond:
            join_strategy, join_plan, join_cost, join_bytes = self._select_best_join_strategy(
                base_tasks, join_tasks, join_cond, table_cardinalities
            )
            total_estimated_cost += join_cost
            total_estimated_net_bytes += join_bytes
            plan_steps.extend(join_plan)

        # Step 3: Aggregation and Sorting at Coordinator
        if decomposed_query.get("group_by") or decomposed_query.get("order_by"):
            coord_cost = 0.15
            total_estimated_cost += coord_cost
            plan_steps.append({
                "step": "Coordinator_PostProcess",
                "node": "NODE_HQ",
                "type": "AGGREGATION_AND_SORT",
                "group_by": decomposed_query.get("group_by"),
                "order_by": decomposed_query.get("order_by"),
                "direction": decomposed_query.get("order_direction"),
                "cost_ms": coord_cost
            })

        return {
            "join_strategy": join_strategy,
            "target_nodes": decomposed_query["target_nodes"],
            "pruned_nodes": decomposed_query["pruned_nodes"],
            "total_estimated_cost_ms": round(total_estimated_cost, 2),
            "total_estimated_network_bytes": total_estimated_net_bytes,
            "plan_steps": plan_steps
        }

    def _select_best_join_strategy(
        self,
        base_tasks: List[SubQueryTask],
        join_tasks: List[SubQueryTask],
        join_cond: tuple,
        cardinalities: Dict[str, int]
    ) -> Tuple[str, List[Dict[str, Any]], float, int]:
        """
        Compares Direct Ship Join vs. Semi-Join Reduction vs. Broadcast Join.
        Selects strategy with lowest network cost.
        """
        t1 = base_tasks[0].table
        t2 = join_tasks[0].table

        # Check if t2 is fully replicated dimension table
        if any(t.fragment_id.endswith("_replicated") for t in join_tasks):
            return "BROADCAST_JOIN", [{
                "step": f"BroadcastJoin_{t1}_{t2}",
                "node": "LOCAL_NODES",
                "type": "BROADCAST_JOIN",
                "description": f"Dimension table '{t2}' is fully replicated locally; zero network transfer required.",
                "cost_ms": 0.05,
                "network_bytes": 0
            }], 0.05, 0

        # Estimate cardinalities and sizes
        card_t1 = cardinalities.get(t1, 100)
        card_t2 = cardinalities.get(t2, 100)
        row_size_t1 = 120
        row_size_t2 = 120
        join_key_size = 16

        # Cost 1: Direct Ship (Ship smaller table to larger table's node)
        direct_ship_bytes = min(card_t1 * row_size_t1, card_t2 * row_size_t2)
        direct_ship_cost = round((direct_ship_bytes / 1024.0) * self.C_NET_KB + 2.0, 3)

        # Cost 2: Semi-Join (Ship projection of join keys -> filter remote -> ship reduced rows)
        selectivity = 0.25 # Semi-join reduction factor
        semijoin_keys_bytes = card_t1 * join_key_size
        semijoin_reduced_bytes = int(card_t2 * selectivity * row_size_t2)
        semijoin_total_bytes = semijoin_keys_bytes + semijoin_reduced_bytes
        semijoin_cost = round((semijoin_total_bytes / 1024.0) * self.C_NET_KB + 2.5, 3)

        if semijoin_total_bytes < direct_ship_bytes:
            # Semi-join reduction is superior
            plan = [
                {
                    "step": "SemiJoin_ProjectKeys",
                    "node": base_tasks[0].node_id,
                    "type": "SEMIJOIN_PROJECTION",
                    "description": f"Project unique join key '{join_cond[0]}' from {t1} ({semijoin_keys_bytes} bytes).",
                    "cost_ms": 0.4,
                    "network_bytes": semijoin_keys_bytes
                },
                {
                    "step": "SemiJoin_ReduceRemote",
                    "node": join_tasks[0].node_id,
                    "type": "SEMIJOIN_REDUCTION",
                    "description": f"Filter {t2} using join keys (reduces size from {card_t2 * row_size_t2} to {semijoin_reduced_bytes} bytes).",
                    "cost_ms": 0.6,
                    "network_bytes": semijoin_reduced_bytes
                },
                {
                    "step": "SemiJoin_FinalMerge",
                    "node": "NODE_HQ",
                    "type": "SEMIJOIN_FINAL_JOIN",
                    "description": f"Execute final join of {t1} with reduced {t2}.",
                    "cost_ms": 0.8,
                    "network_bytes": 0
                }
            ]
            return "SEMI_JOIN_REDUCTION", plan, semijoin_cost, semijoin_total_bytes
        else:
            plan = [{
                "step": f"DirectShipJoin_{t1}_{t2}",
                "node": "NODE_HQ",
                "type": "DIRECT_SHIP_JOIN",
                "description": f"Ship smaller relation to coordinator ({direct_ship_bytes} bytes).",
                "cost_ms": direct_ship_cost,
                "network_bytes": direct_ship_bytes
            }]
            return "DIRECT_SHIP", plan, direct_ship_cost, direct_ship_bytes
