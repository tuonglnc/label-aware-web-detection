# 🎤 KỊCH BẢN TRÌNH BÀY TIẾN ĐỘ NGHIÊN CỨU (SPEAKING SCRIPT)

> **Dành cho:** Trình bày trực tiếp với Giảng viên hướng dẫn (thời lượng ~3 đến 5 phút)  
> **Phong cách:** Mạch lạc, tự tin, dùng hình ảnh ẩn dụ trực quan để người không chuyên sâu về AI cũng hiểu được bản chất vấn đề.

---

## 🕒 PHẦN 1: MỞ ĐẦU & BỐI CẢNH (Ẩn dụ đời thường — ~45 giây)

> *"Em chào Thầy/Cô ạ. Hôm nay em xin phép trình bày ngắn gọn về tiến độ và hướng đi của đề tài mà em đang thực hiện."*

*"Để Thầy/Cô dễ hình dung bức tranh tổng thể, em xin giải thích ngắn gọn ý tưởng cốt lõi của đề tài:*

* Các mô hình AI ngôn ngữ lớn (như GPT hay LLaMA) ngày nay rất thông minh. Khi chúng ta đưa cho AI một đoạn mã hoặc một câu truy vấn web (HTTP Request) để hỏi: **'Đây là người dùng bình thường hay hacker đang tấn công?'**, cách hiệu quả nhất là đưa kèm cho AI vài **ví dụ mẫu đã có lời giải** từ trước để nó học theo (trong ngành gọi là In-Context Learning hay RAG).
* **Nó giống như việc một sinh viên đi thi:** Nếu trước khi làm bài, sinh viên được xem qua 3 bài tập mẫu tương tự đã giải sẵn, thì bạn ấy sẽ làm bài thi đúng hơn rất nhiều."

---

## 🔍 PHẦN 2: TẠI SAO EM TÌM RA GAP NÀY? (Vấn đề "mù nhãn" — ~1 phút 15 giây)

> *"Vậy vấn đề nằm ở đâu mà em chọn làm đề tài này?"*

*"Trong thực tế, các hệ thống tìm kiếm ví dụ mẫu hiện nay đang bị một căn bệnh gọi là **'Nhìn mặt bắt hình dong' (Semantic Blindness)**:*

* Nó chỉ biết tìm những câu có **từ ngữ giống nhau** chứ nó không hiểu câu đó là tốt hay xấu.
* **Ví dụ cụ thể:** 
  * Một người dùng bình thường gõ tìm kiếm: `/search?q=select username from users` (chỉ là tìm kiếm thông thường).
  * Một hacker gõ tấn công SQL Injection: `' UNION SELECT username,password FROM users--`
* Về mặt câu chữ, hai câu này chứa các từ tiếng Anh giống hệt nhau (`SELECT`, `users`). 
* Khi hệ thống tìm kiếm mẫu thông thường hoạt động, thấy từ ngữ giống nhau, nó bốc ngay **ví dụ của người bình thường** đưa vào đề thi và bảo AI: *'Hãy tham khảo câu này để chấm bài nhé'*.
* Kết quả là **AI bị đánh lừa**, bị lẫn lộn giữa người tốt và kẻ xấu (hiện tượng này gọi là **Nhiễm nhãn sai — Label Contamination**), khiến tỷ lệ phát hiện tấn công bị tụt dốc nghiêm trọng.

**👉 Điểm mới (Research Gap) mà em tìm ra:**
* Khi em khảo sát có hệ thống **11 bài báo quốc tế gần đây nhất (2024–2026)**, em nhận thấy: Các nhà khoa học đều khẳng định việc nhầm lẫn ví dụ mẫu làm giảm độ chính xác của AI tới hơn 30%.
* **Tuy nhiên, trong lĩnh vực phát hiện tấn công Web:** Chưa có ai làm một cơ chế **'Tìm kiếm ví dụ có nhận biết trước nhãn' (Label-Aware Retrieval)** — tức là trước khi bốc ví dụ đưa cho AI, hệ thống phải liếc nhanh xem ví dụ đó có đúng là loại tấn công cần tìm hay không rồi mới đưa. Đồng thời, cũng chưa có công trình nào đo lường xem tỷ lệ ví dụ đúng nhãn (gọi là chỉ số $\text{LCR@}k$) ảnh hưởng như thế nào đến độ chính xác cuối cùng."*

