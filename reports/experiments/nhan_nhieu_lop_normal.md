# Nhãn nhiễu ở lớp Normal và ảnh hưởng đến kết quả

**Ngày:** 01/11/2026. **Loại:** phân tích bổ sung (phân tích độ nhạy). Không gọi LLM, không sửa nhãn.

Số liệu đầy đủ: `src/artifacts/reports/label_noise/label_noise.md`. Danh sách request bị đánh dấu để kiểm tra tay: `src/artifacts/reports/label_noise/flagged_normal.jsonl`. Chạy lại:

```bash
python -m src.analysis.label_noise --output src/artifacts/reports/label_noise
```

## 1. Vấn đề

Ở mọi pipeline, lớp Normal đều yếu nhất: F1 khoảng 0,71–0,78 và FPR Normal khoảng 30%, tức gần một phần ba request "bình thường" bị báo là tấn công. Khi xem từng request Normal bị báo nhầm, hầu hết lại chứa **payload tấn công rõ ràng** trong URI, ví dụ:

- `/blog/index.php" / sleep(15) / "/page/2?s`
- `/blog/wp-content/themes';cat /etc/passwd;'/twentyseventeen/assets/js`
- `/blog/index.php/'"<script>alert(1);</script>/oembed`
- `/blog/wp-includes/Set-cookie: Tamper=0ff158bb-.../dashicons.min.css`
- `/c:\/wp-includes/js/jquery/jquery.js`

Đây là dạng payload của công cụ quét lỗ hổng (có cả tên miền `owasp.org` trong một số request). Như vậy với những câu này, LLM đoán **đúng**, còn nhãn NORMAL của SR-BH 2020 là **sai**. `reports/dataset/quyet_dinh_dataset.md` đã ghi nhận hiện tượng này trên 10 mẫu; phân tích này đo nó trên toàn bộ tập đánh giá và pool.

## 2. Cách làm

