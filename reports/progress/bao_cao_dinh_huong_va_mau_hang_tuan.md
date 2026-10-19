# Báo cáo định hướng và mẫu báo cáo hằng tuần

**Đề tài:** Label-Aware Retrieval for LLM-Based Web Attack Detection.  
**Thành viên:** [TV1 — họ tên], [TV2 — họ tên].  
**Giảng viên hướng dẫn:** [Họ tên].  
**Buổi định hướng dự kiến:** 16–18/10/2026; ngày cụ thể thống nhất với giảng viên.

## 1. Mục tiêu của báo cáo tuần này

Nhóm xin cập nhật lại hướng nghiên cứu sau 6 tuần chưa duy trì được việc báo cáo, trình bày đúng hiện trạng và đề xuất kế hoạch triển khai 4 tuần. Nhóm mong nhận góp ý để chốt phạm vi, protocol thực nghiệm và các mốc kiểm chứng kết quả.

Nếu có lý do cụ thể cho việc gián đoạn, nhóm bổ sung ngắn gọn và trung thực. Không tự nhận đã hoàn thành các công việc chỉ mới nằm trong kế hoạch.

## 2. Gợi ý mở đầu buổi gặp

> Thưa thầy, nhóm em đã chưa duy trì được việc báo cáo trong 6 tuần vừa qua. Nhóm xin lỗi thầy về sự gián đoạn này. Trong buổi hôm nay, nhóm xin trình bày hướng nghiên cứu đã lựa chọn, những tài liệu và khảo sát hiện có, cùng kế hoạch triển khai cụ thể cho hai thành viên. Nhóm mong thầy góp ý để chốt phạm vi và thực hiện báo cáo hằng tuần, hướng tới hoàn thành thực nghiệm trong 4 tuần.

## 3. Nội dung 6 slide đề xuất

| Slide | Nội dung chính | Bằng chứng/tài liệu kèm theo |
| --- | --- | --- |
| **1. Hiện trạng và mục tiêu** | Nêu gián đoạn báo cáo, hiện trạng thật, mục tiêu triển khai | Repo, danh sách tài liệu đã có; phân biệt đã làm/chưa làm |
| **2. Bài toán và RQ** | Phân loại Web Attack từ HTTP request; label-aware demonstration selection có giúp LLM hơn similarity-only retrieval không? | Mô tả đề tài và một ví dụ minh họa; ghi rõ ví dụ minh họa nếu chưa lấy từ dữ liệu |
| **3. Phương pháp** | A: zero-shot/fixed few-shot; B: semantic retrieval; C: zero-shot prior + reranking + LLM; inference-only | Sơ đồ pipeline; phân biệt prior dự đoán với ground truth |
| **4. Dữ liệu và đánh giá** | CAPEC là ứng viên ưu tiên; duplicate, imbalance, annotation; Macro-F1, per-class F1, LCR@k và cost | EDA đã có, kế hoạch split/group và chống leakage |
| **5. Kế hoạch cho 2 người** | 4 tuần: dữ liệu/A → B/C → validation/ablation → final benchmark | Timeline và tên người phụ trách từng mảng |
| **6. Quyết định cần xin ý kiến** | Phạm vi, dữ liệu, đối chứng, ngân sách và tiêu chí hoàn thành | Các phương án cùng bằng chứng để thầy góp ý |

LCR@k chỉ là metric phân tích retrieval. Demonstrations khác query label không đồng nghĩa bị gán sai nhãn; cần đánh giá đóng góp thực tế bằng classification metrics.

## 4. Hiện trạng để báo cáo

| Đã có trong repo | Chưa hoàn tất |
| --- | --- |
| Mô tả hướng nghiên cứu, thiết kế A/B/C trong kế hoạch chính | Xác minh đầy đủ novelty và chốt experimental protocol |
| Danh mục papers tham khảo | Kiểm tra lại các công trình gần nhất và lập luận research gap |
| Notebook EDA và mô tả đề tài | Chốt dataset/taxonomy, xử lý dữ liệu và khóa split |
| Kế hoạch 4 tuần cho hai người | Implementation pipeline, benchmark và ablation |

Không dùng “đã chứng minh Label-Aware Retrieval tốt hơn” hoặc “chưa có nghiên cứu nào làm” khi chưa có đủ bằng chứng. Trình bày đây là câu hỏi nhóm sẽ kiểm chứng.

## 5. Các quyết định cần xin ý kiến giảng viên

1. Phạm vi inference-only, một dataset và một LLM chính có phù hợp với mục tiêu nghiên cứu không?
2. Taxonomy dự kiến và quy trình xử lý duplicate/annotation có cần điều chỉnh không?
3. Baselines, ablation và đánh giá đề xuất đã đủ để kiểm chứng đóng góp chưa? Thầy ưu tiên thực nghiệm bổ sung nào?
4. Ngân sách và tiêu chí hoàn thành thực nghiệm cần giới hạn thế nào?
5. Lịch báo cáo hằng tuần và thời gian review kết quả thuận tiện cho thầy là khi nào?

## 6. Mẫu báo cáo hằng tuần sau buổi định hướng

### Thông tin

- **Tuần/khoảng ngày:** [...]
- **Ngày gửi và ngày gặp:** [...]
- **Mục tiêu đã thống nhất ở tuần trước:** [...]

### Kết quả và bằng chứng

| Công việc | Người phụ trách | Kết quả thực tế | Link file/commit/config |
| --- | --- | --- | --- |
| [...] | [...] | Hoàn thành/đang làm/chưa đạt; mô tả sản phẩm | [...] |

### Kết quả thực nghiệm nếu đã có

| Phương pháp/config | Split và số queries | Macro-F1 | LCR@k | Invalid output rate | Latency/cost |
| --- | --- | --- | --- | --- | --- |
| [...] | [...] | [...] | [...] | [...] | [...] |

Ghi model/version, seed, k/N và thời điểm chạy. Đánh dấu pilot/validation/final test; dùng `N/A` nếu metric không áp dụng. Không điền số liệu dự kiến vào bảng kết quả.

### Việc chưa đạt và hướng xử lý

- **Vướng mắc:** [...]
- **Ảnh hưởng đến tiến độ:** [...]
- **Phương án và ngày xử lý:** [...]

### Câu hỏi cần thầy góp ý

Chọn tối đa 3 quyết định cụ thể; kèm phương án nhóm đề xuất và bằng chứng để thầy nhận xét.

### Cam kết tuần tiếp theo

| Việc cần hoàn thành | Người phụ trách | Deadline | Tiêu chí hoàn thành |
| --- | --- | --- | --- |
| [...] | TV1 | [...] | [...] |
| [...] | TV2 | [...] | [...] |

### Ghi nhận sau buổi gặp

- **Ý kiến và quyết định của giảng viên:** [...]
- **Thay đổi phạm vi/protocol:** [...]
- **Action items và ngày báo cáo tiếp theo:** [...]

## 7. Tài liệu đính kèm buổi định hướng

- [Mô tả đề tài](../mo_ta_de_tai.md).
- [Kế hoạch triển khai 4 tuần](../plan/ke_hoach_trien_khai_4_tuan.md).
- [Notebook khảo sát dataset](../../src/notebooks/sr_bh_2020_khao_sat.ipynb).
- [Danh mục papers tham khảo](../references/link_papers.md).

Chỉ gửi các tài liệu cần đọc trước buổi gặp; bộ slide và bản tóm tắt cần đủ ngắn để thầy nắm được hướng và những quyết định đang cần góp ý.
