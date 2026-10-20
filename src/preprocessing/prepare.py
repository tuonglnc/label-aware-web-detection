"""Prepare a reproducible, group-disjoint SR-BH single-label benchmark.

Run from repository root: python3 -m src.preprocessing.prepare --help
Only Python's standard library is required. Final-test requests are never sent
to a model; this module only inspects their structure and class support.
"""

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import itertools
import json
from pathlib import Path
import random
import re
import sqlite3
import sys
import tempfile


LABEL_COLUMN = re.compile(r"^\d+\s+-\s+.+$")
# Never decode or alter the model input. These masks apply only to group keys.
LONG_HEX = re.compile(r"\b[0-9a-fA-F]{16,}\b")
DECIMAL = re.compile(r"(?<![%\w])\d+(?!\w)")


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    with Path(path).open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(canonical(row) + "\n")


def file_hashes(path):
    sha, md5 = hashlib.sha256(), hashlib.md5()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
            md5.update(chunk)
    return {"sha256": sha.hexdigest(), "md5": md5.hexdigest()}


def validate_config(config):
    if config["grouping"] != "full-request-mask-decimal-and-long-hex-v1":
        raise ValueError("Unsupported grouping rule")
    ratios = config["split_ratios"]
    if set(ratios) != {"pool", "validation", "test"} or any(v <= 0 for v in ratios.values()) or abs(sum(ratios.values()) - 1) > 1e-9:
        raise ValueError("Split ratios must be positive and sum to 1")
    if len(set(config["labels"].values())) != len(config["labels"]):
        raise ValueError("Label mapping must be one-to-one")
    if any(not k.startswith("request_") for k in config["headers"]):
        raise ValueError("Only request headers may be included")
    for key in ("max_request_chars", "development_per_class", "min_groups_per_class", "review_per_class"):
        if config[key] < 1:
            raise ValueError(f"{key} must be positive")
    if set(config["subset_sizes"]) != set(ratios) or any(v < 1 for v in config["subset_sizes"].values()):
        raise ValueError("Subset sizes must be positive for each main split")


def build_request(row, config):
    """JSON serialization preserves boundaries, empty fields, encoding and body."""
    return canonical({
        "method": row["request_http_method"],
        "uri": row["request_http_request"],
        "protocol": row["request_http_protocol"],
        "headers": {name: row[col] for col, name in config["headers"].items()},
        "body": row["request_body"],
    })


def group_key(request_text):
    """Conservative template grouping, independent of labels and split."""
    return digest(DECIMAL.sub("<NUM>", LONG_HEX.sub("<HEX>", request_text)))


def endpoint_key(request_text):
    request = json.loads(request_text)
    return digest(canonical([request["method"], request["uri"].split("?", 1)[0]]))


def scan_csv(input_path, config, db):
    db.execute("CREATE TABLE requests (id TEXT PRIMARY KEY, text TEXT, signature TEXT, conflict INTEGER, label TEXT, source_row INTEGER, occurrences INTEGER)")
    counts = Counter({k: 0 for k in (
        "total_rows", "malformed_row", "invalid_label", "zero_label", "multi_label",
        "out_of_scope", "eligible_single_label", "missing_essential", "conflict_unique_requests",
        "conflict_rows", "oversize_unique_requests", "oversize_rows", "retained_source_rows",
        "duplicate_rows_removed", "retained_unique_requests",
    )})
    raw_classes = Counter()
    csv.field_size_limit(16 * 1024 * 1024)
    with Path(input_path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        if len(fields) != len(set(fields)):
            raise ValueError("Duplicate CSV column names")
        labels = [c for c in fields if LABEL_COLUMN.fullmatch(c)]
        required = set(config["labels"]) | set(config["headers"]) | {"request_http_method", "request_http_request", "request_http_protocol", "request_body"}
        missing = required - set(fields)
        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}")
        if not labels:
            raise ValueError("No label columns discovered")
        for line, row in enumerate(reader, 2):
            counts["total_rows"] += 1
            if None in row or any(v is None for v in row.values()):
                counts["malformed_row"] += 1
                continue
            if any(row[c].strip() not in {"0", "1"} for c in labels):
                counts["invalid_label"] += 1
                continue
            active = tuple(c for c in labels if row[c].strip() == "1")
            raw_classes.update(active)
            target = config["labels"].get(active[0]) if len(active) == 1 else None
            if not active:
                reason = "zero_label"
            elif len(active) > 1:
                reason = "multi_label"
            elif target is None:
                reason = "out_of_scope"
            else:
                reason = "eligible_single_label"
            counts[reason] += 1
            if not row["request_http_method"].strip() or not row["request_http_request"].strip():
                counts["missing_essential"] += 1
                continue
            text = build_request(row, config)
            # Check conflicts BEFORE excluding multi-label/out-of-scope/long rows.
            # Otherwise an eligible duplicate could silently survive a conflict.
            request_id, signature = digest(text), canonical(active)
            db.execute("""INSERT INTO requests VALUES (?, ?, ?, 0, ?, ?, 1)
                ON CONFLICT(id) DO UPDATE SET
                conflict = MAX(requests.conflict, requests.signature != excluded.signature),
                occurrences = requests.occurrences + 1""",
                (request_id, text, signature, target, line))
            if counts["total_rows"] % 100000 == 0:
                print(f"Read {counts['total_rows']} rows", flush=True)
        db.commit()
    return counts, raw_classes, fields, labels


