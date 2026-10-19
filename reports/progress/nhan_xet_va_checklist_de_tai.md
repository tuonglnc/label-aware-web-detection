# Nhận xét đề tài và checklist chỉnh sửa

**Đề tài:** Label-Aware Retrieval for LLM-Based Web Attack Detection
**Ngày tổng hợp:** 19/10/2026, dựa trên repo tại commit `fccb77c` và file *Giải thích đề tài và gợi ý hình minh họa*.
**Mục đích:** Tóm tắt nhận xét, các điểm cần bổ sung và việc cần làm, giữ nguyên ý tưởng ban đầu của đề tài.

---

## 1. Đề tài làm gì, nói ngắn gọn

- **Bài toán:** đọc một HTTP request và cho biết nó thuộc lớp nào trong 6 lớp: Normal, SQL Injection, Path Traversal, Code Injection, HTTP Response Splitting, OS Command Injection.
- **Cách làm:** dùng LLM có sẵn, không train. Mỗi lần hỏi, đưa kèm vài request mẫu có nhãn (demonstrations). Kỹ thuật này gọi là In-Context Learning.
- **Vấn đề:** cách phổ biến là chọn ví dụ giống request nhất (semantic retrieval). Nhưng các HTTP request rất hay giống nhau bề ngoài mà khác nhãn, nên ví dụ "trông giống" có thể làm LLM đoán sai.
- **Ý tưởng của nhóm (Pipeline C):**
  1. LLM đoán sơ bộ trước, tạo ra **prior**.
  2. Lấy top-N ứng viên giống nhất.
  3. Xếp hạng lại, ưu tiên ứng viên có nhãn khớp prior.
  4. Lấy top-k ứng viên đưa vào prompt cho LLM ra quyết định cuối.
- **Câu hỏi nghiên cứu:** dùng thông tin nhãn khi chọn ví dụ có giúp LLM phân loại tốt hơn so với chỉ dựa vào độ giống không?

## 2. Hiện trạng theo commit 19/10

| Hạng mục | Tình trạng |
| --- | --- |
| Xử lý dữ liệu SR-BH 2020 | **Tốt.** 907.815 bản ghi, sau lọc và bỏ trùng còn 466.267 request. Chia tập theo nhóm, kiểm tra leakage cho kết quả 0 giao nhau, chạy lại 2 lần cho kết quả giống hệt. |
| Tập con | Pool 3.000, validation 200, test 600, cân bằng lớp, seed 42 |
| Cặp ví dụ minh họa | Cặp Normal và SQLi thật (record 175088 và 174425) giống nhau 99,5%, chỉ khác đoạn `+AND+1%3D1` |
| Pipeline A0 | Đã có code và test. Lần gọi API thật duy nhất bị **lỗi 403**, nên **chưa có kết quả thật** |
| Pipeline A1, B, C | Chưa triển khai |
| **Nhãn nhiễu** | Đọc tay 10 mẫu "Normal" thì **5 mẫu chứa payload tấn công**. Nhãn gốc được tạo dựa trên ModSecurity cộng xử lý bán tự động |
| CSIC 2010 | Chỉ có nhãn Normal/Anomalous, không dùng được cho bài toán nhiều lớp |

## 3. Điểm tốt

- Câu hỏi nghiên cứu rõ ràng và kiểm chứng được. Có baseline trực tiếp (B), thước đo chính (Macro-F1) được chốt từ trước.
- Protocol chặt: chia tập theo nhóm, có đối chứng **class-balanced**, dùng paired bootstrap, chọn cấu hình trên validation rồi khóa trước test, báo cả chi phí.
- Trung thực: tài liệu **không** tự nhận là phương pháp mới hay "đầu tiên", có tính trước trường hợp C không thắng.
- Phần dữ liệu làm kỹ và tái lập được. Đây là phần mạnh nhất hiện nay.

## 4. Thiếu sót chính

