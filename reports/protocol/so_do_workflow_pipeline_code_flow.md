# Sơ đồ workflow, pipelines và code flow

Đối chiếu mã nguồn tại commit `cee6ed1`, ngày 20/10/2026. Đây là mô tả cách hệ thống được triển khai; sơ đồ không có nghĩa mọi thí nghiệm đã chạy xong.

Các sơ đồ dùng Mermaid, xem trực tiếp trên GitHub hoặc trong trình xem Markdown có hỗ trợ Mermaid. Trong VS Code, mở file rồi chọn **Open Preview** (`Ctrl+Shift+V`); nếu sơ đồ hiện dạng code, cần bật/cài hỗ trợ Mermaid cho Markdown Preview.

## 1. Workflow tổng thể

Mục tiêu: phân loại HTTP request thành một trong sáu nhãn. Hệ thống dùng model có sẵn để inference, không huấn luyện hoặc fine-tune. `pool` là kho ví dụ có nhãn dùng cho retrieval và in-context learning.

```mermaid
flowchart TD
    RAW["SR-BH CSV gốc"] --> PREP["preprocessing.prepare<br/>Kiểm tra nguồn, tạo request canonical<br/>Cách ly nhãn mâu thuẫn, lọc và dedup"]
    PREP --> SPLIT["Chia theo group, seed 42<br/>Audit leakage và tạo subset"]
    SPLIT --> POOL["pool_subset.jsonl<br/>Kho ví dụ: 3.000 mẫu"]
    SPLIT --> DEV["development.jsonl<br/>Thử luồng: 30 mẫu"]
    SPLIT --> VAL["validation_subset.jsonl<br/>Chọn cấu hình: 200 mẫu"]
    SPLIT --> TEST["test_subset.jsonl<br/>600 mẫu; suite hiện dùng 300 mẫu đầu"]
    POOL --> BUILD["experiments.build_retrieval<br/>Embedding + cosine search"]
    DEV --> BUILD
    VAL --> BUILD
    TEST -. "Chỉ khi thêm --include-test" .-> BUILD
    BUILD --> NEI["pool_vectors.npy, pool_meta.jsonl<br/>neighbors_split.jsonl, manifest.json"]
    NEI --> RETEVAL["experiments.eval_retrieval<br/>RQ1, kNN, LCR và quét lambda"]
    POOL --> RUN["experiments.run_llm<br/>A0 / A1 / B / BAL / C"]
    DEV --> RUN
    VAL --> RUN
    TEST -. "Khóa cấu hình rồi thêm --allow-test" .-> RUN
    NEI --> RUN
    RUN --> OUT["manifest.json<br/>predictions.jsonl<br/>metrics.json"]
    OUT --> CMP["analysis.compare<br/>So sánh các run hoàn tất<br/>cùng split và cùng tập query"]
    CMP --> REPORT["Bảng Markdown / JSON<br/>Confusion matrix, biểu đồ<br/>Bootstrap, McNemar, phân tích prior"]
    RETEVAL --> REPORT
```

Đường `neighbors → run_llm` chỉ cần cho B/BAL/C. A0/A1 không cần retrieval; runner hiện vẫn đọc pool ở bước khởi tạo cho tất cả pipeline. CSIC có luồng khảo sát riêng trong `preprocessing/csic_2010.py`, chưa phải nguồn của các run SR-BH trong sơ đồ này.

| Tập | File được `experiments.data_io.load_split()` đọc | Vai trò |
| --- | --- | --- |
| pool | `src/data/processed/sr_bh_v1/pool_subset.jsonl` | Ví dụ có nhãn để chọn demonstrations |
| development | `src/data/processed/sr_bh_v1/development.jsonl` | Thử nhanh, sửa lỗi |
| validation | `src/data/processed/sr_bh_v1/validation_subset.jsonl` | Chọn prompt/cấu hình trước benchmark |
| test | `src/data/processed/sr_bh_v1/test_subset.jsonl` | Đánh giá sau khi khóa cấu hình |

