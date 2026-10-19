# Kế hoạch triển khai nghiên cứu trong 4 tuần cho 2 người

**Ngày lập:** 16/10/2026.  
**Giai đoạn triển khai chính:** 16/10–12/11/2026, gồm 4 tuần.  

## 1. Mục tiêu và hiện trạng

Trong 4 tuần, nhóm hoàn thành một nghiên cứu thực nghiệm có phạm vi vừa sức: dữ liệu đã xử lý, các baseline, Label-Aware Retrieval, kết quả so sánh, ablation và tài liệu tái lập.

Hiện repo giữ notebook EDA, danh mục papers, mô tả phương pháp và kế hoạch triển khai này. Dataset/taxonomy cuối cùng chưa được chốt; chưa có implementation các pipeline và kết quả benchmark. Sáu tuần bị lỡ cần được trao đổi thẳng thắn với giảng viên. Báo cáo mở đầu trình bày đúng các sản phẩm hiện có, hướng đã lựa chọn và kế hoạch mới; không quy đổi tài liệu thành kết quả thực nghiệm.

Đây là kế hoạch tiến độ khá gấp. Giả định mỗi người dành **20–25 giờ/tuần**, tổng khoảng **160–200 giờ công trong 4 tuần**, chưa tính thời gian máy chạy. Nhóm cần thống nhất khả năng này trong ngày đầu; nếu không đủ, giảm số cấu hình và thực nghiệm mở rộng ngay từ đầu.

## 2. Phạm vi ưu tiên

### Bắt buộc hoàn thành

- Một dataset HTTP request có nhãn; ưu tiên đánh giá tính phù hợp của SR-BH 2020/CAPEC trước khi tìm thêm dataset.
- Một taxonomy được chốt theo số mẫu độc lập và chất lượng annotation; dự kiến 4–6 lớp, không cố giữ lớp quá ít mẫu.
- Một pretrained embedding model và một LLM chính; inference-only, không train/fine-tune.
- **A0:** LLM zero-shot; **A1:** fixed few-shot; **B:** semantic top-k + LLM; **C:** label-aware reranking + LLM.
- Một đối chứng đơn giản: **class-balanced retrieval**, lấy candidates theo similarity nhưng phân bổ demonstrations theo lớp, để kiểm tra lợi ích có đến từ cân bằng nhãn đơn thuần hay không.
- Đánh giá Macro-F1 là metric chính; bổ sung Accuracy, per-class Precision/Recall/F1, confusion matrix, LCR@k, invalid output rate và chi phí inference.
- Ablation tối thiểu cho prior/reranking; kiểm tra leakage; lưu config, dự đoán, phiên bản model và scripts tạo bảng kết quả.

### Chỉ thực hiện khi phần bắt buộc đã ổn

LLM thứ hai, dataset thứ hai, BM25, robustness với obfuscation, nhiều embedding models và quét tham số lớn. Không làm UI, WAF real-time hoặc thu thập lưu lượng trực tiếp trong giai đoạn này.

## 3. Phân công và cách phối hợp

Tạm gọi hai thành viên là **TV1** và **TV2**; thay bằng tên thật khi nhóm thống nhất.

| Mảng | Người phụ trách chính | Người review |
| --- | --- | --- |
| Dataset, preprocessing, deduplication, split | TV1 | TV2 |
| Embedding, FAISS, semantic retrieval, reranker | TV1 | TV2 |
| LLM client, prompt, parser, cache, experiment runner | TV2 | TV1 |
| Metrics, bảng kết quả, ablation và statistical analysis | TV2 | TV1 |
| Tài liệu dữ liệu, phương pháp và triển khai | TV1 | TV2 |
| Tổng hợp nghiên cứu liên quan và kết quả | TV2 | TV1 |
| Literature verification, phân tích lỗi, báo cáo tiến độ | Cả hai | Review chéo |

