# Khóa cấu hình B-cleanpool (làm sạch pool) trước khi chạy

**Ngày khóa:** 20/11/2026.
**Mốc code:** commit chứa file này. Nguồn chuẩn là commit git.

File này được viết **trước** khi có bất kỳ dự đoán LLM thật nào của cấu hình mới. Từ mốc này **không sửa** quy tắc, k, N, prompt, LLM, dữ liệu hay code ảnh hưởng đến dự đoán cho đến khi chạy xong các run ở mục 4. Nếu buộc phải sửa lỗi thì chạy lại vào thư mục output mới và ghi rõ trong báo cáo.

## 1. Vì sao có thí nghiệm này

`nhan_nhieu_lop_normal.md` cho thấy 27,8% ví dụ Normal trong pool (139/500) thật ra chứa payload tấn công. Với B, câu tấn công bị đoán thành NORMAL ở 6,6% (6/91) khi prompt có ví dụ Normal sai nhãn, so với 3,3% (19/576) khi không có. Số mẫu nhỏ, nên chỉ là gợi ý. Mục "Hướng phát triển" của tài liệu đó đề xuất đúng thí nghiệm này, kèm điều kiện phải khóa giả thuyết trước.

**Câu hỏi:** nếu bỏ các ví dụ Normal sai nhãn khỏi pool, B có tốt hơn không?

**Những gì đã biết trước khi khóa (công khai):**
- Quy tắc `SUSPICIOUS_RULES` được viết sau khi xem lỗi Normal của B trên test 1–300. Vì vậy test 1–300 **không** dùng để kiểm chứng.
- Tỷ lệ Normal đáng ngờ trên test 301–600 (14/50) đã được tính, nhưng chưa có dự đoán nào của cấu hình mới trên tập đó.
- Trên validation, chạy với LLM giả (không gọi API) cho thấy bộ lọc loại 139 ví dụ pool và làm **đổi bộ ví dụ của 32/200 query (16%)**, đúng bằng số query vốn có ví dụ nhiễm bẩn. Đây là mức tối đa hiệu ứng có thể có.
- Chưa có số Macro-F1 nào của B-cleanpool.

## 2. Phương pháp

- **B-cleanpool** giống hệt B (top-30 theo cosine MiniLM, lấy 4 ví dụ đầu, `max_demo_chars` = 500, cùng prompt, cùng LLM gpt-oss-20b, temperature 0), chỉ khác: trước khi cắt top-N, bỏ các ứng viên pool mang nhãn NORMAL mà khớp ít nhất một quy tắc trong `SUSPICIOUS_RULES` (`src/analysis/label_noise.py`). Quy tắc chỉ nhìn nội dung request.
- Không sửa nhãn của query đánh giá. Không loại ví dụ khỏi các lớp khác.
- Code: `pool_filter = "noise_rule"` trong `src/experiments/run_llm.py`; cấu hình `src/configs/experiments/B_cleanpool_k4.json`.
- Không có tham số nào để chỉnh (quy tắc cố định, không ngưỡng), nên không có bước chọn cấu hình trên validation.

## 3. Giả thuyết và tiêu chí, ghi trước khi có dữ liệu

Phép so sánh chính: **B-cleanpool so với B** trên cùng query, Macro-F1, CI 95% bootstrap ghép cặp (2.000 lần, seed 42) và McNemar, đúng như `src/analysis/compare.py`.

1. **H1 (không hại):** trên 600 query gộp (test 301–600 và test mới), cận dưới CI 95% của (B-cleanpool − B) lớn hơn −0,02.
2. **H2 (cơ chế):** số câu tấn công bị đoán thành NORMAL ở B-cleanpool **không nhiều hơn** ở B, trên 600 query gộp.
3. **H3 (dự đoán thẳng thắn):** chênh Macro-F1 **không có ý nghĩa thống kê** (CI chứa 0), trong khoảng [−0,01; +0,02]. Lý do: chỉ khoảng 16% prompt thay đổi, và LLM tự dao động khoảng 0,01 giữa hai lần chạy.

Kết quả được báo cáo **dù đúng hay sai** so với các giả thuyết trên. Không thêm biến thể, không đổi quy tắc sau khi xem dữ liệu. Báo cáo cũng ghi thêm (mô tả, không phải giả thuyết): Macro-F1 khi bỏ Normal đáng ngờ khỏi tập đánh giá, và chỉ riêng nhóm query bị đổi ví dụ.

## 4. Các run

Thứ tự: validation (kiểm tra chạy đúng, không dùng để chọn gì), rồi hai tập test.

| Run | Split | Query | Thư mục output | Mốc so sánh |
| --- | --- | ---: | --- | --- |
| Kiểm tra | validation | 200 | `src/artifacts/runs/validation/B_cleanpool_k4` | `.../validation/B_k4` |
| Chính 1 | test_fresh | 300 | `src/artifacts/runs/test_fresh/B_cleanpool_k4` | `.../test_fresh/B_k4` |
| Chính 2 | test, offset 300 | 300 | `src/artifacts/runs/test_301_600/B_cleanpool_k4` | `.../test_301_600/B_k4` |

Validation chỉ để chắc pipeline chạy đúng (coverage 1,0, không lỗi API). Không có ngưỡng nào được chọn từ đó. Nếu validation cho Macro-F1 thấp hơn B quá 0,03, dừng lại tìm lỗi chạy trước khi dùng tập test; không đổi quy tắc.

Chi phí dự kiến khoảng 800 lượt gọi gpt-oss-20b, đi qua chốt ngân sách `src/configs/llm/budget.json` (sổ hiện ước tính khoảng 2,2 trên 4,5 USD theo giá đã đặt gấp đôi).

## 5. Hạn chế đã biết

- Quy tắc chỉ bắt payload phổ biến, nên pool sau lọc vẫn có thể còn Normal sai nhãn.
- Nhãn của query đánh giá vẫn nhiễu như cũ, nên Macro-F1 tuyệt đối bị kéo thấp bất kể pool.
- Một dataset, một encoder, một LLM, k = 4. Không suy rộng ra ngoài phạm vi này.
