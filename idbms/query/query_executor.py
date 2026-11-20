"""
Distributed Query Executor.
Executes distributed query plans across nodes with parallel dispatch,
horizontal result union, vertical natural join reconstruction, and distributed aggregation.
"""

import time
import re
import concurrent.futures
from typing import Dict, Any, List, Optional, Tuple
from idbms.common.models import QueryResult, OperationType, DataOperation
from idbms.catalog.global_catalog import GlobalCatalog
from idbms.network.rpc_client import RPCClient
from idbms.query.sql_parser import SQLParser, ParsedQuery
from idbms.query.query_decomposer import QueryDecomposer, SubQueryTask
from idbms.query.query_optimizer import DistributedQueryOptimizer
from idbms.transaction.transaction_manager import DistributedTransactionManager

class DistributedQueryExecutor:
    """
    Coordinates distributed query execution across all cluster nodes.
    """
    def __init__(self, coordinator_id: str, catalog: GlobalCatalog, rpc_client: RPCClient, tx_mgr: DistributedTransactionManager):
        self.coordinator_id = coordinator_id
        self.catalog = catalog
        self.rpc_client = rpc_client
        self.tx_mgr = tx_mgr
        self.decomposer = QueryDecomposer(catalog)
        self.optimizer = DistributedQueryOptimizer()

    def execute_sql(self, sql_string: str) -> QueryResult:
        start_t = time.time()
        parsed = SQLParser.parse(sql_string)

        if parsed.command == "SELECT":
            return self._execute_select(parsed, start_t)
        elif parsed.command == "INSERT":
            return self._execute_insert(parsed, start_t)
        elif parsed.command == "UPDATE":
            return self._execute_update(parsed, start_t)
        elif parsed.command == "DELETE":
            return self._execute_delete(parsed, start_t)
        else:
            raise ValueError(f"Unknown command {parsed.command}")

    def _execute_select(self, query: ParsedQuery, start_t: float) -> QueryResult:
        # 1. Decompose
        decomposed = self.decomposer.decompose(query)

        # 2. Estimate table cardinalities from catalog/node stats
        cardinalities = {}
        for nid, node in self.rpc_client.node_registry.items():
            for t_name, count in node.storage.get_table_stats().items():
                cardinalities[t_name] = cardinalities.get(t_name, 0) + count

        # 3. Optimize plan
        opt_plan = self.optimizer.optimize_plan(decomposed, cardinalities)

        # 4. Execute sub-tasks in parallel across branch nodes
        base_tasks: List[SubQueryTask] = decomposed["base_tasks"]
        rows_by_task = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = {
                pool.submit(self._run_subquery_task, task): task
                for task in base_tasks
            }
            for fut in concurrent.futures.as_completed(futures):
                task_res = fut.result()
                rows_by_task.append((futures[fut], task_res))

        # 5. Merge results (Horizontal Union vs Vertical Join)
        merged_rows = []
        if decomposed["has_vertical_fragments"]:
            merged_rows = self._reconstruct_vertical_fragments(rows_by_task, query.table)
        else:
            for task, rows in rows_by_task:
                merged_rows.extend(rows)

        # 6. Perform Distributed Cross-Table Join if requested
        if query.join_table and query.join_condition:
            join_tasks: List[SubQueryTask] = decomposed["join_tasks"]
            join_rows = []
            for j_task in join_tasks:
                j_rows = self._run_subquery_task(j_task)
                join_rows.extend(j_rows)

            merged_rows = self._perform_join(merged_rows, join_rows, query.join_condition)

        # 7. Apply In-memory Group By & Aggregation if specified
        final_rows = self._apply_aggregation_and_projection(merged_rows, query.columns, query.group_by)

        # 8. Apply Ordering
        if query.order_by and final_rows and query.order_by in final_rows[0]:
            reverse = (query.order_direction == "DESC")
            final_rows.sort(key=lambda r: (r.get(query.order_by) is None, r.get(query.order_by)), reverse=reverse)

        # Clean internal metadata fields (_version, _created_at, etc.)
        cleaned_rows = []
        for r in final_rows:
            cleaned = {k: v for k, v in r.items() if not k.startswith("_")}
            cleaned_rows.append(cleaned)

        columns = list(cleaned_rows[0].keys()) if cleaned_rows else (query.columns if "*" not in query.columns else ["Result"])
        exec_time = round((time.time() - start_t) * 1000.0, 2)

        return QueryResult(
            columns=columns,
            rows=cleaned_rows,
            row_count=len(cleaned_rows),
            execution_time_ms=exec_time,
            nodes_queried=decomposed["target_nodes"],
            plan_explanation=opt_plan
        )

    def _run_subquery_task(self, task: SubQueryTask) -> List[Dict[str, Any]]:
        rows = self.rpc_client.call_scan(self.coordinator_id, task.node_id, task.table)
        # Apply local predicate pushdown filter
        filtered = []
        for row in rows:
            matches = True
            for k, expected_v in task.where_clause.items():
                if k in row and str(row[k]) != str(expected_v):
                    matches = False
                    break
            if matches:
                # Apply column projection pushdown
                if "*" in task.columns:
                    filtered.append(row)
                else:
                    proj = {c: row[c] for c in task.columns if c in row}
                    # Keep primary key
                    pk = self.catalog.schemas.get(task.table, {}).get("primary_key", "id")
                    if pk in row:
                        proj[pk] = row[pk]
                    filtered.append(proj)
        return filtered

    def _reconstruct_vertical_fragments(self, rows_by_task: List[Tuple[SubQueryTask, List[Dict[str, Any]]]], table: str) -> List[Dict[str, Any]]:
        """Reconstructs vertical fragments via Natural Join on primary key."""
        pk_field = self.catalog.schemas.get(table, {}).get("primary_key", "id")
        reconstructed: Dict[str, Dict[str, Any]] = {}

        for task, rows in rows_by_task:
            for r in rows:
                pk_val = str(r.get(pk_field))
                if pk_val not in reconstructed:
                    reconstructed[pk_val] = {}
                reconstructed[pk_val].update(r)

        return list(reconstructed.values())

    def _perform_join(self, left_rows: List[Dict[str, Any]], right_rows: List[Dict[str, Any]], join_cond: tuple) -> List[Dict[str, Any]]:
        left_col = join_cond[0].split(".")[-1]
        right_col = join_cond[1].split(".")[-1]

        # Hash join
        right_hash: Dict[Any, List[Dict[str, Any]]] = {}
        for r in right_rows:
            key = str(r.get(right_col))
            if key not in right_hash:
                right_hash[key] = []
            right_hash[key].append(r)

        joined = []
        for l in left_rows:
            key = str(l.get(left_col))
            if key in right_hash:
                for r in right_hash[key]:
                    combined = {**l, **r}
                    joined.append(combined)

        return joined

    def _apply_aggregation_and_projection(self, rows: List[Dict[str, Any]], columns: List[str], group_by: Optional[str]) -> List[Dict[str, Any]]:
        has_agg = any(re.search(r"(COUNT|SUM|AVG|MIN|MAX)\(", c, re.IGNORECASE) for c in columns)

        if not has_agg and not group_by:
            if "*" in columns:
                return rows
            return [{c: r.get(c) for c in columns if c in r} for r in rows]

        # Aggregation logic
        if group_by:
            groups: Dict[Any, List[Dict[str, Any]]] = {}
            for r in rows:
                g_key = r.get(group_by)
                if g_key not in groups:
                    groups[g_key] = []
                groups[g_key].append(r)

            aggregated_results = []
            for g_key, g_rows in groups.items():
                agg_row = {group_by: g_key}
                for col in columns:
                    if col == group_by:
                        continue
                    self._compute_agg_for_group(agg_row, col, g_rows)
                aggregated_results.append(agg_row)
            return aggregated_results
        else:
            # Global aggregation across all rows
            agg_row = {}
            for col in columns:
                self._compute_agg_for_group(agg_row, col, rows)
            return [agg_row]

    def _compute_agg_for_group(self, out_dict: dict, col_expr: str, group_rows: List[dict]):
        col_expr = col_expr.strip()
        m_count = re.match(r"COUNT\((.*?)\)", col_expr, re.IGNORECASE)
        m_sum = re.match(r"SUM\((.*?)\)", col_expr, re.IGNORECASE)
        m_avg = re.match(r"AVG\((.*?)\)", col_expr, re.IGNORECASE)
        m_min = re.match(r"MIN\((.*?)\)", col_expr, re.IGNORECASE)
        m_max = re.match(r"MAX\((.*?)\)", col_expr, re.IGNORECASE)

        if m_count:
            out_dict[col_expr] = len(group_rows)
        elif m_sum:
            attr = m_sum.group(1).strip()
            vals = [float(r[attr]) for r in group_rows if r.get(attr) is not None]
            out_dict[col_expr] = round(sum(vals), 2)
        elif m_avg:
            attr = m_avg.group(1).strip()
            vals = [float(r[attr]) for r in group_rows if r.get(attr) is not None]
            out_dict[col_expr] = round(sum(vals) / len(vals), 2) if vals else 0.0
        elif m_min:
            attr = m_min.group(1).strip()
            vals = [r[attr] for r in group_rows if r.get(attr) is not None]
            out_dict[col_expr] = min(vals) if vals else None
        elif m_max:
            attr = m_max.group(1).strip()
            vals = [r[attr] for r in group_rows if r.get(attr) is not None]
            out_dict[col_expr] = max(vals) if vals else None

    def _execute_insert(self, query: ParsedQuery, start_t: float) -> QueryResult:
        tx_id = self.tx_mgr.begin_transaction()
        try:
            pk_field = self.catalog.schemas.get(query.table, {}).get("primary_key", "id")
            pk_val = query.values.get(pk_field)
            if not pk_val:
                raise ValueError(f"Missing primary key '{pk_field}' in INSERT values.")

            self.tx_mgr.execute_operation(tx_id, DataOperation(
                op_type=OperationType.INSERT,
                table=query.table,
                key_field=pk_field,
                key_value=pk_val,
                data=query.values
            ))
            res = self.tx_mgr.commit_transaction(tx_id)
            exec_time = round((time.time() - start_t) * 1000.0, 2)
            return QueryResult(
                columns=["status", "tx_id", "message", "participants"],
                rows=[{
                    "status": "INSERT_COMMITTED",
                    "tx_id": tx_id,
                    "message": f"Successfully inserted into {query.table}",
                    "participants": ", ".join(res.get("participants", []))
                }],
                row_count=1,
                execution_time_ms=exec_time,
                nodes_queried=res.get("participants", []),
                plan_explanation={"trace": res.get("trace", [])}
            )
        except Exception as e:
            self.tx_mgr.abort_transaction(tx_id, str(e))
            raise e

    def _execute_update(self, query: ParsedQuery, start_t: float) -> QueryResult:
        tx_id = self.tx_mgr.begin_transaction()
        try:
            pk_field = self.catalog.schemas.get(query.table, {}).get("primary_key", "id")
            pk_val = query.where_clause.get(pk_field)
            if not pk_val:
                raise ValueError(f"UPDATE requires primary key filter '{pk_field}' in WHERE clause for atomic routing.")

            self.tx_mgr.execute_operation(tx_id, DataOperation(
                op_type=OperationType.UPDATE,
                table=query.table,
                key_field=pk_field,
                key_value=pk_val,
                data=query.updates
            ))
            res = self.tx_mgr.commit_transaction(tx_id)
            exec_time = round((time.time() - start_t) * 1000.0, 2)
            return QueryResult(
                columns=["status", "tx_id", "message"],
                rows=[{
                    "status": "UPDATE_COMMITTED",
                    "tx_id": tx_id,
                    "message": f"Successfully updated {query.table} record {pk_val}"
                }],
                row_count=1,
                execution_time_ms=exec_time,
                nodes_queried=res.get("participants", []),
                plan_explanation={"trace": res.get("trace", [])}
            )
        except Exception as e:
            self.tx_mgr.abort_transaction(tx_id, str(e))
            raise e

    def _execute_delete(self, query: ParsedQuery, start_t: float) -> QueryResult:
        tx_id = self.tx_mgr.begin_transaction()
        try:
            pk_field = self.catalog.schemas.get(query.table, {}).get("primary_key", "id")
            pk_val = query.where_clause.get(pk_field)
            if not pk_val:
                raise ValueError(f"DELETE requires primary key filter '{pk_field}' in WHERE clause.")

            self.tx_mgr.execute_operation(tx_id, DataOperation(
                op_type=OperationType.DELETE,
                table=query.table,
                key_field=pk_field,
                key_value=pk_val
            ))
            res = self.tx_mgr.commit_transaction(tx_id)
            exec_time = round((time.time() - start_t) * 1000.0, 2)
            return QueryResult(
                columns=["status", "tx_id", "message"],
                rows=[{
                    "status": "DELETE_COMMITTED",
                    "tx_id": tx_id,
                    "message": f"Successfully deleted from {query.table} record {pk_val}"
                }],
                row_count=1,
                execution_time_ms=exec_time,
                nodes_queried=res.get("participants", []),
                plan_explanation={"trace": res.get("trace", [])}
            )
        except Exception as e:
            self.tx_mgr.abort_transaction(tx_id, str(e))
            raise e