- Mỗi ngày dành 10–15 phút cập nhật: đã xong gì, đang vướng gì, việc tiếp theo. Vướng quá một buổi phải báo nhau.
- Chia task thành phần việc 2–6 giờ, có người phụ trách, deadline và tiêu chí hoàn thành. Tránh task chung chung như “làm RAG”.
- Tích hợp code ít nhất hai lần/tuần. TV2 dùng fixture nhỏ để phát triển LLM/metrics trong lúc TV1 xử lý dữ liệu.
- Ngày 18/10 chốt interface chung: `request_id`, `request_text`, `label`; prediction có `predicted_label`, `status`, `latency`, token usage nếu backend cung cấp; retrieval log có candidate IDs, labels, scores và prior.
- Chỉ một người phụ trách mỗi file/module tại một thời điểm. Người còn lại chạy kiểm tra và review trước khi dùng cho benchmark.
- Cập nhật tài liệu từ tuần 1; mọi số liệu phải truy được về file kết quả và config.

## 4. Báo cáo mở đầu tuần này: 16–18/10

**Mục tiêu buổi gặp:** nối lại nhịp hướng dẫn, thống nhất câu hỏi nghiên cứu và phạm vi tối thiểu, xin góp ý kế hoạch triển khai. Đây là buổi xác lập lại kế hoạch; sau đó nhóm gửi báo cáo tiến độ hằng tuần.

Chuẩn bị một bộ 5–6 slide và bản tóm tắt 1–2 trang theo [khung báo cáo mở đầu](../progress/bao_cao_dinh_huong_va_mau_hang_tuan.md). Trước buổi gặp, hai người cùng review để thống nhất cách giải thích prior, retrieval và giới hạn nghiên cứu.

| Người | Việc trước buổi gặp | Sản phẩm |
| --- | --- | --- |
| TV1 | Tóm tắt EDA đã có, các vấn đề duplicate/annotation, đề xuất taxonomy | Một bảng dữ liệu và danh sách quyết định cần chốt |
| TV2 | Tóm tắt RQ, sơ đồ A/B/C, phương pháp đánh giá và lịch triển khai | Sơ đồ pipeline và timeline |
| Cả hai | Kiểm tra các công trình gần nhất, trình bày giới hạn của novelty claim | Bảng đối sánh ngắn, không khẳng định “đầu tiên” khi chưa đủ bằng chứng |

Các điểm cần xin ý kiến thầy: hướng inference-only có phù hợp không; phạm vi dataset/nhãn; đối chứng và kết quả thực nghiệm tối thiểu; lịch báo cáo và các quyết định kỹ thuật cần chốt.

## 5. Kế hoạch chi tiết 4 tuần

### Tuần 1 — 16–22/10: Chốt protocol, dữ liệu và chạy được baseline đầu tiên

| Người | Nhiệm vụ | Sản phẩm cuối tuần |
| --- | --- | --- |
| TV1 | Xác nhận nguồn và quyền sử dụng dataset; kiểm tra schema, annotation; chuẩn hóa request; exact/near-duplicate audit; xây split theo nhóm request tương tự | Dataset selection note, script preprocessing/split, bảng class distribution và leakage audit |
| TV2 | Setup dependency versions; xây LLM client, retry/cache, prompt và parser; chạy A0 trên mẫu nhỏ; dựng metrics | Lệnh chạy A0, prediction log và bảng lỗi parser |
| Cả hai | Chốt RQ, taxonomy, model/backend sau smoke test, protocol và interface; xác minh các related work gần nhất | Protocol v1 và bảng related work có nguồn |

**Mốc nội bộ:** 18/10 chốt interface và thử gọi model; 20/10 quyết định dataset/taxonomy; 22/10 khóa split v1 và demo A0 trên 50–100 mẫu thuộc development/validation set.

**Điều kiện hoàn thành:** có thể dựng môi trường và chạy A0 từ hướng dẫn; split có seed/hash; không có exact request overlap giữa các tập; near-duplicate audit có báo cáo và cách xử lý. Tập test được giữ riêng sau khi khóa split.

