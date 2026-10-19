"""Bước 3: chạy một pipeline LLM (A0, A1, B, BAL hoặc C) trên một split.

Ví dụ (từ thư mục gốc repo):

    # Chạy thử bằng LLM giả, không cần API key:
    python -m src.experiments.run_llm --config src/configs/experiments/B_k4.json \
        --llm src/configs/llm/mock.json --split development --output src/artifacts/runs/dev/B_mock

    # Chạy thật (key đặt trong file .env, KHÔNG đặt trong config):
    python -m src.experiments.run_llm --config src/configs/experiments/A0.json \
        --llm src/configs/llm/groq.json --env-file .env --split validation \
        --output src/artifacts/runs/validation/A0

Thư mục output của mỗi run gồm:
- `manifest.json`: toàn bộ cấu hình, phiên bản prompt, hash dữ liệu/code.
- `predictions.jsonl`: mỗi dòng là một query: ví dụ đã chọn, prior, nhãn
  đoán, trạng thái, token, độ trễ. Ghi ngay sau mỗi query nên có thể dừng giữa
  chừng rồi chạy lại cùng lệnh để chạy tiếp (resume).
- `metrics.json`: Macro-F1, Accuracy, từng lớp, ma trận nhầm lẫn, LCR@k, chi phí.

Quy tắc an toàn:
- Nhãn thật của query KHÔNG được đưa vào prompt hay dùng để chọn ví dụ, trừ
  khi chạy C với `prior_source = "oracle"`; khi đó run được đánh dấu
  `oracle_analysis` và chỉ dùng để phân tích mức trần.
- Split `test` chỉ chạy được khi thêm `--allow-test`. Hãy khóa cấu hình trên
  validation trước khi dùng cờ này.
- Đổi config, model, dữ liệu hoặc code thì phải dùng thư mục output mới
  (runner sẽ từ chối nếu manifest không khớp).
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import time

from src.analysis.metrics import classification_metrics, label_consistency_rate
from src.common.locking import directory_lock
from src.pipeline_a0 import core
from src.retrieval.knn import knn_vote
from src.retrieval.selectors import class_balanced, fixed_examples, label_aware_rerank, semantic_top_k

from .data_io import LABELS, ROOT, file_sha256, load_jsonl, load_split, sha256_of, split_path, write_json
from .prompting import PROMPT_VERSION, SYSTEM, DemoMajorityMock, build_messages, parse_label

PIPELINES = ("A0", "A1", "B", "BAL", "C")
PRIOR_SOURCES = ("llm", "knn", "oracle")
CODE_FILES = ("src/experiments/run_llm.py", "src/experiments/prompting.py", "src/retrieval/selectors.py",
              "src/retrieval/knn.py", "src/retrieval/views.py", "src/pipeline_a0/core.py")


# ----------------------------------------------------------------------------
# Đọc và kiểm tra cấu hình
# ----------------------------------------------------------------------------

def load_experiment(path):
    """Cấu hình thực nghiệm (file JSON trong src/configs/experiments/)."""
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    config.setdefault("k", 6)
    config.setdefault("n_candidates", 30)
    config.setdefault("max_demo_chars", 1500)
    config.setdefault("fixed_seed", 42)
    if config.get("pipeline") not in PIPELINES:
        raise ValueError(f"pipeline must be one of {PIPELINES}")
    if not isinstance(config["k"], int) or not 1 <= config["k"] <= 20:
        raise ValueError("k must be an integer in 1..20")
    if config["pipeline"] in ("B", "BAL", "C"):
        if not config.get("retrieval_dir"):
            raise ValueError("retrieval_dir is required for B/BAL/C")
        if config["n_candidates"] < config["k"]:
            raise ValueError("n_candidates must be >= k")
    if config["pipeline"] == "C":
        if config.get("prior_source") not in PRIOR_SOURCES:
            raise ValueError(f"prior_source must be one of {PRIOR_SOURCES}")
        if not isinstance(config.get("lambda"), (int, float)) or config["lambda"] < 0:
            raise ValueError("lambda must be a non-negative number")
        if config["prior_source"] == "llm" and not config.get("prior_run"):
            raise ValueError("prior_run (an A0 run directory) is required when prior_source = llm")
        config.setdefault("prior_knn_k", 5)
    return config


def load_llm(path):
    """Cấu hình LLM. `mock` → DemoMajorityMock; còn lại dùng bộ kiểm tra của A0."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("backend") == "mock_demo_majority":
        return {"backend": "mock_demo_majority", "model": DemoMajorityMock.model, "max_request_chars": 32768}
    if raw.get("backend") != "chat_completions":
        raise ValueError("llm backend must be chat_completions or mock_demo_majority")
    return core.load_config(path)


