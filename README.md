# Label-Aware Retrieval cho phát hiện tấn công web bằng LLM

Đồ án môn Dự án CNTT (TDTU). Đề tài phân loại HTTP request thành 6 lớp (Normal và 5 loại tấn công) bằng LLM theo kiểu **In-Context Learning**: đưa cho model vài ví dụ có nhãn rồi hỏi nhãn của request mới. Câu hỏi chính: **chọn ví dụ có xét đến nhãn (label-aware) có tốt hơn chọn ví dụ chỉ theo độ giống nhau về nội dung không?**

Dự án chỉ dùng model có sẵn qua API (**inference-only**), không huấn luyện hay fine-tune.

**Bắt đầu đọc:** [Hướng dẫn đọc và chạy code](reports/guides/huong_dan_doc_va_chay_code.md) · [Mục lục tài liệu](reports/README.md) · [Báo cáo giữa kỳ](reports/midterm/bao_cao_giua_ky.md)

## Các pipeline

Mọi pipeline dùng chung một LLM (Groq `openai/gpt-oss-20b`, temperature 0, `reasoning_effort` low), một khung prompt và cùng **k = 4** ví dụ (mỗi ví dụ cắt ở 500 ký tự). Chỉ khác **cách chọn ví dụ**.

| Pipeline | Cách chọn ví dụ | Vai trò |
| --- | --- | --- |
| **kNN vote** | Không gọi LLM: bỏ phiếu nhãn của 5 láng giềng gần nhất | Baseline không LLM; nguồn prior rẻ cho C |
| **A0** | Không có ví dụ (zero-shot) | Năng lực gốc của LLM; nguồn prior cho C |
| **A1** | 4 ví dụ cố định cho mọi request | Kiểm tra: có ví dụ là đủ, hay ví dụ phải liên quan? |
| **B** | Top-4 giống nhất theo embedding | Baseline retrieval chính |
| **BAL** | Từ top-30, lấy luân phiên theo lớp | Cân bằng nhãn có giúp không? |
| **C** | Từ top-30, xếp lại theo `similarity + 0,1·1[nhãn = prior]`, prior từ kNN hoặc A0 | Phương pháp label-aware đề xuất |
| C-oracle | Như C nhưng prior = nhãn thật | Chỉ để phân tích: mức trần nếu prior luôn đúng |

```text
HTTP request ──► embedding ──► top-30 ứng viên từ pool (kèm nhãn)
     │                                   │
     └──► prior (kNN / A0) ──────────────┴──► chọn k = 4 ví dụ (B / BAL / C)
                                                      │
                                     prompt (ví dụ + request) ──► LLM ──► nhãn
```

## Kết quả trên tập test (300 request, 50/lớp)

Cấu hình được khóa trước khi chạy test ([cau_hinh_khoa.md](reports/experiments/cau_hinh_khoa.md)). Bảng đầy đủ: [src/artifacts/reports/test/comparison.md](src/artifacts/reports/test/comparison.md).

| Pipeline | Macro-F1 (gpt-oss-20b) | Δ so với B, CI 95% | Macro-F1 (gpt-oss-120b) |
| --- | ---: | --- | ---: |
| kNN vote (không LLM) | 0,742 | — | — |
| A0 zero-shot | 0,834 | −0,047 [−0,081; −0,016] | 0,793 |
| A1 cố định | 0,797 | −0,084 [−0,118; −0,051] | — |
| **B top-4** | **0,881** | — | **0,869** |
| BAL | 0,865 | −0,016 [−0,041; +0,008] | 0,862 |
| C, prior kNN | 0,862 | −0,019 [−0,047; +0,008] | 0,866 |
| C, prior A0 | 0,861 | −0,020 [−0,042; −0,002] | 0,854 |
| C-oracle (phân tích) | 0,900 | +0,019 [−0,003; +0,043] | 0,880 |

Kết luận chính:

