# Phân công hôm nay và kế hoạch hoàn thiện trong ba tuần

Ngày lập: 19/10/2026. Báo cáo ngày mai: 20/10/2026. Giai đoạn ba tuần sau báo cáo: **21/10–10/11/2026**. TV1/TV2 là tên tạm để thay bằng tên hai thành viên.

Đây là kế hoạch ưu tiên hiện tại, thay lịch thực thi trong bản bốn tuần ngày 16/10; bản cũ giữ làm lịch sử. Mục tiêu hoàn thiện toàn bộ phạm vi nghiên cứu tối thiểu: code A0/A1/B/Balanced/C, dữ liệu/protocol đã chốt, validation, ablation, final benchmark, phân tích, report, slide và gói tái lập. Phần mở rộng như dataset/LLM thứ hai và hệ thống WAF không thuộc đợt ba tuần này.

## 1. Điểm xuất phát và phân vai

Đã có preprocessing/split SR-BH, khảo sát SR-BH/CSIC và A0 mock end-to-end. Chưa có A1/B/C/Balanced hoặc benchmark LLM. Smoke API hiện lưu một lỗi HTTP 403; dataset benchmark chưa chốt vì annotation cần review. Không làm lại phần đã có.

| Người | Trách nhiệm chính | Trách nhiệm tài liệu |
| --- | --- | --- |
| TV1 | Dataset, taxonomy, audit, embedding/index, B, Balanced, reranker C | Dữ liệu, phương pháp retrieval, case studies |
| TV2 | API/client, A0/A1, runner tích hợp, cache prior, metrics, thực nghiệm và cost | Thiết lập thực nghiệm, kết quả, related work, tổng hợp report/slide |
| Cả hai | Chốt protocol, review annotation độc lập, tích hợp, review kết quả và diễn tập | Review chéo toàn bộ báo cáo |

Giả định **20–25 giờ/người/tuần**, tương đương 120–150 giờ công trong ba tuần; thời gian máy chạy tính riêng. Mỗi ngày cập nhật 10–15 phút; task có đầu ra, người phụ trách và hạn. Nếu thiếu quỹ giờ, giảm thực nghiệm mở rộng ngay khi chốt lịch.

## 2. Chia việc hôm nay 19/10 — hoàn tất bộ tài liệu cho ngày mai

Mỗi người dự kiến 5–6 giờ. Các mốc dưới đây tính từ lúc hai người bắt đầu làm; ưu tiên hoàn tất trước khi nghỉ tối, không phải chờ pipeline mới triển khai xong.

| Chặng / thời lượng | TV1 | TV2 | Đầu ra chung |
| --- | --- | --- | --- |
| 0–30 phút | Đọc bản nháp; xác nhận số liệu dataset/split | Đọc bản nháp; xác nhận A0/API và kế hoạch | Chốt vai trò, bố cục và nơi ghép tài liệu |
| 30 phút–2 giờ | Hoàn thiện phần dữ liệu: schema, sáu lớp pilot, preprocessing, split, annotation và leakage; chọn hai hình sẵn có | Hoàn thiện RQ, sơ đồ A0/A1/B/C, metrics và trạng thái implementation; kiểm tra log API 403 | Nội dung report có evidence; không có số liệu dự kiến trong bảng kết quả |
| 2–3,5 giờ | Làm slide 2, 4 và phần dữ liệu của slide 6; viết ghi chú giải thích cặp request | Làm slide 1, 3, 5, 7, 8; ghép lịch ba tuần; đối chiếu các paper đã lưu để viết related work ngắn | Bản slide lần 1, bảng phân công và 3 câu hỏi cho thầy |
| 3,5–4,5 giờ | Review số liệu và phần phương pháp TV2 viết; chuẩn bị hình/mock demo | Review phần dữ liệu TV1 viết; ghép report và đồng nhất thuật ngữ | Bản report và slide cùng một trạng thái tiến độ |
| 4,5–5,5 giờ | Diễn tập phần dữ liệu/phương pháp, ghi câu hỏi dễ bị hỏi | Diễn tập phần mục tiêu/tiến độ/kế hoạch; xuất PDF và kiểm tra hiển thị | Report, slide PDF, ghi chú nói và phụ lục evidence |
| 5,5–6 giờ nếu cần | Sửa lỗi nội dung và soát lần cuối | Sửa bố cục/link, đóng phiên bản bàn giao | Bộ tài liệu sẵn sàng gửi ngày mai |