def load_env_file(path):
    """Nạp KEY=VALUE từ file .env vào biến môi trường (không in giá trị ra màn hình).

    Giá trị trong file GHI ĐÈ biến môi trường sẵn có, để khi đổi sang file key của
    thành viên khác (.env.tv2) thì key mới thật sự được dùng.
    """
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if value.strip():
            os.environ[key.strip()] = value.strip().strip('"').strip("'")


# ----------------------------------------------------------------------------
# Chuẩn bị prior cho Pipeline C
# ----------------------------------------------------------------------------

def load_llm_prior(run_dir):
    """Đọc dự đoán của một run A0 đã chạy; prior = None nếu A0 lỗi ở query đó."""
    run_dir = Path(run_dir)
    if not run_dir.is_absolute():
        run_dir = ROOT / run_dir
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest["experiment"]["pipeline"] != "A0":
        raise ValueError("prior_run must be an A0 run")
    priors, usage = {}, {}
    for rec in load_jsonl(run_dir / "predictions.jsonl"):
        priors[rec["request_id"]] = rec["predicted_label"] if rec["status"] == "ok" else None
        usage[rec["request_id"]] = rec.get("usage")
    return priors, usage, {"run_key": manifest["run_key"], "llm_model": manifest["llm"].get("model")}


# ----------------------------------------------------------------------------
# Runner
# ----------------------------------------------------------------------------

