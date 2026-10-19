# Bản nháp báo cáo tiến độ ngày 20/10/2026

Ngày tổng hợp: 19/10/2026. Người trình bày: [Tên TV1], [Tên TV2]. Bản nháp dựa trên code và artifact hiện có; các mục kế hoạch chưa phải kết quả đã hoàn thành.

## 1. Tóm tắt để đưa vào report

Đề tài nghiên cứu lựa chọn ví dụ có nhãn cho LLM trong bài toán phân loại tấn công web từ HTTP request. Câu hỏi nghiên cứu là: kết hợp thông tin nhãn và dự đoán zero-shot khi lựa chọn ví dụ có cải thiện kết quả so với retrieval chỉ dựa trên độ tương đồng ngữ nghĩa hay không? Nhóm triển khai theo hướng inference-only, không huấn luyện hoặc fine-tune model.

Đến ngày 19/10/2026, nhóm đã khảo sát SR-BH 2020 và CSIC 2010, xây dựng preprocessing, kiểm tra dữ liệu trùng/mâu thuẫn và tạo split v1 cho SR-BH. Dữ liệu nguồn SR-BH có 907.815 bản ghi; sau xử lý theo phạm vi sáu lớp còn 466.267 request duy nhất. Nhóm đã triển khai baseline A0 zero-shot với prompt, parser, lưu prediction, resume và metrics; luồng end-to-end đã được kiểm chứng bằng mock. Bộ kiểm thử gần nhất được ghi nhận đạt 28/28 test. Lần smoke API thật đang có một request lỗi HTTP 403, chưa có prediction hợp lệ để đánh giá năng lực LLM.

Hai vấn đề cần giải quyết trước thực nghiệm chính là chất lượng annotation và khả năng truy cập backend LLM. Trong ba tuần tiếp theo, nhóm dự kiến hoàn thiện A0/A1, semantic retrieval B, label-aware retrieval C và đối chứng cân bằng lớp; chọn cấu hình trên validation, khóa protocol rồi chạy final test. Sản phẩm cuối gồm kết quả so sánh, ablation tối thiểu, phân tích lỗi và chi phí, mã nguồn tái lập, báo cáo và slide. Mục tiêu hoàn tất là ngày 10/11/2026, với giả định mỗi thành viên dành 20–25 giờ/tuần.

## 2. Bài toán và phương pháp

Đầu vào là HTTP request gồm method, URI, protocol, headers và body. Đầu ra là một nhãn trong taxonomy đang khảo sát: Normal, SQL Injection, Path Traversal, Code Injection, HTTP Response Splitting và OS Command Injection. Sáu lớp này đã được dùng trong preprocessing/pilot kỹ thuật; taxonomy benchmark vẫn cần chốt.

| Phương pháp | Cách chọn ví dụ | Mục đích |
| --- | --- | --- |
| A0 | Không đưa ví dụ vào prompt | Baseline zero-shot và nguồn prior cho C |
| A1 | Bộ ví dụ cố định lấy từ pool | Đối chứng few-shot không retrieval |
| B | Top-k theo semantic similarity | Baseline retrieval chính |
| Balanced | Chọn ví dụ theo similarity với phân bổ theo lớp được định nghĩa trước | Kiểm tra lợi ích của cân bằng nhãn |
| C | Retrieve top-N, rerank theo similarity và nhãn prior, chọn top-k | Phương pháp cần kiểm chứng |

Luồng C: `request → embedding/top-N candidates + A0 prior → rerank → top-k demonstrations → LLM → predicted label`.

Nhãn demonstration lấy từ retrieval pool. Prior của query là dự đoán của A0; nhãn thật của query chỉ dùng để đánh giá. Ví dụ hai request rất giống nhau nhưng có nhãn khác nhau là động cơ nghiên cứu, chưa chứng minh retrieval B thất bại hay C tốt hơn.

## 3. Công việc đã thực hiện và bằng chứng