## 2. Các pipeline khác nhau ở đâu?

`Query` là request cần phân loại; `demo` là ví dụ có nhãn đưa vào prompt; `prior` là nhãn dự đoán trước để định hướng chọn demo. Các pipeline LLM dùng chung khung prompt, backend và parser. A0 không có demo; các cấu hình few-shot hiện dùng `k = 4`.

```mermaid
flowchart TD
    Q["Query: request_id + request_text"] --> MODE{"Pipeline?"}
    MODE --> A0["A0: không chọn demo"]
    MODE --> A1["A1: bộ demo cố định từ pool<br/>seed 42, luân phiên các lớp"]
    MODE --> TOP["B / BAL / C<br/>Đọc top-30 từ neighbors đã dựng"]
    TOP --> B["B: lấy 4 ứng viên<br/>có similarity cao nhất"]
    TOP --> BAL["BAL: gom theo lớp<br/>lấy luân phiên đến đủ 4"]
    TOP --> C["C: xếp lại theo<br/>similarity + thưởng nhãn trùng prior<br/>lấy 4 ứng viên"]
    PRIOR["Nguồn prior:<br/>kNN / kết quả A0 / oracle"] --> C
    A0 --> PROMPT["build_messages<br/>System + demos nếu có + query"]
    A1 --> PROMPT
    B --> PROMPT
    BAL --> PROMPT
    C --> PROMPT
    PROMPT --> LLM["ChatClient gọi LLM<br/>hoặc DemoMajorityMock để kiểm thử"]
    LLM --> PARSE["parse_label<br/>JSON chứa một nhãn hợp lệ"]
    PARSE --> PRED["Prediction + status + token + latency"]
    TOP --> KNN["Baseline kNN độc lập<br/>Bỏ phiếu có trọng số similarity<br/>Không gọi LLM"]
    KNN --> KP["Nhãn dự đoán kNN"]
```

| Pipeline | Hàm/chỗ triển khai | Cách chọn demo / prior | Lượt LLM cho một query mới, chưa tính retry |
| --- | --- | --- | --- |
| A0 | `run_llm.py: select()` | Danh sách demo rỗng | 1 |
| A1 | `selectors.fixed_examples()` | Một bộ cố định, ngẫu nhiên trong lớp với seed cố định | 1 |
| B | `selectors.semantic_top_k()` | Top-k theo similarity | 1 |
| BAL | `selectors.class_balanced()` | Luân phiên các lớp xuất hiện trong top-N | 1 |
| C_knn | `knn_vote()` → `label_aware_rerank()` | Prior từ 5 hàng xóm; rerank top-30 | 1 |
| C_llm | `load_llm_prior()` → `label_aware_rerank()` | Prior đọc từ predictions của A0 đã chạy | 1 lượt C; tổng A0 + C là 2 |
| C_oracle | `truth` → `label_aware_rerank()` | Prior là nhãn thật, chỉ dùng phân tích mức trần | 1 |
| kNN | `knn.knn_vote()` qua `eval_retrieval.py` | Bỏ phiếu nhãn, không dựng prompt | 0 |

Với sáu lớp và `k = 4`, A1/BAL không thể chứa đủ sáu lớp trong một prompt. BAL chỉ cân bằng trong các lớp có mặt ở top-N. kNN mặc định cộng `max(similarity, 0)` theo nhãn; hòa điểm thì ưu tiên nhãn có hàng xóm đứng trước.

## 3. Luồng retrieval: chạy trước LLM

