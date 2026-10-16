# Lộ trình thực hiện: Label-Aware Retrieval for LLM-Based Web Attack Detection

**Sản phẩm cuối:** (1) source code trên git, tái lập được; (2) báo cáo khoa học (LaTeX).
**Thời lượng dự kiến:** 16 tuần (co giãn theo deadline thực tế, không bỏ phase nào).
**Hướng phương pháp đã chọn:** label-aware rerank (retrieve rộng top-N theo similarity, rerank theo điểm có tính nhãn, lấy top-k đưa vào prompt).

---

## 0. Tổng quan

| Tuần | Phase | Kết quả bàn giao |
|---|---|---|
| 1 | 0. Chốt phạm vi | RQ, giả thuyết, protocol thực nghiệm (1-2 trang) |
| 1-3 | 1. Tổng quan tài liệu | Bảng so sánh related work, xác nhận khoảng trống |
| 2-4 | 2. Dữ liệu | Dataset đã làm sạch, khử trùng, chia train/val/test |
| 4-6 | 3. Hạ tầng và baseline | Harness chạy được, kết quả các baseline |
| 6-9 | 4. Phương pháp | Pilot, cài đặt rerank, chỉnh tham số trên validation |
| 9-12 | 5. Thực nghiệm chính | Bảng kết quả, ablation, cross-dataset, chi phí |
| 12-15 | 6. Phân tích và viết report | Bản nháp đầy đủ |
| 15-16 | 7. Đóng gói | Repo tái lập được, report bản cuối |

Kế hoạch kiểm thử (Mục 9) chạy song song xuyên suốt các phase.

### Các cổng kiểm tra (go/no-go)

| Thời điểm | Điều kiện để đi tiếp | Nếu không đạt |
|---|---|---|
| Tuần 3 | Không có paper trùng gần như hoàn toàn | Đổi định vị (cross-dataset, độ bền) |
| Tuần 4 | Test chống leakage pass | Sửa khâu khử trùng/chia dữ liệu |
| Tuần 6 | Harness tái lập kết quả giữa hai lần chạy | Sửa cache/seed/parser |
| Tuần 6-7 | Pilot cho thấy label skew/ambiguity thật sự tồn tại | Đổi hướng hoặc hạ contribution 1 thành giả thuyết |
| Tuần 9 | Rerank hơn kNN rõ rệt trên validation | Xem lại điểm số; nếu vẫn không thì chuyển sang báo cáo kết quả âm có phân tích |

---

## 1. Phase 0: Chốt phạm vi (tuần 1)

- Viết 3-4 RQ:
  - RQ1: rerank theo nhãn có cải thiện macro-F1 và FPR so với kNN thuần similarity không?
  - RQ2: lợi ích lớn nhất ở lớp nào (lớp hiếm, ca sát ranh giới)?
  - RQ3: với pool nhỏ, rerank có bù được thiếu dữ liệu không?
  - RQ4: phương pháp có giữ được hiệu năng khi chuyển dataset không?
- Với mỗi RQ, ghi giả thuyết và **điều kiện bị bác bỏ** (ví dụ: rerank không hơn kNN quá 1 điểm macro-F1 thì bác bỏ). Viết trước khi chạy để tránh chọn kết quả theo ý muốn.
- Chọn LLM: **Primary** — Ollama local (Qwen2.5-7B hoặc Llama-3.1-8B, chạy inference không train); **Secondary** — free API (Google AI Studio Gemini Flash hoặc Groq). Không dùng API trả phí làm primary.
- Cấu hình Pipeline C dùng **LLM zero-shot làm prior** (cùng model local, prompt ngắn) → rerank → few-shot ICL. Không train bất kỳ classifier hay encoder nào.
- Tạo repo git, chốt cấu trúc thư mục (Mục 8).

## 2. Phase 1: Tổng quan tài liệu (tuần 1-3)

