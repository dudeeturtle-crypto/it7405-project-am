"""MongoDB helper tools: CRUD, index management and query diagnosis.

Usage examples (run as script):
  python scripts/mongo_tools.py list-indexes --collection movies
  python scripts/mongo_tools.py explain --collection movies --filter '{"slug": "inception"}'
  python scripts/mongo_tools.py create-index --collection movies --keys 'title:1,slug:1' --unique

This module prefers the project's `get_db()` helper at
`accounts.mongo_connection.get_db`. If `USE_MONGODB` is not enabled this
script will raise a helpful error.
"""
from __future__ import annotations

import os
import sys
import argparse
import json
from pprint import pprint
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

# Ensure project root is on sys.path when running the script directly so
# `from accounts.mongo_connection import get_db` works whether this module is
# executed as a script (`python scripts/mongo_tools.py`) or imported.
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from accounts.mongo_connection import get_db
except Exception:  # pragma: no cover - fallback when imported outside Django
    get_db = None  # type: ignore


def get_db_or_raise():
    if get_db is None:
        raise RuntimeError("No MongoDB helper available (could not import get_db)")
    db = get_db()
    if db is None:
        raise RuntimeError("MongoDB is disabled (USE_MONGODB is not True) or connection failed")
    return db


def create_document(collection: str, doc: Dict[str, Any]) -> Any:
    db = get_db_or_raise()
    res = db[collection].insert_one(doc)
    return res.inserted_id


def read_documents(
    collection: str,
    filter: Dict[str, Any] = None,
    projection: Dict[str, int] = None,
    limit: int = 0,
    sort: Optional[Sequence[Tuple[str, int]]] = None,
) -> List[Dict[str, Any]]:
    db = get_db_or_raise()
    cursor = db[collection].find(filter or {}, projection)
    if sort:
        cursor = cursor.sort(list(sort))
    if limit and limit > 0:
        cursor = cursor.limit(limit)
    return list(cursor)


def update_documents(
    collection: str,
    filter: Dict[str, Any],
    update: Dict[str, Any],
    many: bool = False,
    upsert: bool = False,
    raw_update: bool = False,
) -> Dict[str, Any]:
    db = get_db_or_raise()
    if raw_update:
        update_doc = update
    else:
        update_doc = {"$set": update}
    if many:
        res = db[collection].update_many(filter, update_doc, upsert=upsert)
    else:
        res = db[collection].update_one(filter, update_doc, upsert=upsert)
    return {"matched": res.matched_count, "modified": res.modified_count, "upserted_id": getattr(res, "upserted_id", None)}


def delete_documents(collection: str, filter: Dict[str, Any], many: bool = False) -> int:
    db = get_db_or_raise()
    if many:
        res = db[collection].delete_many(filter)
    else:
        res = db[collection].delete_one(filter)
    return res.deleted_count


def create_index(collection: str, keys: Sequence[Tuple[str, int]], unique: bool = False, background: bool = True) -> str:
    db = get_db_or_raise()
    return db[collection].create_index(list(keys), unique=unique, background=background)


def list_indexes(collection: str) -> List[Dict[str, Any]]:
    db = get_db_or_raise()
    return list(db[collection].list_indexes())


def index_stats(collection: str) -> List[Dict[str, Any]]:
    db = get_db_or_raise()
    # $indexStats requires MongoDB server >= 3.2
    try:
        return list(db[collection].aggregate([{"$indexStats": {}}]))
    except Exception as e:
        return [{"error": str(e)}]


def analyze_query_performance(collection: str, filter: Dict[str, Any], projection: Optional[Dict[str, int]] = None, sort: Optional[Sequence[Tuple[str, int]]] = None, limit: Optional[int] = None, threshold_ms: int = 50) -> Dict[str, Any]:
    """Run explain and return a compact analysis with simple recommendations.

    The function runs the query with `explain("executionStats")` and checks
    `executionTimeMillis`. If the plan uses COLLSCAN, it suggests indexes on
    filter fields.
    """
    plan = explain_query(collection, filter, projection=projection, sort=sort, limit=limit)
    analysis: Dict[str, Any] = {"plan": plan}
    try:
        exec_stats = plan.get("executionStats") or plan.get("stages") or {}
        # executionTimeMillis usually appears under executionStats
        exec_time = None
        if isinstance(exec_stats, dict):
            exec_time = exec_stats.get("executionTimeMillis")
        analysis["executionTimeMillis"] = exec_time
    except Exception:
        analysis["executionTimeMillis"] = None

    # Detect collection scan
    def _uses_collscan(p: Dict[str, Any]) -> bool:
        if not p:
            return False
        # common keys where stage info appears
        if p.get("stage") == "COLLSCAN":
            return True
        for k, v in p.items():
            if isinstance(v, dict) and _uses_collscan(v):
                return True
            if isinstance(v, list):
                for it in v:
                    if isinstance(it, dict) and _uses_collscan(it):
                        return True
        return False

    analysis["usesCollScan"] = _uses_collscan(plan)
    recommendations: List[str] = []
    if analysis["usesCollScan"]:
        # naive suggestion: index the top-level filter fields
        if filter:
            rec = _suggest_index_from_filter(filter)
            if rec:
                recommendations.append(f"Consider adding an index on: {rec}")
            else:
                recommendations.append("Query does a collection scan; consider indexing filter fields.")
        else:
            recommendations.append("Query does a collection scan with no filter; consider limiting or adding filters.")

    if analysis.get("executionTimeMillis") is not None and analysis["executionTimeMillis"] > threshold_ms:
        recommendations.append(f"Query executionTimeMillis {analysis['executionTimeMillis']}ms exceeds threshold {threshold_ms}ms")

    analysis["recommendations"] = recommendations
    return analysis