```mermaid
flowchart TD
    ENTRY["python -m src.experiments.build_retrieval"] --> MAIN["main: tạo SentenceTransformerEncoder"]
    MAIN --> BUILD["build: load_split pool và các query split"]
    BUILD --> PV["Pool: encode_requests<br/>embedding_view → encoder.encode"]
    BUILD --> QV["Query: encode_requests<br/>embedding_view → encoder.encode"]
    PV --> INDEX["VectorIndex<br/>Chuẩn hóa vector; lưu ID và nhãn pool"]
    INDEX --> SAVE["index.save<br/>pool_vectors.npy + pool_meta.jsonl"]
    QV --> SEARCH["VectorIndex.search<br/>Cosine = dot product vector chuẩn hóa"]
    INDEX --> SEARCH
    SEARCH --> TOP["Lưu tối đa 50 ứng viên / query<br/>request_id, label ứng viên, similarity, rank"]
    TOP --> FILE["neighbors_development.jsonl<br/>neighbors_validation.jsonl<br/>neighbors_test.jsonl nếu được yêu cầu"]
    BUILD --> MAN["manifest.json<br/>Encoder, N, kích thước, thời gian, hash input"]
```

- Encoder mặc định: `sentence-transformers/all-MiniLM-L6-v2`, tối đa 256 token.
- `embedding_view()` đưa method, URI, protocol và body lên trước headers để phần chứa payload xuất hiện sớm; không decode payload.
- Build mặc định lưu **50** hàng xóm. Các config B/BAL/C hiện chỉ dùng **30** ứng viên đầu, rồi chọn **4** demo.
- Embedding chỉ đọc `request_text`. File neighbors ghi nhãn **ứng viên trong pool**, không ghi nhãn thật của query.
- `run_llm.py` đọc file neighbors; không gọi embedding/search lại cho từng request.

## 4. Pipeline C: prior và label-aware reranking

```mermaid
flowchart TD
    CFG["C config: prior_source"] --> SOURCE{"Nguồn prior?"}
    SOURCE --> K["knn<br/>5 hàng xóm từ neighbors<br/>knn_vote"]
    SOURCE --> L["llm<br/>Đọc run A0 của cùng split<br/>load_llm_prior"]
    SOURCE --> O["oracle<br/>Đọc nhãn thật của query<br/>Đánh dấu oracle_analysis"]
    K --> P["prior cho query"]
    L --> P
    O --> P
    P --> VALID{"Có prior hợp lệ?"}
    VALID -- "Không: A0 trả lỗi" --> FALL["Giữ thứ tự semantic như B"]
    VALID -- "Có" --> SCORE["score = similarity<br/>+ lambda nếu nhãn demo trùng prior"]
    N["Top-30 ứng viên"] --> SCORE
    N --> FALL
    SCORE --> SORT["Sắp score giảm dần<br/>Hòa điểm: giữ rank similarity ban đầu"]
    SORT --> SEL["Chọn top-4 demo"]
    FALL --> SEL
    SEL --> PROMPT["Prompt với demo và query"]
    PROMPT --> FINAL["LLM đưa ra nhãn cuối"]
```

Công thức đang dùng:

```text
score(query, demo) = cosine_similarity(query, demo)
                  + lambda * 1[demo.label == prior(query)]

lambda = 0.1; N = 30; k = 4; prior_knn_k = 5
```

Prior chỉ ảnh hưởng việc chọn demo, không được chèn thành trường prior riêng trong prompt. LLM vẫn phân loại từ nội dung query và demo. `lambda = 0` hoặc `prior = None` đưa selector C về cách chọn của B. Nếu run A0 thiếu hẳn một query, runner chặn C_llm; nếu A0 có record lỗi cho query đó, prior là `None` và dùng fallback.

## 5. Code flow của runner LLM

