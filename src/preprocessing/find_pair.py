"""Search development/pool only for an inspectable Normal/SQLi illustration.

The similarity is character similarity, not embedding similarity. Candidate
screening is deliberately conservative and does not adjudicate source labels.
"""

import argparse
from collections import defaultdict
import difflib
import json
from pathlib import Path
import re
from urllib.parse import unquote_plus

from .prepare import canonical, digest, write_json


CLEAN_URI = re.compile(r"[/A-Za-z0-9?&=_.~:@+-]*")
SUSPICIOUS = re.compile(r"<script|alert\(|sleep|union|select\s|order\s+by|\b(?:and|or)\s+['\"\d]|/etc/|\.\./|\$\{|set-cookie|print\(|chr\(", re.I)
SQL_SIGNAL = re.compile(r"union\s+(?:all\s+)?select|select\s|order\s+by|\band\s+['\"\w]+\s*(?:=|>|<)", re.I)


def iter_requests(root):
    for split in ("development", "pool"):
        with (Path(root) / f"{split}.jsonl").open(encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                yield split, record, json.loads(record["request_text"])


def context_key(request):
    return digest(canonical({k: v for k, v in request.items() if k != "uri"}))


def search(root):
    contexts = defaultdict(list)
    normal_count = 0
    for split, r, q in iter_requests(root):
        if r["label"] != "NORMAL" or q["method"] != "GET" or q["body"]:
            continue
        if not CLEAN_URI.fullmatch(unquote_plus(q["uri"])) or SUSPICIOUS.search(unquote_plus(r["request_text"])):
            continue
        normal_count += 1
        contexts[context_key(q)].append((q["uri"], r["request_id"], r["source_row"], split))
    # Limit within-context comparisons; this is a bounded candidate search,
    # not a claim to find the globally most similar pair in the dataset.
    for key in contexts:
        contexts[key] = sorted(contexts[key], key=lambda x: (len(x[0]), x[0], x[1]))[:30]
    best, considered, compared = [], 0, 0
    for split, r, q in iter_requests(root):
        if r["label"] != "SQL_INJECTION" or q["method"] != "GET" or q["body"] or not SQL_SIGNAL.search(unquote_plus(q["uri"])):
            continue
        key = context_key(q)
        if key not in contexts:
            continue
        considered += 1
        for uri, rid, source_row, normal_split in contexts[key]:
            matcher = difflib.SequenceMatcher(None, uri, q["uri"], autojunk=False)
            if matcher.quick_ratio() < 0.80:
                continue
            compared += 1
            ratio = matcher.ratio()
            if ratio < 0.80:
                continue
            best.append({"uri_similarity": ratio, "normal_uri": uri, "attack_uri": q["uri"],
                         "normal_id": rid, "normal_source_row": source_row, "normal_split": normal_split,
                         "attack_id": r["request_id"], "attack_source_row": r["source_row"],
                         "attack_split": split, "context_sha256": key})
            if len(best) > 200:
                best = sorted(best, key=lambda v: (-v["uri_similarity"], v["normal_source_row"], v["attack_source_row"]))[:30]
    best = sorted(best, key=lambda v: (-v["uri_similarity"], v["normal_source_row"], v["attack_source_row"]))[:30]
    return {"method": "Same method/protocol/headers/body; conservative Normal URI screening; explicit SQL syntax in attack URI; at most 30 shortest Normal URIs per context",
            "metric": "difflib.SequenceMatcher(autojunk=False).ratio on raw URI strings",
            "normal_candidates": normal_count, "attacks_with_matching_context": considered,
            "pairs_compared_after_quick_filter": compared, "candidates": best,
            "final_test_read": False, "globally_exhaustive": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed", default="src/data/processed/sr_bh_v1")
    parser.add_argument("--output", default="src/artifacts/data/sr_bh_survey/pair_search.json")
    args = parser.parse_args()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    result = search(args.processed)
    write_json(args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k != "candidates"}, indent=2))
    print(json.dumps(result["candidates"][:3], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
