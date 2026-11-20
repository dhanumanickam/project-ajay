"""
FastAPI Server exposing REST APIs for distributed database administration,
query execution, 2PC transaction execution, fault injection, and evaluation.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from idbms.system import DistributedDatabaseCluster
from evaluation.generate_charts import generate_all_evaluation_charts

app = FastAPI(title="Intelligent Distributed DBMS (IDBMS) Console", version="2.0")

# Initialize global cluster instance
cluster = DistributedDatabaseCluster(reset_data=False)

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

class QueryRequest(BaseModel):
    sql: str

class TransferRequest(BaseModel):
    from_account: str
    to_account: str
    amount: float

class FaultToggleRequest(BaseModel):
    node_id: str
    action: str  # "OFFLINE", "ONLINE", "SIMULATE_ABORT"

class PartitionRequest(BaseModel):
    node_a: str
    node_b: str
    partitioned: bool

@app.get("/")
def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "IDBMS API Server is Running. Dashboard UI available at /static/index.html"}

@app.get("/api/cluster/status")
def get_cluster_status():
    return cluster.get_cluster_status()

@app.get("/api/catalog")
def get_catalog():
    return cluster.catalog.get_catalog_summary()

@app.post("/api/query/execute")
def execute_query(req: QueryRequest):
    try:
        res = cluster.query_executor.execute_sql(req.sql)
        return res.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/transaction/transfer")
def execute_transfer(req: TransferRequest):
    try:
        res = cluster.tx_mgr.execute_cross_branch_transfer(
            from_acc=req.from_account,
            to_acc=req.to_account,
            amount=req.amount
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/nodes/fault")
def toggle_node_fault(req: FaultToggleRequest):
    if req.node_id not in cluster.nodes:
        raise HTTPException(status_code=404, detail=f"Node {req.node_id} not found.")

    node = cluster.nodes[req.node_id]
    if req.action == "OFFLINE":
        node.is_offline = True
        cluster.catalog.update_node_status(req.node_id, "OFFLINE")
    elif req.action == "ONLINE":
        node.is_offline = False
        node.simulate_abort_vote = False
        cluster.catalog.update_node_status(req.node_id, "ONLINE")
    elif req.action == "SIMULATE_ABORT":
        node.simulate_abort_vote = not node.simulate_abort_vote
    return {"node_id": req.node_id, "is_offline": node.is_offline, "simulate_abort": node.simulate_abort_vote}

@app.post("/api/network/partition")
def toggle_partition(req: PartitionRequest):
    cluster.net_sim.set_partition(req.node_a, req.node_b, req.partitioned)
    return {"partitioned": req.partitioned, "partitions": cluster.net_sim.get_stats()["active_partitions"]}

@app.get("/api/concurrency/locks")
def get_locks():
    all_locks = {}
    wfgs = {}
    for nid, node in cluster.nodes.items():
        all_locks[nid] = node.lock_mgr.get_lock_table_snapshot()
        wfgs[nid] = node.lock_mgr.get_wait_for_graph()
    return {"locks_by_node": all_locks, "wait_for_graphs": wfgs}

@app.post("/api/concurrency/deadlock/detect")
def run_deadlock_detection():
    resolutions = cluster.tx_mgr.run_deadlock_detection_cycle()
    return {"resolutions": resolutions, "active_deadlocks_resolved": len(resolutions)}

@app.post("/api/evaluation/run")
def run_evaluation_benchmarks():
    try:
        metrics = generate_all_evaluation_charts()
        return {
            "status": "SUCCESS",
            "metrics": metrics,
            "charts": [
                "/static/charts/benchmark_throughput.png",
                "/static/charts/benchmark_latency.png",
                "/static/charts/benchmark_semijoin.png",
                "/static/charts/benchmark_consistency.png"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
