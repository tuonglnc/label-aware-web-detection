# Kết quả C-gated trên nửa sau tập test (dòng 301–600)

Thí nghiệm này được đăng ký trước trong `reports/experiments/cau_hinh_khoa_c_gated.md` (viết ngày 22/10/2026 lúc 22:39). Ba run chạy ngày 23/10/2026 từ 19:53 đến 20:05. Mã băm code trong `manifest.json` của cả ba run trùng đúng bảng mã băm ở mục 7 của file khóa. Ngưỡng 0,7 không bị đổi sau khi có dữ liệu.

Số liệu gốc:
- `src/artifacts/reports/test_301_600/comparison.md`
- `src/artifacts/reports/gating/test_301_600/gating.md`
- `src/artifacts/retrieval/minilm/eval_test_301_600/retrieval_metrics.md`

## 1. Kết quả chính (300 request, 50 mỗi lớp)

| Run | Macro-F1 | Accuracy | FPR Normal | LCR@4 | So với B: Δ [CI 95%] | Chỉ run đúng / chỉ B đúng | p McNemar |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| B (top-4 semantic) | 0,869 | 0,870 | 32,0% | 0,727 | — | — | — |
| C, prior kNN | 0,873 | 0,873 | 30,0% | 0,782 | +0,004 [−0,015; +0,025] | 5 / 4 | 1,000 |
| **C-gated (ngưỡng 0,7)** | **0,882** | **0,883** | **30,0%** | 0,741 | **+0,013 [−0,002; +0,030]** | **5 / 1** | 0,219 |

C-gated dùng C cho 64% số query (gate vào). Chỉ 30 query (10%) có bộ ví dụ thật sự khác B.

## 2. Đối chiếu với giả thuyết đã đăng ký trước

| Giả thuyết | Tiêu chí | Kết quả | Kết luận |
| --- | --- | --- | --- |
| H1: không kém B | Cận dưới CI 95% của (C-gated − B) > −0,02 | −0,002 | **Đạt** |
| H2: gating sửa điểm yếu của C | Macro-F1 C-gated ≥ C prior kNN; làm hỏng ít câu B đúng hơn | 0,882 ≥ 0,873; làm hỏng 1 câu so với 4 câu | **Đạt** |
| H3: không tốt hơn B có ý nghĩa thống kê | CI chứa 0; Δ quan sát trong [−0,01; +0,02] | CI [−0,002; +0,030] chứa 0; Δ = +0,013 | **Đúng như dự đoán** |

Bảng prior đúng/sai so với B:

| Run | Prior đúng (235 câu): sửa / hỏng | Prior sai (65 câu): sửa / hỏng |
| --- | ---: | ---: |
| C prior kNN | 4 / 0 | 1 / 4 |
| C-gated | 4 / 0 | 1 / 1 |

Đúng như thiết kế, gating giữ nguyên lợi ích khi prior đúng và cắt phần lớn thiệt hại khi prior sai (từ 4 câu hỏng xuống 1).

## 3. Phân tích bổ sung: một phần chênh lệch là do nhiễu của LLM

Phân tích này làm **sau** khi có dữ liệu, không có trong đăng ký trước; báo cáo để người đọc đánh giá đúng con số +0,013.

Với mỗi câu, prompt của C-gated **giống hệt** prompt của B (nếu gate ra) hoặc của C prior kNN (nếu gate vào). Dù vậy, có **6/300 câu (2%)** mà C-gated trả lời khác run "anh em" có cùng prompt, dù temperature = 0. Groq không bảo đảm kết quả tất định.

Tách 5 câu C-gated sửa được và 1 câu làm hỏng so với B:

| Loại câu | Sửa được | Làm hỏng | Ý nghĩa |
| --- | ---: | ---: | --- |
| Bộ ví dụ **giống hệt** B (270 câu) | 3 | 0 | Chỉ do nhiễu của LLM, không phải do phương pháp |
| Bộ ví dụ **khác** B (30 câu) | 2 | 1 | Tác dụng thật của gating |

Nếu ghép dự đoán của hai run đã có (B cho câu gate ra, C prior kNN cho câu gate vào), tức là bỏ nhiễu của lần chạy thứ ba, C-gated đạt **0,873**, hơn B **+0,003** [−0,007; +0,017].

Kết luận trung thực: tác dụng thật của C-gated so với B vào khoảng **+0,003 đến +0,013**, không có ý nghĩa thống kê. Phần lớn con số +0,013 nhiều khả năng đến từ nhiễu.

## 4. So sánh với nửa đầu tập test

| | Test 1–300 (đã khóa, kết quả chính) | Test 301–600 (đăng ký trước) |
| --- | ---: | ---: |
| B | 0,881 | 0,869 |
| C prior kNN | 0,862 (−0,019) | 0,873 (+0,004) |
| C-gated 0,7 | 0,878 (−0,003), chỉ tham khảo* | 0,882 (+0,013) |

\* Trên 300 câu đầu, C-gated là phản thực tế ghép từ hai run B và C prior kNN, không phải run riêng.

Trên cả hai nửa, C-gated đều **ngang B** (chênh lệch trong khoảng ±0,015, CI chứa 0) và **không kém hơn C prior kNN**. Ngược lại, C prior kNN dao động mạnh giữa hai nửa (−0,019 rồi +0,004). Đúng như kỳ vọng, gating làm phương pháp ổn định hơn.

## 5. Kết luận cho báo cáo

1. Label-aware reranking với prior kNN (C) không vượt được B. Nó gây hại chủ yếu ở những câu mà prior sai.
2. Chỉ dùng reranking khi prior kNN đủ tự tin (C-gated) loại bỏ phần lớn thiệt hại đó. Trên 300 câu chưa từng dùng, với giả thuyết và ngưỡng khóa trước, C-gated đạt 0,882 so với 0,869 của B. Kết quả thỏa cả ba giả thuyết đã đăng ký, nhưng chênh lệch với B **không có ý nghĩa thống kê**.
3. Dư địa của label-aware reranking trên SR-BH 2020 là nhỏ. Khi 5/5 hàng xóm cùng nhãn thì C trùng B, nên C-gated chỉ thay ví dụ ở khoảng 10% số câu. Nhiễu của LLM (khoảng 1–2% câu đổi kết quả với cùng prompt) có cùng cỡ với tác dụng của phương pháp.
