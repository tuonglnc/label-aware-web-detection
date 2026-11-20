# Kết quả B-cleanpool (bỏ ví dụ Normal sai nhãn khỏi pool)

**Ngày:** 20/11/2026. Giả thuyết và tiêu chí đã khóa trước khi chạy: `cau_hinh_khoa_pool_sach.md` (commit `4a638b1`). Số liệu đầy đủ: `src/artifacts/reports/cleanpool/cleanpool.json`. Chạy lại phân tích:

```bash
python -m src.analysis.cleanpool --output src/artifacts/reports/cleanpool
```

Các run: `src/artifacts/runs/{validation,test_fresh,test_301_600}/B_cleanpool_k4`. Cả ba run coverage 1,000, không lỗi API. Chi phí khoảng 800 lượt gọi gpt-oss-20b, thêm khoảng 0,19 USD vào sổ ước tính (giá đã đặt gấp đôi giá tham khảo, nên chi phí thật thấp hơn), sổ 20b nay ghi khoảng 2,43/4,5 USD.

## 1. Kết quả

| Tập | n | B | B-cleanpool | Chênh [CI 95%] | McNemar p |
| --- | ---: | ---: | ---: | --- | ---: |
| Validation (kiểm tra chạy đúng) | 200 | 0,893 | 0,888 | −0,005 | – |
| Test mới | 300 | 0,833 | 0,841 | +0,008 [−0,011; +0,027] | 0,727 |
| Test 301–600 | 300 | 0,869 | 0,884 | +0,014 [−0,003; +0,034] | 0,289 |
| **Gộp 600** | 600 | 0,852 | 0,863 | **+0,011 [−0,002; +0,025]** | 0,210 |

## 2. Đối chiếu với giả thuyết đã khóa

| Giả thuyết | Kết quả | Kết luận |
| --- | --- | --- |
| H1: cận dưới CI của chênh Macro-F1 > −0,02 | −0,002 | Đúng, không làm hại |
| H2: câu tấn công bị đoán NORMAL không nhiều hơn B | 23 so với 25 | Đúng (giảm 2 câu) |
| H3: chênh không có ý nghĩa thống kê, trong [−0,01; +0,02] | +0,011, CI chứa 0, p = 0,21 | Đúng |

Cả ba giả thuyết đúng. Nói cách khác: bỏ ví dụ Normal sai nhãn **không cải thiện có ý nghĩa thống kê**.

## 3. Phần chênh +0,011 có phải do bộ lọc không?

Có vẻ **không**. Chia 600 query theo việc bộ ví dụ có đổi so với B hay không:

| Nhóm | Số query | Câu sửa (B sai, mới đúng) | Câu hỏng (B đúng, mới sai) |
| --- | ---: | ---: | ---: |
| Bộ ví dụ **đã đổi** (đúng nhóm bộ lọc tác động) | 110 (18%) | 5 | 4 |
| Bộ ví dụ **giống hệt** B (cùng prompt) | 490 | 6 | 1 |

Trong 490 query có prompt giống hệt, 10 câu (2%) vẫn đổi đáp án, và chênh ròng +5 nghiêng về B-cleanpool. Đây là LLM dao động giữa hai lần chạy (đã đo khoảng 0,01 ở các run chạy lại B: `src/artifacts/runs/validation_rerun`, `src/artifacts/runs/test_fresh_rerun`), có thể cộng thêm việc hai run cách nhau vài tuần. Ở nhóm bộ lọc thật sự tác động, 5 sửa so với 4 hỏng, gần như hòa. Vì vậy phần lớn mức +0,011 nhiều khả năng là nhiễu, không phải lợi ích của việc làm sạch pool.

## 4. Mô tả thêm (không phải giả thuyết)

| Tập | Macro-F1 khi bỏ Normal đáng ngờ khỏi tập đánh giá: B | B-cleanpool |
| --- | ---: | ---: |
| Test mới (284 câu) | 0,872 | 0,881 |
| Test 301–600 (286 câu) | 0,910 | 0,921 |

Thứ hạng không đổi, như ở các phân tích trước.

## 5. Ý nghĩa cho báo cáo

1. Giả thuyết "ví dụ Normal sai nhãn làm hại B" **không được ủng hộ** ở mức đo được: bỏ chúng đi thì chênh lệch không có ý nghĩa thống kê, và ở nhóm query thật sự đổi ví dụ gần như hòa (5 so với 4).
2. Điều này khớp các kết quả âm khác của đề tài (C-gated, 6 phương pháp công bố): B là baseline mạnh, các thay đổi ở khâu chọn ví dụ chỉ chạm tới khoảng 16–18% prompt nên khó vượt nhiễu cỡ 0,01.
3. Số 6,6% so với 3,3% ở `nhan_nhieu_lop_normal.md` (mẫu rất nhỏ) chỉ là gợi ý và không được thí nghiệm này xác nhận về mặt nhân quả.

## 6. Hạn chế

- Quy tắc chỉ bắt payload phổ biến; pool sau lọc có thể còn Normal sai nhãn.
- Mỗi tập chỉ 300 query; kiểm định không đủ độ mạnh để phát hiện chênh lệch dưới khoảng 0,02.
- B và B-cleanpool chạy ở hai thời điểm khác nhau, không thể tách hẳn nhiễu LLM khỏi thay đổi phía nhà cung cấp.
- Một dataset, một encoder, một LLM, k = 4.
