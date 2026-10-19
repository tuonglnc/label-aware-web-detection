"""Parse and inspect the three raw HTTP CSIC 2010 files without inventing subtypes."""

import argparse
from collections import Counter, defaultdict
import difflib
import itertools
import json
from pathlib import Path
import re
from urllib.parse import unquote_plus

from .prepare import canonical, digest, file_hashes, write_json


FILES = {
    "normalTrafficTraining.txt": ("NORMAL", "source_train"),
    "normalTrafficTest.txt": ("NORMAL", "source_test_normal"),
    "anomalousTrafficTest.txt": ("ANOMALOUS", "source_test_anomalous"),
}
MIRROR_COMMIT = "424c6e1c1951570473d9d6c0227eaaac6fdd6d02"
REQUEST_LINE = re.compile(rb"(?m)^([!#$%&'*+\-.^_`|~0-9A-Za-z]+) (.+?) (HTTP/[0-9.]+)\r?$\n")
SEPARATOR = re.compile(rb"\r?\n\r?\n")
SQL = re.compile(r"\bDROP\s+TABLE\b|\bUNION\s+(?:ALL\s+)?SELECT\b|\bSELECT\s+.{0,160}?\bFROM\b|\b(?:OR|AND)\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+", re.I)
XSS = re.compile(r"<script\b|\bonerror\s*=|javascript\s*:|<iframe\b", re.I)


def parse_bytes(data, filename, label, split):
    data.decode("utf-8")  # Fail explicitly rather than silently replacing bytes.
    matches = list(REQUEST_LINE.finditer(data))
    if not matches or data[:matches[0].start()].strip():
        raise ValueError(f"Unparsed content before first request in {filename}")
    records = []
    previous, line_number = 0, 1
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(data)
        line_number += data[previous:start].count(b"\n")
        previous = start
        raw = data[start:end]
        sep = SEPARATOR.search(raw)
        if not sep:
            raise ValueError(f"No header/body boundary: {filename} record {i}")
        headers = []
        invalid_headers = []
        header_region = raw[match.end() - start:sep.start()]
        for line in header_region.splitlines():
            if b":" not in line:
                invalid_headers.append(line.decode("utf-8"))
                continue
            key, value = line.split(b":", 1)
            headers.append([key.decode("utf-8"), value.lstrip(b" \t").decode("utf-8")])
        tail = raw[sep.end():]
        body = tail.rstrip(b"\r\n")
        lengths = [v for k, v in headers if k.lower() == "content-length"]
        length_issue = False
        if lengths:
            if len(lengths) == 1 and lengths[0].isdigit():
                n = int(lengths[0])
                if len(tail) >= n and not tail[n:].strip(b"\r\n"):
                    body = tail[:n]
                else:
                    length_issue = True
            else:
                length_issue = True
        request = {"method": match.group(1).decode(), "uri": match.group(2).decode("utf-8"),
                   "protocol": match.group(3).decode(), "headers": headers, "body": body.decode("utf-8")}
        text = canonical(request)
        no_cookie = {**request, "headers": [[k, v] for k, v in headers if k.lower() != "cookie"]}
        records.append({"source_file": filename, "source_index": i, "source_line": line_number,
                        "byte_start": start, "byte_end": end, "label": label, "source_split": split,
                        "request_id": digest(text), "without_cookie_hash": digest(canonical(no_cookie)),
                        "raw_sha256": file_hash_bytes(raw), "request": request, "raw_http": raw.decode("utf-8"),
                        "content_length_issue": length_issue, "invalid_header_lines": invalid_headers})
    return records


def file_hash_bytes(raw):
    import hashlib
    return hashlib.sha256(raw).hexdigest()


def screen(record):
    # Analyst-only screening. No source subtype labels are created.
    q = record["request"]
    value = q["uri"] + "\n" + q["body"] + "\n" + "\n".join(v for _, v in q["headers"])
    decoded = unquote_plus(value, encoding="latin-1")
    return {"sql_pattern": bool(SQL.search(decoded)), "xss_pattern": bool(XSS.search(decoded))}


def payload_parts(record):
    q = record["request"]
    if q["method"] == "GET" and "?" in q["uri"]:
        base, _, payload = q["uri"].partition("?")
    elif q["method"] == "POST" and q["body"]:
        base, payload = q["uri"], q["body"]
    else:
        return None
    params = [part.partition("=") for part in payload.split("&")]
    if len(params) > 15 or any(not sep for _, sep, _ in params):
        return None
    headers = [[k, v] for k, v in q["headers"] if k.lower() not in {"cookie", "content-length"}]
    context = canonical([q["method"], base, q["protocol"], headers])
    return context, params, payload