**Báo cáo thầy ngày 22/10:** dataset và lý do chọn, số mẫu trước/sau xử lý, protocol, demo baseline, khả năng chạy model và rủi ro còn lại. Số liệu pilot phải ghi rõ là validation, chưa phải final test results.

### Tuần 2 — 23–29/10: Hoàn thiện baselines và triển khai Pipeline C

| Người | Nhiệm vụ | Sản phẩm cuối tuần |
| --- | --- | --- |
| TV1 | Xây embedding/index, Pipeline B, class-balanced retrieval; implement reranker đơn giản với similarity và prior match | Các retrieval modules, logs top-N/top-k, config reranking |
| TV2 | Hoàn thiện A1, experiment runner, cache prior từ A0; kết nối C; xuất classification/retrieval metrics và cost logs | Chạy A0/A1/B/C trên cùng validation subset, bảng so sánh sơ bộ |
| Cả hai | Kiểm tra prior sai ảnh hưởng thế nào; chọn một số request đại diện để đọc lỗi; ghi lại dữ liệu, thiết lập thực nghiệm và phương pháp | Tài liệu phương pháp và phân tích pilot |

**Mốc nội bộ:** 25/10 B chạy end-to-end; 27/10 C chạy end-to-end; 29/10 hoàn thành pilot khoảng 100–200 validation requests nếu dữ liệu cho phép.

**Điều kiện hoàn thành:** A/B/C dùng cùng request representation, taxonomy và LLM; B/C có cùng candidate pool và số demonstrations khi so sánh chính; prior không sử dụng ground truth. Có thể truy lại từng prediction và prompt/config đã dùng.

**Báo cáo thầy ngày 29/10:** bảng pilot, ví dụ thành công/thất bại, LCR@k đi kèm Macro-F1, chi phí thêm của prior, phần Method v1. Xin góp ý trước khi khóa cấu hình.

### Tuần 3 — 30/10–05/11: Chọn cấu hình trên validation và khóa protocol

| Người | Nhiệm vụ | Sản phẩm cuối tuần |
| --- | --- | --- |
| TV1 | Thử một grid nhỏ cho k và trọng số prior; kiểm tra contrastive/diversity chỉ nếu còn thời gian; chuẩn bị config cuối | Validation results, config đã chọn, ghi nhận các cấu hình đã thử |
| TV2 | Chạy ablation trên validation, đo latency/token và estimate runtime cho final test; hoàn thiện scripts tạo bảng/hình | Ablation table, cost estimate và kế hoạch final run |
| Cả hai | Review leakage lần cuối; kiểm tra claim nghiên cứu; hoàn thiện tài liệu phương pháp và thiết lập; chốt có cần giảm phạm vi | Protocol v2 khóa ngày 05/11 và hướng dẫn thực nghiệm |

**Điều kiện hoàn thành:** chọn cấu hình chỉ trên validation; khóa model, prompt, request truncation, taxonomy, k/N, trọng số và split trước final test. Có quyết định rõ về test size và uncertainty analysis.

**Báo cáo thầy ngày 05/11:** tác động từng thành phần trên validation, hướng kết quả, cấu hình cuối, thời gian chạy test và tài liệu thực nghiệm. Nếu C không hơn B, báo trung thực và thống nhất phân tích failure modes, không mở rộng grid vô hạn.

### Tuần 4 — 06–12/11: Final benchmark và chốt kết quả nghiên cứu chính

| Người | Nhiệm vụ | Sản phẩm cuối tuần |
| --- | --- | --- |
| TV1 | Chạy và giám sát final benchmark với config đã khóa; audit retrieval logs, per-class errors và prior failure cases | Raw predictions đầy đủ, manifest/config và case studies |
| TV2 | Tổng hợp metrics, paired uncertainty analysis, ablation và cost; tạo bảng/hình; ghi nhận phân tích và giới hạn | Bộ bảng/hình và báo cáo kết quả |
| Cả hai | Review chéo kết quả; chạy lại một cấu hình từ hướng dẫn; đối chiếu claim với bằng chứng | Gói kết quả v1 và hướng dẫn tái lập ngày 12/11 |