def assign_groups(records, config):
    groups = defaultdict(list)
    for record in records:
        groups[record["group_id"]].append(record)
    strata = defaultdict(list)
    for gid, members in groups.items():
        strata[tuple(sorted({r["label"] for r in members}))].append(gid)
    assignments = {}
    # Stratify by the set of labels in a group, not by individual rows.
    for signature in sorted(strata):
        ids = sorted(strata[signature])
        random.Random(f"{config['seed']}:{canonical(signature)}").shuffle(ids)
        nval = int(len(ids) * config["split_ratios"]["validation"])
        ntest = int(len(ids) * config["split_ratios"]["test"])
        for i, gid in enumerate(ids):
            assignments[gid] = "validation" if i < nval else "test" if i < nval + ntest else "pool"
    # Reserve whole pool groups for development. Multi-label groups stay intact.
    dev_counts = Counter()
    pool_ids = sorted(g for g, split in assignments.items() if split == "pool")
    random.Random(config["seed"]).shuffle(pool_ids)
    for gid in pool_ids:
        if any(dev_counts[r["label"]] < config["development_per_class"] for r in groups[gid]):
            assignments[gid] = "development"
            dev_counts.update(r["label"] for r in groups[gid])
    splits = {name: [] for name in ("pool", "development", "validation", "test")}
    for r in records:
        splits[assignments[r["group_id"]]].append(r)
    for rows in splits.values():
        rows.sort(key=lambda r: r["request_id"])
    return splits


def balanced_subset(rows, size, seed):
    """Round-robin classes, random within class; explicit balanced pilot policy."""
    by_label = defaultdict(list)
    for row in rows:
        by_label[row["label"]].append(row)
    rng = random.Random(seed)
    for label in sorted(by_label):
        by_label[label].sort(key=lambda r: r["request_id"])
        rng.shuffle(by_label[label])
    result = []
    while len(result) < size:
        available = False
        for label in sorted(by_label):
            if by_label[label] and len(result) < size:
                result.append(by_label[label].pop())
                available = True
        if not available:
            break
    return result


def audit_splits(splits):
    overlaps = {}
    for a, b in itertools.combinations(sorted(splits), 2):
        overlaps[f"{a}/{b}"] = {
            key: len({r[key] for r in splits[a]} & {r[key] for r in splits[b]})
            for key in ("request_id", "group_id", "exact_hash")
        }
    passed = all(v == 0 for pair in overlaps.values() for v in pair.values())
    endpoint_overlaps = {}
    endpoint_sets = {s: {r["endpoint_hash"] for r in rows} for s, rows in splits.items()}
    for a, b in itertools.combinations(sorted(splits), 2):
        endpoint_overlaps[f"{a}/{b}"] = len(endpoint_sets[a] & endpoint_sets[b])
    return {"passed": passed, "overlaps": overlaps, "endpoint_overlaps": endpoint_overlaps,
            "limitation": "No overlap under the declared exact/template rule; endpoint overlap and unrecognized semantic near-duplicates can remain."}


