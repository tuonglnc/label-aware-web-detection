# 📅 KẾ HOẠCH THỰC THI CHI TIẾT THÁNG 10/2026 (ACTION PLAYBOOK)

> **Đề tài:** Label-Aware Retrieval for LLM-Based Web Attack Detection  
> **Ràng buộc nghiên cứu cốt lõi:** Label-aware **rerank**, **hoàn toàn không train model**, LLM qua Ollama local / free API (Groq, Google AI Studio)  
> **Xuất phát điểm (01/10):** Literature review sơ bộ ✅ | Dataset phân tích EDA ✅ | Code = 0 | Dataset chưa chốt ❌  

---

## 🗓️ TỔNG QUAN 4 TUẦN THÁNG 10

| Tuần | Ngày | Focus | Phase (Roadmap) | Must-have deliverable |
|:---:|:---|:---|:---|:---|
| **W1** | 01–07/10 | Chốt dataset + Setup môi trường | Phase 0 cleanup + Phase 2 bắt đầu | Dataset chốt, env chạy được, Ollama test OK |
| **W2** | 08–14/10 | Tiền xử lý dữ liệu (Dedup + Split) | Phase 2 (Data) | File `.parquet` sạch: retrieval pool + test set |
| **W3** | 15–21/10 | Pipeline A (Zero-shot) + B (kNN RAG) | Phase 3 (Infrastructure) | Macro-F1 A, B và LCR@k B có số thật |
| **W4** | 22–31/10 | Pipeline C (Label-Aware Rerank) | Phase 4 (Method core) | So sánh sơ bộ A vs B vs C, LCR@k C > B |

---

## 📦 TUẦN 1 (01–07/10): CHỐT DATASET + SETUP MÔI TRƯỜNG

### 🎯 Mục tiêu cuối tuần
- Chốt chính thức dataset (có file lập luận rõ ràng).
- Ollama chạy được trên máy local hoặc cấu hình free API (Groq / Gemini Flash).
- Cấu trúc thư mục code sẵn sàng.

---

### 📋 Task list W1

#### 🔴 Task 1.1 — Khảo sát + chốt dataset (Ưu tiên cao nhất)
- [ ] **1.1a.** Tải CSIC 2010 từ Kaggle: `https://www.kaggle.com/datasets/ispangler/csic-2010-http-dataset`
  - Đánh giá: Có bao nhiêu dòng? Nhãn binary hay multiclass?
- [ ] **1.1b.** Khảo sát thêm dataset Web Attack multiclass.
- [ ] **1.1c.** Hoàn thành bảng so sánh:

| Tiêu chí | CAPEC (đã có) | CSIC 2010 | Dataset mới |
|:---|:---|:---|:---|
| Số mẫu sau dedup | ~346K unique | ? | ? |
| Số class rõ ràng | 12 (nhiều noise) | ? (binary?) | ? |
| HTTP path đầy đủ? | ✓ URL path | ? | ? |
| Nhãn rõ không? | ⚠️ CAPEC noise | ? | ? |
| Hard cases? | ✓ 1,430 paths | ? | ? |

- [ ] **1.1d.** Chốt quyết định vào `mini-reports/p1_dataset_selection_report.md`:
  - **Phương án A (Khuyến nghị):** CAPEC (lọc 5–6 class sạch) làm primary benchmark, CSIC 2010 làm Out-of-Distribution (OOD) test.
  - **Phương án B:** Dùng dataset khác nếu chất lượng multiclass vượt trội rõ rệt.

---

#### 🔵 Task 1.2 — Setup môi trường Python

```bash
conda create -n itp python=3.10 -y
conda activate itp
pip install pandas numpy scikit-learn matplotlib seaborn tqdm
pip install faiss-cpu sentence-transformers
pip install requests httpx python-dotenv groq google-generativeai
# Kiểm tra
python -c "import pandas, faiss, sentence_transformers; print('Environment OK')"
pip freeze > requirements.txt
```

---

#### 🟢 Task 1.3 — Cài và test Ollama Local (hoặc Free API)

```bash
# 1. Cài Ollama từ https://ollama.com
# 2. Tải model nhẹ, hỗ trợ instruction tốt:
ollama pull qwen2.5:7b-instruct    # ~4.7 GB (khuyến nghị nếu có GPU/RAM 16GB)
# Hoặc model siêu nhẹ nếu máy yếu:
ollama pull qwen2.5:3b-instruct    # ~2.3 GB
```

