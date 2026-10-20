"""Bước 1 của thực nghiệm: dựng kho vector cho pool và tìm top-N cho từng query.

Chạy (từ thư mục gốc repo):

    python -m src.experiments.build_retrieval --output src/artifacts/retrieval/minilm

Kết quả trong thư mục output:
- `pool_vectors.npy`, `pool_meta.jsonl`: vector và nhãn của 3.000 ví dụ pool.
- `neighbors_<split>.jsonl`: với mỗi query, danh sách top-N ứng viên
  (request_id, label CỦA ỨNG VIÊN, similarity, rank).
  File này KHÔNG chứa nhãn của query, nên các pipeline có thể đọc an toàn.
- `manifest.json`: model, tham số, hash dữ liệu, thời gian chạy.

Mặc định chỉ tính cho development và validation. Tập test chỉ được tính khi
thêm `--include-test`. Bước này không đọc nhãn test, nhưng tách riêng để
nhóm chủ động quyết định thời điểm động vào test.
"""

import argparse
import time

from src.retrieval.embedding import DEFAULT_MODEL, SentenceTransformerEncoder, encode_requests
from src.retrieval.index import VectorIndex

from .data_io import file_sha256, load_split, split_path, write_json, write_jsonl


def build(encoder, output, splits, n_candidates, data_dir=None):
    kwargs = {} if data_dir is None else {"data_dir": data_dir}
    started = time.perf_counter()
    pool = load_split("pool", **kwargs)
    index = VectorIndex([r["request_id"] for r in pool], [r["label"] for r in pool], encode_requests(encoder, pool))
    index.save(output)
    timings = {"pool_encode_seconds": round(time.perf_counter() - started, 2)}
    sizes = {}
    for split in splits:
        t0 = time.perf_counter()
        queries = load_split(split, **kwargs)
        neighbors = index.search(encode_requests(encoder, queries), n_candidates)
        # Chỉ ghi request_id của query, không ghi nhãn query.
        write_jsonl(f"{output}/neighbors_{split}.jsonl",
                    [{"request_id": q["request_id"], "candidates": cands} for q, cands in zip(queries, neighbors)])
        timings[f"{split}_seconds"] = round(time.perf_counter() - t0, 2)
        sizes[split] = len(queries)
    manifest = {"encoder": encoder.describe(), "n_candidates": n_candidates, "pool_size": len(pool),
                "query_sizes": sizes, "timings": timings,
                "inputs_sha256": {s: file_sha256(split_path(s, **kwargs)) for s in ["pool", *splits]}}
    write_json(f"{output}/manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-seq-length", type=int, default=256)
    parser.add_argument("--n-candidates", type=int, default=50, help="N ứng viên lưu cho mỗi query (≥ N dùng ở C)")
    parser.add_argument("--include-test", action="store_true")
    args = parser.parse_args()
    splits = ["development", "validation"] + (["test"] if args.include_test else [])
    encoder = SentenceTransformerEncoder(args.model, args.max_seq_length)
    print(build(encoder, args.output, splits, args.n_candidates))


if __name__ == "__main__":
    main()