- Dùng Zotero, chia 4 nhóm: (a) web attack detection ML/DL, (b) LLM cho phát hiện xâm nhập, (c) demonstration selection/retrieval trong ICL, (d) RAG trong bảo mật.
- Chạy truy vấn trên Scopus, Google Scholar, IEEE Xplore; ghi lại chuỗi truy vấn và ngày tìm để report có phần phương pháp tìm tài liệu. Ví dụ:
  - `"in-context learning" "web attack" OR "HTTP request" retrieval`
  - `"demonstration selection" intrusion detection LLM`
  - `"retrieval-augmented" WAF LLM SQL injection classification`
- Theo dõi mục "cited by" của các paper gần đề tài nhất (Prompt Engineering-Based NIDS, CyberRAG).
- Làm bảng so sánh: paper, tác vụ, dữ liệu, cách retrieve, dùng nhãn hay không, LLM.

## 3. Phase 2: Dữ liệu (tuần 2-4)

- **Nguồn:** CSIC 2010, ECML/PKDD 2007, và tập tự sinh trên lab cục bộ (DVWA/Burp) cho tấn công hiện đại. Chỉ tấn công hệ thống của chính mình, không quét hay thử payload lên hệ thống thật.
- **Nhãn:** CSIC 2010 chủ yếu gán nhãn nhị phân. Muốn đa lớp (SQLi, XSS, ...) phải dùng dataset có nhãn loại hoặc gán bằng luật rồi kiểm tay một mẫu; ghi rõ cách gán trong report.
- **Tiền xử lý:** chuẩn hóa request (URL decode, gộp header không cần thiết), giữ cùng một định dạng chuỗi cho mọi phương pháp.
- **Khử trùng:** loại request trùng và gần trùng (hash sau chuẩn hóa, MinHash) giữa pool và test.
- **Chia dữ liệu:** train (pool ví dụ và huấn luyện classifier tiên nghiệm), validation (chỉnh tham số), test (chỉ dùng cuối). Cố định seed, lưu hash file split.
- **Thống kê mô tả:** phân phối lớp, độ dài request, tỉ lệ láng giềng khác nhãn (nguyên liệu cho pilot).

## 4. Phase 3: Hạ tầng và baseline (tuần 4-6)

- Module: embedding, FAISS index, retriever, prompt builder, LLM client (retry, cache theo hash prompt, ghi token và độ trễ), parser JSON có xử lý output hỏng.
- Prompt cố định: hướng dẫn, tập nhãn hợp lệ, định dạng đầu ra, temperature 0. Thứ tự ví dụ là một biến cấu hình để ablation sau.
- **Baseline:**
  - Zero-shot
  - Random few-shot
  - kNN top-k
  - BM25
  - Class-balanced top-k mỗi lớp
  - Mô hình fine-tune (BERT/CodeBERT) — **trích số liệu từ literature**, không reproduce (ngoài scope không train)
  - LLM zero-shot (thay cho "classifier tiên nghiệm" — đây là mốc baseline quan trọng: nếu zero-shot đã đủ tốt thì contribution của rerank bị hỏi)
- Ước lượng chi phí trước: số cấu hình × số request test × token mỗi request. Nếu quá đắt, dùng tập test con phân tầng và nêu rõ trong report.

## 5. Phase 4: Phương pháp (tuần 6-9)

1. **Pilot** (cho contribution 1): đo tỉ lệ ví dụ benign trong top-k, tỉ lệ láng giềng khác nhãn, và tỉ lệ lỗi của kNN rơi vào các trường hợp đó.
2. **Cài đặt các thành phần điểm rerank**, mỗi thành phần có công tắc bật/tắt trong config:
   - Similarity (điểm gốc từ bước retrieve)
   - Nhập nhằng nhãn ở vùng lân cận: nếu top-N chứa nhiều nhãn khác nhau thì query sát ranh giới, tăng điểm cho ví dụ của nhãn thiểu số trong vùng đó
   - Khớp với dự đoán sơ bộ của classifier nhẹ: ưu tiên ví dụ có nhãn thuộc top-2 phân phối dự đoán, kèm ít nhất một ví dụ nhãn đối lập làm đối chiếu
   - Đa dạng theo nhãn: phạt khi tập được chọn toàn cùng một nhãn (kiểu MMR nhưng tính theo nhãn)