TV2 có thể dành tối đa 30–45 phút trong chặng kiểm tra kỹ thuật để xác định nguyên nhân 403. Chỉ thử API lại nếu đã có cấu hình/quyền hợp lệ và ngân sách; không để việc này chặn hoàn thiện report. Nếu chưa xử lý được, giữ nguyên trạng thái lỗi và trình bày phương án giải quyết tuần 1. Không cần thêm benchmark tối nay để có một báo cáo tiến độ hợp lệ.

**Điều kiện xong hôm nay:** bản report đã review; nội dung tám slide đã chuyển thành file trình chiếu/PDF; có hình và evidence; có lịch chia người ba tuần; diễn tập ít nhất một lượt và thống nhất ba quyết định cần xin ý kiến. [Bản nháp báo cáo](../progress/ban_nhap_bao_cao_2026_10_20.md) đã cung cấp phần nội dung để ghép; file slide/PDF là sản phẩm hai thành viên còn phải xuất.

## 3. Ngày báo cáo 20/10

TV1 trả lời dữ liệu, taxonomy, annotation và leakage; TV2 trả lời LLM, đánh giá và tiến độ. Sau buổi gặp, hai người dành 30–60 phút ghi quyết định của thầy, cập nhật phạm vi và lịch. Nếu chưa có quyết định dataset, tiếp tục phát triển module bằng fixture/development; chưa khóa benchmark theo một phương án chưa được thống nhất.

## 4. Tuần 1 — 21–27/10: Chốt đầu vào và tích hợp các pipeline

| Hạn | TV1 | TV2 | Điều kiện hoàn thành |
| --- | --- | --- | --- |
| 21–22/10 | Review độc lập cùng 60 mẫu development/pool với TV2; tổng hợp bất đồng, kiểm tra nhóm trùng; đề xuất dataset/taxonomy | Cùng review nhãn; xử lý lỗi 403, kiểm tra model/context; smoke nhỏ có status/latency/usage thật nếu backend hoạt động | Có quyết định dữ liệu bằng văn bản; API có prediction hợp lệ hoặc blocker và backend dự phòng cụ thể |
| 23–24/10 | Tạo embedding/index cho pool; top-N/top-k có log ID/label/score; xây B và Balanced | Hoàn thiện A1 với demonstrations cố định từ pool; mở rộng runner cho validation và nhiều pipeline; giữ manifest/resume/error handling | A0/A1/B chạy được trên development; Balanced có quy tắc phân bổ xác định |
| 25–26/10 | Implement C tối thiểu: similarity + prior-label match; kiểm tra trọng số bằng 0 trả về thứ tự B | Cache/tái sử dụng prior A0, tích hợp C và xuất metrics/retrieval logs; pilot cùng 30–60 validation queries | A0/A1/B/Balanced/C chạy cùng IDs; C không đọc ground truth để rerank |
| 27/10 | Review retrieval logs và minh họa trường hợp chọn ví dụ | Tổng hợp pilot, error rate, runtime/token và dự toán lần chạy chính | Demo end-to-end, bảng pilot ghi rõ validation và báo cáo tuần 1 |

Phân bổ dự kiến: TV1 5 giờ dữ liệu/audit + 8 giờ retrieval + 5 giờ reranker + 3–5 giờ tích hợp/tài liệu; TV2 5 giờ API + 6 giờ A1/runner + 6 giờ tích hợp/metrics + 4–6 giờ pilot/tài liệu.

**Phụ thuộc cần xử lý:** runner API hiện chỉ cho development tối đa 10 mẫu mỗi lệnh. Chạy validation/test cần task mở rộng runner có cấu hình split/budget, kiểm tra và manifest riêng; không chỉ đổi đường dẫn hoặc bỏ chốt chặn. Smoke giai đoạn đầu giữ giới hạn hiện tại, các batch lớn chỉ bắt đầu sau khi chốt protocol và ngân sách. Pool 3.000 có thể dùng cosine search trực tiếp nếu phù hợp; FAISS không phải điều kiện bắt buộc để đạt mốc tích hợp.

## 5. Tuần 2 — 28/10–03/11: Validation, ablation và khóa protocol