1. Ví dụ **liên quan** quan trọng hơn **có** ví dụ: B hơn A0 rõ rệt, còn A1 (ví dụ cố định) còn kém A0.
2. Label-aware rerank (C) **không** vượt B với prior thực tế. Khi prior sai, C làm hỏng nhiều hơn sửa (prior kNN: hỏng 11, sửa 2).
3. Với prior hoàn hảo (C-oracle), C nhỉnh hơn B nhưng chưa có ý nghĩa thống kê. Nút thắt là **chất lượng prior**, không phải cách rerank.
4. Kết luận giữ nguyên khi đổi sang model lớn hơn gpt-oss-120b ([thí nghiệm bổ sung](reports/experiments/thi_nghiem_bo_sung_120b.md)).

Tổng chi phí API thực tế khoảng 0,75 USD. Sổ chi phí (ước tính với giá cố ý đặt cao): [`src/artifacts/api_spend_ledger.json`](src/artifacts/api_spend_ledger.json), [`api_spend_ledger_120b.json`](src/artifacts/api_spend_ledger_120b.json).

## Cấu trúc repo

```text
.
├── README.md
├── requirements.txt              # thư viện cho code thí nghiệm
├── requirements-demo.txt         # thêm Streamlit cho app demo
├── env.example                   # mẫu file .env (key để trống)
├── src/
│   ├── preprocessing/            # (1) CSV gốc SR-BH 2020 → pool / validation / test; khảo sát CSIC 2010
│   ├── retrieval/                # (2) embedding, index, kNN, các cách chọn ví dụ
│   ├── experiments/              # (3) build_retrieval, eval_retrieval, run_llm, run_suite.sh
│   ├── llm/                      #     client gọi API (Groq, tương thích OpenAI) + parser nhãn
│   ├── analysis/                 # (4) metric, bootstrap, McNemar, bảng và hình so sánh
│   ├── demo/                     #     app demo Streamlit: so sánh B và C cho một request
│   ├── common/                   #     khóa thư mục chạy được trên Windows/Linux, chốt ngân sách
│   ├── configs/                  #     data.json, llm/, experiments/ (20b), experiments_120b/
│   ├── tests/                    #     56 bài kiểm thử tự động (không gọi API)
│   ├── notebooks/                #     notebook khảo sát dữ liệu
│   ├── data/                     #     dữ liệu (không có trên Git, tự tạo lại)
│   └── artifacts/
│       ├── data/                 #     thống kê, audit rò rỉ, kiểm chứng tái lập
│       ├── retrieval/minilm/     #     neighbors và đánh giá retrieval/kNN
│       ├── runs/                 #     dự đoán của từng pipeline (validation, test)
│       ├── runs_120b/            #     dự đoán với gpt-oss-120b (test)
│       └── reports/              #     bảng so sánh và confusion matrix
└── reports/                      # tài liệu, báo cáo — xem reports/README.md
```

## Chạy lại

Mọi lệnh chạy từ thư mục gốc repo, Python ≥ 3.10 (đã kiểm chứng 3.11.9 trên Windows 11). Hướng dẫn chi tiết cho cả PowerShell và Git Bash: [huong_dan_chay_thuc_nghiem.md](reports/guides/huong_dan_chay_thuc_nghiem.md).

```bash
python -m venv .venv
source .venv/Scripts/activate      # Git Bash trên Windows; Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s src/tests
```

Các bước (bước 1–3 và 5 không cần API key):