```mermaid
flowchart TD
    CLI["run_llm.main<br/>Đọc CLI, env file, experiment và LLM config"] --> RUN["run_experiment"]
    RUN --> GATE["Kiểm tra quyền dùng split test<br/>Load query và pool"]
    GATE --> SEP["Tách query thành public và truth<br/>public chỉ có ID + request_text"]
    SEP --> DEP["B/BAL/C: load neighbors<br/>C: chuẩn bị prior<br/>A1: tạo bộ ví dụ cố định"]
    DEP --> MAN["Tạo run_key và manifest<br/>Hash dữ liệu, code, prompt, cấu hình"]
    MAN --> LOCK["directory_lock trên output"]
    LOCK --> CHECK{"Manifest cũ phù hợp?"}
    CHECK -- "Không" --> STOP["Chặn run; dùng output mới<br/>Ngoại lệ: run hoàn tất chỉ khác hash code<br/>được bỏ qua"]
    CHECK -- "Có hoặc output mới" --> REC["recover_predictions<br/>Lấy record cuối của mỗi request_id"]
    REC --> RETRY["Nếu --retry-errors:<br/>bỏ backend_error khỏi tập đã xong"]
    RETRY --> NEXT{"Còn query?"}
    NEXT -- "Có" --> SELECT["select query_id<br/>Chọn demos theo pipeline"]
    SELECT --> MSG["Lấy nội dung demo từ pool<br/>build_messages + tạo cache_key"]
    MSG --> CACHE{"Đã có prediction?"}
    CACHE -- "Có, cache_key khớp" --> NEXT
    CACHE -- "Có, cache_key khác" --> ERR["Chặn vì prompt cache không khớp"]
    CACHE -- "Chưa" --> LENGTH{"Query quá dài?"}
    LENGTH -- "Có" --> INPUT["status = input_error"]
    LENGTH -- "Không" --> CALL["ChatClient hoặc DemoMajorityMock"]
    CALL --> RESP{"Kết quả gọi?"}
    RESP -- "Có output" --> PARSE["parse_label<br/>ok hoặc invalid_output"]
    RESP -- "Lỗi backend" --> BACK["status = backend_error"]
    RESP -- "Hết quota ngày" --> QUOTA["Dừng; không ghi lỗi cho query này"]
    INPUT --> WRITE["Append predictions.jsonl<br/>flush + fsync sau mỗi query"]
    PARSE --> WRITE
    BACK --> WRITE
    WRITE --> NEXT
    NEXT -- "Không" --> SUM["summarize<br/>Đối chiếu với truth để tính metrics"]
    QUOTA --> SUM
    SUM --> MET["metrics.json<br/>complete, n_selected, F1, coverage,<br/>LCR, lỗi, token và latency"]
```

`complete = true` nghĩa mọi query được chọn đã có record, không đảm bảo mọi record đều `ok`. Metrics coi prediction lỗi là sai. Khi quota dừng giữa chừng, metrics chỉ tính trên các query đã có record và `complete = false`.

Prompt dùng `prompt_view()`: demo cắt sau 500 ký tự rồi thêm dấu đánh dấu truncation; query không bị cắt. Demo có rank tốt nhất được đặt cuối danh sách, gần query nhất. Query dài hơn giới hạn LLM config (hiện 32.768 ký tự) được ghi `input_error` thay vì gửi API.

## 6. Theo dấu một query B/C qua các module

```mermaid
sequenceDiagram
    participant U as CLI
    participant R as run_llm.py
    participant D as data_io.py
    participant S as selectors.py
    participant P as prompting.py
    participant C as core.ChatClient
    participant F as Artifact files
    U->>R: main → run_experiment
    R->>D: load_split + load_jsonl neighbors
    D-->>R: queries, pool, candidates
    Note over R: Tách truth; chuẩn bị prior cho C
    R->>F: Kiểm tra manifest, recover predictions
    loop Mỗi query chưa có kết quả
        R->>S: semantic_top_k / class_balanced / label_aware_rerank
        S-->>R: Demo IDs, labels, scores
        R->>P: build_messages(query, demo_rows, max_demo_chars)
        P-->>R: System + user messages
        R->>C: client(messages)
        C-->>R: raw_output, usage, attempts hoặc BackendError
        R->>P: parse_label(raw_output)
        P-->>R: Nhãn hoặc ValueError
        R->>F: Append record; flush; fsync
    end
    R->>R: summarize(records, truths, prior_usage)
    R->>F: Ghi metrics.json
    R-->>U: selected, resumed, processed_now, status_counts
```