| Hạn | TV1 | TV2 | Điều kiện hoàn thành |
| --- | --- | --- | --- |
| 28–29/10 | Chốt reranking đơn giản; kiểm tra candidate pool, thứ tự demonstrations và logging | Chạy A0/A1/B/Balanced trên cùng validation subset; bổ sung LCR@k offline | Baseline table có query IDs/model/config và đầy đủ mẫu lỗi |
| 30–31/10 | Thử grid nhỏ cho C, phân tích prior đúng/sai và cases B/C khác nhau | Chạy C, ablation và tổng hợp Macro-F1/per-class/cost; lưu mọi cấu hình đã thử | Chọn config từ validation, không dựa vào test |
| 01–02/11 | Kiểm tra leakage/nhãn lần cuối; viết Method và Dataset | Viết Experimental Setup/Results validation; ước lượng ngân sách test; xây bảng/hình và uncertainty analysis | Report bản đầu có phương pháp và kết quả validation truy vết được |
| 03/11 | Review và ký nhận config cuối với TV2 | Khóa protocol/config, ghi hash, chuẩn bị lệnh và output directory final run | Model/prompt/split/k/N/trọng số/retry/budget đã khóa; báo cáo tuần 2 |

Phân bổ dự kiến: TV1 6 giờ reranker/ablation + 6 giờ audit/phân tích + 8–11 giờ viết/tích hợp; TV2 9 giờ thực nghiệm + 5 giờ metrics/chi phí + 6–11 giờ viết/khóa cấu hình.

Grid khởi điểm để dự toán, chưa phải cấu hình đã chốt: k ∈ {4, 6}, N=30, trọng số prior ∈ {0, 0,25, 0,5}. Chuẩn hóa similarity theo quy tắc công bố trước khi cộng prior; cấu hình trọng số 0 là B nên tái sử dụng kết quả khi thiết lập trùng nhau. Chỉ thử grid nếu số lớp và context model cho phép; có thể giảm còn một k và hai trọng số dương. Balanced định nghĩa trước cách chia quota nếu k không chia hết cho số lớp hoặc có lớp thiếu candidates, dùng cùng k với B/C.

Ablation tối thiểu so sánh B (similarity-only), C (similarity + prior) và Balanced. Nếu bổ sung diversity/contrastive thì cần thêm cấu hình tắt từng thành phần; mặc định chưa thêm trong lịch ba tuần. C không hơn B vẫn là kết quả có thể báo cáo; phân tích ảnh hưởng prior sai thay vì kéo dài tuning.

## 6. Tuần 3 — 04–10/11: Final benchmark và bàn giao toàn bộ

| Hạn | TV1 | TV2 | Điều kiện hoàn thành |
| --- | --- | --- | --- |
| 04–06/11 | Giám sát retrieval và dữ liệu final run, kiểm tra lỗi vận hành; bắt đầu phân tích case theo tiêu chí đã định nghĩa | Điều phối final run A0/A1/B/Balanced/C với config khóa; theo dõi quota và prediction coverage | Predictions/manifest đầy đủ trên cùng test IDs; lỗi không bị bỏ khỏi kết quả |
| 07–08/11 | Viết phân tích per-class, prior failure, request dễ nhầm và giới hạn | Tạo bảng/hình final, paired uncertainty analysis và cost; hoàn thiện Results/Discussion | Report đầy đủ kết quả và kết luận theo bằng chứng |
| 09/11 | Kiểm tra hướng dẫn dựng môi trường, tái lập metrics từ prediction; review Results | Ghép report/slide/phụ lục, review Method/Dataset và kiểm tra trích dẫn | Gói bàn giao chạy lại được; không cần gọi lại API để tái tạo bảng |
| 10/11 | Review cuối, diễn tập, kiểm tra tài liệu dữ liệu và source linkage | Review cuối, xuất report/slide PDF, đóng danh mục sản phẩm và giới hạn | Bộ code/config/results/report/slides sẵn sàng bàn giao |

Phân bổ dự kiến: TV1 6 giờ giám sát/audit + 7 giờ phân tích + 7–12 giờ tài liệu/review; TV2 6 giờ vận hành + 7 giờ tổng hợp + 7–12 giờ report/slide/review.

Final test dự kiến 600 mẫu đã tạo, chỉ dùng sau khi khóa protocol. Nếu ngân sách buộc giảm, chốt subset/seed trước khi mở kết quả test và dùng chung cho mọi phương pháp. Không điều chỉnh prompt hoặc trọng số sau khi đọc test rồi tiếp tục gọi đó là final test độc lập. Sửa lỗi code ảnh hưởng dự đoán phải ghi phiên bản mới và đánh giá lại các phương pháp bị ảnh hưởng; báo rõ việc test đã được quan sát.

## 7. Ngân sách thực nghiệm và các mốc quyết định

