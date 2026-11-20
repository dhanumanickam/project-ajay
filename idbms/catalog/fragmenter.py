"""
Fragmentation engine supporting Horizontal, Vertical, and Hybrid partitioning schemes.
"""

from typing import Dict, Any, List, Optional, Tuple
from idbms.common.models import FragmentationType

class FragmentRule:
    """Defines how a table is fragmented."""
    def __init__(
        self,
        table_name: str,
        frag_type: FragmentationType,
        frag_id: str,
        assigned_node: str,
        predicate: Optional[Dict[str, Any]] = None,      # For horizontal (e.g. {'branch_id': 'BRANCH_LON'})
        attributes: Optional[List[str]] = None,           # For vertical (e.g. ['cust_id', 'name', 'email'])
        parent_table: Optional[str] = None,              # For derived horizontal fragmentation
        parent_fk: Optional[str] = None
    ):
        self.table_name = table_name
        self.frag_type = frag_type
        self.frag_id = frag_id
        self.assigned_node = assigned_node
        self.predicate = predicate or {}
        self.attributes = attributes or []
        self.parent_table = parent_table
        self.parent_fk = parent_fk

    def matches_horizontal_predicate(self, record: Dict[str, Any]) -> bool:
        """Checks if a record satisfies this fragment's horizontal predicate."""
        if not self.predicate:
            return True
        for key, expected_val in self.predicate.items():
            val = record.get(key)
            if isinstance(expected_val, list):
                if val not in expected_val:
                    return False
            elif isinstance(expected_val, dict):
                # Supports operators like {"$gte": 100, "$lt": 500}
                for op, bound in expected_val.items():
                    if op == "$eq" and val != bound:
                        return False
                    elif op == "$ne" and val == bound:
                        return False
                    elif op == "$gt" and (val is None or val <= bound):
                        return False
                    elif op == "$gte" and (val is None or val < bound):
                        return False
                    elif op == "$lt" and (val is None or val >= bound):
                        return False
                    elif op == "$lte" and (val is None or val > bound):
                        return False
            else:
                if str(val) != str(expected_val):
                    return False
        return True

    def project_vertical_attributes(self, record: Dict[str, Any], key_field: str = "id") -> Dict[str, Any]:
        """Projects record to only the attributes present in this vertical fragment."""
        if not self.attributes:
            return record.copy()
        projected = {}
        # Always retain primary key
        if key_field in record:
            projected[key_field] = record[key_field]
        for attr in self.attributes:
            if attr in record:
                projected[attr] = record[attr]
        return projected

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_name": self.table_name,
            "frag_type": self.frag_type.value,
            "frag_id": self.frag_id,
            "assigned_node": self.assigned_node,
            "predicate": self.predicate,
            "attributes": self.attributes,
            "parent_table": self.parent_table,
            "parent_fk": self.parent_fk
        }
