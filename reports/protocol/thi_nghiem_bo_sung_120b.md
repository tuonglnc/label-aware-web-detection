# Thí nghiệm bổ sung: kiểm tra kết luận với model lớn hơn (gpt-oss-120b)

**Loại thí nghiệm:** khám phá (exploratory), quyết định chạy **sau khi đã xem kết quả test** của `gpt-oss-20b`. Kết quả chính của đề tài vẫn là kết quả 20b theo [cấu hình đã khóa](cau_hinh_khoa.md). Thí nghiệm này chỉ trả lời câu hỏi: *các kết luận có giữ nguyên khi dùng model mạnh hơn không?* Báo cáo phải ghi rõ tính chất khám phá này.

## 1. Câu hỏi

1. Khoảng cách giữa B và A0 (lợi ích của ví dụ giống nhất) có thu hẹp khi model mạnh hơn không? Với 20b, khoảng cách là +0,047.
2. C với prior LLM có vượt B không, khi prior (dự đoán của A0) chính xác hơn?
3. Mức trần C-oracle so với B có lớn hơn không? Với 20b là +0,019 và không có ý nghĩa thống kê.

## 2. Thay đổi so với cấu hình chính

**Chỉ đổi model:** `openai/gpt-oss-120b` thay cho `openai/gpt-oss-20b` (file `src/configs/llm/groq_120b.json`). Những thứ sau giữ nguyên:
- prompt, `temperature`, `max_tokens`, `reasoning_effort`;
- pool, embedding, neighbors, k = 4, N = 30, λ = 0,1;
- tập test 300 request.

Cấu hình thí nghiệm nằm trong `src/configs/experiments_120b/`. Có test tự động kiểm tra rằng các file này giống hệt `src/configs/experiments/`, chỉ khác tên run và đường dẫn prior: C_llm dùng A0 của **chính model 120b** làm prior.

Kết quả lưu ở `src/artifacts/runs_120b/`, tách hoàn toàn khỏi kết quả 20b. Model ghi trong file cấu hình luôn thắng biến `A0_MODEL` trong `.env`, nên không thể vô tình chạy 20b vào thư mục 120b.

## 3. Ngân sách

- Giá tham khảo của `gpt-oss-120b` trên Groq: khoảng 0,15 USD/1 triệu token đầu vào, 0,60–0,75 USD/1 triệu token đầu ra (từ các trang tổng hợp, chưa xác minh trên trang chính thức).
- Sổ chi phí và ngưỡng **riêng**: `src/configs/llm/budget_120b.json`, ngưỡng 3,0 USD, tính với giá gấp đôi (0,30 và 1,50). Cộng với khoảng 0,7 USD (ước tính giá gấp đôi) đã dùng cho 20b, tổng vẫn dưới trần 5 USD.
- Ước tính: 4 run × 300 request, khoảng 1,6 triệu token, tức khoảng 0,25 USD tiền thật. Thêm `EXTRA=1` (C prior kNN, BAL) thì khoảng 0,45 USD.

## 4. Lệnh chạy (Git Bash, thư mục gốc repo)

```bash
source .venv/Scripts/activate && MODEL=120b bash src/experiments/run_suite.sh test --locked
```

Tùy chọn, chạy thêm C prior kNN và BAL:

```bash
MODEL=120b EXTRA=1 bash src/experiments/run_suite.sh test --locked
```

Dòng đầu output phải ghi `Model: 120b (src/configs/llm/groq_120b.json) | Kết quả: src/artifacts/runs_120b/test`.

## 5. Phân tích

```bash
python -m src.analysis.compare --split test --reference B_semantic_k4_120b --runs "src/artifacts/runs_120b/test/*" --output src/artifacts/reports/test_120b
```

So sánh với kết quả 20b trong `src/artifacts/reports/test/comparison.md`.

Cách đọc kết quả:
- Nếu với 120b, C vẫn không hơn B: kết luận "label-aware reranking không cải thiện" **mạnh hơn**, vì đúng với cả hai cỡ model.
- Nếu C hoặc C-oracle hơn B rõ rệt với 120b: kết luận chính phải **thu hẹp** lại thành "với model nhỏ", và đây là hướng nghiên cứu tiếp theo.

## 6. Kết quả (chạy ngày 20/10/2026, 300 request test)

| Run | 20b Macro-F1 | 120b Macro-F1 | 120b so với B cùng model (CI 95%) |
| --- | ---: | ---: | --- |
| A0 (zero-shot) | 0,834 | **0,793** | −0,076 [−0,113; −0,040], p < 0,001 |
| B (top-4) | **0,881** | **0,869** | — |
| BAL | 0,865 | 0,862 | −0,006 [−0,027; +0,013] |
| C, prior kNN | 0,862 | 0,866 | −0,003 [−0,027; +0,022] |
| C, prior LLM | 0,861 | 0,854 | −0,015 [−0,041; +0,010] |
| C-oracle (chỉ phân tích) | 0,900 | 0,880 | +0,011 [−0,014; +0,037] |

Chi tiết: `src/artifacts/reports/test_120b/comparison.md`. Chi phí thật khoảng 0,41 USD (sổ: `src/artifacts/api_spend_ledger_120b.json`).

Trả lời các câu hỏi ở mục 1:
1. **Khoảng cách B so với A0 không thu hẹp mà còn rộng hơn** (+0,076 với 120b so với +0,047 với 20b). Lý do: zero-shot của 120b **kém hơn** 20b (−0,041; CI [−0,080; −0,001]; McNemar p = 0,121). Lỗi chủ yếu là 120b gọi payload `";sleep 15;"`, `"|sleep 15#"` là SQL Injection (20/50 request OS Command Injection), trong khi dataset gán OS Command Injection. Khi có ví dụ trong prompt, model học được quy ước gán nhãn của dataset, nên B của hai model gần ngang nhau (−0,012, không có ý nghĩa thống kê).
2. **C với prior LLM vẫn không vượt B.** Prior của 120b còn kém chính xác hơn 20b (80% so với 83%). Khi prior sai, C làm hỏng 6 ca và chỉ sửa 2.
3. **Mức trần C-oracle vẫn nhỏ và không có ý nghĩa thống kê** (+0,011).

**Kết luận:** các kết luận chính (B tốt hơn zero-shot; label-aware reranking không cải thiện so với B; mức trần nhỏ) **giữ nguyên với model lớn gấp khoảng 6 lần**. Phát hiện thêm: model lớn hơn không tự động tốt hơn trên bài toán có quy ước nhãn riêng; ví dụ truy hồi giúp đưa model về đúng quy ước đó.
