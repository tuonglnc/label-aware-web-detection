"""Re-read the actual CSV and export evidence for the seven faculty questions."""

import argparse
from collections import Counter
import csv
import difflib
import json
from pathlib import Path
import re

from .prepare import LABEL_COLUMN, build_request, canonical, digest, file_hashes, write_json


def survey(input_path, config, selection, processed):
    hashes = file_hashes(input_path)
    if hashes["md5"] != config["source"]["expected_md5"]:
        raise ValueError("Dataset checksum differs from verified source")
    counts, cardinality, empty, methods = Counter(), Counter(), Counter(), Counter()
    rows_by_index = {}
    wanted = set(selection.values())
    totals = Counter()
    missing_request_indices = []
    with Path(input_path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        labels = [c for c in fields if LABEL_COLUMN.fullmatch(c)]
        for i, row in enumerate(reader):
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f"Malformed record at index {i}")
            if any(row[c] not in {"0", "1"} for c in labels):
                raise ValueError(f"Invalid binary label at index {i}")
            active = [c for c in labels if row[c] == "1"]
            counts.update(active)
            cardinality[len(active)] += 1
            empty.update(c for c in fields if row[c] == "")
            methods[row["request_http_method"]] += 1
            totals["records"] += 1
            normal = "000 - Normal" in active
            attack = any(c != "000 - Normal" for c in active)
            totals["normal_records"] += normal
            totals["attack_records"] += attack
            totals["normal_and_attack_records"] += normal and attack
            if not row["request_http_method"] or not row["request_http_request"]:
                missing_request_indices.append(i)
            if i in wanted:
                text = build_request(row, config)
                rows_by_index[i] = {"raw_index": i, "csv_record": i + 2, "labels": active,
                                    "request_id": digest(text), "request_text": text, "row": row}
    if set(rows_by_index) != wanted:
        raise ValueError("Selected example index is outside the CSV")
    examples = {name: rows_by_index[index] for name, index in selection.items()}
    # Check the real annotations and visible example identity, not invented labels.
    assert examples["benign"]["labels"] == ["000 - Normal"]
    assert examples["sqli"]["labels"] == ["66 - SQL Injection"]
    assert "<script>alert(document.cookie)</script>" in examples["xss"]["row"]["request_http_request"]
    assert examples["pair_normal"]["labels"] == ["000 - Normal"]
    assert examples["pair_attack"]["labels"] == ["66 - SQL Injection"]
    a, b = [json.loads(examples[name]["request_text"]) for name in ("pair_normal", "pair_attack")]
    different = [k for k in a if a[k] != b[k]]
    assert different == ["uri"], different
    pair_ids = {examples[name]["request_id"] for name in ("pair_normal", "pair_attack")}
    memberships = {}
    # Deliberately never open final-test request text for illustration selection.
    for split in ("development", "pool"):
        manifest = json.loads((Path(processed) / f"{split}_manifest.json").read_text(encoding="utf-8"))
        for record in manifest:
            if record["request_id"] in pair_ids:
                memberships[record["request_id"]] = split
    assert pair_ids == set(memberships), "Illustration must come from development/pool"
    attack_counts = {c: counts[c] for c in labels if c != "000 - Normal"}
    observed = {c: n for c, n in attack_counts.items() if n > 0}
    biggest = max(observed, key=observed.get) if observed else None
    smallest = min(observed, key=observed.get) if observed else None
    non_singleton = {c: n for c, n in attack_counts.items() if n > 1}
    stats = {
        "input": {"path": str(input_path), "bytes": Path(input_path).stat().st_size, **hashes},
        "source": config["source"], "totals": dict(totals), "columns": fields,
        "label_columns": labels, "attack_class_count": len(attack_counts),
        "class_distribution": [{"label": c, "samples": counts[c], "percent_of_records": counts[c] / totals["records"] * 100} for c in labels],
        "label_cardinality": dict(sorted(cardinality.items())),
        "empty_fields": {c: empty[c] for c in fields}, "methods": dict(methods),
        "missing_method_or_uri_indices": missing_request_indices,
        "imbalance": {"largest_attack_class": biggest, "smallest_attack_class": smallest,
                      "zero_support_attack_columns": [c for c, n in attack_counts.items() if n == 0],
                      "ratio_scope": "Observed classes with positive support; zero-support columns listed separately",
                      "attack_max_min_ratio": observed[biggest] / observed[smallest] if observed else None,
                      "including_normal_max_min_ratio": max(counts.values()) / min(counts.values()) if counts else None,
                      "attack_ratio_excluding_singletons": max(non_singleton.values()) / min(non_singleton.values()) if non_singleton else None,
                      "binary_normal_attack_ratio": totals["normal_records"] / totals["attack_records"] if totals["attack_records"] else None},
        "predefined_split_columns": [c for c in fields if re.search(r"(?:^|_)(?:train|test|split|fold|partition|subset)(?:_|$)", c, re.I)],
    }
    matcher = difflib.SequenceMatcher(None, a["uri"], b["uri"], autojunk=False)
    pair = {
        "normal_id": examples["pair_normal"]["request_id"], "attack_id": examples["pair_attack"]["request_id"],
        "normal_raw_index": examples["pair_normal"]["raw_index"], "attack_raw_index": examples["pair_attack"]["raw_index"],
        "memberships": memberships, "different_request_fields": different,
        "uri_similarity": matcher.ratio(),
        "request_text_similarity": difflib.SequenceMatcher(None, examples["pair_normal"]["request_text"], examples["pair_attack"]["request_text"], autojunk=False).ratio(),
        "metric": "SequenceMatcher character similarity, autojunk=False; not embedding similarity",
        "uri_changes": [{"operation": tag, "normal": a["uri"][i:j], "attack": b["uri"][k:l]} for tag, i, j, k, l in matcher.get_opcodes() if tag != "equal"],
        "source_label_adjudicated_by_human": False,
        "establishes_retrieval_failure": False,
    }
    assert sum(cardinality.values()) == totals["records"]
    assert sum(counts.values()) == sum(k * v for k, v in cardinality.items())
    return stats, examples, pair


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="src/data/raw/data_capec_multilabel.csv")
    parser.add_argument("--config", default="src/configs/data.json")
    parser.add_argument("--selection", default="src/configs/sr_bh_survey_examples.json")
    parser.add_argument("--processed", default="src/data/processed/sr_bh_v1")
    parser.add_argument("--output", default="src/artifacts/data/sr_bh_survey")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    selection = json.loads(Path(args.selection).read_text(encoding="utf-8"))
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    stats, examples, pair = survey(args.input, config, selection, args.processed)
    write_json(output / "stats.json", stats)
    write_json(output / "examples.json", examples)
    write_json(output / "motivating_pair.json", pair)
    write_json(output / "verification.json", {"passed": True, "records_scanned": stats["totals"]["records"],
               "source_md5_verified": True, "selected_raw_records_retrieved": len(set(selection.values())),
               "example_labels_verified": True, "pair_only_uri_differs": True,
               "pair_from_development_or_pool": True, "label_count_accounting_verified": True,
               "survey_module_sha256": file_hashes(__file__)["sha256"],
               "selection_sha256": digest(canonical(selection))})
    print(json.dumps({"totals": stats["totals"], "imbalance": stats["imbalance"], "pair": pair}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
