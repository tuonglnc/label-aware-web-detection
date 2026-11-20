# Chương 4. Thực nghiệm

> Dàn ý theo bản nháp báo cáo cuối kỳ (`reports/final/Bao_cao_cuoi_ky_LabelAware.docx`). Mỗi mục gồm: câu hỏi mà mục trả lời, kết quả quan sát, diễn giải, số liệu và nguồn, chỗ cần sửa. Ghi nhận xét vào "Chỉnh sửa" rồi sửa trong file Word.

## Nguyên tắc viết chương này

1. **Chương 4 trả lời "dữ liệu cho thấy gì?"**, không lặp lại phương pháp (Chương 3) và không kết luận chung (Chương 5).
2. **Mỗi mục đi theo một câu hỏi nghiên cứu (RQ).** Mục nào không phục vụ RQ nào thì ghi rõ là mục kiểm chứng (độ tin cậy, chi phí).
3. **Tách hai lớp trong mỗi mục:** *Kết quả* (con số quan sát được từ dữ liệu) và *Diễn giải* (vì sao, so với nghiên cứu trước, ý nghĩa). Không viết bảng số mà thiếu câu "điều này liên quan gì đến RQ".
4. **Không khẳng định quá dữ liệu.** Chỗ nào p không có ý nghĩa thống kê thì viết "không phân biệt được", không viết "tốt hơn".
5. **Mọi số trong chương phải truy được về file nguồn** (cột "Nguồn") để người khác tái lập được.

### Mạch lập luận của cả báo cáo (kiểm tra trước khi nộp)