---

## 🛠️ PHẦN 3: EM ĐÃ LÀM ĐƯỢC NHỮNG GÌ TRONG TUẦN QUA? (~1 phút)

> *"Dựa trên khoảng trống nghiên cứu đó, trong tuần qua em đã hoàn thành 4 việc cụ thể:*

1. **Khảo sát hệ thống 11 bài báo:** Đã lập bảng so sánh đối sánh chi tiết, chứng minh rõ ràng tính mới của đề tài để đưa vào Chương 2 của khóa luận.
2. **Thiết kế khung thí nghiệm 3 nhánh so sánh công bằng:**
   * *Nhánh A:* Cho AI tự đoán mò (không xem ví dụ mẫu).
   * *Nhánh B:* Cho AI xem ví dụ mẫu theo cách truyền thống (dễ bị nhiễm nhãn sai).
   * *Nhánh C (Phương pháp của em):* Cho AI xem ví dụ mẫu đã được bộ lọc nhận biết nhãn kiểm tra trước.
3. **Mổ xẻ bộ dữ liệu thực tế (907.000 dòng log Web):**
   * Em đã phát hiện ra **hơn 1.400 trường hợp 'oái oăm' (Hard Cases)** — tức là đường dẫn URL trông giống hệt nhau nhưng một bên là người dùng thật, một bên là hacker. Đây chính là tập dữ liệu đắt giá nhất để chứng minh phương pháp của em vượt trội so với cách làm cũ.
4. **Lập Checklist thực thi chi tiết từ A đến Z:** Phân chia thành 6 giai đoạn rõ ràng từ khâu làm sạch dữ liệu đến khâu viết khóa luận."*

---

## 🚀 PHẦN 4: KẾ HOẠCH TUẦN TỚI EM SẼ LÀM GÌ? (~45 giây)

> *"Kế hoạch trong tuần tới của em gồm 3 bước hành động cụ thể:*

1. **Khảo sát và chốt bộ dữ liệu chuẩn:** So sánh thêm 1–2 bộ dữ liệu chuẩn của thế giới (như CSIC 2010) để chọn ra bộ dữ liệu sạch nhất, sau đó chia làm 2 phần: 80% làm 'ngân hàng ví dụ' và 20% làm 'đề thi kiểm tra' độc lập (đảm bảo không bị lộ đề).
2. **Lập trình hệ thống cơ sở:** Cài đặt xong mô hình AI chạy local (`Qwen2.5` hoặc `Llama-3.1`) và cơ sở dữ liệu vector (FAISS) để chạy thử nghiệm nhánh A và nhánh B trên 100 mẫu đầu tiên.
3. **Thử nghiệm bộ lọc nhãn nhanh:** Bắt đầu cài đặt thuật toán lọc nhãn cho nhánh C để đo lường tỷ lệ cải thiện."*

---

## ❓ PHẦN 5: XIN Ý KIẾN HƯỚNG DẪN CỦA THẦY / CÔ (~30 giây)

> *"Dạ, để chuẩn bị tốt nhất cho giai đoạn code thực nghiệm tuần tới, em có 2 điểm muốn xin thêm định hướng từ Thầy/Cô ạ:*
>
> 1. Về phạm vi bài toán, em dự kiến tập trung vào **5 đến 6 loại tấn công phổ biến nhất trên Web** (như SQL Injection, Path Traversal, Code Injection,...) để đảm bảo dữ liệu sạch và đủ mẫu, Thầy/Cô thấy phạm vi này đã phù hợp chưa ạ?
> 2. Về bộ dữ liệu, Thầy/Cô có gợi ý thêm nguồn dữ liệu log HTTP nào uy tín mà lab mình từng dùng để em đưa vào so sánh không ạ?
>
> Em xin cảm ơn Thầy/Cô và rất mong nhận được những góp ý từ Thầy/Cô ạ!"*