Sơ đồ sequence mô tả đường chạy thông thường. Các nhánh lỗi, quota và cache được chi tiết ở sơ đồ runner phía trên.

## 7. Suite: thứ tự chạy và tiếp tục khi hết quota

```mermaid
flowchart TD
    CMD["bash src/experiments/run_suite.sh validation"] --> ENV["Tìm .env và .env.* có API key"]
    ENV --> A0["A0"]
    A0 --> B["B_k4"]
    B --> BAL["BAL_k4"]
    BAL --> CK["C_knn_k4"]
    CK --> CL["C_llm_k4<br/>Đọc prior từ output A0"]
    CL --> EXTRA{"EXTRA=1?"}
    EXTRA -- "Có" --> OR["C_oracle_k4 → A1_k4"]
    EXTRA -- "Không" --> DONE["Kết thúc suite"]
    OR --> DONE
    Q["Trong bất kỳ run nào:<br/>quota_exhausted"] --> KEY{"Còn file key?"}
    KEY -- "Có" --> RES["Đổi key; chạy lại cùng config/output<br/>Resume phần còn thiếu"]
    KEY -- "Không" --> HALT["Dừng suite<br/>Chạy lại cùng lệnh sau khi quota được cấp lại"]
```

Suite không tự preprocessing hoặc build retrieval; cần chuẩn bị trước. Các run dùng `--sleep 1 --retry-errors`. Nhánh quota áp dụng cho từng run; lỗi runner khác được script ghi nhận rồi chuyển sang run tiếp theo. Với test, script yêu cầu `test --locked` và truyền `--allow-test --limit 300` cho runner.

## 8. Luồng đánh giá và phân tích

```mermaid
flowchart TD
    NEI["Neighbors + nhãn thật query"] --> ER["eval_retrieval.evaluate_retrieval"]
    ER --> RQ["RQ1: top-1 khác nhãn<br/>kNN: Macro-F1, Accuracy, FPR Normal<br/>LCR của B/BAL/C và quét lambda"]
    ER --> RA["retrieval_metrics.json / .md<br/>retrieval_overview.png, confusion_knn.png"]
    RUN["Các run LLM hoàn tất"] --> CHECK["compare.compare<br/>Kiểm tra cùng split, cùng tập query"]
    CHECK --> TRUTH["Đối chiếu predictions với nhãn thật"]
    TRUTH --> MET["Macro-F1, Accuracy, từng lớp<br/>FPR Normal, lỗi và chi phí"]
    TRUTH --> STAT["Paired bootstrap, McNemar<br/>C: nhóm prior đúng / sai so với reference"]
    MET --> OUT["Bảng so sánh Markdown / JSON<br/>F1 từng lớp và hình confusion matrix"]
    STAT --> OUT
```

LCR@k là tỷ lệ demo có nhãn trùng nhãn thật query, dùng để phân tích sau khi chọn demo. LCR tăng chưa đủ chứng minh chất lượng phân loại tăng. Nhãn thật query phục vụ đánh giá; chỉ C_oracle được dùng nó để chọn demo và run đó được đánh dấu riêng.

## 9. Bản đồ file để đọc code

Các đường dẫn dưới đây tính từ gốc repo; liên kết mở trực tiếp mã nguồn.

