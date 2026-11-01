"""Phân tích nhãn nhiễu ở lớp Normal (phân tích độ nhạy, KHÔNG sửa nhãn, KHÔNG gọi LLM).

Chạy (từ thư mục gốc repo):

    python -m src.analysis.label_noise --output src/artifacts/reports/label_noise

Câu hỏi: bao nhiêu request mang nhãn NORMAL trong SR-BH 2020 thật ra chứa payload
tấn công rõ ràng (`sleep(15)`, `cat /etc/passwd`, `<script>`...), và các con số
chính (Macro-F1, FPR Normal) thay đổi thế nào nếu bỏ riêng các request đó ra.

Cách làm:
1. Một bộ quy tắc cố định (`SUSPICIOUS_RULES`) quét URI và body (giải mã URL hai
   lần) và giá trị header. Quy tắc chỉ nhìn nội dung request, không nhìn dự đoán
   của model. Request NORMAL khớp ít nhất một quy tắc được gọi là "Normal đáng ngờ".
2. Đếm Normal đáng ngờ trong pool, validation, test 1–300 và test 301–600. Quét
   cùng quy tắc trên các lớp tấn công để biết quy tắc bắt payload tấn công tốt đến đâu.
3. Với mỗi run LLM đã có: metrics gốc và metrics khi BỎ các Normal đáng ngờ khỏi
   tập đánh giá; chênh lệch so với B kèm CI bootstrap 95% trên tập đã bỏ.
4. Nhiễm bẩn ví dụ: bao nhiêu prompt có ví dụ "NORMAL" mà thật ra chứa payload,
   và câu tấn công có hay bị đoán thành NORMAL hơn khi có ví dụ đó không.

Kết quả chính của đề tài vẫn tính trên nhãn gốc; đây chỉ là phân tích bổ sung.
Danh sách Normal đáng ngờ được xuất ra `flagged_normal.jsonl` để người kiểm tra tay.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from urllib.parse import unquote_plus

from src.experiments.data_io import LABELS, ROOT, load_jsonl, load_split, write_json, write_jsonl

from .metrics import classification_metrics, paired_bootstrap

# Mỗi quy tắc là một dấu hiệu payload tấn công phổ biến; khớp không phân biệt hoa thường.
SUSPICIOUS_RULES = {
    "time_delay": r"\bsleep\s*\(|\bbenchmark\s*\(|waitfor\s+delay|pg_sleep",
    "sensitive_file": r"/etc/(passwd|shadow|hosts)|win\.ini|boot\.ini",
    "script_tag": r"<\s*script|javascript:|\bonerror\s*=|\balert\s*\(",
    "shell_command": r"/bin/(sh|bash|sleep|cat|ls)|[;&|`]\s*(cat|id|ls|whoami|uname|ping|wget|curl)\b|\$\(|\(\)\s*\{",
    "header_injection": r"set-cookie\s*:|[\r\n]",
    "path_traversal": r"\.\./|\.\.\\|\b[a-z]:\\",
    "sql_keywords": r"\bunion\b.+\bselect\b|\bor\s+1\s*=\s*1|\band\s+1\s*=\s*1|'\s*or\s*'1'\s*=\s*'1",
}
_COMPILED = {name: re.compile(pattern, re.IGNORECASE) for name, pattern in SUSPICIOUS_RULES.items()}

# (tên nhóm, split, offset, limit, thư mục run, tên run tham chiếu)
GROUPS = (
    ("validation", "validation", 0, None, "src/artifacts/runs/validation", "B_semantic_k4"),
    ("test 1-300", "test", 0, 300, "src/artifacts/runs/test", "B_semantic_k4"),
    ("test 301-600", "test", 300, 300, "src/artifacts/runs/test_301_600", "B_semantic_k4"),
    ("test 1-300 (gpt-oss-120b)", "test", 0, 300, "src/artifacts/runs_120b/test", "B_semantic_k4_120b"),
)


def _decode(text):
    # Payload trong SR-BH thường bị mã hóa URL một hoặc hai lần.
    return unquote_plus(unquote_plus(text or ""))


def suspicious_rules(request_text):
    """Tên các quy tắc mà request khớp (danh sách rỗng nếu không đáng ngờ)."""
    request = json.loads(request_text)
    parts = [_decode(request.get("uri")), _decode(request.get("body"))]
    headers = " ".join(_decode(str(v)) for v in (request.get("headers") or {}).values())
    matched = [name for name, rx in _COMPILED.items() if any(rx.search(p) for p in parts)]
    # Header được nối bằng dấu cách nên quy tắc xuống dòng không áp dụng cho header.
    matched += [name for name, rx in _COMPILED.items()
                if name not in matched and name != "header_injection" and rx.search(headers)]
    return matched


def noise_summary(rows):
    """Số request khớp quy tắc theo từng lớp; với NORMAL đây là ước lượng nhãn sai."""
    by_label = {label: {"n": 0, "flagged": 0} for label in LABELS}
    rules = Counter()
    for row in rows:
        hits = suspicious_rules(row["request_text"])
        by_label[row["label"]]["n"] += 1
        by_label[row["label"]]["flagged"] += bool(hits)
        if row["label"] == "NORMAL":
            rules.update(hits)
    for value in by_label.values():
        value["rate"] = value["flagged"] / value["n"] if value["n"] else None
    return {"by_label": by_label, "normal_rules": dict(rules.most_common())}


def _predictions(records, ids):
    return [records[q]["predicted_label"] if records[q]["status"] == "ok" else None for q in ids]


def sensitivity(rows, runs, reference, n_resamples=2000):
    """`runs`: {tên run: {request_id: bản ghi dự đoán}}. So sánh metrics gốc với metrics khi bỏ Normal đáng ngờ."""
    flagged = {r["request_id"] for r in rows if r["label"] == "NORMAL" and suspicious_rules(r["request_text"])}
    all_ids = [r["request_id"] for r in rows]
    kept_ids = [q for q in all_ids if q not in flagged]
    truth = {r["request_id"]: r["label"] for r in rows}
    y_all, y_kept = [truth[q] for q in all_ids], [truth[q] for q in kept_ids]
    ref_kept = _predictions(runs[reference], kept_ids) if reference in runs else None
    table = []
    for name, records in runs.items():
        full = classification_metrics(y_all, _predictions(records, all_ids), LABELS)
        kept_preds = _predictions(records, kept_ids)
        kept = classification_metrics(y_kept, kept_preds, LABELS)
        normal_fp = [q for q in all_ids if truth[q] == "NORMAL" and records[q]["predicted_label"] != "NORMAL"]
        entry = {"name": name, "n": len(all_ids), "n_kept": len(kept_ids),
                 "macro_f1": full["macro_f1"], "normal_fpr": full["normal_false_positive_rate"],
                 "normal_f1": full["per_class"]["NORMAL"]["f1"],
                 "macro_f1_kept": kept["macro_f1"], "normal_fpr_kept": kept["normal_false_positive_rate"],
                 "normal_f1_kept": kept["per_class"]["NORMAL"]["f1"],
                 "normal_false_positives": len(normal_fp),
                 "normal_false_positives_flagged": sum(q in flagged for q in normal_fp)}
        if ref_kept is not None and name != reference:
            boot = paired_bootstrap(y_kept, kept_preds, ref_kept, LABELS, n_resamples)
            entry["kept_vs_reference"] = {"diff": boot["observed_diff"], "ci95": boot["ci95"]}
        table.append(entry)
    return {"n_flagged_normal": len(flagged), "n_normal": sum(t == "NORMAL" for t in y_all), "runs": table}


def demo_contamination(rows, records, flagged_pool):
    """Ví dụ NORMAL đáng ngờ trong prompt và tỷ lệ câu tấn công bị đoán thành NORMAL."""
    groups = {True: {"attack_queries": 0, "predicted_normal": 0}, False: {"attack_queries": 0, "predicted_normal": 0}}
    with_bad = 0
    for row in rows:
        rec = records[row["request_id"]]
        has_bad = any(d in flagged_pool for d in rec["demo_ids"])
        with_bad += has_bad
        if row["label"] != "NORMAL":
            groups[has_bad]["attack_queries"] += 1
            groups[has_bad]["predicted_normal"] += rec["predicted_label"] == "NORMAL"
    for value in groups.values():
        value["miss_rate"] = value["predicted_normal"] / value["attack_queries"] if value["attack_queries"] else None
    return {"queries_with_flagged_normal_demo": with_bad / len(rows) if rows else None,
            "with_flagged_demo": groups[True], "without_flagged_demo": groups[False]}


def load_runs(run_root):
    """{tên run (theo manifest): {request_id: bản ghi}} cho mọi run con đã chạy xong."""
    runs = {}
    for run_dir in sorted(Path(run_root).iterdir()):
        if not (run_dir / "manifest.json").exists():
            continue
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        records = {}
        for rec in load_jsonl(run_dir / "predictions.jsonl"):
            records[rec["request_id"]] = rec  # dòng sau cùng là kết quả hiện hành
        runs[manifest["experiment"].get("name", run_dir.name)] = records
    return runs


def analyze(groups=GROUPS, n_resamples=2000, data_dir=None):
    kwargs = {} if data_dir is None else {"data_dir": data_dir}
    pool = load_split("pool", **kwargs)
    flagged_pool = {r["request_id"] for r in pool if r["label"] == "NORMAL" and suspicious_rules(r["request_text"])}
    result = {"rules": SUSPICIOUS_RULES, "pool": noise_summary(pool), "groups": []}
    flagged_rows = [{"split": "pool", "position": i + 1, "request_id": r["request_id"],
                     "rules": suspicious_rules(r["request_text"]),
                     "uri": _decode(json.loads(r["request_text"]).get("uri"))[:300]}
                    for i, r in enumerate(pool) if r["request_id"] in flagged_pool]
    for name, split, offset, limit, run_root, reference in groups:
        rows = load_split(split, **kwargs)[offset:]
        rows = rows[:limit] if limit else rows
        run_root = Path(run_root) if Path(run_root).is_absolute() else ROOT / run_root
        if not run_root.exists():
            continue
        runs = {k: v for k, v in load_runs(run_root).items() if all(r["request_id"] in v for r in rows)}
        group = {"name": name, "split": split, "offset": offset, "n": len(rows), "reference": reference,
                 "noise": noise_summary(rows), "sensitivity": sensitivity(rows, runs, reference, n_resamples),
                 "demo_contamination": {k: demo_contamination(rows, v, flagged_pool)
                                        for k, v in runs.items() if any(r["demo_ids"] for r in v.values())}}
        result["groups"].append(group)
        if not name.endswith("(gpt-oss-120b)"):
            flagged_rows += [{"split": name, "position": offset + i + 1, "request_id": r["request_id"],
                              "rules": suspicious_rules(r["request_text"]),
                              "uri": _decode(json.loads(r["request_text"]).get("uri"))[:300]}
                             for i, r in enumerate(rows)
                             if r["label"] == "NORMAL" and suspicious_rules(r["request_text"])]
    result["flagged_pool_normal"] = len(flagged_pool)
    return result, flagged_rows


def to_markdown(result):
    pct = lambda v: "–" if v is None else f"{v:.1%}"
    pool = result["pool"]["by_label"]
    lines = ["# Nhãn nhiễu ở lớp Normal: phân tích độ nhạy", "",
             "Số liệu tự sinh bởi `src/analysis/label_noise.py`; không gọi LLM, không sửa nhãn.", "",
             "\"Normal đáng ngờ\" = request mang nhãn NORMAL nhưng khớp ít nhất một quy tắc payload tấn công "
             "(xem `SUSPICIOUS_RULES`). Danh sách để kiểm tra tay: `flagged_normal.jsonl`.", "",
             "## 1. Tỷ lệ khớp quy tắc theo lớp", "",
             "| Tập | " + " | ".join(LABELS) + " |", "| --- |" + " ---: |" * len(LABELS)]
    sets = [("pool", result["pool"])] + [(g["name"], g["noise"]) for g in result["groups"]
                                          if not g["name"].endswith("(gpt-oss-120b)")]
    for name, summary in sets:
        cells = [f"{v['flagged']}/{v['n']} ({pct(v['rate'])})" for v in (summary["by_label"][l] for l in LABELS)]
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    lines += ["", "Với NORMAL, đây là ước lượng số nhãn sai. Với các lớp tấn công, đây chỉ cho biết quy tắc "
              "bắt được bao nhiêu payload (quy tắc hẹp, nên không bắt hết).", "",
              "Quy tắc khớp nhiều nhất ở Normal trong pool: "
              + ", ".join(f"`{k}` {v}" for k, v in result["pool"]["normal_rules"].items()) + ".", ""]
    lines += ["## 2. Metrics gốc và khi bỏ Normal đáng ngờ", ""]
    for g in result["groups"]:
        s = g["sensitivity"]
        lines += [f"### {g['name']} ({g['n']} request, {s['n_flagged_normal']}/{s['n_normal']} Normal đáng ngờ bị bỏ)", "",
                  "| Run | Macro-F1 gốc | FPR Normal gốc | F1 Normal gốc | Normal bị báo nhầm (đáng ngờ) | "
                  "Macro-F1 khi bỏ | FPR khi bỏ | F1 Normal khi bỏ | So với tham chiếu khi bỏ [CI 95%] |",
                  "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
        for r in s["runs"]:
            vs = r.get("kept_vs_reference")
            vs = f"{vs['diff']:+.3f} [{vs['ci95'][0]:+.3f}; {vs['ci95'][1]:+.3f}]" if vs else "(tham chiếu)"
            lines.append(f"| {r['name']} | {r['macro_f1']:.3f} | {pct(r['normal_fpr'])} | {r['normal_f1']:.2f} | "
                         f"{r['normal_false_positives']} ({r['normal_false_positives_flagged']}) | "
                         f"{r['macro_f1_kept']:.3f} | {pct(r['normal_fpr_kept'])} | {r['normal_f1_kept']:.2f} | {vs} |")
        lines.append("")
    lines += ["## 3. Nhiễm bẩn ví dụ: prompt có ví dụ \"NORMAL\" chứa payload", "",
              "| Tập | Run | Query có ≥ 1 ví dụ Normal đáng ngờ | Câu tấn công bị đoán NORMAL: có ví dụ đó | "
              "Không có ví dụ đó |", "| --- | --- | ---: | ---: | ---: |"]
    for g in result["groups"]:
        for name, c in g["demo_contamination"].items():
            w, wo = c["with_flagged_demo"], c["without_flagged_demo"]
            lines.append(f"| {g['name']} | {name} | {pct(c['queries_with_flagged_normal_demo'])} | "
                         f"{w['predicted_normal']}/{w['attack_queries']} ({pct(w['miss_rate'])}) | "
                         f"{wo['predicted_normal']}/{wo['attack_queries']} ({pct(wo['miss_rate'])}) |")
    lines += ["", "Kết quả chính của đề tài vẫn tính trên nhãn gốc; bảng trên chỉ là phân tích độ nhạy.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", default="src/artifacts/reports/label_noise")
    parser.add_argument("--resamples", type=int, default=2000)
    args = parser.parse_args()
    result, flagged_rows = analyze(n_resamples=args.resamples)
    output = Path(args.output)
    write_json(output / "label_noise.json", result)
    write_jsonl(output / "flagged_normal.jsonl", flagged_rows)
    (output / "label_noise.md").write_text(to_markdown(result), encoding="utf-8")
    print(to_markdown(result))


if __name__ == "__main__":
    main()
