"""
Lightweight SQL Parser supporting SELECT, INSERT, UPDATE, DELETE,
cross-table JOINs, WHERE filtering, and distributed aggregates.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

class ParsedQuery:
    def __init__(
        self,
        command: str,
        table: str,
        columns: List[str] = None,
        join_table: Optional[str] = None,
        join_condition: Optional[Tuple[str, str]] = None,
        where_clause: Optional[Dict[str, Any]] = None,
        raw_where_text: Optional[str] = None,
        values: Optional[Dict[str, Any]] = None,
        updates: Optional[Dict[str, Any]] = None,
        group_by: Optional[str] = None,
        order_by: Optional[str] = None,
        order_direction: str = "ASC"
    ):
        self.command = command.upper()
        self.table = table.lower()
        self.columns = columns or ["*"]
        self.join_table = join_table.lower() if join_table else None
        self.join_condition = join_condition
        self.where_clause = where_clause or {}
        self.raw_where_text = raw_where_text
        self.values = values or {}
        self.updates = updates or {}
        self.group_by = group_by
        self.order_by = order_by
        self.order_direction = order_direction.upper()

class SQLParser:
    """Parses SQL queries into structured representation for distributed decomposition."""

    @staticmethod
    def parse(sql: str) -> ParsedQuery:
        sql = sql.strip().rstrip(";")
        tokens = sql.split()
        if not tokens:
            raise ValueError("Empty SQL query")

        cmd = tokens[0].upper()

        if cmd == "SELECT":
            return SQLParser._parse_select(sql)
        elif cmd == "INSERT":
            return SQLParser._parse_insert(sql)
        elif cmd == "UPDATE":
            return SQLParser._parse_update(sql)
        elif cmd == "DELETE":
            return SQLParser._parse_delete(sql)
        else:
            raise ValueError(f"Unsupported SQL command: {cmd}")

    @staticmethod
    def _parse_select(sql: str) -> ParsedQuery:
        # SELECT col1, col2 FROM table [JOIN table2 ON t1.id = t2.id] [WHERE ...] [GROUP BY col]
        select_match = re.search(r"SELECT\s+(.+?)\s+FROM\s+([a-zA-Z0-9_]+)", sql, re.IGNORECASE)
        if not select_match:
            raise ValueError(f"Malformed SELECT query: {sql}")

        cols_str = select_match.group(1).strip()
        table_name = select_match.group(2).strip()

        columns = [c.strip() for c in cols_str.split(",")]

        # JOIN
        join_table = None
        join_cond = None
        join_match = re.search(r"JOIN\s+([a-zA-Z0-9_]+)\s+ON\s+([a-zA-Z0-9_.]+)\s*=\s*([a-zA-Z0-9_.]+)", sql, re.IGNORECASE)
        if join_match:
            join_table = join_match.group(1).strip()
            join_cond = (join_match.group(2).strip(), join_match.group(3).strip())

        # WHERE
        where_clause = {}
        raw_where = None
        where_match = re.search(r"WHERE\s+(.+?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|$)", sql, re.IGNORECASE)
        if where_match:
            raw_where = where_match.group(1).strip()
            # Parse simple 'col = val' expressions separated by AND
            conditions = re.split(r"\s+AND\s+", raw_where, flags=re.IGNORECASE)
            for cond in conditions:
                m_eq = re.match(r"([a-zA-Z0-9_.]+)\s*=\s*['\"]?([^'\"]+)['\"]?", cond.strip())
                if m_eq:
                    col_name = m_eq.group(1).strip().split(".")[-1] # Remove table prefix if present
                    val = m_eq.group(2).strip()
                    # Type conversion
                    try:
                        val = float(val) if "." in val else int(val)
                    except ValueError:
                        pass
                    where_clause[col_name] = val

        # GROUP BY
        group_by = None
        group_match = re.search(r"GROUP\s+BY\s+([a-zA-Z0-9_]+)", sql, re.IGNORECASE)
        if group_match:
            group_by = group_match.group(1).strip()

        # ORDER BY
        order_by = None
        direction = "ASC"
        order_match = re.search(r"ORDER\s+BY\s+([a-zA-Z0-9_]+)(?:\s+(ASC|DESC))?", sql, re.IGNORECASE)
        if order_match:
            order_by = order_match.group(1).strip()
            if order_match.group(2):
                direction = order_match.group(2).upper()

        return ParsedQuery(
            command="SELECT",
            table=table_name,
            columns=columns,
            join_table=join_table,
            join_condition=join_cond,
            where_clause=where_clause,
            raw_where_text=raw_where,
            group_by=group_by,
            order_by=order_by,
            order_direction=direction
        )

    @staticmethod
    def _parse_insert(sql: str) -> ParsedQuery:
        # INSERT INTO table (c1, c2) VALUES (v1, v2)
        match = re.search(r"INSERT\s+INTO\s+([a-zA-Z0-9_]+)\s*\((.+?)\)\s*VALUES\s*\((.+?)\)", sql, re.IGNORECASE)
        if not match:
            raise ValueError(f"Malformed INSERT statement: {sql}")
        table = match.group(1).strip()
        cols = [c.strip() for c in match.group(2).split(",")]
        raw_vals = [v.strip().strip("'\"") for v in match.group(3).split(",")]

        values = {}
        for c, v in zip(cols, raw_vals):
            try:
                v = float(v) if "." in v else int(v)
            except ValueError:
                pass
            values[c] = v

        return ParsedQuery(command="INSERT", table=table, values=values)

    @staticmethod
    def _parse_update(sql: str) -> ParsedQuery:
        # UPDATE table SET col1 = val1, col2 = val2 WHERE id = val
        match = re.search(r"UPDATE\s+([a-zA-Z0-9_]+)\s+SET\s+(.+?)(?:\s+WHERE\s+(.+))?$", sql, re.IGNORECASE)
        if not match:
            raise ValueError(f"Malformed UPDATE statement: {sql}")
        table = match.group(1).strip()
        set_str = match.group(2).strip()
        where_str = match.group(3).strip() if match.group(3) else ""

        updates = {}
        for assignment in set_str.split(","):
            parts = assignment.split("=")
            if len(parts) == 2:
                k = parts[0].strip()
                v = parts[1].strip().strip("'\"")
                try:
                    v = float(v) if "." in v else int(v)
                except ValueError:
                    pass
                updates[k] = v

        where_clause = {}
        if where_str:
            conds = re.split(r"\s+AND\s+", where_str, flags=re.IGNORECASE)
            for cond in conds:
                m_eq = re.match(r"([a-zA-Z0-9_]+)\s*=\s*['\"]?([^'\"]+)['\"]?", cond.strip())
                if m_eq:
                    k = m_eq.group(1).strip()
                    v = m_eq.group(2).strip()
                    try:
                        v = float(v) if "." in v else int(v)
                    except ValueError:
                        pass
                    where_clause[k] = v

        return ParsedQuery(command="UPDATE", table=table, updates=updates, where_clause=where_clause)

    @staticmethod
    def _parse_delete(sql: str) -> ParsedQuery:
        # DELETE FROM table WHERE col = val
        match = re.search(r"DELETE\s+FROM\s+([a-zA-Z0-9_]+)(?:\s+WHERE\s+(.+))?$", sql, re.IGNORECASE)
        if not match:
            raise ValueError(f"Malformed DELETE statement: {sql}")
        table = match.group(1).strip()
        where_str = match.group(2).strip() if match.group(2) else ""

        where_clause = {}
        if where_str:
            conds = re.split(r"\s+AND\s+", where_str, flags=re.IGNORECASE)
            for cond in conds:
                m_eq = re.match(r"([a-zA-Z0-9_]+)\s*=\s*['\"]?([^'\"]+)['\"]?", cond.strip())
                if m_eq:
                    k = m_eq.group(1).strip()
                    v = m_eq.group(2).strip()
                    try:
                        v = float(v) if "." in v else int(v)
                    except ValueError:
                        pass
                    where_clause[k] = v

        return ParsedQuery(command="DELETE", table=table, where_clause=where_clause)