def prepare(input_path, config, output, artifacts):
    validate_config(config)
    input_path, output, artifacts = Path(input_path), Path(output), Path(artifacts)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output must be empty: choose a new directory to preserve prior manifests")
    hashes = file_hashes(input_path)
    expected = config.get("source", {}).get("expected_md5")
    if expected and hashes["md5"] != expected:
        raise ValueError("Source MD5 mismatch; do not proceed with an unverified file")
    output.mkdir(parents=True, exist_ok=True)
    artifacts.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sr-bh-") as tmp:
        db = sqlite3.connect(str(Path(tmp) / "requests.sqlite"))
        try:
            counts, raw_classes, fields, label_columns = scan_csv(input_path, config, db)
        except Exception:
            # Windows cannot delete the temp directory while the DB file is open.
            db.close()
            raise
        records, quarantine = [], []
        for rid, text, signature, conflict, label, source_row, occurrences in db.execute("SELECT * FROM requests ORDER BY id"):
            if conflict:
                counts["conflict_unique_requests"] += 1
                counts["conflict_rows"] += occurrences
                quarantine.append({"request_id": rid, "first_source_row": source_row, "occurrences": occurrences, "reason": "conflicting_annotations"})
                continue
            if label is None:
                continue
            if len(text) > config["max_request_chars"]:
                counts["oversize_unique_requests"] += 1
                counts["oversize_rows"] += occurrences
                continue
            counts["retained_source_rows"] += occurrences
            counts["duplicate_rows_removed"] += occurrences - 1
            records.append({"request_id": rid, "exact_hash": rid, "group_id": group_key(text),
                            "endpoint_hash": endpoint_key(text), "request_text": text, "label": label,
                            "source_row": source_row, "source_occurrences": occurrences})
        db.close()
    splits = assign_groups(records, config)
    audit = audit_splits(splits)
    if not audit["passed"]:
        raise ValueError("Leakage audit failed")
    support = {s: dict(Counter(r["label"] for r in rows)) for s, rows in splits.items()}
    group_support = {label: len({r["group_id"] for r in records if r["label"] == label}) for label in config["labels"].values()}
    warnings = []
    for label, n in group_support.items():
        if n < config["min_groups_per_class"]:
            warnings.append(f"{label}: only {n} independent template groups")
        for split in splits:
            if support[split].get(label, 0) == 0:
                warnings.append(f"{label}: absent from {split}")
    subsets = {s: balanced_subset(splits[s], size, config["seed"]) for s, size in config["subset_sizes"].items()}
    for split, size in config["subset_sizes"].items():
        if len(subsets[split]) < size:
            warnings.append(f"{split}: subset shortfall {len(subsets[split])}/{size}")
    for split, rows in splits.items():
        write_jsonl(output / f"{split}.jsonl", rows)
        write_json(output / f"{split}_manifest.json", [{k: r[k] for k in ("request_id", "group_id", "label", "source_row")} for r in rows])
    for split, rows in subsets.items():
        write_jsonl(output / f"{split}_subset.jsonl", rows)
    # Review candidates come only from development/pool, never final test.
    review = balanced_subset(splits["development"] + splits["pool"], config["review_per_class"] * len(config["labels"]), config["seed"])
    write_jsonl(artifacts / "manual_review.jsonl", [{**r, "review_status": "pending", "review_note": ""} for r in review])
    by_group = defaultdict(list)
    for r in splits["development"] + splits["pool"]:
        by_group[r["group_id"]].append(r)
    examples = []
    ranked = [g for g in sorted(by_group, key=lambda g: (-len(by_group[g]), g)) if len(by_group[g]) > 1]
    review_groups = set(ranked[:8])
    for label in config["labels"].values():
        review_groups.update([g for g in ranked if any(r["label"] == label for r in by_group[g])][:2])
    for gid in ranked:
        if gid in review_groups:
            examples.append({"group_id": gid, "members": len(by_group[gid]), "examples": by_group[gid][:3], "review_status": "pending"})
    write_jsonl(artifacts / "group_review.jsonl", examples)
    write_jsonl(artifacts / "quarantine.jsonl", quarantine)
    counts["retained_unique_requests"] = len(records)
    summary = {"protocol_version": config["protocol_version"], "config_sha256": digest(canonical(config)),
               "input": {"path": str(input_path), "bytes": input_path.stat().st_size, **hashes},
               "source": config.get("source", {}), "columns": fields, "label_columns": label_columns,
               "counts": dict(counts), "raw_class_counts": dict(raw_classes),
               "group_support": group_support, "class_distribution": support,
               "split_sizes": {s: len(rows) for s, rows in splits.items()},
               "split_groups": {s: len({r['group_id'] for r in rows}) for s, rows in splits.items()},
               "subset_distribution": {s: dict(Counter(r['label'] for r in rows)) for s, rows in subsets.items()},
               "warnings": warnings, "manual_review_status": "pending", "group_review_status": "pending",
               "ready_for_task_2": False,
               "readiness_note": "Require manual annotation/group review and explicit taxonomy decision, even if automated checks pass.",
               "runtime": {"python": sys.version.split()[0], "dependencies": "standard-library only",
                           "prepare_module_sha256": file_hashes(__file__)["sha256"]}}
    write_json(output / "config_snapshot.json", config)
    # Checksums cover all generated data/manifests, excluding the checksum file itself.
    write_json(output / "checksums.json", {p.name: file_hashes(p)["sha256"] for p in sorted(output.iterdir()) if p.is_file()})
    write_json(artifacts / "summary.json", summary)
    write_json(artifacts / "leakage_audit.json", audit)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="src/data/raw/data_capec_multilabel.csv")
    parser.add_argument("--config", default="src/configs/data.json")
    parser.add_argument("--output", default="src/data/processed/sr_bh_v1")
    parser.add_argument("--artifacts", default="src/artifacts/data")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    summary = prepare(args.input, config, args.output, args.artifacts)
    print(json.dumps({k: summary[k] for k in ("counts", "split_sizes", "group_support", "warnings")}, indent=2))


if __name__ == "__main__":
    main()