3. Bắt đầu với 2-3 thành phần rồi mở rộng, vì càng nhiều thành phần càng khó lập luận cái nào thực sự có ích.
4. Chỉnh trọng số, N, k **chỉ trên validation** (random search hoặc grid nhỏ).

## 6. Phase 5: Thực nghiệm chính (tuần 9-12)

| Nhóm | Nội dung |
|---|---|
| Chính | Mọi baseline và phương pháp đề xuất trên test, ít nhất 2 LLM |
| Ablation | Thêm dần từng thành phần; ablation thứ tự ví dụ |
| Quét tham số | k, N, kích thước pool (100 / 500 / 2000), embedding model |
| Cross-dataset | Pool từ dataset A, test trên B, và ngược lại |
| Độ bền (tùy chọn) | Payload bị làm rối/mã hóa; đầu độc pool (chèn ví dụ sai nhãn) |
| Chi phí | Độ trễ, token, tiền |

**Chuẩn thống kê:**
- Nhiều seed cho các bước ngẫu nhiên (lấy mẫu pool, random few-shot); báo trung bình và độ lệch chuẩn.
- Khoảng tin cậy bootstrap 95%.
- Kiểm định cặp (McNemar) cho so sánh trên cùng tập test; hiệu chỉnh đa so sánh (Holm).
- Metric: macro-F1, F1 từng lớp, FPR tại TPR cố định, PR-AUC, MCC.

## 7. Phase 6-7: Phân tích, viết report, đóng gói (tuần 12-16)

**Phân tích lỗi định tính:** lấy mẫu các request bị đoán sai, phân loại nguyên nhân (nhiễu bởi ví dụ sai nhãn, payload làm rối, LLM bỏ qua ví dụ, ...).

**Cấu trúc report (LaTeX, template IEEE hoặc Elsevier tùy nơi nộp):**
1. Abstract, Introduction
2. Related Work (theo 4 nhóm ở Phase 1)
3. Method (bài toán, pipeline, điểm rerank, pseudocode)
4. Experimental Setup (dataset, chia dữ liệu, baseline, LLM, metric, chi tiết cài đặt)
5. Results (mỗi RQ một bảng/hình)
6. Analysis and Discussion (ablation, lỗi, chi phí)
7. Threats to Validity và Limitations (dataset cũ, LLM cụ thể, leakage còn sót, tính ngẫu nhiên của LLM)
8. Ethics và Conclusion

Viết Method và Setup từ tuần 9, không dồn đến cuối. Đưa thầy hướng dẫn đọc bản nháp ít nhất một lần ở tuần 13-14.

**Đóng gói repo:**
- README hướng dẫn chạy từng bước; file cấu hình cho mọi thí nghiệm; script tạo lại mọi bảng và hình từ kết quả lưu sẵn.
- Khóa phiên bản thư viện; ghi phiên bản model và ngày chạy API.
- Tag release, giấy phép, mục dữ liệu (chỉ chỉ dẫn tải dataset công khai; cân nhắc kỹ trước khi đăng payload tự sinh).
- Nhờ một người chạy thử repo từ đầu.

---

## 8. Cấu trúc repo gợi ý

```
label-aware-retrieval/
├── configs/            # yaml cho từng thí nghiệm
├── data/               # raw/ (không commit), processed/, splits/ (chỉ hash)
├── src/
│   ├── data/           # tải, chuẩn hóa, khử trùng, chia
│   ├── retrieval/      # embedding, index, rerank
│   ├── prompts/        # template
│   ├── llm/            # client, cache, parser
│   ├── baselines/      # bert fine-tune, tf-idf, ...
│   └── eval/           # metric, thống kê, bảng, hình
├── scripts/            # run_experiment.py, make_tables.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── sanity/         # kiểm tra tính hợp lệ của thực nghiệm
│   └── fixtures/       # tập mẫu nhỏ (~50-100 request) + mock LLM
├── results/            # log dự đoán từng request
├── paper/              # LaTeX
├── Makefile            # make test, make reproduce-small, make tables
├── .github/workflows/  # CI chạy test
└── README.md
```