1. **Quy tắc cố định** (`SUSPICIOUS_RULES` trong `src/analysis/label_noise.py`) gồm 7 nhóm dấu hiệu: hàm trì hoãn (`sleep(`), file nhạy cảm (`/etc/passwd`), thẻ script, lệnh shell, chèn header (`Set-cookie:`), path traversal (`../`, `c:\`) và từ khóa SQL. Quy tắc quét URI, body (giải mã URL hai lần) và giá trị header. Quy tắc **chỉ nhìn nội dung request, không nhìn dự đoán của model**.
2. Request mang nhãn NORMAL khớp ít nhất một quy tắc được gọi là **"Normal đáng ngờ"**.
3. Tính lại metrics của mọi run LLM đã có khi **bỏ** các Normal đáng ngờ khỏi tập đánh giá. Nhãn của các request còn lại giữ nguyên.

**Kiểm tra tay:** cả 36 Normal đáng ngờ trong validation và test đã được đọc từng URI. Cả 36 đều chứa payload tấn công thật, không có trường hợp nào là request bình thường bị đánh dấu nhầm. Việc đọc do trợ lý AI thực hiện, chưa phải chuyên gia bảo mật xác nhận; danh sách để nhóm kiểm tra lại nằm trong `flagged_normal.jsonl`.

**Hạn chế cần nói rõ:** quy tắc được viết sau khi đã xem các lỗi Normal của B trên test 1–300. Để giảm thiên lệch, quy tắc chỉ dựa vào nội dung request, và cho tỷ lệ tương tự trên pool và validation (mục 3), là những tập không dùng để viết quy tắc. Quy tắc cũng chỉ bắt được payload phổ biến, nên số nhãn sai thật có thể còn **cao hơn**.

## 3. Bao nhiêu nhãn Normal bị sai?

| Tập | Normal đáng ngờ |
| --- | ---: |
| Pool (kho ví dụ, 500 Normal) | **139/500 (27,8%)** |
| Validation | 7/33 (21,2%) |
| Test 1–300 | 15/50 (30,0%) |
| Test 301–600 | 14/50 (28,0%) |

Khoảng **một phần tư đến gần một phần ba** request mang nhãn Normal thật ra là request tấn công. Quy tắc phổ biến nhất là lệnh shell và `/etc/passwd`, tức là dạng OS Command Injection. Điều này khớp với lỗi hay gặp nhất: Normal bị đoán thành OS Command Injection.

## 4. Kết quả khi bỏ Normal đáng ngờ khỏi tập đánh giá

| Tập | Run | Macro-F1 gốc | Macro-F1 khi bỏ | FPR Normal gốc | FPR khi bỏ | Normal bị báo nhầm (trong đó đáng ngờ) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Test 1–300 | A0 (zero-shot) | 0,834 | 0,873 | 34,0% | 8,6% | 17 (14) |
| Test 1–300 | **B** | 0,881 | **0,927** | 30,0% | **0,0%** | 15 (**15**) |
| Test 1–300 | C prior kNN | 0,862 | 0,901 | 32,0% | 5,7% | 16 (14) |
| Test 1–300 | C-oracle (chỉ phân tích) | 0,900 | 0,943 | 28,0% | 0,0% | 14 (14) |
| Test 301–600 | **B** | 0,869 | **0,910** | 32,0% | **5,6%** | 16 (14) |
| Test 301–600 | C prior kNN | 0,873 | 0,910 | 30,0% | 5,6% | 15 (13) |
| Test 301–600 | **C-gated** | 0,882 | **0,925** | 30,0% | **2,8%** | 15 (14) |
| Test 1–300, gpt-oss-120b | B | 0,869 | 0,917 | 34,0% | 5,7% | 17 (15) |

Đọc bảng:

- **29/31 lần B báo nhầm Normal** (gộp hai nửa test) rơi vào Normal đáng ngờ. Trên test 1–300, **cả 15/15** đều như vậy. FPR Normal "thật" của B khoảng **0–6%**, không phải 30%.
- Bỏ Normal đáng ngờ, Macro-F1 của B tăng khoảng **+0,04** (lên 0,91–0,93). Mọi pipeline đều tăng tương tự, kể cả model 120b.
- **Thứ hạng giữa các pipeline không đổi**, và chênh lệch so với B gần như giữ nguyên:

| Tập | Run | So với B, nhãn gốc | So với B, khi bỏ Normal đáng ngờ |
| --- | --- | --- | --- |
| Test 1–300 | C prior kNN | −0,019 [−0,051; +0,011] | −0,025 [−0,055; +0,001] |
| Test 1–300 | C-oracle | +0,019 [−0,003; +0,043] | +0,016 [−0,007; +0,039] |
| Test 301–600 | C prior kNN | +0,004 [−0,015; +0,025] | −0,000 [−0,019; +0,019] |
| Test 301–600 | C-gated | +0,013 [−0,002; +0,030] | +0,015 [−0,002; +0,033] |

Như vậy nhãn nhiễu **không làm thay đổi kết luận so sánh** của đề tài. Nó chỉ cho thấy con số tuyệt đối (Macro-F1, FPR) bị kéo thấp bởi nhãn sai, chứ không phải do LLM.

## 5. Ví dụ "Normal" sai nhãn lọt vào prompt

Vì 27,8% ví dụ Normal trong pool chứa payload, một số prompt có ví dụ được dán nhãn NORMAL nhưng nội dung là tấn công. Đây đúng là tình huống "demonstration có nhãn nhiễu" mà bài tham khảo [3] *In-Context Learning with Noisy Labels* nghiên cứu.

| Pipeline | Query có ≥ 1 ví dụ Normal đáng ngờ (test 1–300) |
| --- | ---: |
| B | 15,7% |
| BAL (cân bằng lớp) | 35,7% |
| C prior kNN | 7,3% |

Gộp validation và hai nửa test cho B: câu tấn công bị đoán thành NORMAL ở **6/91 (6,6%)** khi prompt có ví dụ Normal đáng ngờ, so với **19/576 (3,3%)** khi không có. Tỷ lệ cao gấp khoảng hai lần, nhưng số câu quá ít để kết luận chắc chắn. Ghi nhận này phù hợp với giả thuyết rằng ví dụ sai nhãn làm LLM bỏ sót tấn công. BAL ép đưa ví dụ của nhiều lớp vào prompt, nên hay kéo ví dụ Normal sai nhãn vào hơn; đây có thể là một lý do khiến BAL kém B.

## 6. Ý nghĩa cho báo cáo

1. **Kết quả chính giữ nguyên** trên nhãn gốc, theo đúng quyết định "không tự sửa nhãn" trong `quyet_dinh_dataset.md`. Phân tích này được trình bày như **phân tích độ nhạy**.
2. **Giải thích FPR Normal khoảng 30%:** phần lớn không phải lỗi của LLM mà là nhãn sai trong dataset. FPR thật của B ước tính chỉ khoảng 0–6%.
3. **Kết luận so sánh không đổi:** B vẫn là cấu hình tốt nhất trong các phương pháp dùng được thật. C-gated vẫn ngang B, không hơn có ý nghĩa thống kê.
4. **Hạn chế:** nhãn nhiễu là đặc điểm của SR-BH 2020, ảnh hưởng cả tập đánh giá lẫn kho ví dụ. Kết quả trên dataset khác có thể khác.
5. **Hướng phát triển:**
   - Nhờ chuyên gia gán lại nhãn các Normal đáng ngờ.
   - Thử loại Normal đáng ngờ khỏi pool để có kho ví dụ sạch. Thí nghiệm này phải được khóa giả thuyết trên validation trước, như C-gated.