```python
# Test nhanh trong Python: test_ollama.py
import requests

def llm_query(prompt, model="qwen2.5:7b-instruct"):
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=60
    )
    return resp.json()["response"]

req = "GET /search?q=select+username+from+users HTTP/1.1"
result = llm_query(
    f"Classify this HTTP request into ONE label: [Normal, SQL Injection, Path Traversal, XSS]\n"
    f"Request: {req}\nLabel:"
)
print("Kết quả:", result)  # Mong đợi: SQL Injection
```

---

#### 🟡 Task 1.4 — Khởi tạo cấu trúc thư mục code

```
src/
├── data/
│   ├── raw/          ← dataset thô (cho vào .gitignore)
│   ├── processed/    ← parquet sạch sau dedup
│   └── splits/       ← split_hash.json, retrieval_pool & test_set
├── retrieval/        ← FAISS index, rerank logic, LLM prior module
├── llm/              ← client.py, cache.json, prompt templates
├── eval/             ← metrics (F1, LCR@k, error breakdown)
├── experiments/      ← config yaml cho từng thí nghiệm
├── results/          ← kết quả log parquet / json
└── scripts/          ← run_pipeline_a.py, run_pipeline_b.py, run_pipeline_c.py
```

---

## 🧹 TUẦN 2 (08–14/10): TIỀN XỬ LÝ DỮ LIỆU (DEDUP + SPLIT)

### 🎯 Mục tiêu cuối tuần
- Có file `retrieval_pool.parquet` và `test_set.parquet` sạch 100%, không data leakage.
- Tách riêng `hard_cases.parquet` (1,430 requests có nhãn xung đột) để phân tích sâu.

---

### 📋 Task list W2

#### 🔴 Task 2.1 — Viết script Deduplication (`data/dedup.py`)

```python
# data/dedup.py
import pandas as pd
from urllib.parse import unquote

df = pd.read_csv("data/raw/data_capec_multilabel.csv")

# 1. Target 5-6 attack classes chính
TARGET_CLASSES = {
    "000 - Normal":                  "Normal",
    "66 - SQL Injection":            "SQL Injection",
    "126 - Path Traversal":          "Path Traversal",
    "242 - Code Injection":          "Code Injection",
    "34 - HTTP Response Splitting":  "HTTP Response Splitting",
    "88 - OS Command Injection":     "OS Command Injection",
}

# 2. Format input text cho LLM
def format_request(row):
    method = row.get("request_http_method", "GET")
    path   = unquote(str(row.get("request_http_request", "/")))
    return f"{method} {path}"

df["input_text"] = df.apply(format_request, axis=1)

# 3. Exact row dedup
df = df.drop_duplicates(subset=["input_text", "label"])

# 4. Tách hard cases (cùng path, khác label do annotation noise)
path_label_counts = df.groupby("input_text")["label"].nunique()
hard_paths = path_label_counts[path_label_counts > 1].index
hard_cases = df[df["input_text"].isin(hard_paths)]
df_clean   = df[~df["input_text"].isin(hard_paths)]

print(df_clean["label"].value_counts())
hard_cases.to_parquet("data/processed/hard_cases.parquet")
df_clean.to_parquet("data/processed/clean_dataset.parquet")
```

---

#### 🔴 Task 2.2 — Stratified Split & Kiểm tra chống Leakage (`data/split.py`)

```python
# data/split.py
import hashlib, json
import pandas as pd
from sklearn.model_selection import train_test_split

df_clean = pd.read_parquet("data/processed/clean_dataset.parquet")

# 80% Retrieval DB Pool, 20% Test Set (Stratified)
df_pool, df_test = train_test_split(
    df_clean,
    test_size=0.20,
    stratify=df_clean["label"],
    random_state=42
)

# Chống rò rỉ dữ liệu tuyệt đối
pool_set = set(df_pool["input_text"])
test_set = set(df_test["input_text"])
overlap  = pool_set & test_set
assert len(overlap) == 0, f"DATA LEAKAGE DETECTED: {len(overlap)} samples!"
print("✓ Anti-leakage test PASSED: 0 overlap between Pool and Test.")

# Lưu hash để đảm bảo tính tái lập (Reproducibility)
split_hash = {
    "n_pool": len(df_pool),
    "n_test": len(df_test),
    "pool_sha256": hashlib.sha256("".join(sorted(df_pool["input_text"])).encode()).hexdigest(),
    "test_sha256": hashlib.sha256("".join(sorted(df_test["input_text"])).encode()).hexdigest(),
    "random_state": 42
}
json.dump(split_hash, open("data/splits/split_hash.json", "w"), indent=2)

df_pool.to_parquet("data/processed/retrieval_pool.parquet")
df_test.to_parquet("data/processed/test_set.parquet")
```