| Hạng mục | Kết quả hiện có | Bằng chứng |
| --- | --- | --- |
| Khảo sát SR-BH | Đọc dữ liệu thật, trả lời 7 câu hỏi khảo sát, có payload và cặp request minh họa | [Khảo sát SR-BH](../surveys/khao_sat_sr_bh_2020.md) |
| Khảo sát CSIC | 97.065 request trong ba file đã tải; nhãn nguồn Normal/Anomalous | [Khảo sát CSIC](../surveys/khao_sat_csic_2010.md) |
| Preprocessing | Chuẩn hóa representation, lọc single-label, cách ly conflict, exact dedup, group split seed 42 | [Báo cáo Task 1](task_1_dataset_va_protocol.md), [summary](../../src/artifacts/data/summary.json) |
| Kiểm tra split | Không giao nhau ID/exact hash/group theo quy tắc hiện có; endpoint vẫn có overlap | [Leakage audit](../../src/artifacts/data/leakage_audit.json) |
| Tái lập dữ liệu | Hai lần xử lý toàn dataset tạo 12 file có hash giống nhau | [Reproducibility](../../src/artifacts/data/reproducibility.json) |
| Review annotation ban đầu | Review kỹ thuật 60 mẫu development/pool; chưa được hai người adjudicate | [Review assessment](../../src/artifacts/data/manual_review_assessment.json) |
| A0 | Có backend client, prompt/parser, retry giới hạn, lưu từng prediction, resume và metrics | [Code A0](../../src/pipeline_a0/core.py), [README hiện tại](../../README.md) |
| Kiểm thử phần mềm | Bằng chứng lần chạy gần nhất: 28/28 test, gồm 12 test A0 | [Test log](../../src/artifacts/pipeline_a0/test_results.txt) |
| Smoke API thật | Một request có `backend_error`, `http_403`, chưa có output LLM hợp lệ | [Predictions](../../src/artifacts/pipeline_a0/groq_dev_one_01/predictions.jsonl), [metrics](../../src/artifacts/pipeline_a0/groq_dev_one_01/metrics.json) |
| A1/B/C, Balanced và benchmark | Chưa triển khai/chưa có kết quả | Công việc trong kế hoạch tiếp theo |

Một số tài liệu cũ còn ghi “chưa có A0” hoặc “chưa gọi API”; trạng thái trong bản này ưu tiên code/artifact hiện có. Không sử dụng bảng hiện trạng cũ để báo cáo tiến độ mới.

### Số liệu dữ liệu cần trình bày

| Chỉ số SR-BH | Giá trị |
| --- | ---: |
| Record nguồn / số cột / cột nhãn | 907.815 / 38 / 14 |
| Multi-label trên toàn bộ nhãn nguồn | 9.238 |
| Request unique mâu thuẫn nhãn / record liên quan | 288 / 2.331 |
| Exact duplicate rows bỏ trong phần dữ liệu được giữ | 358.720 |
| Request unique sau xử lý | 466.267 |
| Pool đầy đủ / development / validation đầy đủ / test đầy đủ | 326.595 / 30 / 69.950 / 69.692 |
| Subset đã tạo: pool / validation / test | 3.000 / 200 / 600 |

Các counters lọc có thể giao nhau, không cộng các dòng thành một chuỗi loại trừ. Subset pool và test cân bằng lớp; validation có 33–34 mẫu/lớp. Các subset này chưa được chốt thành benchmark chính thức, không đại diện phân bố traffic tự nhiên. Không cần chạy toàn bộ 466.267 request qua LLM để hoàn thành nghiên cứu.

## 4. Vướng mắc và cách xử lý