1. **Rủi ro "tự xác nhận".** Prior sai thì reranking kéo về ví dụ sai lớp, và LLM càng tin vào cái sai. Prior đúng thì LLM vốn đã đúng. Vì vậy cần phân tích riêng hai trường hợp prior đúng và prior sai.
2. **Thiếu đối chứng không dùng LLM** (TF-IDF và kNN, giải thích ở mục 5). Nếu không có, sẽ khó trả lời câu hỏi "vì sao phải dùng LLM".
3. **Nhãn nhiễu đánh thẳng vào chữ "label-aware".** C dựa vào nhãn của kho ví dụ, mà nhãn lại không sạch. Điểm số hiện tại chỉ đo mức đồng thuận với nhãn gốc.
4. **Dataset có thể quá dễ:** nhãn sinh từ luật WAF, nhiều endpoint chung giữa pool và test (khoảng 18 nghìn). Hệ quả là mọi cách đều có thể đạt điểm cao và khó thấy khác biệt.
5. **Cỡ mẫu nhỏ:** 100 mẫu mỗi lớp trong test, nên khoảng tin cậy của Macro-F1 sẽ rộng.
6. **Tính thực tiễn:** mỗi request phải gọi LLM 2 lần. Nên định vị là phân tích log offline, không phải WAF real-time.
7. **Tiến độ:** chưa có con số thật nào từ LLM và chưa chốt hội nghị đích.

## 5. TF-IDF và kNN là gì

Cả hai **không có trong ý tưởng ban đầu**. Chúng được đề xuất thêm làm **mốc đối chứng**, không thay thế phương pháp của nhóm.

### kNN vote ("hỏi hàng xóm")

- Tìm k request giống nhất trong kho. Bước này Pipeline B đã làm sẵn.
- Nhãn nào xuất hiện nhiều nhất trong k hàng xóm thì chọn nhãn đó. **Không gọi LLM.**
- **Ý nghĩa:** nếu chỉ đếm nhãn hàng xóm đã đạt 95%, LLM phải vượt được mức này mới chứng tỏ có giá trị.
- **Dùng thêm được làm prior cho C** thay cho LLM zero-shot. C khi đó chỉ cần gọi LLM 1 lần thay vì 2. Đây vẫn nằm trong ý tưởng gốc, chỉ đổi nguồn của prior.

### TF-IDF + Logistic Regression ("bộ lọc thư rác kiểu cũ")

- **TF-IDF** cắt request thành các mẩu ký tự ngắn (character n-gram, ví dụ `1=1`, `../`, `<script`). Mẩu phổ biến như `HTTP/1.1` bị giảm trọng số, mẩu hiếm và đặc trưng được tăng trọng số.
- **Logistic Regression** là một mô hình nhỏ, học xem mẩu nào cộng điểm cho lớp nào. Train trong vài giây đến vài phút trên CPU.
- **Ý nghĩa:** nhãn SR-BH dựa trên luật so khớp ký tự của ModSecurity, nên TF-IDF có thể bắt chước gần như hoàn toàn. Cần biết con số này **trước khi** reviewer hỏi.
- **Không mâu thuẫn với inference-only.** Đây chỉ là baseline; phương pháp chính vẫn không train.

### Ba khả năng kết quả

| Kết quả | Cách đọc |
| --- | --- |
| TF-IDF hoặc kNN ≈ 100% | Dataset quá dễ. Báo thầy sớm và nhấn vào giá trị khác của LLM (giải thích lý do, xử lý payload lạ) |
| TF-IDF và kNN cao, LLM (B hoặc C) cao hơn rõ | Bằng chứng mạnh nhất cho đề tài |
| LLM thấp hơn TF-IDF | Vẫn là kết quả trung thực, nhưng cần định vị lại bài |

**Công sức:** khoảng nửa ngày. kNN dùng lại index của B, còn TF-IDF chỉ cần khoảng 20 dòng scikit-learn.

## 6. Checklist chỉnh sửa

🔴 Bắt buộc, trước buổi báo cáo 22/10 · 🟡 Trước benchmark cuối · 🟢 Nên có cho bài báo

### A. Định vị và câu hỏi nghiên cứu

- [ ] 🔴 Tách thành 3 câu hỏi nghiên cứu:
  - **RQ1:** Semantic retrieval lấy về bao nhiêu phần trăm ví dụ khác nhãn? Câu này không cần LLM.
  - **RQ2:** C có hơn B và class-balanced về Macro-F1 không?
  - **RQ3:** C giúp hay hại khi prior đúng, khi prior sai, ở lớp ít mẫu và khi nhãn nhiễu?