def run_experiment(experiment, llm, split, output_dir, limit=None, allow_test=False, client=None,
                   data_dir=None, sleep_seconds=0.0, retry_errors=False):
    if split == "test" and not allow_test:
        raise ValueError("test split is locked; pass allow_test=True only after freezing the configuration")
    kwargs = {} if data_dir is None else {"data_dir": data_dir}
    queries = load_split(split, **kwargs)
    if limit is not None:
        queries = queries[:limit]
    # Tách nhãn ra khỏi dữ liệu query ngay từ đầu: phần chọn ví dụ/prompt chỉ thấy `public`.
    truth = {q["request_id"]: q["label"] for q in queries}
    public = [{"request_id": q["request_id"], "request_text": q["request_text"]} for q in queries]
    pool = {r["request_id"]: r for r in load_split("pool", **kwargs)}
    pipeline = experiment["pipeline"]

    neighbors, retrieval_manifest = {}, None
    if pipeline in ("B", "BAL", "C"):
        rdir = Path(experiment["retrieval_dir"])
        rdir = rdir if rdir.is_absolute() else ROOT / rdir
        full = json.loads((rdir / "manifest.json").read_text(encoding="utf-8"))
        # Chỉ giữ phần ổn định (model, N, hash pool); thời gian chạy hay danh sách split
        # thay đổi khi dựng lại retrieval không được làm hỏng khả năng resume.
        retrieval_manifest = {"encoder": full["encoder"], "n_candidates": full["n_candidates"],
                              "pool_sha256": full["inputs_sha256"]["pool"],
                              "neighbors_sha256": file_sha256(rdir / f"neighbors_{split}.jsonl")}
        neighbors = {r["request_id"]: r["candidates"] for r in load_jsonl(rdir / f"neighbors_{split}.jsonl")}
        missing = [q["request_id"] for q in public if q["request_id"] not in neighbors]
        if missing:
            raise ValueError(f"{len(missing)} queries have no neighbors; rebuild retrieval for split {split}")

    priors, prior_usage, prior_info = {}, {}, None
    experiment_kind = "mock" if llm["backend"] == "mock_demo_majority" else "llm"
    if pipeline == "C":
        source = experiment["prior_source"]
        if source == "llm":
            # "{split}" trong prior_run được thay bằng tên split, ví dụ runs/{split}/A0 -> runs/validation/A0.
            priors, prior_usage, prior_info = load_llm_prior(experiment["prior_run"].format(split=split))
            absent = [q["request_id"] for q in public if q["request_id"] not in priors]
            if absent:
                raise ValueError(f"A0 prior run lacks {len(absent)} queries of this split")
        elif source == "knn":
            priors = {q["request_id"]: knn_vote(neighbors[q["request_id"]][:experiment["n_candidates"]],
                                                experiment["prior_knn_k"])[0] for q in public}
        else:  # oracle: chỉ để phân tích mức trần, KHÔNG phải phương pháp
            priors = dict(truth)
            experiment_kind += "_oracle_analysis"

    fixed = None
    if pipeline == "A1":
        fixed = fixed_examples(list(pool.values()), experiment["k"], experiment["fixed_seed"], LABELS)

    def select(query_id):
        """Trả về danh sách ví dụ đã chọn (theo thứ tự xếp hạng) cho một query."""
        if pipeline == "A0":
            return []
        if pipeline == "A1":
            return fixed
        cands = neighbors[query_id][:experiment["n_candidates"]]
        if pipeline == "B":
            return semantic_top_k(cands, experiment["k"])
        if pipeline == "BAL":
            return class_balanced(cands, experiment["k"])
        return label_aware_rerank(cands, experiment["k"], priors.get(query_id), experiment["lambda"])

    llm_public = {k: v for k, v in llm.items() if k != "mock_responses"}
    run_key = sha256_of({"experiment": experiment, "llm": llm_public, "prompt": [PROMPT_VERSION, SYSTEM],
                         "split": split, "prior": prior_info})
    manifest = {
        "run_key": run_key, "experiment": experiment, "llm": llm_public, "split": split, "limit": limit,
        "experiment_kind": experiment_kind, "prompt_version": PROMPT_VERSION, "system_prompt": SYSTEM,
        "data_sha256": {"queries": file_sha256(split_path(split, **kwargs)), "pool": file_sha256(split_path("pool", **kwargs))},
        "query_ids_sha256": sha256_of([q["request_id"] for q in public]),
        "retrieval": retrieval_manifest, "prior_run": prior_info,
        "code_sha256": {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in CODE_FILES},
        "python": platform.python_version(),
    }
    manifest = json.loads(json.dumps(manifest))
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with directory_lock(output_dir):
        manifest_path = output_dir / "manifest.json"
        if manifest_path.exists():
            old = json.loads(manifest_path.read_text(encoding="utf-8"))
            if old != manifest:
                # Run đã XONG và chỉ khác phiên bản code (cấu hình, prompt, dữ liệu như cũ): không chạy lại, chỉ báo.
                # Run còn dở thì luôn bị chặn, để một run không trộn kết quả của hai phiên bản code.
                strip = lambda m: {k: v for k, v in m.items() if k != "code_sha256"}
                metrics_path = output_dir / "metrics.json"
                finished = metrics_path.exists() and json.loads(metrics_path.read_text(encoding="utf-8")).get("complete")
                if strip(old) == strip(manifest) and finished:
                    return {"selected": len(public), "resumed": len(public), "processed_now": 0,
                            "skipped": "already complete (recorded with an earlier code version)"}
                raise ValueError("manifest/config/data/code changed; use a new output directory")
        else:
            if (output_dir / "predictions.jsonl").exists():
                raise ValueError("predictions without manifest; use a new output directory")
            write_json(manifest_path, manifest)
        # Nếu một query có nhiều dòng (đã chạy lại), dòng sau cùng là kết quả hiện hành.
        done = {r["request_id"]: r for r in core.recover_predictions(output_dir / "predictions.jsonl")}
        if retry_errors:
            # Gọi lại các query từng lỗi API (ví dụ hết quota); dòng lỗi cũ vẫn nằm trong file để truy vết.
            done = {rid: r for rid, r in done.items() if r["status"] != "backend_error"}
        resumed = len(done)
        if client is None and len(done) < len(public):
            client = DemoMajorityMock() if llm["backend"] == "mock_demo_majority" else core.ChatClient(llm)

        stopped = None
        with (output_dir / "predictions.jsonl").open("a", encoding="utf-8") as stream:
            for query in public:
                qid = query["request_id"]
                demos = select(qid)
                demo_rows = [{"request_text": pool[d["request_id"]]["request_text"], "label": d["label"]} for d in demos]
                prompt = build_messages(query["request_text"], demo_rows, experiment["max_demo_chars"])
                cache_key = sha256_of({"run_key": run_key, "request_id": qid, "messages": prompt})
                if qid in done:
                    if done[qid]["cache_key"] != cache_key:
                        raise ValueError("cached prediction does not match the current prompt")
                    continue
                record = {"request_id": qid, "cache_key": cache_key, "pipeline": pipeline,
                          "demo_ids": [d["request_id"] for d in demos], "demo_labels": [d["label"] for d in demos],
                          "demo_scores": [d.get("score") for d in demos],
                          "prior": priors.get(qid) if pipeline == "C" else None,
                          "predicted_label": None, "status": "input_error", "error": None,
                          "raw_output": None, "usage": None, "attempts": 0}
                started = time.perf_counter()
                if len(query["request_text"]) > llm.get("max_request_chars", 32768):
                    record["error"] = "request_too_long; no truncation"
                else:
                    try:
                        record.update(client(prompt))
                        try:
                            record["predicted_label"] = parse_label(record["raw_output"])
                            record["status"] = "ok"
                        except ValueError:
                            record.update(status="invalid_output", error="invalid_label_json")
                    except core.BackendError as exc:
                        if str(exc) == core.QUOTA_EXHAUSTED:
                            # Hết quota trong ngày: KHÔNG ghi dòng lỗi, dừng lại; chạy lại cùng lệnh để tiếp tục.
                            stopped = "quota_exhausted"
                            break
                        record.update(status="backend_error", error=str(exc), attempts=exc.attempts)
                record["latency_seconds"] = round(time.perf_counter() - started, 4)
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
                done[qid] = record
                if sleep_seconds:
                    time.sleep(sleep_seconds)  # tránh vượt giới hạn tốc độ của API miễn phí

        finished = [q for q in public if q["request_id"] in done]
        records = [done[q["request_id"]] for q in finished]
        metrics = summarize(records, [truth[q["request_id"]] for q in finished], prior_usage)
        metrics.update(experiment_kind=experiment_kind, run_key=run_key, pipeline=pipeline, split=split,
                       complete=len(finished) == len(public), n_selected=len(public))
        write_json(output_dir / "metrics.json", metrics)
        result = {"selected": len(public), "resumed": resumed, "processed_now": len(finished) - resumed,
                  "macro_f1": metrics["macro_f1"], "coverage": metrics["coverage"],
                  "status_counts": metrics["status_counts"]}
        if stopped:
            result["stopped"] = f"{stopped}: {len(public) - len(finished)} queries left; rerun the same command later"
        return result