Với 200 validation và 600 test, một vòng so sánh năm phương pháp cần khoảng **1.000 + 3.000 = 4.000 lượt inference LLM**, chưa tính development, tuning và retry. Ước lượng giả định mỗi phương pháp một lượt/query và C tái sử dụng prior từ A0; nếu gọi prior riêng sẽ phát sinh thêm. Mỗi cấu hình C mới trên toàn validation cộng khoảng 200 lượt final inference nếu prior đã cache.

Sau smoke thành công, TV2 đo token và thời gian thực để quy đổi ngân sách, không dùng latency mock. Tổng runtime/quota phải gồm context của demonstrations, giới hạn tốc độ, lỗi/retry và thời gian index. Không chốt giá tiền từ số lượt gọi khi chưa có token/đơn giá được xác minh.

| Mốc kiểm tra | Nếu chưa đạt | Xử lý để giữ tiến độ |
| --- | --- | --- |
| 22/10: chốt dataset và API hoạt động | Annotation chưa rõ hoặc API vẫn 403 | Chốt với thầy phương án nhãn nguồn có giới hạn hoặc đổi phạm vi; chọn backend dự phòng sau kiểm tra; phát triển code bằng fixture trong lúc chờ |
| 24/10: B chạy được | Embedding/index hoặc tích hợp chậm | Ưu tiên cosine top-k đơn giản, giảm tối ưu hóa hạ tầng |
| 27/10: C end-to-end | Reranker phức tạp chưa xong | Chỉ giữ similarity + prior match; bỏ diversity/contrastive |
| 31/10: kết quả chưa ổn định | API chậm hoặc grid tốn quota | Giảm grid/lặp, giữ baseline và cùng query IDs; không chọn các mẫu có lợi cho C |
| 03/11: chưa khóa được protocol | Còn bất đồng hoặc phụ thuộc chưa giải quyết | Báo ngay phạm vi/tiến độ mới với thầy; không dùng test để giải quyết tuning |
| 06/11: final run chưa đủ | Quota/lỗi vận hành | Dùng thời gian dự phòng 07–08/11, ghi coverage và hạn chế; nếu vẫn thiếu phải công bố thiếu kết quả |

Lịch ba tuần khả thi khi dataset và backend được giải quyết sớm; không cam kết có kết quả thực nghiệm hợp lệ nếu các phụ thuộc này vẫn chưa được xử lý.

## 8. Tiêu chí hoàn thiện toàn bộ vào 10/11

- [ ] Có quyết định dataset/taxonomy và chính sách annotation; lưu kết quả review của hai người, không chỉ assessment Codex.
- [ ] Có split/config/version/hash, kiểm tra leakage và công bố giới hạn endpoint/near-duplicate.
- [ ] A0/A1/B/Balanced/C chạy cùng interface; prediction lỗi, retry/cache và retrieval logs truy vết được.
- [ ] Có validation, config khóa và final predictions trên cùng query IDs; không trộn mock vào benchmark.
- [ ] Có bảng Macro-F1/Accuracy/per-class, confusion matrix, LCR@k khi áp dụng, coverage/error rate và latency/token đo được.
- [ ] Có ablation tối thiểu, phân tích prior sai, chi phí C gồm prior và độ bất định của so sánh.
- [ ] Có script tái tạo bảng/hình từ predictions; hướng dẫn cài đặt/lệnh chạy và dependency/config cần thiết.
- [ ] Report có Introduction, Related Work, Method, Dataset/Protocol, Experiments, Results/Discussion, Limitations và Conclusion; trích dẫn đã đối chiếu nguồn.
- [ ] Slide và PDF đã review/diễn tập; mỗi số liệu truy về artifact; mọi phần chưa đạt được ghi rõ.

## 9. Lịch báo cáo và bàn giao giữa hai người

Ngày 27/10 báo cáo dữ liệu/protocol và pilot A0/A1/B/Balanced/C; ngày 03/11 báo cáo validation/ablation và cấu hình khóa; ngày 10/11 bàn giao final benchmark, report và slide. Đây là lịch nội bộ đề xuất, giờ gặp thầy theo lịch xác nhận.

Mỗi task bàn giao kèm: file/module, config và lệnh chạy, artifact kết quả, tiêu chí đã đạt và phần còn vướng. TV1 review phần LLM/metrics; TV2 review phần dữ liệu/retrieval. Chỉ một người chỉnh mỗi module tại một thời điểm; hai người dành ít nhất 30 phút tích hợp ở mỗi mốc chính.