- [ ] 🔴 Viết giả thuyết kèm tiêu chí bác bỏ. Ví dụ: chấp nhận nếu khoảng tin cậy 95% của chênh lệch Macro-F1 giữa C và B nằm hoàn toàn trên 0.
- [ ] 🔴 Ghi rõ phạm vi là phân tích hoặc triage log offline, không phải WAF real-time.
- [ ] 🔴 Nêu 2–3 lý do vì sao dùng LLM.
- [ ] 🟡 Viết lại đóng góp: trọng tâm là phân tích khi nào thông tin nhãn giúp hoặc hại, còn C là phương tiện để phân tích.
- [ ] 🟡 Lập bảng related work (KATE, EPR, CLL-RetICL, ICL Noisy Labels, DemoShapley, CyberRAG, phát hiện bất thường web cổ điển), đặt nhóm mình ở dòng cuối.
- [ ] 🟡 Sửa tài liệu tham khảo không khớp: link CLL-RetICL (`findings-ijcnlp.22` hay `.97`) và venue của KATE (DeeLIO hay NAACL).

### B. Phương pháp

- [ ] 🔴 Viết công thức reranking, ví dụ `score(d) = sim(q,d) + λ·1[label(d) = prior(q)]`. Định nghĩa N, k, λ, chọn soft hay hard, quy tắc khi điểm bằng nhau.
- [ ] 🔴 Quy định khi prior lỗi thì C quay về hành vi của B. Ghi trước khi chạy.
- [ ] 🟡 B và C dùng cùng embedding, N, k, LLM và mẫu prompt. Báo token thực tế của từng cách.
- [ ] 🟡 Giải thích lý do chọn embedding model cho dữ liệu HTTP.
- [ ] 🟢 Cân nhắc giữ đa dạng nhãn trong top-k, ví dụ luôn có ít nhất 1 ví dụ Normal. Chỉ thêm nếu ablation cho thấy có ích.

### C. Đối chứng và ablation

- [ ] 🔴 Đủ các đối chứng chính: A0, A1, random-k, B, class-balanced, C.
- [ ] 🔴 Thêm **kNN vote** và **TF-IDF + LR**.
- [ ] 🔴 Thêm **C-oracle**: dùng nhãn thật thay prior, chỉ để phân tích. Kết quả cho biết mức tối đa label-aware có thể đạt.
- [ ] 🔴 Lập bảng prior đúng/sai × B đúng/sai × C đúng/sai. Đếm số lỗi C sửa được và số lần C làm hỏng.
- [ ] 🟡 Ablation nguồn prior: LLM, kNN và oracle.
- [ ] 🟡 Ablation λ, k, N, soft và hard. Chỉ chạy trên validation.

### D. Dữ liệu và nhãn

- [ ] 🔴 Sửa lỗi 403, chạy A0 thật trên 30 mẫu development.
- [ ] 🔴 Đưa vấn đề nhãn nhiễu vào báo cáo và xin thầy quyết định cách xử lý.
- [ ] 🟡 Hai người dán nhãn lại test 600 mẫu một cách độc lập. Báo Cohen's kappa và báo kết quả trên cả nhãn gốc lẫn nhãn đã chỉnh. Ước tính khoảng 10 giờ mỗi người.
- [ ] 🟡 Thí nghiệm nhiễu có kiểm soát: cố ý làm sai 0, 10, 20, 30% nhãn trong pool, rồi so tốc độ suy giảm của C và B.
- [ ] 🟡 Viết data statement: nguồn, giấy phép CC0, cách thu thập, cách gắn nhãn, giới hạn.
- [ ] 🟢 Tạo tập test con không trùng endpoint với pool.

### E. Đánh giá và thống kê

- [ ] 🔴 Macro-F1 làm thước đo chính, kèm F1 từng lớp, confusion matrix và FPR trên lớp Normal.
- [ ] 🔴 Khóa cấu hình (ghi commit hash và config) trước khi chạm vào test.
- [ ] 🟡 Dùng paired bootstrap và McNemar; ghi chú vấn đề so sánh nhiều lần.
- [ ] 🟡 Ước lượng chênh lệch nhỏ nhất có thể phát hiện với cỡ test hiện tại.
- [ ] 🟡 Chạy lặp 2–3 lần trên một tập con để đo độ dao động của LLM.
- [ ] 🟡 Báo chi phí: số lần gọi, token, độ trễ. Vẽ biểu đồ Macro-F1 theo chi phí.
- [ ] 🟢 LCR@k chỉ dùng để chẩn đoán, không dùng làm bằng chứng.

