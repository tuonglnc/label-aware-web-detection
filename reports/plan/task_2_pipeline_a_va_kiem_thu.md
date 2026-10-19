# Task 2 — Triển khai Pipeline A0/A1, kiểm thử và báo cáo pilot

Ngày lập: 19/10/2026. Đây là kế hoạch thực hiện, chưa xác nhận pipeline đã chạy hoặc có metrics.

**Cập nhật mốc A0 ngày 19/10/2026:** zero-shot implementation, mock end-to-end và resume đã chạy; 12 test A0 và toàn suite 28/28 pass. Chưa có smoke API thật do thiếu backend/model/key; chưa chạy A1 hay validation. Phạm vi phiên này chỉ A0 và tối đa 10 mẫu development thật, thay cho số smoke dự kiến bên dưới. Xem [bản bàn giao A0](../../docs/handoff/pipeline_a0_handoff.md) để dùng đúng lệnh và artifact.

Phụ thuộc: [Task 1 — Dataset và protocol](task_1_dataset_va_protocol_pipeline_a.md). Có thể phát triển client/parser/runner với fixture trong lúc Task 1 đang làm; chỉ chạy pilot có ý nghĩa sau khi dữ liệu thật, taxonomy và split đã được bàn giao.

## Kết quả cần đạt

Hoàn thành A0 zero-shot và A1 fixed few-shot trên cùng validation subset, có predictions, metrics, logs, kiểm thử và hướng dẫn tái lập. Final test tiếp tục được giữ riêng cho benchmark A/B/C.

## Trình tự thực hiện — dự kiến 4–5 giờ

### 1. Kiểm tra bàn giao và backend

- Đọc dataset decision, label mapping, split manifests, request representation và leakage audit của Task 1; không tự đổi taxonomy hoặc split để tăng điểm.
- Xác minh các dependency và khả năng truy cập backend. Chọn một LLM/model version đang chạy được sau smoke test; không mặc định máy có GPU, Ollama hoặc API key.
- Chỉ hỏi thông tin backend/credential thực sự thiếu; không ghi secret vào config, log hoặc git.
- Khóa model ID/version, temperature (ưu tiên 0 nếu hỗ trợ), context limit, output limit, truncation, timeout và retry policy. Ghi rõ temperature 0 không bảo đảm tuyệt đối deterministic.

### 2. Xây A0 và A1

- **A0:** hướng dẫn phân loại, định nghĩa các nhãn và một query HTTP; không có demonstrations.
- **A1:** cùng hướng dẫn/định nghĩa nhãn, thêm một demonstration mỗi lớp từ pool. Chọn bằng seed cố định, lưu demo IDs và thứ tự; dùng nguyên bộ này cho mọi query. Không lấy demos từ development/validation/test.
- Đánh dấu nội dung request là dữ liệu không đáng tin cậy; không thực thi chỉ dẫn nằm trong HTTP request.
- Giữ query ground truth ngoài hàm prompt/model; evaluator đọc nhãn qua `request_id` sau inference.
- Output kỳ vọng: JSON dạng `{"label": "SQL_INJECTION"}`, dùng đúng mapping từ Task 1. Parser chỉ chấp nhận nhãn hợp lệ; output hỏng/ngoài taxonomy phải có status riêng.
- Khóa chính sách cắt request/demo trước khi chạy; kiểm tra A1 không vượt context và log trường hợp truncation.

### 3. Runner, logging và cache

- Lưu mỗi prediction cùng `request_id`, pipeline, predicted label, status, raw output, latency, token usage nếu backend cung cấp và config/prompt version.
- Lưu prompt hoặc thông tin đủ để dựng lại prompt, kèm checksum. Lưu đủ phiên bản dữ liệu/model/dependency để truy vết.
- Retry lỗi backend tạm thời có giới hạn; không retry vô hạn để tìm câu trả lời đúng. Chốt riêng cách xử lý output sai định dạng và áp dụng nhất quán A0/A1.
- Cache key phải phụ thuộc model, cấu hình sinh, prompt version, query và demos/thứ tự. Đổi prompt/model/demo phải làm mất hiệu lực cache tương ứng.
- Hỗ trợ resume sau khi ngắt; tránh ghi trùng hoặc bỏ mất query. Báo latency cold run riêng với cached run, không tính cache hit như inference mới.

### 4. Smoke test và pilot validation

- Dùng mock backend cho kiểm thử tự động và backend thật cho smoke test khoảng 20 request **development**.
- Sửa lỗi kỹ thuật/prompt dựa trên development rồi khóa cấu hình pilot.
- Đo token và latency từ smoke test, ước tính runtime/chi phí cho A0+A1 rồi chọn validation subset 100–200 mẫu theo manifest/seed đã thống nhất. Dùng cùng query IDs cho cả hai pipeline.
- Nếu ngân sách hạn chế, giảm xuống 50–100 mẫu và ghi rõ là pilot. Nếu sửa prompt sau khi xem validation thì ghi phiên bản và đánh giá trên validation, không gọi đó là final test.
- Final test không được đưa vào runner trong task này.

## Kiểm thử bắt buộc