Đã đối chiếu với `workspace/Katun.md` (bản trên `main`, PR #8, 07/11/2026).

| Chương | Câu hỏi nó trả lời | Chương 4 phải cung cấp |
|---|---|---|
| 1. Giới thiệu tổng quan | Vấn đề gì? Khoảng trống: request gần nhau chưa chắc cùng nhãn; ba RQ | Bằng chứng cho khoảng trống (4.3) và số liệu trả lời RQ1–RQ3 |
| 2. Cơ sở lý thuyết | Kiến thức nào giải thích vấn đề? Đã định nghĩa Macro-F1, FPR Normal, LCR@k, bootstrap, McNemar (mục 2.5) | Không cần định nghĩa lại |
| 3. Thiết kế hệ thống và phương pháp | Dữ liệu, tiền xử lý, top-30, prior, các cấu hình kNN/A0/A1/B/BAL/C-kNN/C-LLM/C-oracle, prompt, công thức reranking | Bằng chứng các cấu hình đó chạy đúng như thiết kế (4.4) |
| 4. Thực nghiệm và đánh giá | Dữ liệu cho thấy gì? | Chính chương này |
| 5. Kết luận và hướng phát triển | Trả lời RQ1–RQ3, giới hạn, hướng phát triển | Số liệu để mỗi câu trả lời có dẫn chứng |

> **Ba RQ chính thức (Chương 1, mục 1.2.4).** Phải dùng đúng nghĩa này trong cả Chương 4.
> - **RQ1:** tỷ lệ ví dụ gần nhất nhưng khác nhãn nguồn với query là bao nhiêu, phân bố giữa các lớp ra sao.
> - **RQ2:** xếp hạng lại bằng prior có cải thiện Macro-F1 và giảm FPR Normal so với truy xuất theo similarity (B) và luân phiên theo lớp (BAL) không; chi phí thay đổi thế nào.
> - **RQ3:** prior đúng và prior sai ảnh hưởng thế nào đến số lỗi sửa được, số lỗi mới phát sinh, kết quả theo lớp; C-oracle còn gặp hạn chế gì.

### Bảng liên kết RQ → mục → bằng chứng

| RQ | Mục trả lời | Bằng chứng chính |
|---|---|---|
| RQ1 | 4.3 | LCR 23–24%; Normal 45,5%, SQLi 39,4% |
| RQ2 (C có hơn B, BAL không; chi phí) | 4.4, 4.9; mở rộng ở 4.5, 4.6, 4.7 | Test 1–300: B 0,881; BAL 0,865; C-kNN 0,862; C-LLM 0,861. FPR Normal: B 30%, BAL 28%, C-kNN 32%, C-LLM 32%. Gộp tập: C-kNN +0,002. C-LLM tốn 2 lượt gọi |
| RQ3 (prior đúng/sai, oracle) | 4.4, 4.7, 4.8 | C-kNN: prior đúng sửa 5/hỏng 2, prior sai sửa 2/hỏng 11. C-oracle 0,900 vẫn còn 26 câu cả hai cùng sai; nhãn nhiễu Normal |
| Nền tảng so sánh (A0, A1 thấp hơn B) | 4.4 | A0 0,834; A1 0,797 |

---

## Câu chuyện chính của đề tài (dùng cho Chương 1, 4 và 5)

> Dành cho cả hai người: thống nhất cách kể này trước khi viết tiếp. Mục đích là báo cáo có một thông điệp rõ, không phải một danh sách kết quả.

**Một câu:** truy xuất theo độ giống (B) đã là baseline mạnh; thêm nhãn dự đoán (prior) để xếp hạng lại không cải thiện được, và nguyên nhân phần lớn nằm ở dữ liệu và độ dao động đo lường chứ không chỉ ở phương pháp.

**Chuỗi lập luận:**
1. *Vấn đề (RQ1).* Khoảng 24% request có ví dụ giống nhất mang nhãn khác. Nghe như một lý do để dùng nhãn khi truy xuất.
2. *Giả thuyết.* Dùng prior để ưu tiên ví dụ cùng nhãn sẽ giúp LLM (RQ2).
3. *Bằng chứng.* Không giúp: C-kNN, C-LLM không vượt B, FPR Normal không giảm; 6 phương pháp đã công bố cũng không vượt B sau Holm. Prior sai làm hỏng nhiều hơn sửa (RQ3).
4. *Vì sao.* (a) Hai lần chạy cùng prompt đã lệch khoảng 0,01, bằng cỡ mọi chênh lệch đang so. (b) Nhãn Normal trong dataset có nhiễu (27,8% đáng ngờ), và toàn bộ 15 lần B báo nhầm Normal ở test 1–300 rơi vào nhóm này. Một phần "lỗi" thật ra là nhãn sai.
   (c) Dù vậy, làm sạch pool cũng không giúp: bỏ ví dụ Normal sai nhãn khỏi pool chỉ cho +0,011 (p = 0,21), và ở nhóm query thật sự đổi ví dụ gần như hòa (5 sửa, 4 hỏng). Nhãn nhiễu làm lệch con số tuyệt đối, không phải là nút thắt của phương pháp.
5. *Ý nghĩa.* Với phát hiện tấn công web dùng LLM, đo đúng quan trọng hơn thêm kỹ thuật: cần báo cáo độ dao động, kiểm tra nhãn nhiễu, và so sánh trên nhiều tập test độc lập.

**Ba đóng góp nên đứng tên ở Chương 1 và Chương 5** (thay vì chỉ liệt kê pipeline):
- Đo được hiện tượng giống nhưng khác nhãn trên HTTP request và mức độ theo lớp.
- Một kết quả âm có kiểm soát: prior-based reranking không vượt similarity retrieval, kèm phân tích prior đúng/sai và 6 phương pháp công bố làm đối chứng.
- Chỉ ra và định lượng nhiễu nhãn Normal và độ dao động của LLM, kèm quy trình đánh giá tránh chọn kết quả theo test (khóa cấu hình, test mới, gộp tập, Holm).

**Cách viết kết quả âm:** nói thẳng "không cải thiện", nêu giới hạn phạm vi (một encoder, một họ LLM, một dataset, k = 4), không viết "có xu hướng tốt hơn" khi p không có ý nghĩa.

---

## 4.1 Dữ liệu thực nghiệm

- Trả lời: thực nghiệm chạy trên dữ liệu nào, có công bằng không?
- Lưu ý trùng lặp: mô tả chi tiết bộ dữ liệu và tiền xử lý đã nằm ở Chương 1 (1.2.2) và sẽ nằm ở Chương 3. Mục này chỉ tóm tắt vài dòng và trình bày các tập dùng trong thực nghiệm (Bảng 4.1), rồi trỏ về chương trước.
- Kết quả: SR-BH 2020 (website WordPress, 12 ngày tháng 7/2020, gán nhãn thủ công hoặc bán tự động); lọc 6 lớp đơn nhãn; chia theo nhóm để chống rò rỉ.
- Số liệu: 907.815 bản ghi gốc, 466.267 request sau lọc; pool 3.000, validation 200, test 1–300, test 301–600, test mới 300.
- Diễn giải: vì sao chia theo nhóm (cùng một phiên tấn công không rơi vào cả pool lẫn test); vì sao có test mới (kiểm tra không tinh chỉnh quá mức trên test cũ).
- Hình/bảng: Hình 4.1 (phân bố 14 nhãn, thang log), Bảng 4.1 (các tập dữ liệu).
- Nguồn: `reports/dataset/`, `src/artifacts/data/`.
- Chỉnh sửa:

## 4.2 Cài đặt thực nghiệm

- Trả lời: các phương án có so sánh công bằng không, đo bằng gì?
- Kết quả: mọi phương án dùng chung LLM, prompt, k = 4; chỉ khác cách chọn ví dụ.
- Số liệu: gpt-oss-20b (kiểm tra thêm 120b), temperature 0, top-30 ứng viên, λ = 0,1, ngân sách 4,5 USD.
- Diễn giải ngắn: không định nghĩa lại Macro-F1, FPR Normal, LCR@k, bootstrap, McNemar vì đã có ở mục 2.5 của Chương 2; chỉ nói mỗi chỉ số dùng để trả lời RQ nào và trỏ về 2.5. Báo cáo kèm coverage (dự đoán lỗi/sai định dạng tính là sai), đúng nguyên tắc ở 2.5.1.
- **Việc còn thiếu:** hiệu chỉnh Holm (dùng ở 4.6) chưa được định nghĩa ở Chương 2. Phải thêm 1–2 câu vào mục 2.5.4 (nhờ Katun) hoặc giải thích ngay ở 4.2.
- Hình/bảng: Bảng 4.2 (cấu hình).
- Nguồn: `reports/experiments/cau_hinh_khoa.md`, `src/configs/`.
- Chỉnh sửa:

## 4.3 Ví dụ giống nhất có cùng nhãn không? (RQ1)

- Trả lời: khoảng trống nêu ở Chương 1 có thật trên dữ liệu không?
- Kết quả: khoảng một phần tư request có ví dụ giống nhất mang nhãn khác.
- Số liệu: 23,0% (validation), 24,3% (test 1–300 và test mới); Normal 45,5%, SQLi 39,4% (validation).
- Diễn giải: vì sao nặng ở Normal và SQLi (payload chỉ là vài ký tự trong request trông bình thường, nên embedding gần nhau). Giữ đúng lập trường của Chương 1 (1.3.1) và mục 2.5.1: tỷ lệ trùng nhãn là chỉ số mô tả retrieval, chưa chứng minh ví dụ khác nhãn là có hại; một ví dụ khác nhãn vẫn có thể giúp làm rõ ranh giới. Lợi ích hay thiệt hại thật sự phải đọc ở 4.4.
- Hình/bảng: Hình 4.2 (RQ1 và LCR theo lớp).
- Nguồn: `src/artifacts/retrieval/minilm/eval_*/retrieval_metrics.md`.
- Chỉnh sửa:

## 4.4 Kết quả chính trên tập test (RQ2, RQ3)

- Trả lời: RQ2 (C có cải thiện Macro-F1 và giảm FPR Normal so với B và BAL không) và RQ3 (prior đúng/sai, oracle).
- Kết quả RQ2 (test 1–300, đều coverage 1,000): Macro-F1 — A0 0,834; A1 0,797; BAL 0,865; B 0,881; C-kNN 0,862; C-LLM 0,861. FPR Normal — A0 34%; A1 40%; BAL 28%; B 30%; C-kNN 32%; C-LLM 32%. Chênh so với B: BAL −0,016; C-kNN −0,019 (CI [−0,047; +0,008], McNemar p = 0,263); C-LLM −0,020 (p = 0,109). **Bảng 4.3 phải có đủ BAL, FPR Normal, coverage, LCR@4 và token**, vì RQ2 hỏi đúng các chỉ số này; dàn ý cũ thiếu BAL và FPR Normal.
- Kết quả RQ3: C-kNN prior sai (76 câu): sửa 2, hỏng 11; prior đúng (224 câu): sửa 5, hỏng 2. C-LLM prior sai (50 câu): sửa 1, hỏng 7. C-oracle 0,900 (CI so với B [−0,003; +0,043], p = 0,180): sửa 10, hỏng 4, còn 26 câu cả B lẫn C-oracle cùng sai. F1 theo lớp: Normal và OS Command Injection thấp nhất (B 0,77 và 0,79).
- Diễn giải: trên test này, xếp hạng lại bằng prior không hơn B và không giảm FPR Normal, tức câu trả lời RQ2 là "chưa", cần nói thẳng. Khi prior sai thì C làm hỏng nhiều hơn sửa, nhưng nhóm prior sai có thể gồm những query vốn khó nên **không kết luận quan hệ nhân quả** (đúng như Chương 1 mục 1.2.4 đã rào). C-oracle không phải cận trên toán học (Chương 2, 2.4.1): đây là phân tích offline, và việc nó vẫn có 26 câu cùng sai cho thấy phần lỗi còn lại không do prior. Tránh gọi 0,900 là "trần".
- Hình/bảng: Bảng 4.3 (kết quả test, đủ cột nêu trên), Bảng 4.4 (prior đúng/sai cho C-kNN và C-LLM), Hình 4.3 (Macro-F1 trên 4 tập). Nên thêm 1 bảng F1 theo từng lớp vì RQ3 hỏi "kết quả theo từng lớp".
- Nguồn: `src/artifacts/reports/test/comparison.md`.

**Bảng 4.3 (bản đầy đủ, test 1–300, số lấy từ `comparison.md`)**

| Phương án | Macro-F1 | FPR Normal | Coverage | LCR@4 | Lượt LLM/query | Token TB |
|---|---:|---:|---:|---:|---:|---:|
| A0 (zero-shot) | 0,834 | 34,0% | 1,000 | – | 1 | 630 |
| A1 (ví dụ cố định) | 0,797 | 40,0% | 1,000 | 0,167 | 1 | 1.431 |
| BAL (cân bằng lớp) | 0,865 | 28,0% | 1,000 | 0,416 | 1 | 1.486 |
| **B (similarity)** | **0,881** | 30,0% | 1,000 | 0,692 | 1 | 1.487 |
| C-kNN | 0,862 | 32,0% | 1,000 | 0,745 | 1 | 1.488 |
| C-LLM | 0,861 | 32,0% | 1,000 | 0,845 | 2 | 1.490 |
| C-oracle (chỉ phân tích offline) | 0,900 | 28,0% | 1,000 | 0,943 | 1 | 1.487 |

Chênh Macro-F1 so với B: A0 −0,047 (p = 0,007); A1 −0,084 (p < 0,001); BAL −0,016 (p = 0,302); C-kNN −0,019 (p = 0,263); C-LLM −0,020 (p = 0,109); C-oracle +0,019 (p = 0,180).

Câu đọc kết quả gợi ý: "B cao hơn A0 và A1 có ý nghĩa thống kê, còn BAL, C-kNN, C-LLM không phân biệt được với B; LCR@4 tăng dần từ B đến C-oracle nhưng Macro-F1 không tăng theo, nên nhất quán nhãn cao hơn không đồng nghĩa phân loại tốt hơn." (Ý cuối khớp mục 2.5.1 của Chương 2.)

**F1 theo lớp (cho RQ3)**

| Phương án | Normal | SQLi | Path Trav. | Code Inj. | HTTP Resp. Split. | OS Cmd Inj. |
|---|---:|---:|---:|---:|---:|---:|
| A0 | 0,73 | 0,93 | 0,91 | 0,94 | 0,81 | 0,68 |
| A1 | 0,61 | 0,92 | 0,86 | 0,89 | 0,83 | 0,67 |
| BAL | 0,76 | 0,92 | 0,94 | 0,92 | 0,89 | 0,76 |
| B | 0,77 | 0,94 | 0,94 | 0,96 | 0,89 | 0,79 |
| C-kNN | 0,73 | 0,93 | 0,91 | 0,94 | 0,88 | 0,78 |
| C-LLM | 0,76 | 0,93 | 0,92 | 0,96 | 0,84 | 0,76 |
| C-oracle | 0,78 | 0,96 | 0,94 | 0,97 | 0,92 | 0,83 |

Quan sát: Normal và OS Command Injection là hai lớp thấp nhất ở mọi phương án; C-kNN thấp hơn B nhiều nhất ở Normal (−0,04) và Path Traversal (−0,03).
- Chỉnh sửa:

## 4.5 Kiểm tra với model lớn hơn

- Trả lời: kết luận RQ2 có phụ thuộc vào model 20b không? (Mục kiểm chứng bổ sung; Chương 1 chưa nhắc đến 120b, xem phần "Việc cần báo Katun" cuối file.)
- Kết quả: kết luận giữ nguyên với gpt-oss-120b.
- Số liệu: 120b: A0 0,793; B 0,869; C-kNN 0,866; C-oracle 0,880.
- Diễn giải: zero-shot của 120b kém hơn 20b vì gọi payload `;sleep 15;` là SQLi; việc có ví dụ đúng nhãn (B) sửa được lỗi này.
- Hình/bảng: Bảng 4.5.
- Nguồn: `reports/experiments/thi_nghiem_bo_sung_120b.md`.
- Chỉnh sửa:

## 4.6 Vòng cải tiến Pipeline C (mở rộng RQ2 và RQ3)

- Trả lời: có cách nào làm C vượt B không? (Mục mở rộng; Chương 1 chưa đề cập C-gated và các phương pháp đã công bố.)
- Kết quả: C-gated (chỉ dùng nhãn dự đoán khi kNN tự tin) và 6 phương pháp đã công bố (MMR, CLL-RetICL, ENN, C-kNN-ENN, IDS, bỏ phiếu); không phương pháp nào vượt B sau hiệu chỉnh Holm.
- Số liệu: C-gated test 301–600: 0,882 so với B 0,869. Test mới: B 0,833; B-MMR 0,858; B-ENN 0,847; C-gated 0,841; mọi p Holm = 1,000.
- Diễn giải: chênh lệch nhỏ nằm trong dao động ngẫu nhiên (xem 4.7); khóa cấu hình trước khi chạy test mới nên không bị chọn lọc kết quả.
- Hình/bảng: Bảng 4.6 (phương pháp và nguồn), Hình 4.4 (forest plot test mới), Bảng 4.7 (Holm).
- Nguồn: `reports/experiments/ket_qua_c_gated.md`, `reports/experiments/cai_tien_pipeline_c.md`.
- Chỉnh sửa:

## 4.7 Kết quả có đáng tin không?

- Trả lời: chênh lệch quan sát được là thật hay do LLM dao động?
- Kết quả: LLM dao động khoảng 0,01 giữa hai lần chạy cùng prompt; gộp các tập test độc lập cho thấy C-kNN ngang B, C-oracle hơn B có ý nghĩa thống kê.
- Số liệu: chạy lại B: 6/200 và 5/300 câu đổi đáp án. Gộp: C-kNN +0,002 (20/19 trên 900 câu); C-oracle +0,026, p = 0,004 (600 câu); C-gated +0,010, p = 0,109.
- Diễn giải: mọi chênh lệch dưới ~0,01 không nên coi là khác biệt; chỉ C-oracle vượt ngưỡng (phân tích offline dùng nhãn thật, không phải phương án triển khai được), còn phương án thực tế thì không.
- Hình/bảng: Hình 4.5 (forest plot gộp), Bảng 4.8.
- Nguồn: `src/artifacts/reports/pooled/`.
- Chỉnh sửa:

## 4.8 Phân tích lỗi: nhãn nhiễu ở lớp Normal

- Trả lời: lỗi còn lại của B đến từ đâu? Liên quan RQ3 (giới hạn còn lại khi prior đúng) và khớp mục 2.5.2 (nhiễu nhãn khác với prior sai; không coi mọi bất đồng giữa mô hình và dữ liệu là mô hình sai).
- Kết quả: phần lớn lỗi "báo nhầm Normal" là do nhãn dataset sai (request Normal chứa payload); bỏ chúng thì điểm tăng nhưng thứ hạng không đổi.
- Số liệu: 27,8% Normal trong pool đáng ngờ; 15/15 lần B báo nhầm Normal ở test 1–300 rơi vào nhóm này; B: 0,881 → 0,927, FPR 30% → 0%.
- Diễn giải: đây là giới hạn của dữ liệu chứ không phải của phương pháp; cũng giải thích vì sao LCR ở Normal cao (4.3). Phần này chuyển nguyên ý sang mục Hạn chế ở Chương 5.
- **Thí nghiệm bổ sung có đăng ký trước (20/11/2026): bỏ ví dụ Normal sai nhãn khỏi pool (B-cleanpool).** Hỏi: nếu pool sạch thì B có hơn không? Bộ lọc (139 ví dụ pool) làm đổi bộ ví dụ của 18% query (110/600).
  - Số liệu (600 query gộp, test mới + test 301–600): B 0,852; B-cleanpool 0,863; chênh +0,011 [−0,002; +0,025], McNemar p = 0,21. Câu tấn công bị đoán NORMAL: 25 → 23.
  - Cả 3 giả thuyết đã khóa đều đúng: không hại (cận dưới > −0,02), không nhiều lỗi NORMAL hơn, và chênh không có ý nghĩa thống kê.
  - Điểm cần nói trong báo cáo: ở nhóm 110 query thật sự đổi ví dụ chỉ có 5 sửa so với 4 hỏng; phần chênh còn lại đến từ 490 query có prompt giống hệt B (10 câu đổi đáp án, +5 nghiêng về cleanpool), tức là dao động của LLM. Vậy **không có bằng chứng** rằng ví dụ Normal sai nhãn làm hại B.
  - Bảng đề xuất 4.10: B, B-cleanpool, chênh, CI, McNemar, và hàng "đổi ví dụ / giống hệt" (sửa/hỏng).
  - Nguồn: `reports/experiments/cau_hinh_khoa_pool_sach.md` (khóa), `reports/experiments/ket_qua_pool_sach.md`, `src/artifacts/reports/cleanpool/cleanpool.json`.
- Hình/bảng: Hình 4.6 (ma trận nhầm lẫn của B), Bảng 4.9, Bảng 4.10 (B-cleanpool).
- Nguồn: `reports/experiments/nhan_nhieu_lop_normal.md`.
- Chỉnh sửa:

## 4.9 Chi phí và sản phẩm

- Trả lời: phần "chi phí thay đổi thế nào" của RQ2, và phương pháp có tái lập được không. Cần nêu rõ C-LLM tốn 2 lượt gọi/query (một lượt tạo prior, một lượt phân loại) trong khi B, C-kNN chỉ 1 lượt; kNN không gọi LLM (theo bảng 2.5.3). Token trung bình: A0 630; B 1.487; C-kNN 1.488; C-LLM 1.490 (nếu bảng chỉ tính lượt phân loại cuối thì ghi rõ phạm vi, như 2.5.3 yêu cầu).
- Kết quả: chi phí thấp, có demo và quy trình tái lập.
- Số liệu: hơn 12.000 lượt gọi (sổ chi phí: 9.576 + 1.800 lượt đến 20/11 trước khi thêm B-cleanpool, cộng khoảng 800 lượt mới), khoảng 1,5–1,7 USD theo giá tham khảo; sổ chi phí đặt giá gấp đôi nên ghi 2,43 USD (20b) và 0,85 USD (120b), đều dưới ngưỡng 4,5 và 3,0 USD. Khoảng 1.500 token/request với B; trung vị 0,6–0,8 giây/lượt gọi; 94 bài kiểm thử (đã chạy lại ngày 20/11/2026, tất cả đạt).
- Nguồn: `src/artifacts/api_spend_ledger*.json`.
- Chỉnh sửa:

## 4.10 Tóm tắt chương

- Năm ý, mỗi ý gắn một RQ để Chương 5 trích lại:
  1. (RQ1) Hiện tượng giống nhưng khác nhãn: ~24%.
  2. (RQ2) B hơn không ví dụ (A0), ví dụ cố định (A1) và BAL; xếp hạng lại bằng prior (C-kNN, C-LLM) không hơn B và không giảm FPR Normal; các phương pháp đã công bố cũng không vượt B.
  3. (RQ3) Prior sai làm C hỏng nhiều hơn sửa (kèm lưu ý về độ khó của query); C-oracle không phải cận trên và vẫn còn lỗi.
  4. (Độ tin cậy) LLM dao động ~0,01.
  5. (Hạn chế dữ liệu) Nhãn Normal có nhiễu.
- Cầu nối sang Chương 5: mỗi ý trên là một dẫn chứng cho mục "Trả lời ba câu hỏi nghiên cứu"; ý 4 và 5 là cơ sở cho mục "Hạn chế".
- Chỉnh sửa:

---

## Việc cần làm sau khi sửa dàn ý này

- [ ] Trong file Word, thêm 1–2 câu đầu mỗi mục 4.3–4.8: "Mục này trả lời RQx".
- [ ] Mỗi bảng/hình có một câu đọc kết quả ngay bên dưới (không để bảng đứng một mình).
- [ ] Tách rõ hai đoạn trong mỗi mục: kết quả, rồi diễn giải.
- [ ] Rà lại từ ngữ: không dùng "tốt hơn" khi p không có ý nghĩa.
- [ ] Đối chiếu RQ ở Chương 1, 4 và 5 (cùng nội dung, cùng thứ tự). Dùng đúng ba RQ ở khung trên.
- [ ] Bổ sung BAL, FPR Normal, coverage, LCR@4, token vào Bảng 4.3; thêm bảng F1 theo lớp.
- [ ] Bỏ chữ "trần" cho C-oracle trong file Word.

## Việc cần báo Katun (lệch giữa Chương 1–2 và Chương 4)

1. **Công thức reranking:** mục 2.4.1 ghi "Công thức ở mục 1.2.5" nhưng Chương 1 không có mục 1.2.5. Cần thêm công thức vào Chương 3 và sửa tham chiếu.
2. **Phần mở rộng chưa được báo trước:** Chương 4 có C-gated, 6 phương pháp đã công bố, kiểm tra gpt-oss-120b, test mới, gộp các tập test và phân tích nhãn nhiễu. Mục tiêu 1.2.3, đóng góp 1.3.2 và cấu trúc báo cáo 1.4 chưa nhắc. Nên thêm 1–2 dòng (ví dụ ở 1.4 hoặc Chương 3) rằng đây là các kiểm chứng bổ sung cho RQ2 và RQ3.
3. **Holm:** mục 2.5.4 chỉ nêu bootstrap và McNemar, thiếu hiệu chỉnh Holm.
4. **Đường dẫn tài liệu [20]:** ghi `reports/protocol/cau_hinh_khoa.md` nhưng thư mục đó đang trống; file thật là `reports/experiments/cau_hinh_khoa.md`. Dàn ý Chương 4 dùng đường dẫn thật.
5. **Tên Chương 3:** Katun ghi "Thiết kế hệ thống và Phương pháp nghiên cứu", bản Word hiện là "Mô hình đề xuất". Tên Chương 4: "Thực nghiệm và Đánh giá" so với "Thực nghiệm" trong Word. Cần thống nhất.