def summarize(records, truths, prior_usage=None):
    """Gộp metrics phân loại + LCR@k + chi phí cho một run."""
    preds = [r["predicted_label"] if r["status"] == "ok" else None for r in records]
    metrics = classification_metrics(truths, preds, LABELS)
    statuses = {}
    for r in records:
        statuses[r["status"]] = statuses.get(r["status"], 0) + 1
    lcr = [label_consistency_rate(r["demo_labels"], t) for r, t in zip(records, truths) if r["demo_labels"]]
    tokens = [r["usage"]["total_tokens"] for r in records if r.get("usage") and "total_tokens" in r["usage"]]
    prior_tokens = [u["total_tokens"] for u in (prior_usage or {}).values() if u and "total_tokens" in u]
    latencies = sorted(r["latency_seconds"] for r in records if r["attempts"] > 0)
    metrics.update(
        status_counts=statuses,
        invalid_output_rate=statuses.get("invalid_output", 0) / len(records) if records else None,
        backend_error_rate=statuses.get("backend_error", 0) / len(records) if records else None,
        lcr_at_k=sum(lcr) / len(lcr) if lcr else None,
        cost={"llm_calls_per_query": 1 + (1 if prior_usage else 0),
              "mean_total_tokens": sum(tokens) / len(tokens) if tokens else None,
              "mean_prior_tokens": sum(prior_tokens) / len(prior_tokens) if prior_tokens else None,
              "token_samples": len(tokens),
              "mean_latency_seconds": sum(latencies) / len(latencies) if latencies else None,
              "p95_latency_seconds": latencies[int(0.95 * (len(latencies) - 1))] if latencies else None},
    )
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", required=True, help="file cấu hình thực nghiệm (pipeline, k, λ, …)")
    parser.add_argument("--llm", required=True, help="file cấu hình LLM (mock hoặc chat_completions)")
    parser.add_argument("--split", default="development", choices=["development", "validation", "test"])
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, help="chỉ chạy N query đầu (để thử nhanh)")
    parser.add_argument("--env-file", help="file .env chứa A0_API_KEY, A0_BASE_URL, A0_MODEL")
    parser.add_argument("--sleep", type=float, default=0.0, help="nghỉ giữa hai lần gọi (giây)")
    parser.add_argument("--allow-test", action="store_true", help="CHỈ dùng sau khi đã khóa cấu hình")
    parser.add_argument("--retry-errors", action="store_true", help="gọi lại các query trước đó bị lỗi API")
    args = parser.parse_args()
    if args.env_file:
        load_env_file(args.env_file)
    try:
        result = run_experiment(load_experiment(args.config), load_llm(args.llm), args.split, args.output,
                                args.limit, args.allow_test, sleep_seconds=args.sleep,
                                retry_errors=args.retry_errors)
    except (ValueError, OSError, KeyError) as exc:
        # Không in nội dung lỗi của provider để tránh lộ thông tin nhạy cảm.
        parser.exit(2, f"run_llm stopped: {type(exc).__name__}: {str(exc)[:200]}\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