| Nhóm test | Trường hợp | Điều kiện đạt |
| --- | --- | --- |
| Prompt | A0/A1, nhãn query dạng canary, HTTP chứa chỉ dẫn giả | A0 không demos; A1 đúng demos cố định từ pool; ground truth query không vào prompt |
| Parser | JSON hợp lệ, JSON hỏng, thiếu trường, nhãn lạ, output rỗng | Phân biệt đúng hợp lệ/invalid; không đoán nhãn bằng substring tùy tiện |
| Context | Request dài, A1 nhiều demos, thiếu token budget | Không vượt giới hạn âm thầm; quy tắc truncation có thể truy vết |
| Backend | Timeout, rate limit, lỗi không retry được | Số retry có giới hạn; lưu status và tổng chi phí/latency có thể đo được |
| Cache/resume | Chạy lại; đổi model/prompt/demo; ngắt giữa chừng | Không gọi lại kết quả đã cache đúng key; config mới không dùng nhầm cache; đủ đúng một kết quả cuối mỗi query/pipeline |
| Metrics | Fixture biết trước kết quả, lớp không được dự đoán, prediction thất bại | Metrics đúng; cố định thứ tự taxonomy; prediction lỗi không bị âm thầm loại |
| End-to-end | Fixture → A0/A1 → predictions → metrics | Một lệnh chạy được toàn luồng với mock backend |
| Integration thật | Development smoke và validation pilot | Có log/predictions thật; đủ query IDs; không đụng final test |

Không viết test gọi API thật trong bộ test mặc định. Mock test không chứng minh backend thật hoặc chất lượng phân loại; báo kết quả hai phần riêng.

## Metrics và báo cáo

- Metric chính: **Macro-F1** trên toàn bộ taxonomy đã khóa, kể cả lớp không có prediction.
- Bổ sung Accuracy, Weighted-F1, per-class Precision/Recall/F1 và support; confusion matrix có thể hiện prediction invalid/error.
- Prediction invalid/backend error được tính là sai khi tính metrics tổng. Tính F1 trên toàn bộ query IDs, giữ các lỗi như prediction ngoài taxonomy để phản ánh false negatives; không thêm lớp invalid vào trung bình Macro-F1 của các lớp mục tiêu.
- Báo coverage, invalid output rate, backend error rate, retries, latency trung bình/p50/p95 và token usage/chi phí nếu có dữ liệu xác thực. Không bịa token/cost khi backend không cung cấp.
- Ghi phân bố lớp thực tế, sampling policy, số query, số demos, model/prompt/config và giới hạn của pilot. Không dùng một pilot nhỏ để kết luận A1 tốt hơn A0 nói chung.
- Đọc một số lỗi mỗi lớp; dùng cùng protocol khi so sánh A0/A1. Chưa cần LCR@k vì Pipeline A không có retrieval.

## Artifact đề xuất

Các đường dẫn là đề xuất để triển khai; dùng cấu trúc thực tế của Task 1 nếu đã có convention phù hợp.

- `src/llm/`: backend client, prompt builder và parser.
- `src/experiments/`: A0/A1 runner, cache/resume và evaluator.
- `src/configs/pipeline_a.yaml`: model, generation, prompts/demo IDs và validation manifest.
- `src/tests/`: fixture và các test tự động ở trên.
- `src/artifacts/pipeline_a/<run_id>/`: config snapshot, predictions, metrics, confusion matrix và logs.
- `reports/progress/pipeline_a_pilot.md`: kết quả thật, phân tích lỗi và giới hạn.
- Hướng dẫn setup, chạy test, chạy smoke, pilot và resume; chốt dependency versions để tái lập.

## Điều kiện hoàn thành và xử lý thiếu thời gian

- [ ] Task 1 được bàn giao và kiểm tra; dataset/split có provenance.
- [ ] A0/A1 dùng cùng model, input representation, taxonomy và query IDs.
- [ ] Test tự động đạt; smoke test backend thật đạt.
- [ ] Cả A0/A1 hoàn tất validation pilot, có bản ghi cho mọi query kể cả lỗi.
- [ ] Có metrics, confusion matrix, runtime/token logs và báo cáo kết quả thật.
- [ ] Chạy lại từ config được; cache/resume hoạt động; final test chưa dùng để tinh chỉnh.

Nếu thiếu thời gian, giảm số validation query trước khi bỏ kiểm thử hoặc leakage audit. Nếu chỉ xong A0, ghi rõ A1 còn thiếu và không đánh dấu toàn bộ Pipeline A hoàn thành. Nếu backend thật chưa hoạt động, chỉ báo phần implementation/mock tests đã đạt; chưa có kết quả pilot.

## Prompt cho phiên Codex tiếp theo

```text
Hãy cùng tôi thực hiện Task 2 trong reports/plan/task_2_pipeline_a_va_kiem_thu.md.
Đọc AGENTS.md nếu có, kế hoạch này và artifact bàn giao của Task 1 trong
reports/plan/task_1_dataset_va_protocol_pipeline_a.md; kiểm tra trạng thái thật trước khi triển khai.
Mục tiêu là hoàn thành A0 zero-shot và A1 fixed few-shot, test tự động bằng mock,
smoke test backend thật, chạy validation pilot và xuất báo cáo metrics tái lập được.
Trao đổi bằng tiếng Việt. Hỏi sớm backend/ngân sách hoặc đầu vào thực sự thiếu,
đồng thời tiếp tục các phần không phụ thuộc câu trả lời. Không tự thay model hoặc protocol giữa benchmark.
Giữ các thay đổi hiện có của tôi; tiến hành implementation và kiểm thử, không chỉ lập lại kế hoạch.
Không dùng final test để chỉnh prompt, không đưa ground truth query vào model và không bịa kết quả.
Cuối phiên báo artifact, lệnh chạy lại, kết quả test/pilot và checklist còn thiếu.
```
