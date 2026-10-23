# Khóa cấu hình C-gated trước khi chạy nửa sau tập test

**Ngày khóa:** 22/10/2026.
**Mốc code:** commit chứa file này. Mã băm bên dưới chỉ để đối chiếu nhanh; nguồn chuẩn là commit git (mã băm file có thể đổi khi Git chuyển LF/CRLF trên Windows).

File này được viết **trước** khi có bất kỳ dự đoán nào trên nửa sau tập test. Từ mốc này, **không sửa** ngưỡng, λ, k, prompt, cấu hình LLM, dữ liệu hoặc code ảnh hưởng đến dự đoán cho đến khi chạy xong ba run ở mục 4. Nếu buộc phải sửa lỗi, chạy lại vào **thư mục output mới** và ghi rõ trong báo cáo.

## 1. Vì sao có thí nghiệm này

Trên 300 request test đầu tiên (đã khóa theo `cau_hinh_khoa.md`), C không thắng B: B đạt 0,881 Macro-F1, C prior kNN 0,862. Bảng "prior đúng/sai" cho thấy C chủ yếu làm hỏng các câu mà **prior sai**: khi prior kNN sai, C làm hỏng 11 câu B đã đúng và chỉ sửa được 2.

Ý tưởng C-gated: chỉ xếp hạng lại theo nhãn khi prior kNN **đủ tự tin**; còn lại dùng nguyên top-4 của B.

**Những gì đã biết trước khi khóa (công khai để người đọc tự đánh giá):** kết quả tổng hợp của 300 test đầu, kể cả bảng prior đúng/sai ở trên, đã được xem; chính nó gợi ra ý tưởng này. Vì vậy 300 test đầu **không** được dùng để kiểm chứng C-gated. Ngưỡng được chọn **chỉ** trên validation, và được chốt **trước** khi chạy phân tích gating trên 300 test đầu.

## 2. Phương pháp C-gated

- Prior: bỏ phiếu kNN có trọng số similarity trên 5 hàng xóm gần nhất (như C prior kNN).
- Độ tự tin của prior: `share = điểm của nhãn thắng / tổng điểm 5 hàng xóm` (`src/retrieval/knn.py`, hàm `vote_share`).
- Nếu `share ≥ 0,7`: chọn ví dụ như C, `score = similarity + 0,1 · 1[nhãn ứng viên = prior]`, lấy top-4 trong 30 ứng viên.
- Nếu `share < 0,7`: chọn như B, top-4 theo similarity.
- Code: `gated_label_aware_rerank` trong `src/retrieval/selectors.py`; cấu hình `src/configs/experiments/C_gated_k4.json` (giống hệt `C_knn_k4.json`, chỉ thêm `"prior_min_share": 0.7` và đổi tên).

Nhận xét quan trọng: khi 5/5 hàng xóm cùng nhãn thì 4 ví dụ của B đã cùng nhãn prior, nên C không đổi gì. C chỉ thay ví dụ ở những query có hàng xóm bất đồng, và đó lại là nơi prior hay sai. Ngưỡng phải nằm ở giữa: đủ cao để prior đáng tin, đủ thấp để C còn thay đổi được gì đó.

## 3. Chọn ngưỡng trên validation (200 request)

Số liệu: `src/artifacts/reports/gating/validation/gating.md` (sinh bởi `python -m src.experiments.analyze_gating`, không gọi LLM). Cột "phản thực tế" ghép dự đoán đã có: câu gate vào lấy dự đoán của run C prior kNN, câu gate ra lấy của run B. Cách ghép này đúng với C-gated vì prompt của từng câu trùng hệt prompt của một trong hai run đó.

| Ngưỡng | Gate vào | Prior đúng (gate vào) | Bộ ví dụ khác B | Prior đúng (ở câu khác B) | Macro-F1 phản thực tế | Sửa / làm hỏng so với B |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 (= C prior kNN) | 100% | 81,0% | 98 | 65,3% | 0,882 | 1 / 3 |
| 0,5 | 85,0% | 84,7% | 69 | 68,1% | 0,893 | 1 / 1 |
| 0,6 | 74,5% | 90,6% | 48 | 79,2% | 0,898 | 1 / 0 |
| **0,7** | **63,5%** | **93,7%** | **26** | **84,6%** | **0,899** | **1 / 0** |
| 0,8 | 56,5% | 96,5% | 12 | 100% | 0,899 | 1 / 0 |
| 0,9 trở lên (= B) | ≤ 45,5% | 97,8% | 0 | – | 0,893 | 0 / 0 |