def find_pair(normal, anomalous):
    index = defaultdict(dict)
    for r in normal:
        if any(screen(r).values()):
            continue
        parts = payload_parts(r)
        if not parts:
            continue
        context, params, payload = parts
        for i, (key, _, value) in enumerate(params):
            fingerprint = digest(canonical([context, key, i, params[:i] + params[i + 1:]]))
            if value not in index[fingerprint] and len(index[fingerprint]) < 30:
                index[fingerprint][value] = (r, payload)
    best, score, pairs = None, 0, 0
    for r in anomalous:
        flags = screen(r)
        if not any(flags.values()):
            continue
        parts = payload_parts(r)
        if not parts:
            continue
        context, params, payload = parts
        decoded_payload = unquote_plus(payload, encoding="latin-1")
        if not (SQL.search(decoded_payload) or XSS.search(decoded_payload)):
            continue
        for i, (key, _, _) in enumerate(params):
            fingerprint = digest(canonical([context, key, i, params[:i] + params[i + 1:]]))
            for n, normal_payload in index.get(fingerprint, {}).values():
                if normal_payload == payload:
                    continue
                pairs += 1
                ratio = difflib.SequenceMatcher(None, normal_payload, payload, autojunk=False).ratio()
                if ratio > score:
                    score = ratio
                    best = {"normal": n, "anomalous": r, "changed_parameter": key,
                            "payload_similarity": ratio, "screening_flags": flags,
                            "header_differences": [[a, b] for a, b in itertools.zip_longest(n["request"]["headers"], r["request"]["headers"]) if a != b]}
    if best:
        best["pairs_compared"] = pairs
        best["scope"] = "One raw query/form parameter changed; same endpoint/method/protocol; headers compared ignoring Cookie and Content-Length. Bounded search, not exhaustive."
        best["embedding_similarity_measured"] = False
    return best


def inspect(root):
    root = Path(root)
    all_records, summaries = {}, {}
    for filename, (label, split) in FILES.items():
        path = root / filename
        data = path.read_bytes()
        records = parse_bytes(data, filename, label, split)
        all_records[split] = records
        headers = Counter(k for r in records for k in {name for name, _ in r["request"]["headers"]})
        pattern_counts = Counter()
        for r in records:
            pattern_counts.update(k for k, hit in screen(r).items() if hit)
        summaries[filename] = {"records": len(records), "label": label, "split": split, "bytes": len(data), **file_hashes(path),
                               "methods": dict(Counter(r["request"]["method"] for r in records)),
                               "header_presence": dict(headers), "empty_body": sum(not r["request"]["body"] for r in records),
                               "content_length_issues": sum(r["content_length_issue"] for r in records),
                               "invalid_header_records": sum(bool(r["invalid_header_lines"]) for r in records),
                               "screening_pattern_hits_not_subtype_labels": dict(pattern_counts)}
    overlap = {}
    for a, b in itertools.combinations(all_records, 2):
        overlap[f"{a}/{b}"] = {key: len({r[key] for r in all_records[a]} & {r[key] for r in all_records[b]}) for key in ("request_id", "without_cookie_hash")}
    grouped = defaultdict(set)
    for rows in all_records.values():
        for r in rows:
            grouped[r["request_id"]].add(r["label"])
    anomalous = all_records["source_test_anomalous"]
    examples = {"normal": all_records["source_train"][0]}
    for key, flag in (("sqli_payload", "sql_pattern"), ("xss_payload", "xss_pattern")):
        examples[key] = next((r for r in anomalous if screen(r)[flag]), None)
    pair = find_pair(all_records["source_train"], anomalous)
    total = sum(len(rows) for rows in all_records.values())
    summary = {"files": summaries, "total_records": total,
               "class_counts": dict(Counter(r["label"] for rows in all_records.values() for r in rows)),
               "source_test_records": len(all_records["source_test_normal"]) + len(anomalous),
               "native_labels": ["NORMAL", "ANOMALOUS"], "native_attack_subtype_labels_available": False,
               "overlap": overlap, "unique_exact_requests": len(grouped), "exact_conflicting_requests": sum(len(v) > 1 for v in grouped.values()),
               "analyst_screening_is_ground_truth": False, "license_verified": False,
               "mirror_commit": MIRROR_COMMIT, "primary_url": "http://www.isi.csic.es/dataset/",
               "primary_download_accessible_in_session": False,
               "mirror_url": "https://github.com/msudol/Web-Application-Attack-Datasets/tree/" + MIRROR_COMMIT + "/OriginalDataSets/csic_2010",
               "existing_project_test_used_for_tuning": False,
               "original_csic_test_inspected_for_eda": True}
    assert summary["class_counts"]["NORMAL"] + summary["class_counts"]["ANOMALOUS"] == total
    return summary, examples, pair


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", default="src/data/raw/csic_2010")
    parser.add_argument("--output", default="src/artifacts/data/csic_2010")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    summary, examples, pair = inspect(args.raw)
    write_json(output / "summary.json", summary)
    write_json(output / "examples.json", examples)
    write_json(output / "motivating_pair.json", pair)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if pair:
        print(json.dumps({"normal_index": pair["normal"]["source_index"], "anomalous_index": pair["anomalous"]["source_index"],
                          "parameter": pair["changed_parameter"], "payload_similarity": pair["payload_similarity"]}, indent=2))


if __name__ == "__main__":
    main()
