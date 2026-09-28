#!/usr/bin/env python3
"""Validate the seed labels and print a compact coverage report."""
from collections import Counter
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "data/sources.json").read_text(encoding="utf-8"))
sources = {s["id"]: s for s in manifest["sources"]}
rows = [json.loads(line) for line in (ROOT / "data/eval_v1.jsonl").read_text(encoding="utf-8").splitlines()]
ids = set()
questions = set()
for row in rows:
    assert row["id"] not in ids, row["id"]
    assert row["question"].casefold() not in questions, row["question"]
    ids.add(row["id"])
    questions.add(row["question"].casefold())
    assert row["split"] in {"development", "holdout"}
    assert row["expected_behavior"] in {"answer", "clarify", "fallback"}
    assert row["source_ids"] and all(source in sources for source in row["source_ids"])
    assert row["source_access"] == [sources[s]["access"] for s in row["source_ids"]]
    assert row["client_approval_status"] == "pending_confirmation"
    if row["expected_behavior"] == "answer":
        assert row["gold_answer_summary"] and row["source_locator"]
        assert not row["review_hint"]
    else:
        assert not row["gold_answer_summary"] and not row["source_locator"]
        assert row["review_hint"]
for source in sources.values():
    assert urlparse(source["url"]).scheme == "https"
    assert source["access"] in {"document_read", "page_read", "indexed_excerpt"}
print("Cases:", len(rows))
print("Behaviors:", dict(Counter(r["expected_behavior"] for r in rows)))
print("Topics:", dict(Counter(r["topic"] for r in rows)))
print("Splits:", dict(Counter(r["split"] for r in rows)))
print("Sources:", len(sources))
print("Indexed-only answer cases:", sum(
    r["expected_behavior"] == "answer" and "indexed_excerpt" in r["source_access"] for r in rows
))