B trên validation: 0,893.

**Quy tắc chọn (ghi lại trước khi xem test):** các ngưỡng 0,6, 0,7 và 0,8 cho Macro-F1 phản thực tế gần như bằng nhau, chênh nhau đúng một câu, nên Macro-F1 trên validation không phân biệt được chúng. Vì vậy chọn theo tiêu chí retrieval: **ngưỡng nhỏ nhất mà prior đúng ở các câu bị đổi ví dụ không thấp hơn độ chính xác chung của prior kNN (81,0%)**. Ngưỡng 0,6 cho 79,2%, chưa đạt. Ngưỡng 0,7 cho 84,6%, đạt. Do đó chọn **0,7**. Ngưỡng này cũng nằm giữa vùng bằng nhau 0,6–0,8, nên ít nhạy với nhiễu.

## 4. Thí nghiệm mới trên nửa sau tập test

**Dữ liệu:** dòng 301–600 của `src/data/processed/sr_bh_v1/test_subset.jsonl`, 50 request mỗi lớp, cố định từ khi tạo dữ liệu. Đã kiểm tra trước khi khóa: không có file `predictions.jsonl` nào trong `src/artifacts/` chứa request nào của nửa này, và `eval_retrieval` trên test chỉ chấm 300 câu đầu. Runner chọn đúng nửa này bằng `--allow-test --offset 300 --limit 300`; manifest của run ghi `"offset": 300`.

| Run | File cấu hình | Thư mục output |
| --- | --- | --- |
| B (mốc so sánh) | `B_k4.json` | `src/artifacts/runs/test_301_600/B_k4` |
| C, prior kNN | `C_knn_k4.json` | `src/artifacts/runs/test_301_600/C_knn_k4` |
| **C-gated** | `C_gated_k4.json` | `src/artifacts/runs/test_301_600/C_gated_k4` |

LLM, prompt, pool, embedding, N = 30, k = 4, λ = 0,1 giữ nguyên như `cau_hinh_khoa.md`. Không chạy A0, A1, BAL, C-oracle trên nửa này.

## 5. Giả thuyết và tiêu chí, ghi trước khi có dữ liệu

Phép so sánh chính: **C-gated so với B**, Macro-F1 trên 300 request (dòng 301–600), CI 95% bootstrap ghép cặp (2.000 lần lặp, seed 42) và McNemar, đúng như `src/analysis/compare.py`.

1. **H1 (không kém B):** cận dưới CI 95% của (C-gated − B) lớn hơn −0,02.
2. **H2 (gating sửa được điểm yếu của C):** Macro-F1 của C-gated ≥ C prior kNN, và số câu "B đúng, C-gated sai" ít hơn số câu "B đúng, C prior kNN sai".
3. **H3 (dự đoán thẳng thắn):** C-gated **không** tốt hơn B một cách có ý nghĩa thống kê (CI chứa 0). Chênh lệch quan sát dự kiến trong khoảng [−0,01; +0,02], vì chỉ khoảng 13% số câu có bộ ví dụ khác B.

Kết quả được báo cáo **dù đúng hay sai** so với các giả thuyết trên. Không đổi ngưỡng sau khi xem dữ liệu. Kết quả trên 300 test đầu vẫn là kết quả chính đã khóa; nửa sau là một thí nghiệm bổ sung có đăng ký trước, phải được báo cáo tách riêng.

## 6. Tham khảo: 300 test đầu (phân tích chạy SAU khi đã chốt ngưỡng 0,7)

Chỉ để tham khảo, **không** phải kiểm chứng, vì tập này đã được xem. Số liệu: `src/artifacts/reports/gating/test_1_300_exploratory/gating.md`.

| Ngưỡng | Bộ ví dụ khác B | Macro-F1 phản thực tế | So với B (0,881) | Sửa / làm hỏng so với B |
| --- | ---: | ---: | ---: | ---: |
| 0 (= C prior kNN) | 139 | 0,862 | −0,019 [−0,051; +0,011] | 7 / 13 |
| 0,7 (đã khóa) | 24 | 0,878 | −0,003 [−0,018; +0,010] | 2 / 3 |
| 0,9 trở lên (ví dụ y hệt B) | 0 | 0,878 | −0,003 | 0 / 1 |

