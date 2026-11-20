"""Tính sẵn thông tin pool cho các cách chọn ví dụ cải tiến (không gọi LLM).

    python -m src.experiments.build_pool_aux --retrieval src/artifacts/retrieval/minilm

Ghi `pool_aux.json` vào thư mục retrieval:
- `enn`: các ví dụ pool bị Wilson-ENN (k = 3) đánh dấu nghi nhiễu nhãn;
- `cll`: số hạng nhãn của CLL-RetICL cho từng ví dụ pool.
Xem giải thích trong `src/retrieval/pool_aux.py`.
"""

import argparse
from collections import Counter
from pathlib import Path

from src.retrieval.pool_aux import AUX_FILE, LABEL_WORDS, PoolSpace, cll_label_terms, enn_flags

from .data_io import file_sha256, write_json


def build(retrieval_dir, encoder, enn_k=3):
    retrieval_dir = Path(retrieval_dir)
    space = PoolSpace.load(retrieval_dir)
    flagged = enn_flags(space, enn_k)
    words = [LABEL_WORDS[label] for label in LABEL_WORDS]
    label_vectors = dict(zip(LABEL_WORDS, encoder.encode(words)))
    labels_of = dict(zip(space.ids, space.labels))
    aux = {
        "pool_vectors_sha256": file_sha256(retrieval_dir / "pool_vectors.npy"),
        "enn": {"k": enn_k, "flagged": flagged,
                "flagged_by_label": dict(sorted(Counter(labels_of[r] for r in flagged).items()))},
        "cll": {"label_words": LABEL_WORDS, "encoder": encoder.describe(), "term": cll_label_terms(space, label_vectors)},
    }
    write_json(retrieval_dir / AUX_FILE, aux)
    return {"pool": len(space.ids), "enn_flagged": len(flagged), "enn_flagged_by_label": aux["enn"]["flagged_by_label"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--retrieval", default="src/artifacts/retrieval/minilm")
    parser.add_argument("--enn-k", type=int, default=3)
    args = parser.parse_args()
    from src.retrieval.embedding import SentenceTransformerEncoder
    print(build(args.retrieval, SentenceTransformerEncoder(), args.enn_k))


if __name__ == "__main__":
    main()