| Vấn đề | Ảnh hưởng | Việc tiếp theo |
| --- | --- | --- |
| Annotation đáng nghi | Review kỹ thuật thấy 5/10 mẫu Normal có payload đáng nghi; chưa thể xem sai khác với nhãn nguồn là lỗi phát hiện thực tế | Hai thành viên review độc lập cùng mẫu development/pool, ghi bất đồng; chốt chính sách nhãn với thầy trước 22/10 |
| API trả HTTP 403 | Chưa kiểm chứng inference thật, latency/token hay chất lượng phân loại | Kiểm tra endpoint, quyền model và phản hồi backend; thử lại có giới hạn sau khi xử lý nguyên nhân. Artifact hiện tại chưa đủ để kết luận nguyên nhân 403 |
| Grouping chưa bao phủ mọi near-duplicate | Audit hiện tại chưa chứng minh khả năng tổng quát sang endpoint/campaign mới | Review nhóm development/pool, công bố endpoint overlap và giới hạn; nếu đổi split phải version hóa trước benchmark |
| CSIC không có nhãn subtype gốc | Không thể thay trực tiếp bài toán sáu lớp bằng CSIC | Giữ vai trò khảo sát; nếu chuyển sang nhị phân phải đổi RQ/taxonomy/protocol. Quyền sử dụng bản tải cũng cần xác minh |
| Thời gian ba tuần | Dễ thiếu thời gian phân tích và viết báo cáo nếu mở rộng nhiều cấu hình | Một dataset, một LLM, một embedding; ưu tiên đối chứng và ablation tối thiểu |

Review 60 mẫu do Codex ghi nhận chỉ là sàng lọc kỹ thuật, chưa phải xác nhận chuyên gia và không cho phép ước lượng tỷ lệ nhãn sai toàn dataset. Giữ nguyên nhãn nguồn đến khi có protocol; không loại mẫu chỉ vì model dự đoán khác.

## 5. Kế hoạch thực hiện tiếp theo — đoạn có thể chép vào report

Trong tuần 1 (21–27/10/2026), TV1 phụ trách chốt dữ liệu/taxonomy và xây semantic retrieval, TV2 hoàn thiện kết nối LLM, A1 và runner đánh giá. Nhóm tích hợp B, Balanced và C ở dạng tối thiểu trên development/validation. Trong tuần 2 (28/10–03/11/2026), TV1 hoàn thiện reranker và kiểm tra retrieval, TV2 chạy so sánh validation, ablation và đo chi phí; hai thành viên chọn cấu hình và khóa protocol trước cuối ngày 03/11. Trong tuần 3 (04–10/11/2026), nhóm chạy final benchmark trên cùng test IDs với cấu hình đã khóa, phân tích per-class và failure cases, hoàn thiện báo cáo, slide và hướng dẫn tái lập. Ngày 10/11 dành cho review chéo và diễn tập báo cáo.

Kế hoạch chi tiết theo người, đầu ra và điều kiện hoàn thành nằm trong [phân công hôm nay và kế hoạch ba tuần](../plan/ke_hoach_2_nguoi_hom_nay_va_3_tuan.md).

## 6. Protocol đánh giá dự kiến

- Metric chính: Macro-F1; bổ sung Accuracy, Weighted-F1, Precision/Recall/F1 từng lớp và confusion matrix.
- Báo coverage, invalid output/backend error rate; lỗi vẫn được tính vào tổng số query đánh giá.
- LCR@k chỉ tính offline bằng nhãn query, dùng để phân tích retrieval; không đưa nhãn query vào selection.
- A0/A1/B/Balanced/C dùng cùng query IDs, taxonomy, LLM và representation. B/C dùng cùng candidate pool, embedding, k và prompt format.
- Chỉ chọn tham số trên development/validation; khóa model, prompt, split, k/N, reranking, budget và retry trước final test.
- Báo latency và token usage khi đo được. Chi phí C cho request mới phải tính cả prior, dù thực nghiệm có tái sử dụng cache A0.
- Ước lượng độ bất định của chênh lệch Macro-F1 bằng paired bootstrap theo query hoặc theo group khi có phụ thuộc; ghi rõ một seed nếu chỉ đủ ngân sách một seed.

Chưa có Macro-F1/Accuracy của LLM thật để điền vào report. Điểm trong mock hoặc điểm 0 của run toàn lỗi backend không phải kết quả đánh giá năng lực LLM.