Dòng cuối cho thấy mức nhiễu của LLM: dù prompt y hệt B, vẫn có 1 câu cho kết quả khác giữa hai lần chạy ở temperature 0. Trên tập này C-gated gần như hòa B và tốt hơn C prior kNN, phù hợp với H2 và H3.

## 7. Mã băm tại thời điểm khóa (16 ký tự đầu của SHA-256)

| File | SHA-256 |
| --- | --- |
| `src/experiments/run_llm.py` | `c265bdc3a0fca752` |
| `src/experiments/prompting.py` | `f63100ab21d9460c` |
| `src/retrieval/selectors.py` | `50000c54894a3048` |
| `src/retrieval/knn.py` | `b3c90a3978c24b1f` |
| `src/retrieval/views.py` | `d36740d8f3b07396` |
| `src/llm/client.py` | `006a5d3b5019cae4` |
| `src/configs/llm/groq.json` | `37a620716bcfac4a` |
| `src/configs/experiments/B_k4.json` | `e7a65111c5a57d9e` |
| `src/configs/experiments/C_knn_k4.json` | `e27bb60c6dd78bb0` |
| `src/configs/experiments/C_gated_k4.json` | `ba014dcedbc218db` |
| `src/data/processed/sr_bh_v1/test_subset.jsonl` | `64c009b41a370ab9` |
| `src/data/processed/sr_bh_v1/pool_subset.jsonl` | `6dd9ad930e6286bc` |
| `src/artifacts/retrieval/minilm/neighbors_test.jsonl` | `0a54ae10ec80dc01` |
| Danh sách `request_id` dòng 301–600 (`sha256_of`, như `query_ids_sha256` trong manifest) | `98cb3ec4c465b6db` |

## 8. Lệnh chạy

Chạy trong Git Bash, ở thư mục gốc repo, trên code của commit đã khóa. Ba run dùng chung một key trong `.env` và chốt ngân sách `src/configs/llm/budget.json`.

```bash
source .venv/Scripts/activate && export PYTHONIOENCODING=utf-8
```

```bash
for c in B_k4 C_knn_k4 C_gated_k4; do python -m src.experiments.run_llm --config src/configs/experiments/$c.json --llm src/configs/llm/groq.json --env-file .env --split test --allow-test --offset 300 --limit 300 --retry-errors --budget src/configs/llm/budget.json --output src/artifacts/runs/test_301_600/$c || break; done
```

Nếu dừng giữa chừng (hết quota, mất mạng), chạy lại đúng lệnh trên: run đã xong được bỏ qua, run dở được chạy tiếp.

Kiểm tra đường chạy: sau khi khóa, lệnh trên đã được chạy thử với LLM giả (`--llm src/configs/llm/mock.json`, output ngoài repo) để xác nhận manifest ghi `offset = 300` và mã băm danh sách query khớp mục 7. LLM giả chỉ đếm nhãn của ví dụ, không gọi API, và không có gì được chỉnh sau lần chạy thử này.

Sau khi cả ba run xong (không gọi API):

```bash
python -m src.analysis.compare --split test --reference B_semantic_k4 --runs "src/artifacts/runs/test_301_600/*" --output src/artifacts/reports/test_301_600
```

```bash
python -m src.experiments.analyze_gating --split test --offset 300 --limit 300 --runs-dir src/artifacts/runs/test_301_600 --output src/artifacts/reports/gating/test_301_600 --title "C-gated: kiểm tra phản thực tế trên test 301-600"
```

```bash
python -m src.experiments.eval_retrieval --retrieval src/artifacts/retrieval/minilm --split test --offset 300 --limit 300 --output src/artifacts/retrieval/minilm/eval_test_301_600
```

**Chi phí dự kiến:** 900 lần gọi × (khoảng 1.446 token vào + 42 token ra, lấy trung bình thực tế của B và C trên 300 test đầu) ≈ 1,34 triệu token. Theo giá tham khảo của `openai/gpt-oss-20b` (0,075 / 0,30 USD mỗi triệu token) là khoảng **0,11 USD**. Sổ chi phí (giá gấp đôi) sẽ tăng khoảng 0,22 USD, từ 0,68 lên khoảng 0,90 USD, vẫn xa ngưỡng 4,5 USD.
