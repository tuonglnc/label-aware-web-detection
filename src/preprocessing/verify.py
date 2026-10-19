"""Independently verify exported requests, manifests, subsets and checksums."""

import argparse
from collections import Counter
import json
from pathlib import Path

from .prepare import canonical, digest, endpoint_key, file_hashes, group_key, write_json


def verify(output, input_path=None):
    output = Path(output)
    config = json.loads((output / "config_snapshot.json").read_text())
    expected = json.loads((output / "checksums.json").read_text())
    actual_names = {p.name for p in output.iterdir() if p.is_file()} - {"checksums.json"}
    if actual_names != set(expected):
        raise ValueError("Exported file list differs from checksum manifest")
    for name, sha in expected.items():
        if file_hashes(output / name)["sha256"] != sha:
            raise ValueError(f"Checksum mismatch: {name}")
    id_splits, group_splits = {}, {}
    sizes, supports = {}, {}
    for split in ("pool", "development", "validation", "test"):
        manifest = json.loads((output / f"{split}_manifest.json").read_text())
        manifest_index = {r["request_id"]: r for r in manifest}
        if len(manifest) != len(manifest_index):
            raise ValueError(f"Duplicate ID in {split} manifest")
        counts, ids = Counter(), set()
        with (output / f"{split}.jsonl").open() as f:
            for line in f:
                r = json.loads(line)
                rid, gid = r["request_id"], r["group_id"]
                if rid in id_splits:
                    raise ValueError("Request ID overlaps or repeats")
                if gid in group_splits and group_splits[gid] != split:
                    raise ValueError("Group overlaps splits")
                if rid != digest(r["request_text"]) or r["exact_hash"] != rid:
                    raise ValueError("Invalid exact hash")
                if gid != group_key(r["request_text"]) or r["endpoint_hash"] != endpoint_key(r["request_text"]):
                    raise ValueError("Invalid group/endpoint hash")
                if r["label"] not in config["labels"].values():
                    raise ValueError("Unknown label")
                if {k: r[k] for k in ("request_id", "group_id", "label", "source_row")} != manifest_index.get(rid):
                    raise ValueError("Manifest entry mismatch")
                id_splits[rid], group_splits[gid] = split, split
                ids.add(rid)
                counts[r["label"]] += 1
        if ids != set(manifest_index):
            raise ValueError("Manifest coverage mismatch")
        sizes[split], supports[split] = len(ids), dict(counts)
        if split in config["subset_sizes"]:
            subset_ids = set()
            with (output / f"{split}_subset.jsonl").open() as f:
                for line in f:
                    r = json.loads(line)
                    rid = r["request_id"]
                    if rid not in ids or rid in subset_ids:
                        raise ValueError("Subset membership/uniqueness failure")
                    if rid != digest(r["request_text"]) or {k: r[k] for k in ("request_id", "group_id", "label", "source_row")} != manifest_index[rid]:
                        raise ValueError("Subset content differs from full split")
                    subset_ids.add(rid)
            if len(subset_ids) != min(len(ids), config["subset_sizes"][split]):
                raise ValueError("Unexpected subset size")
    result = {"passed": True, "checked_files": len(expected), "split_sizes": sizes,
              "class_distribution": supports, "unique_groups": len(group_splits),
              "config_sha256": digest(canonical(config))}
    if input_path:
        result["input_hashes"] = file_hashes(input_path)
        if result["input_hashes"]["md5"] != config["source"]["expected_md5"]:
            raise ValueError("Raw input differs from source checksum")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="src/data/processed/sr_bh_v1")
    parser.add_argument("--input")
    parser.add_argument("--report", default="src/artifacts/data/export_verification.json")
    args = parser.parse_args()
    result = verify(args.output, args.input)
    write_json(args.report, result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