| Bước | File | Hàm/điểm cần đọc |
| --- | --- | --- |
| Chuẩn bị dữ liệu | [prepare.py](../../src/preprocessing/prepare.py) | `prepare`, `scan_csv`, `assign_groups`, `balanced_subset`, `audit_splits` |
| Kiểm chứng export | [verify.py](../../src/preprocessing/verify.py) | `verify` |
| Quy ước split | [data_io.py](../../src/experiments/data_io.py) | `SPLIT_FILES`, `load_split` |
| Hai cách trình bày request | [views.py](../../src/retrieval/views.py) | `embedding_view`, `prompt_view` |
| Embedding | [embedding.py](../../src/retrieval/embedding.py) | `encode_requests`, `SentenceTransformerEncoder` |
| Cosine search | [index.py](../../src/retrieval/index.py) | `VectorIndex.search`, `save` |
| Dựng retrieval | [build_retrieval.py](../../src/experiments/build_retrieval.py) | `main`, `build` |
| Chọn demonstrations | [selectors.py](../../src/retrieval/selectors.py) | B, BAL, C, A1 |
| kNN baseline / prior | [knn.py](../../src/retrieval/knn.py) | `knn_vote` |
| Chạy pipeline | [run_llm.py](../../src/experiments/run_llm.py) | `main`, `run_experiment`, `select`, `load_llm_prior`, `summarize` |
| Prompt / parser / mock | [prompting.py](../../src/experiments/prompting.py) | `build_messages`, `parse_label`, `DemoMajorityMock` |
| API client dùng lại từ A0 | [core.py](../../src/pipeline_a0/core.py) | `ChatClient`, `BackendError`, `recover_predictions`, `parse_output` |
| Khóa run | [locking.py](../../src/common/locking.py) | `directory_lock` |
| Chạy nhiều cấu hình | [run_suite.sh](../../src/experiments/run_suite.sh) | Thứ tự config, đổi key, resume |
| Đánh giá retrieval | [eval_retrieval.py](../../src/experiments/eval_retrieval.py) | `evaluate_retrieval` |
| Metrics và kiểm định | [metrics.py](../../src/analysis/metrics.py) | Các hàm metrics, bootstrap, McNemar |
| So sánh run | [compare.py](../../src/analysis/compare.py) | `compare`, `prior_breakdown` |

Lệnh `python -m src.pipeline_a0` là runner zero-shot/smoke có từ giai đoạn đầu. Bộ thí nghiệm A0/A1/B/BAL/C hiện đi qua `python -m src.experiments.run_llm`; nó dùng lại client và tiện ích của `pipeline_a0.core`, nhưng dùng prompt ICL chung trong `experiments.prompting`.

## 10. Đường chạy thực tế để đối chiếu sơ đồ

Chạy từ gốc repo sau khi đã cài dependency và có các split dữ liệu. Lần đầu encoder có thể cần tải model. Các lệnh dưới đây là hướng dẫn, không phải những lệnh đã được chạy để tạo tài liệu này.

```bash
# 1. Dựng neighbors cho development + validation
python -m src.experiments.build_retrieval --output src/artifacts/retrieval/minilm

# 2. Đánh giá retrieval / kNN; không gọi LLM
python -m src.experiments.eval_retrieval --retrieval src/artifacts/retrieval/minilm --split validation

# 3. Thử luồng B với mock; vẫn cần pool, development và neighbors
python -m src.experiments.run_llm --config src/configs/experiments/B_k4.json --llm src/configs/llm/mock.json --split development --output src/artifacts/runs/development/B_mock_diagram

# 4. Chạy bộ LLM thật; cần cấu hình key trong .env
bash src/experiments/run_suite.sh validation

# 5. Chỉ chạy sau khi các run chính hoàn tất trên cùng tập query
python -m src.analysis.compare --split validation --reference B_k4 --runs src/artifacts/runs/validation/A0 src/artifacts/runs/validation/B_k4 src/artifacts/runs/validation/BAL_k4 src/artifacts/runs/validation/C_knn_k4 src/artifacts/runs/validation/C_llm_k4 --output src/artifacts/reports/validation
```

`--reference` dùng tên thư mục run (`B_k4` trong suite), không phải trường `name` trong experiment config. Run dở có manifest/code không còn khớp cần output mới theo thông báo runner; không sửa manifest để ép resume.

Đọc thêm: [hướng dẫn chạy thực nghiệm](huong_dan_chay_thuc_nghiem.md), [hướng dẫn đọc và chạy code](huong_dan_doc_va_chay_code.md), [chuẩn bị dữ liệu](README.md).
