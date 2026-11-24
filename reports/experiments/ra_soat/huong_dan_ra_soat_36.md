# Hướng dẫn rà thủ công 36 yêu cầu Normal đáng ngờ

## 1. Việc này để làm gì

Trong SR-BH 2020, nhiều yêu cầu mang nhãn **Normal** thật ra chứa mã tấn công (mục 4.8 của báo cáo). Để đếm các yêu cầu này, nhóm dùng một bộ quy tắc tự động (`SUSPICIOUS_RULES` trong `src/analysis/label_noise.py`). Bộ quy tắc đánh dấu **36 yêu cầu Normal đáng ngờ** trong tập validation (7), test 1–300 (15) và test 301–600 (14).

Trước đó, trợ lý AI đã đọc 36 yêu cầu này và kết luận "cả 36 đều chứa mã tấn công thật". Kết luận đó **chưa có người kiểm tra**, và báo cáo đang ghi thẳng điều này ở phần hạn chế. Việc của bạn là đọc từng yêu cầu và tự quyết định, để báo cáo có thể ghi "đã được thành viên nhóm rà soát".

## 2. Cách làm

1. Mở `phieu_ra_soat_36.csv` (cùng thư mục) bằng Excel. File đã mã hóa UTF-8, mở trực tiếp đọc được tiếng Việt.
2. Với mỗi dòng, đọc cột **URI (đã giải mã URL)**, cột **Body** và **Header khác rỗng**. Cột "Quy tắc khớp" chỉ cho biết vì sao bộ quy tắc đánh dấu dòng đó; đừng coi nó là đáp án.
3. Điền cột **Có mã tấn công? (C/K/?)**:
   - **C**: bạn thấy rõ có chuỗi cố ý tấn công.
   - **K**: trông là yêu cầu bình thường, chuỗi bị đánh dấu chỉ là trùng hợp.
   - **?**: không chắc.
4. Nếu chọn C, điền **Loại**: `SQLi`, `Path Traversal`, `Code Injection`, `OS Command`, `XSS`, `Response Splitting` hoặc `Khác`.
5. Cột **Ghi chú**: một dòng ngắn nói vì sao (ví dụ "có `;cat /etc/passwd;` chèn giữa đường dẫn").
6. Lưu file (giữ định dạng CSV) và gửi lại cho trợ lý để tổng hợp.

**Lưu ý để kết quả công bằng:**
- Đọc bằng mắt, không tra lại kết luận của AI hay danh sách trong `flagged_normal.jsonl`.
- Không dùng dự đoán của model (B, C) để quyết định. Phiếu cố ý không có cột này.
- Nếu có thể, nhờ Katun làm riêng một bản độc lập, rồi so sánh. Hai người cùng đồng ý thì kết quả đáng tin hơn một người.
- Khoảng 36 dòng, mỗi dòng 1–2 phút, tổng cộng khoảng 1 giờ.

## 3. Cách nhận biết (tóm tắt)

| Dấu hiệu | Ví dụ | Thường là |
| --- | --- | --- |
| Lệnh hệ điều hành nối vào đường dẫn | `;cat /etc/passwd;`, `&&cat /etc/passwd`, `` `cat /etc/passwd` ``, `\|\|cat ...` | **C**, OS Command |
| Hàm làm trễ | `" / sleep(15) / "`, `/bin/sleep 15` | **C**, OS Command hoặc SQLi dạng time-based |
| Đoạn `() { :;};` | `() { :;}; /bin/sleep 15` | **C**, OS Command (kiểu Shellshock) |
| Thẻ script | `<script>alert(1);</script>` | **C**, XSS |
| Đường dẫn ngược | `../../etc/passwd` | **C**, Path Traversal |
| Xuống dòng và `Set-cookie:` chèn vào URL | `Set-cookie: Tamper=...` | **C**, Response Splitting |

Yêu cầu bình thường của WordPress thường có đường dẫn như `/blog/index.php/2020/04/...`, `/wp-content/uploads/...png`, `?ver=1.11.4`. Chuỗi lạ chèn **vào giữa** các đường dẫn đó (dấu `;`, `&`, `|`, dấu nháy, `sleep`, `cat`) là dấu hiệu bị chèn có chủ ý.

## 4. Các dòng khó, cần đọc kỹ

Không phải dòng nào cũng rõ ràng. Hãy ghi lý do của bạn vào cột Ghi chú:

- **STT 1, 28, 34, 35:** có `/etc/passwd` nằm như một đoạn đường dẫn, không có `;`, `cat` hay `..`. Đây có thể là dò quét đường dẫn, nhưng cũng có người cho là chưa đủ để gọi là "tấn công". Bạn quyết định C hay ?.
- **STT 20, 22, 24:** có `c:\` trong đường dẫn. Hãy xem đây có phải thử lấy file hệ thống Windows không, hay chỉ là chuỗi lạ.
- **STT 15:** `Set-cookie: Tamper=...` nằm trong URL. Đây là chuỗi do công cụ quét chèn vào để thử lỗ hổng, nhưng bản thân yêu cầu chỉ tải một file ảnh hoặc CSS.
- **STT 13:** `cat$jj $jj/etc$jj/passwd` là cách viết nhằm tránh bị bộ lọc phát hiện.

## 5. Lưu ý an toàn

Các chuỗi trong phiếu chỉ là **văn bản**. Không cần (và không nên) mở URL, dán vào trình duyệt hay chạy thử. Chỉ đọc.

## 6. Sau khi xong thì sao

Bạn gửi lại file đã điền, trợ lý sẽ:
1. Đếm số dòng C, K, ?, và (nếu có hai người) mức đồng ý giữa hai người.
2. Cập nhật câu ở mục 4.8 và 5.2 từ "chưa được chuyên gia bảo mật xác nhận" thành mô tả đúng việc đã làm (ví dụ "đã được hai thành viên nhóm rà soát độc lập, X/36 xác nhận có mã tấn công"). Việc này **không** biến thành "chuyên gia bảo mật xác nhận", báo cáo vẫn ghi rõ giới hạn đó.
3. Nếu có dòng K, chạy lại phép tính "bỏ Normal đáng ngờ" (Bảng 4.11) chỉ với các dòng bạn xác nhận là C, rồi báo lại xem kết luận có đổi không.