**Điều kiện hoàn thành:** có kết quả final test cho A0/A1/B/C và class-balanced baseline, ablation tối thiểu, phân tích chi phí và giới hạn. Nếu thiếu kết quả, ghi rõ phần thiếu và ngày bù; không thay bằng số ước lượng.

**Báo cáo thầy ngày 12/11:** kết luận theo từng RQ, kết quả tốt/xấu, mức độ chắc chắn, giới hạn và thực nghiệm cần bổ sung.

## 6. Protocol thực nghiệm tối thiểu

### Dữ liệu và chống leakage

- Định nghĩa `request_text` từ các trường HTTP có sẵn, tránh đưa label, response hoặc metadata tiết lộ đáp án vào input. Ghi rõ chính sách giữ/cắt headers và body.
- Không tự động URL-decode hoặc xóa nội dung có thể làm mất tín hiệu tấn công mà chưa kiểm tra tác động. Lưu bản gốc và quy tắc normalization.
- Group các request trùng/gần trùng trước khi split; không chỉ random split theo row. Audit thêm theo endpoint/template và thời gian nếu metadata cho phép.
- Mục tiêu ban đầu: retrieval pool/validation/test khoảng **70/15/15 theo nhóm**; điều chỉnh nếu class support không đủ, ghi lại tỷ lệ thực tế. Retrieval pool không dùng để train model.
- Kiểm tra annotation trên mẫu nhỏ của mỗi lớp và các trường hợp mâu thuẫn. Không kết luận cùng URL khác label là annotation noise nếu chưa xét method, headers và body.
- Nếu có ambiguous/multi-label rows, chốt chính sách xử lý trước benchmark. Hard cases được định nghĩa trước, tránh chỉ chọn ví dụ có lợi cho C sau khi xem kết quả.

### Ngân sách và tính công bằng

- Sau pilot tuần 1, đo thời gian và token/request để chốt ngân sách. Ước tính: `số queries × số cấu hình × số lần lặp`, cộng chi phí tạo prior chưa cache.
- Mục tiêu vận hành ban đầu: retrieval pool 2.000–5.000 mẫu, validation 200–300 mẫu, final test 500–1.000 mẫu nếu class support và compute cho phép. Đây là ngân sách dự kiến, không bảo đảm đủ statistical power; ghi rõ cách lấy mẫu và phân bố lớp thực tế.
- Nếu cần subset, chọn một lần bằng seed cố định trước khi chạy, dùng cùng query IDs cho mọi phương pháp; không cherry-pick mẫu. Báo cáo class distribution và giới hạn đại diện của subset.
- B và C dùng cùng embedding, top-N candidates, k, LLM và format prompt; ghi token usage thực tế vì cùng k không đồng nghĩa cùng độ dài prompt.
- Cache zero-shot prediction có thể giảm chi phí khi chạy nghiên cứu. Khi báo latency/cost của C, vẫn cộng bước prior cho request mới; tách cold run và cached run.
- Log invalid output và lỗi backend; áp dụng cùng retry/fallback policy. Báo coverage và cách tính lỗi, không âm thầm loại các prediction thất bại.

### Metrics và ablation