### F. Tái lập

- [ ] 🔴 Chạy được trên Windows: phần resume dùng `fcntl` nên không chạy native. Sửa code hoặc hướng dẫn dùng WSL.
- [ ] 🟡 Ghi đúng phiên bản model và lưu toàn bộ output gốc.
- [ ] 🟡 Có script tạo lại mọi bảng và hình từ file kết quả.
- [ ] 🟢 Thêm một model mã nguồn mở qua Ollama để người khác tái lập được.

### G. Trình bày

- [ ] 🔴 Dùng cặp request thật giống nhau 99,5% làm hình mở đầu.
- [ ] 🔴 Cập nhật file giải thích đề tài (xem mục 7).
- [ ] 🟡 Viết sẵn Limitations: một dataset, traffic WordPress 12 ngày, nhãn nhiễu, endpoint chồng lấn, chỉ đánh giá offline.
- [ ] 🟡 Chốt hội nghị đích, template, số trang và deadline.

## 7. Góp ý cho file "Giải thích đề tài và gợi ý hình minh họa"

**Điểm tốt:** dẫn dắt dễ hiểu, trung thực, có nói rủi ro prior sai (Hình 6), có baseline class-balanced, hình minh họa thực dụng.

**Cần sửa:**
1. Thêm phần **nhãn nhiễu** vào mục 8 và đoạn trình bày ở mục 12.
2. Thay ví dụ tự chế `shop.example` bằng **cặp request thật**. Hình có sẵn tại `reports/surveys/figures/sr_bh_motivating_pair.png`.
3. Cập nhật tiến độ thật: 466.267 request, split v1, A0 đã có code.
4. Hình 4 nên chọn ví dụ mà tập ví dụ được chọn **thực sự thay đổi** sau reranking. Ví dụ: ứng viên giống nhất là request Normal song sinh và bị thay bằng một ví dụ SQLi.
5. Bảng đối chứng ở mục 9 bổ sung A1, kNN/TF-IDF và C-oracle.
6. Mục 2 nói rõ ngay đây là bài toán **6 lớp**.

## 8. Các mốc quyết định

| Mốc | Điều kiện | Nếu không đạt |
| --- | --- | --- |
| Cuối tuần 1 | A0 chạy thật; có RQ1, kNN và TF-IDF | Nếu kNN hoặc TF-IDF gần 100%, báo thầy và chuyển trọng tâm sang giải thích hoặc phân tích |
| Giữa tuần 2 | C-oracle hơn B rõ rệt trên validation | Nếu C-oracle ≈ B thì trần của label-aware thấp; chuyển sang bài phân tích kết quả âm |
| Cuối tuần 3 | Cấu hình đã khóa, có bảng prior đúng/sai | Thu hẹp cấu hình, giữ B, C và các đối chứng chính |

**Nếu chỉ làm được 5 việc:** chạy A0 thật; đo RQ1 cùng kNN và TF-IDF; thêm C-oracle; lập bảng prior đúng/sai; đưa vấn đề nhãn nhiễu ra trao đổi với thầy.

---

## Phụ lục: hai hướng dự phòng nếu cần đổi hướng

Chỉ cân nhắc khi kết quả ở các mốc quyết định không thuận lợi **và** thầy đồng ý.

1. **Nghiên cứu so sánh các chiến lược chọn ví dụ.** Không coi C là "phương pháp đề xuất" nữa, mà so 6–8 cách chọn ví dụ trong điều kiện request gần giống nhau và nhãn có nhiễu. Kết quả nào cũng có giá trị, và gần như toàn bộ code vẫn dùng lại được.
2. **"Tìm điểm khác biệt" (benign-twin diff).** Tìm request **bình thường** giống nhất ở cùng endpoint, rồi chỉ đưa cho LLM **phần khác biệt** để hỏi phần đó có độc hại không. Hướng này không cần nhãn của các loại tấn công, có thể phát hiện kiểu tấn công chưa có trong kho, và chỉ ra được vị trí payload.
   - Kiểm tra trong 1 ngày, chưa cần LLM: tỷ lệ request test có "song sinh lành" trong pool, và phần khác biệt có chứa đúng payload không.
   - Hướng này đổi trọng tâm đề tài, nên cần thầy đồng ý.