---

## 9. Kế hoạch kiểm thử (Test plan)

Gồm 5 tầng: unit, integration, kiểm tra tính hợp lệ của thực nghiệm (sanity), regression/tái lập, và an toàn/đạo đức.

### 9.1 Unit test (viết cùng lúc với module, tuần 2-9)

| Module | Kiểm tra | Tiêu chí pass |
|---|---|---|
| Chuẩn hóa request | URL decode, idempotent (chạy hai lần cho cùng kết quả), giữ nguyên payload ý nghĩa | Đầu ra khớp mẫu đúng cho bộ ca khó (encode kép, ký tự lạ) |
| Khử trùng | Trùng chính xác và gần trùng bị loại | Không còn cặp trùng vượt ngưỡng giữa pool và test |
| Chia dữ liệu | Không giao nhau giữa train/val/test; phân tầng theo lớp; deterministic theo seed | Giao của tập hash = rỗng; cùng seed cho cùng split |
| Retriever | Trả đúng k kết quả; **loại chính query khỏi pool** khi query nằm trong pool; kết quả deterministic | Đúng số lượng, không tự retrieve chính mình |
| Rerank | Điểm từng thành phần trên ca đồ chơi có đáp án tay; khi mọi trọng số ngoài similarity = 0 thì kết quả trùng kNN; ràng buộc đa dạng nhãn hoạt động | Khớp đáp án tay; trùng kNN khi tắt hết công tắc |
| Prompt builder | Có đủ nhãn và thứ tự đúng; cắt theo ngân sách token; **không lộ nhãn thật của query** vào prompt | Không chuỗi nhãn query trong prompt |
| Parser output LLM | JSON hợp lệ, JSON kèm chữ thừa, JSON hỏng, nhãn ngoài tập hợp lệ | Ca hỏng được ghi là "invalid" và đếm, không làm crash hay gán bừa |
| Cache | Cùng prompt trả cùng kết quả; khác cấu hình không đụng cache | Hit/miss đúng |
| Metric | So với scikit-learn trên ca đồ chơi; FPR tại TPR cố định; bootstrap tái lập theo seed | Sai số số học < 1e-9 |

### 9.2 Integration test (tuần 6 trở đi)

- Chạy toàn pipeline trên fixture nhỏ với **mock LLM** (trả lời xác định, không gọi mạng) và kiểm tra: đầu ra sinh đủ file, số dòng dự đoán bằng số request, config sai bị từ chối với thông báo rõ.
- Chạy CLI `run_experiment.py` với một cấu hình mẫu, so sánh file kết quả với bản chuẩn đã lưu.
- Thử ngắt giữa chừng và chạy lại: cache giúp tiếp tục, không chạy trùng.

### 9.3 Sanity test cho tính hợp lệ của thực nghiệm (tuần 4-12)

Đây là các thí nghiệm nhỏ để chứng minh pipeline không lừa mình.