- **Metric chính:** Macro-F1. Bổ sung Accuracy, per-class Precision/Recall/F1, confusion matrix và false-positive rate trên lớp Normal khi phù hợp.
- **LCR@k:** tỷ lệ retrieved demonstrations trùng ground-truth query label, chỉ tính offline. Không dùng metric này làm bằng chứng duy nhất: demonstrations khác lớp vẫn có thể hữu ích cho ICL.
- **Ablation tối thiểu:** similarity-only (B), similarity + prior match (C); nếu C có diversity/contrastive component thì thêm cấu hình tắt thành phần đó.
- Để ablation “không prior” không chỉ lặp lại B, ghi rõ thành phần nào vẫn còn. Giới hạn cấu hình bổ sung; thí nghiệm k/trọng số trên validation.
- Dùng paired bootstrap theo cùng query IDs để ước lượng 95% confidence interval của chênh lệch Macro-F1; nếu queries còn phụ thuộc theo nhóm/template, bootstrap theo nhóm và nêu giới hạn.
- Mục tiêu 3 seed cho lấy mẫu pool/demonstrations nếu ngân sách cho phép; nếu chỉ có một seed thì báo rõ. Temperature 0 hỗ trợ giảm biến động, không bảo đảm tuyệt đối deterministic.
- Không so trực tiếp số liệu literature khác dataset/split như một đối chứng công bằng. Không khẳng định novelty hoặc hiệu quả trước khi kiểm chứng.

## 7. Nhịp báo cáo và xử lý khi chậm

**Lịch đề xuất:** buổi định hướng 16–18/10; sau đó báo cáo vào 22/10, 29/10, 05/11 và 12/11. Giờ gặp cụ thể thống nhất với thầy. Nếu chưa xếp được lịch gặp, nhóm vẫn gửi bản báo cáo đúng ngày.

Mỗi tuần gửi một trang trước buổi gặp khoảng 24 giờ: mục tiêu, sản phẩm có link/commit, kết quả có config, việc chưa đạt và nguyên nhân, quyết định cần thầy góp ý, kế hoạch tuần sau chia theo người. Khi gặp dành khoảng 10 phút trình bày và 10 phút trao đổi; gửi lại action items sau buổi gặp.

| Rủi ro hoặc mốc không đạt | Cách xử lý |
| --- | --- |
| Chưa chốt dataset vào 20/10 | Chốt tiêu chí loại/chọn với thầy, giới hạn thời gian khảo sát; thu hẹp số lớp dựa trên support/chất lượng thay vì tiếp tục tìm không giới hạn |
| Annotation mâu thuẫn hoặc class thiếu mẫu độc lập | Xử lý ambiguous rows theo protocol, giảm taxonomy nếu hợp lý; ghi rõ giới hạn |
| Model chạy quá chậm hoặc API không ổn định | Sau smoke test chọn một backend chính và phương án dự phòng; giảm số cấu hình trước khi giảm chất lượng split/đánh giá; không đổi model giữa benchmark mà không chạy lại đối chứng |
| Cuối tuần 2 C chưa chạy được | Ưu tiên reranker similarity + prior match; dừng diversity/contrastive và mọi phần mở rộng |
| C không cải thiện trên validation | Kiểm tra prior và retrieval logs trong thời gian giới hạn; báo kết quả âm, phân tích điều kiện hữu ích/thất bại; xin thầy góp ý hướng thực nghiệm |
| Bị chậm từ 2 ngày trở lên | Bỏ LLM/dataset thứ hai, giảm parameter grid; giữ leakage checks, baseline B, ablation và thời gian thầy review |
| Kết quả chưa đủ vào 12/11 | Cùng thầy xác định thực nghiệm cần bổ sung và thu hẹp kết luận theo bằng chứng |

## 8. Checklist bắt đầu trong 48 giờ

- [ ] Chốt TV1/TV2, quỹ giờ mỗi tuần và lịch làm việc chung.
- [ ] Chuẩn bị báo cáo định hướng và gửi lịch xin gặp thầy.
- [ ] Xác nhận file dataset, nguồn, schema và khả năng sử dụng.
- [ ] Thử LLM trên 20–50 request development; đo latency và kiểm tra output format.
- [ ] Chốt interface module và mở task cho tuần 1.
- [ ] Chốt buổi báo cáo tiếp theo ngày 22/10 hoặc ngày phù hợp với thầy.

Kế hoạch này là lịch thực thi chính từ 16/10/2026. Theo dõi sản phẩm và tiêu chí hoàn thành mỗi tuần; không dùng các tỷ lệ hoàn thành trong kế hoạch cũ để suy ra tiến độ hiện tại.