---

## ⚙️ TUẦN 3 (15–21/10): PIPELINE A (ZERO-SHOT) + B (kNN RAG)

### 🎯 Mục tiêu cuối tuần
- `llm/client.py` hoàn chỉnh với Disk Cache (tránh tốn inference nhiều lần).
- Pipeline A (Zero-shot) chạy xong → lấy Macro-F1 A.
- Pipeline B (Vanilla kNN + LLM) chạy xong → lấy Macro-F1 B và LCR@k B.

---

### 📋 Task list W3

#### 🔴 Task 3.1 — LLM Client với Disk Cache (`llm/client.py`)

```python
# llm/client.py
import requests, hashlib, json, os

LABEL_LIST = ["Normal", "SQL Injection", "Path Traversal",
              "Code Injection", "HTTP Response Splitting", "OS Command Injection"]

SYSTEM_PROMPT = (
    "You are a web security analyst. "
    f"Classify the HTTP request into exactly ONE label from: {LABEL_LIST}. "
    "Respond ONLY with the label name, nothing else."
)

CACHE_FILE = "llm/cache.json"
_cache = json.load(open(CACHE_FILE)) if os.path.exists(CACHE_FILE) else {}

def classify(request_text: str, demonstrations: list = None,
             model: str = "qwen2.5:7b-instruct") -> str:
    demo_block = ""
    if demonstrations:
        demo_block = "\n".join(
            f"Request: {d['input']}\nLabel: {d['label']}" for d in demonstrations
        )
        demo_block = f"Demonstrations:\n{demo_block}\n\n"

    prompt = f"{SYSTEM_PROMPT}\n\n{demo_block}Request: {request_text}\nLabel:"
    key = hashlib.md5(prompt.encode()).hexdigest()

    if key in _cache:
        return _cache[key]

    resp = requests.post("http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False}, timeout=60)
    raw = resp.json().get("response", "").strip()

    # Match nhãn chuẩn
    matched = next((l for l in LABEL_LIST if l.lower() in raw.lower()), "INVALID")
    _cache[key] = matched
    json.dump(_cache, open(CACHE_FILE, "w"))
    return matched
```

---

#### 🔴 Task 3.2 — Pipeline A Runner (`scripts/run_pipeline_a.py`)

```python
# scripts/run_pipeline_a.py
from llm.client import classify
import pandas as pd
from sklearn.metrics import f1_score, classification_report
from tqdm import tqdm

df_test = pd.read_parquet("data/processed/test_set.parquet")
# Chạy mẫu nhanh 500 dòng hoặc full test
preds = [classify(row["input_text"]) for _, row in tqdm(df_test.iterrows(), total=len(df_test))]

df_test["pred_a"] = preds
macro_f1 = f1_score(df_test["label"], preds, average="macro", zero_division=0)
print(f"\n=== Pipeline A (Zero-shot) Macro-F1: {macro_f1:.4f} ===")
print(classification_report(df_test["label"], preds, zero_division=0))
df_test.to_parquet("results/pipeline_a_results.parquet")
```

---

#### 🔴 Task 3.3 — Pipeline B (Vanilla kNN + LLM) (`scripts/run_pipeline_b.py`)

```python
# retrieval/index.py
from sentence_transformers import SentenceTransformer
import faiss, numpy as np, pandas as pd

embedder = SentenceTransformer("all-MiniLM-L6-v2")

def build_index(df_pool):
    texts = df_pool["input_text"].tolist()
    embs = embedder.encode(texts, batch_size=128, show_progress_bar=True, normalize_embeddings=True)
    idx = faiss.IndexFlatIP(embs.shape[1])
    idx.add(embs.astype(np.float32))
    return idx, df_pool.reset_index(drop=True)

def retrieve_topk(query: str, index, df_pool: pd.DataFrame, k: int = 5):
    q_emb = embedder.encode([query], normalize_embeddings=True).astype(np.float32)
    scores, indices = index.search(q_emb, k)
    return [{"input": df_pool.iloc[i]["input_text"],
             "label": df_pool.iloc[i]["label"],
             "score": float(s)}
            for s, i in zip(scores[0], indices[0])]
```