## 7. Bố cục slide nháp và lời trình bày

| Slide | Nội dung đưa lên slide | Ghi chú nói |
| --- | --- | --- |
| 1. Bài toán và câu hỏi | HTTP request → nhãn attack; label-aware so với semantic-only; inference-only | “Nhóm kiểm chứng cách chọn ví dụ cho LLM, không huấn luyện model.” |
| 2. Động cơ | Hình cặp Normal/SQLi gần giống nhau; nhãn nguồn và khác biệt payload | “Ví dụ giải thích lý do nghiên cứu; chưa phải kết quả retrieval.” |
| 3. Phương pháp | A0/A1/B/Balanced/C và sơ đồ C | “Prior là dự đoán zero-shot, ground truth chỉ dùng đánh giá.” |
| 4. Dữ liệu | SR-BH 907.815 → 466.267; sáu lớp pilot; subset 3.000/200/600 | “Đã có split kỹ thuật; annotation benchmark còn cần chốt.” |
| 5. Tiến độ thật | Preprocessing/split/reproducibility; A0 mock; 28 test; API 403 | “Chưa có benchmark LLM thật; A1/B/C là phần tiếp theo.” |
| 6. Rủi ro và đánh giá | Annotation, leakage còn giới hạn, Macro-F1/per-class/cost | “Không dùng mock để kết luận hiệu quả phương pháp.” |
| 7. Kế hoạch ba tuần | 27/10 tích hợp → 03/11 khóa config → 10/11 bàn giao | Chỉ rõ TV1 dữ liệu/retrieval, TV2 LLM/đánh giá; cả hai viết và review |
| 8. Xin góp ý | Dataset/nhãn, phạm vi đối chứng, tiêu chí hoàn tất | Chốt quyết định trước khi chạy benchmark |

Hình đã có: [cặp request SR-BH](../surveys/figures/sr_bh_motivating_pair.png) và [phân bố nhãn](../surveys/figures/sr_bh_class_distribution.png). Bộ slide trên là nội dung nháp, chưa phải file trình chiếu đã xuất.

Lời mở đầu gợi ý: “Nhóm đã hoàn thành phần khảo sát và chuẩn bị dữ liệu, đồng thời dựng baseline zero-shot có kiểm thử. Hiện nhóm chưa có kết quả benchmark LLM thật do smoke API trả 403 và còn cần chốt chất lượng nhãn. Nhóm xin trình bày bằng chứng hiện có và kế hoạch ba tuần để hoàn thiện các đối chứng, phương pháp đề xuất và báo cáo kết quả.”

## 8. Các quyết định cần thầy góp ý ngày mai

1. Có đồng ý ưu tiên SR-BH theo nhãn nguồn, kèm audit và giới hạn rõ, hay yêu cầu đổi dataset/taxonomy trước benchmark? Nhóm đề xuất chốt trong 21–22/10 để giữ lịch ba tuần.
2. Phạm vi một LLM, một embedding, A0/A1/B/Balanced/C và ablation tối thiểu đã phù hợp chưa? Nhóm đề xuất bỏ thực nghiệm mở rộng trước nếu thiếu thời gian.
3. Có thống nhất các mốc review 27/10, 03/11 và bàn giao 10/11 không? Cần dành thời gian thầy phản hồi trước khi khóa protocol.

## 9. Checklist trước khi gửi

- [ ] Thay tên TV1/TV2, tên môn/đề tài và thông tin buổi báo cáo.
- [ ] Hai người kiểm tra từng số liệu và trạng thái API lần cuối; chỉ cập nhật bằng artifact mới.
- [ ] Chuyển nội dung tám slide sang công cụ trình chiếu và xuất PDF.
- [ ] Chuẩn bị hình, mock demo và bảng evidence chạy được tại máy; demo API chỉ khi đã kiểm chứng.
- [ ] Điền tối đa ba quyết định cần góp ý; thống nhất lời trình bày và người trả lời.
- [ ] Review chéo bản report/PDF, link và phiên bản cuối trước khi gửi.