```bash
# 1. Dữ liệu: đặt CSV SR-BH 2020 vào src/data/raw/ (xem reports/dataset/huong_dan_xu_ly_du_lieu.md)
python -m src.preprocessing.prepare --config src/configs/data.json
# 2. Embedding pool và tìm top-30 ứng viên
python -m src.experiments.build_retrieval --output src/artifacts/retrieval/minilm
python -m src.experiments.build_retrieval --output src/artifacts/retrieval/minilm --add-split test
# 3. Đánh giá retrieval và kNN
python -m src.experiments.eval_retrieval --retrieval src/artifacts/retrieval/minilm --split validation
# 4. Các pipeline LLM (cần key trong .env, tạo từ env.example)
bash src/experiments/run_suite.sh validation
EXTRA=1 bash src/experiments/run_suite.sh validation
# 5. So sánh
python -m src.analysis.compare --split validation --runs "src/artifacts/runs/validation/*" --output src/artifacts/reports/validation
```

Muốn thử luồng mà không tốn API, dùng LLM giả: `--llm src/configs/llm/mock.json` với `run_llm` (xem hướng dẫn).

**An toàn khi chạy:**

- Chỉ dùng **một** key Groq trong `.env`; điều khoản của Groq không cho dùng nhiều tài khoản để vượt giới hạn.
- Chốt ngân sách (`src/configs/llm/budget.json`) dừng **trước khi** chi phí ước tính vượt 4,5 USD.
- Tập test bị khóa: phải có `--locked` (script) hoặc `--allow-test` (run_llm).
- Run đã xong thì được bỏ qua; run dở chạy tiếp từ chỗ dừng.

## Demo

App nhỏ chạy trên máy (Streamlit, [`src/demo/app.py`](src/demo/app.py)): dán một HTTP request hoặc chọn 1 trong 8 ví dụ lấy từ tập validation, app hiện song song B và C (prior kNN, λ = 0,1): prior kNN và phiếu của 5 láng giềng, 4 ví dụ được chọn (nhãn, similarity, điểm) và nhãn LLM trả về. Có nút bật thêm A0 (zero-shot). App dùng lại đúng code và cấu hình đã khóa của thực nghiệm.

```bash
pip install -r requirements-demo.txt
streamlit run src/demo/app.py
```

Mở trình duyệt ở `http://localhost:8501`. Lần đầu mất khoảng 1 phút để nạp model embedding.

- Mặc định là **Mock**: không gọi API, không cần key. Nhãn "LLM" khi đó chỉ là nhãn đa số của 4 ví dụ, không phải kết quả của LLM.
- Chọn **Groq thật** ở thanh bên: key đọc từ `.env` (giống `--env-file`), mỗi lần gọi đều qua chốt ngân sách `budget.json` và ghi vào cùng sổ chi phí. Câu trả lời được nhớ lại, nên bấm lại cùng request không tốn thêm. Mỗi request tốn khoảng 2–3 lần gọi (B, C, A0), dưới 0,001 USD.
- Nếu thiếu `src/artifacts/retrieval/minilm/pool_vectors.npy` (không có trên Git), app tự mã hóa lại pool lần đầu (vài phút) mà không đụng đến file neighbors. App cần dữ liệu đã xử lý trong `src/data/processed/sr_bh_v1/` (bước 1 ở trên).
- `.streamlit/config.toml` chỉ mở app trên `localhost`, để người khác trong cùng mạng không dùng được key.

## Dữ liệu

[SR-BH 2020](reports/dataset/khao_sat_sr_bh_2020.md) (Harvard Dataverse, CC0): 907.815 bản ghi gốc. Chỉ giữ request có đúng một nhãn, còn 466.267 request không trùng. Chia theo nhóm 70/15/15 (seed 42) để tránh rò rỉ giữa các tập.

6 lớp: `NORMAL`, `SQL_INJECTION`, `PATH_TRAVERSAL`, `CODE_INJECTION`, `HTTP_RESPONSE_SPLITTING`, `OS_COMMAND_INJECTION`.

Dùng: pool 3.000 (500/lớp), validation 200, test 300 (50/lớp). Lý do chọn dataset và giới hạn (nhiễu nhãn ở lớp Normal): [quyet_dinh_dataset.md](reports/dataset/quyet_dinh_dataset.md).
