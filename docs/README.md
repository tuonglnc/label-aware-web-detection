# Tập trung triển khai từ đây

Chỉ dùng kế hoạch 4 tuần bên dưới để theo dõi tiến độ. Các kế hoạch, checklist và bản báo cáo cũ đã được dọn khỏi `docs`.

## Ba tài liệu cần dùng

| Thứ tự | Tài liệu | Khi nào dùng |
| --- | --- | --- |
| 1 | [Kế hoạch 4 tuần cho 2 người](plan/ke_hoach_4_tuan_va_nop_hoi_nghi.md) | Theo dõi phân công, deadline và sản phẩm mỗi tuần; đây là kế hoạch chính |
| 2 | [Báo cáo định hướng và mẫu hằng tuần](report/bao_cao_dinh_huong_va_mau_hang_tuan.md) | Chuẩn bị buổi gặp thầy tuần này và cập nhật mỗi tuần |
| 3 | [Mô tả đề tài](mo_ta_de_tai.md) | Gửi mô tả lên hệ thống hoặc giới thiệu ngắn gọn hướng nghiên cứu |

## Việc cần làm trước tiên

- [ ] Hai người thống nhất vai trò TV1/TV2 và quỹ thời gian 20–25 giờ/người/tuần.
- [ ] Chuẩn bị báo cáo định hướng, xin lịch gặp thầy và trao đổi hội nghị đích/deadline.
- [ ] Xác nhận dataset, kiểm tra annotation và chốt taxonomy.
- [ ] Setup môi trường, thử LLM trên 20–50 request development và đo latency.
- [ ] Chốt interface module; chia task tuần 1 với deadline và sản phẩm cụ thể.

## Các mốc chính

| Hạn nội bộ | Sản phẩm |
| --- | --- |
| 22/10/2026 | Dataset/protocol, split và baseline A0 đầu tiên |
| 29/10/2026 | Baselines và Pipeline C chạy trên validation |
| 05/11/2026 | Validation, ablation và cấu hình cuối đã khóa |
| 12/11/2026 | Final benchmark và phân tích kết quả chính |
| 19/11/2026 | Bản thảo bài báo đầy đủ gửi thầy |
| 26/11/2026 | Bản sửa theo góp ý |
| 01/12/2026 | Bản sẵn sàng nộp, điều chỉnh theo deadline hội nghị chính thức |

Nếu chậm, giảm các thực nghiệm mở rộng theo kế hoạch chính; giữ kiểm tra leakage, các đối chứng cần thiết và thời gian giảng viên review.