def _suggest_index_from_filter(filter: Dict[str, Any]) -> List[Tuple[str, int]]:
    """Naive index suggestion: convert top-level equality fields into ascending keys.

    This is a heuristic: for filters like {"slug": "inception", "year": 2010}
    it suggests [('slug', 1), ('year', 1)]. It does not analyze nested or
    $or/$in complexity.
    """
    keys: List[Tuple[str, int]] = []
    if not filter:
        return keys
    for k, v in filter.items():
        # skip operators
        if k.startswith("$"):
            continue
        # only suggest for simple equality or range queries
        if isinstance(v, (str, int, float, bool)):
            keys.append((k, 1))
        elif isinstance(v, dict):
            # common operators: $eq, $gt, $lt, $in
            if any(op in v for op in ["$eq", "$gt", "$lt", "$in", "$gte", "$lte"]):
                keys.append((k, 1))
    return keys



def explain_query(collection: str, filter: Dict[str, Any], projection: Optional[Dict[str, int]] = None, sort: Optional[Sequence[Tuple[str, int]]] = None, limit: Optional[int] = None) -> Dict[str, Any]:
    db = get_db_or_raise()
    cursor = db[collection].find(filter or {}, projection)
    if sort:
        cursor = cursor.sort(list(sort))
    if limit and limit > 0:
        cursor = cursor.limit(limit)
    # .explain() returns the command/execution plan
    return cursor.explain()


def _parse_keys_arg(s: str) -> List[Tuple[str, int]]:
    # Accepts formats like 'title:1,slug:-1' or 'title'
    out: List[Tuple[str, int]] = []
    for part in [p.strip() for p in s.split(",") if p.strip()]:
        if ":" in part:
            k, v = part.split(":", 1)
            out.append((k.strip(), int(v.strip())))
        else:
            out.append((part, 1))
    return out


def _arg_parse_json(s: str) -> Any:
    try:
        return json.loads(s)
    except Exception as e:
        raise argparse.ArgumentTypeError(f"Invalid JSON: {e}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description="MongoDB tools: CRUD, index and explain utilities for this project.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub_list = sub.add_parser("list-indexes")
    sub_list.add_argument("--collection", required=True)

    sub_create_index = sub.add_parser("create-index")
    sub_create_index.add_argument("--collection", required=True)
    sub_create_index.add_argument("--keys", required=True, help="Comma-separated keys e.g. 'slug:1,title:1'")
    sub_create_index.add_argument("--unique", action="store_true")

    sub_explain = sub.add_parser("explain")
    sub_explain.add_argument("--collection", required=True)
    sub_explain.add_argument("--filter", type=_arg_parse_json, default="{}")
    sub_explain.add_argument("--projection", type=_arg_parse_json, default=None)
    sub_explain.add_argument("--limit", type=int, default=0)
    sub_explain.add_argument("--sort", default=None, help="Comma-separated sort, e.g. 'year:-1,title:1'")

    sub_analyze = sub.add_parser("analyze")
    sub_analyze.add_argument("--collection", required=True)
    sub_analyze.add_argument("--filter", type=_arg_parse_json, default="{}")
    sub_analyze.add_argument("--threshold-ms", type=int, default=50)

    sub_suggest = sub.add_parser("suggest-index")
    sub_suggest.add_argument("--filter", type=_arg_parse_json, required=True)

    sub_find = sub.add_parser("find")
    sub_find.add_argument("--collection", required=True)
    sub_find.add_argument("--filter", type=_arg_parse_json, default="{}")
    sub_find.add_argument("--limit", type=int, default=0)

    sub_create = sub.add_parser("create")
    sub_create.add_argument("--collection", required=True)
    sub_create.add_argument("--doc", type=_arg_parse_json, required=True)

    sub_update = sub.add_parser("update")
    sub_update.add_argument("--collection", required=True)
    sub_update.add_argument("--filter", type=_arg_parse_json, required=True)
    sub_update.add_argument("--update", type=_arg_parse_json, required=True)
    sub_update.add_argument("--many", action="store_true")

    sub_delete = sub.add_parser("delete")
    sub_delete.add_argument("--collection", required=True)
    sub_delete.add_argument("--filter", type=_arg_parse_json, required=True)
    sub_delete.add_argument("--many", action="store_true")

    args = p.parse_args(argv)

    try:
        if args.cmd == "list-indexes":
            pprint(list_indexes(args.collection))
        elif args.cmd == "create-index":
            keys = _parse_keys_arg(args.keys)
            idx = create_index(args.collection, keys, unique=args.unique)
            print("Created index:", idx)
        elif args.cmd == "explain":
            sort = _parse_keys_arg(args.sort) if args.sort else None
            plan = explain_query(args.collection, args.filter or {}, projection=args.projection, sort=sort, limit=(args.limit or None))
            pprint(plan)
        elif args.cmd == "analyze":
            plan = analyze_query_performance(args.collection, args.filter or {}, threshold_ms=args.threshold_ms)
            pprint(plan)
        elif args.cmd == "suggest-index":
            rec = _suggest_index_from_filter(args.filter or {})
            print(rec)
        elif args.cmd == "find":
            docs = read_documents(args.collection, args.filter or {}, limit=(args.limit or 0))
            pprint(docs)
        elif args.cmd == "create":
            _id = create_document(args.collection, args.doc)
            print("Inserted id:", _id)
        elif args.cmd == "update":
            res = update_documents(args.collection, args.filter, args.update, many=args.many)
            pprint(res)
        elif args.cmd == "delete":
            n = delete_documents(args.collection, args.filter, many=args.many)
            print("Deleted:", n)
        return 0
    except Exception as e:
        print("ERROR:", e)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