---

## 🚀 TUẦN 4 (22–31/10): PIPELINE C (LABEL-AWARE RERANK) + ĐO METRICS

### 🎯 Mục tiêu cuối tuần
- Xây dựng **LLM Zero-shot Prior Module** và **Label-Aware Reranking Module** (hoàn toàn không train).
- Pipeline C chạy thành công, so sánh trực tiếp với Pipeline A và Pipeline B.
- Chứng minh **LCR@k của C > LCR@k của B**.

---

### 📋 Task list W4

#### 🔴 Task 4.1 — LLM Zero-shot Prior Module (`retrieval/prior.py`)

```python
# retrieval/prior.py
from llm.client import classify

def get_prior_label(request_text: str) -> str:
    """
    Dự đoán nhãn tiên nghiệm y_prior bằng chính LLM zero-shot.
    Tận dụng Disk Cache đã lưu từ Pipeline A -> Latency = 0ms (cache hit).
    """
    return classify(request_text, demonstrations=None)
```

---

#### 🔴 Task 4.2 — Label-Aware Reranker (`retrieval/rerank.py`)

```python
# retrieval/rerank.py
from typing import List, Dict

def label_aware_rerank(candidates: List[Dict], prior_label: str,
                       k: int = 5, alpha: float = 0.7, beta: float = 0.3) -> List[Dict]:
    """
    Công thức: Score = alpha * Sim + beta * I[label == prior_label]
    Đồng thời chèn ít nhất 1 contrastive example khác nhãn để LLM so sánh.
    """
    scored = []
    for c in candidates:
        match_prior = 1.0 if c["label"] == prior_label else 0.0
        final_score = alpha * c["score"] + beta * match_prior
        scored.append({**c, "final_score": final_score})

    # Sắp xếp theo điểm rerank
    scored.sort(key=lambda x: x["final_score"], reverse=True)

    selected = []
    contrastive_added = False

    for item in scored:
        if len(selected) >= k:
            break
        # Đảm bảo 1 ví dụ đối chiếu (contrastive) nếu có
        if not contrastive_added and item["label"] != prior_label:
            selected.append(item)
            contrastive_added = True
        elif item["label"] == prior_label:
            selected.append(item)

    # Bù thêm nếu chưa đủ k
    extras = [x for x in scored if x not in selected]
    selected += extras[:k - len(selected)]
    return selected[:k]
```

---

#### 🔴 Task 4.3 — Pipeline C Runner & Bảng So Sánh Tổng Hợp

```python
# scripts/compare.py
import pandas as pd
from sklearn.metrics import f1_score

a = pd.read_parquet("results/pipeline_a_results.parquet")[["label", "pred_a"]]
b = pd.read_parquet("results/pipeline_b_results.parquet")[["label", "pred_b", "lcr_k_b"]]
c = pd.read_parquet("results/pipeline_c_results.parquet")[["label", "pred_c", "lcr_k_c"]]

df = a.join(b[["pred_b", "lcr_k_b"]]).join(c[["pred_c", "lcr_k_c"]])

print(f"\n{'Pipeline':<28} {'Macro-F1':>10} {'LCR@5':>10}")
print("-" * 52)
for name, pred_col, lcr_col in [
    ("A — Zero-shot",      "pred_a", None),
    ("B — Vanilla kNN RAG", "pred_b", "lcr_k_b"),
    ("C — Label-Aware Rerank", "pred_c", "lcr_k_c"),
]:
    f1 = f1_score(df["label"], df[pred_col], average="macro", zero_division=0)
    lcr = f"{df[lcr_col].mean():.4f}" if lcr_col else "   —   "
    print(f"{name:<28} {f1:>10.4f} {lcr:>10}")
```

---

## 📊 DELIVERABLES THÁNG 10 (MUST-HAVE)

1. `p1_dataset_selection_report.md` (Lý do chọn dataset).
2. `requirements.txt` + Ollama test thành công.
3. `retrieval_pool.parquet` + `test_set.parquet` (chống leakage qua split_hash).
4. `results/pipeline_a_results.parquet` (Macro-F1 A).
5. `results/pipeline_b_results.parquet` (Macro-F1 B + LCR@k B).
6. `results/pipeline_c_results.parquet` (Macro-F1 C + LCR@k C).
7. Báo cáo tổng kết tháng 10 (`mini-reports/monthly_report_october.md`).