| Test | Cách làm | Kỳ vọng nếu pipeline đúng |
|---|---|---|
| Canary chống leakage | Cố tình chèn một request test vào pool | Hệ thống phải phát hiện và loại; nếu không loại thì kết quả bị nghi ngờ |
| Xáo nhãn ví dụ (label shuffle) | Xáo nhãn của các ví dụ trong prompt | Hiệu năng giảm rõ, chứng tỏ LLM thực sự dùng nhãn |
| Cận dưới | Retrieval ngẫu nhiên hoàn toàn | Tệ hơn kNN |
| Cận trên (oracle) | Đưa ví dụ cùng nhãn thật với query | Tốt hơn mọi phương pháp thật; nếu không thì prompt/parser có vấn đề |
| Tính nhất quán | Chạy hai lần cùng cấu hình | Kết quả giống hoặc chênh trong ngưỡng đã chốt |
| Tỉ lệ output không hợp lệ | Đếm output invalid trên mỗi cấu hình | Dưới ngưỡng đã chốt (ví dụ 1-2%); vượt thì sửa prompt/parser trước khi so sánh |
| Nhạy với thứ tự ví dụ | Hoán vị thứ tự ví dụ trong prompt | Ghi lại biên độ dao động; dùng làm khoảng nhiễu để đọc ablation |
| Baseline tiên nghiệm | Chạy classifier tiên nghiệm độc lập | Là mốc so sánh; nếu vượt hoặc ngang phương pháp đề xuất thì phải giải thích |

### 9.4 Regression, CI và tái lập

- **CI (GitHub Actions):** chạy unit và integration test, lint (ruff), kiểm tra định dạng, mỗi lần push.
- **Regression:** lưu số liệu chuẩn cho fixture nhỏ với mock LLM; sửa code làm số liệu lệch quá dung sai thì test fail.
- **Tái lập:** `make reproduce-small` từ bản clone sạch phải tạo lại bảng kết quả trên tập con trong dung sai đã chốt; kiểm tra hash file split và file cấu hình.
- **Bảng và hình trong report** đều sinh từ script, không sửa tay.

### 9.5 An toàn và đạo đức

- Payload chỉ được xử lý như chuỗi văn bản; không có đường code nào gửi request tới máy đích hay thực thi payload. Có test đảm bảo module xử lý dữ liệu không mở kết nối mạng.
- Quét bí mật (ví dụ detect-secrets/gitleaks) để không commit API key; dữ liệu thô nằm ngoài git.
- Dữ liệu tự sinh từ lab cục bộ; ghi rõ trong report và xem xét trước khi công bố.

### 9.6 Lịch kiểm thử theo phase

| Phase | Test phải xong |
|---|---|
| 2 (Dữ liệu) | Unit: chuẩn hóa, khử trùng, chia dữ liệu; sanity: canary leakage |
| 3 (Hạ tầng) | Unit: retriever, prompt, parser, cache, metric; integration với mock LLM; sanity: cận dưới, tính nhất quán, invalid rate |
| 4 (Phương pháp) | Unit: rerank (bao gồm trùng kNN khi tắt công tắc); sanity: label shuffle, oracle |
| 5 (Thực nghiệm) | Sanity: nhạy thứ tự, baseline tiên nghiệm; regression số liệu chuẩn |
| 7 (Đóng gói) | Tái lập từ clone sạch, quét bí mật, CI xanh |

---

## 10. Rủi ro và phương án dự phòng

| Rủi ro | Cách xử lý |
|---|---|
| Rerank không hơn kNN | Đổi sang báo cáo kết quả âm có phân tích, hoặc chuyển thành contrastive ở inference (hard negatives) |
| Chi phí API vượt ngân sách | Tập test con phân tầng, ưu tiên model local, cache mọi lệnh gọi |
| Thiếu thời gian | Cắt theo thứ tự: độ bền → dataset thứ ba → LLM thứ hai. Không cắt ablation, baseline và test |
| Leakage phát hiện muộn | Test canary và khử trùng ở Phase 2, in số trùng vào log |
| Kết quả không ổn định do LLM | Temperature 0, nhiều seed cho pool, báo khoảng tin cậy, đo nhạy thứ tự |

---

## 11. Câu hỏi còn mở

- Deadline thực tế là khi nào (để chia lại tuần)?
- Ngân sách API hay chỉ chạy local (để chọn LLM và kích thước tập test)?
- Nơi nộp/báo cáo (khóa luận, hội nghị, tạp chí) để chọn template LaTeX.
