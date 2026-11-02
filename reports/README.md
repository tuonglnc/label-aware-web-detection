# Mục lục tài liệu

Tài liệu của đồ án, xếp theo thứ tự nên đọc. Tổng quan, kết quả chính và cách chạy nhanh nằm ở [README của repo](../README.md).

| Thư mục | Tài liệu | Nội dung |
| --- | --- | --- |
| `project/` | [mo_ta_de_tai.md](project/mo_ta_de_tai.md) | Mô tả đề tài đã đăng ký (ngắn) |
| | [tong_quan_de_tai.md](project/tong_quan_de_tai.md) | Câu hỏi nghiên cứu và thiết kế thí nghiệm |
| `dataset/` | [khao_sat_sr_bh_2020.md](dataset/khao_sat_sr_bh_2020.md) | Khảo sát SR-BH 2020: phân bố lớp, payload thật, cặp request minh họa |
| | [khao_sat_csic_2010.md](dataset/khao_sat_csic_2010.md) | Khảo sát CSIC 2010 (dataset được cân nhắc nhưng không dùng) |
| | [quyet_dinh_dataset.md](dataset/quyet_dinh_dataset.md) | Vì sao chọn SR-BH 2020 và các giới hạn của nó |
| | [huong_dan_xu_ly_du_lieu.md](dataset/huong_dan_xu_ly_du_lieu.md) | Tải dữ liệu, cách biểu diễn request, chia tập, audit rò rỉ |
| | [ket_qua_xu_ly_du_lieu.md](dataset/ket_qua_xu_ly_du_lieu.md) | Kết quả xử lý dữ liệu và các vấn đề về nhãn |
| `guides/` | [huong_dan_doc_va_chay_code.md](guides/huong_dan_doc_va_chay_code.md) | **Bắt đầu từ đây:** bản đồ code, cài đặt, giải thích từng file |
| | [huong_dan_chay_thuc_nghiem.md](guides/huong_dan_chay_thuc_nghiem.md) | Các lệnh chạy từng bước, PowerShell và Git Bash |
| `experiments/` | [cau_hinh_khoa.md](experiments/cau_hinh_khoa.md) | Cấu hình khóa trước khi chạy test, giả thuyết đăng ký trước |
| | [thi_nghiem_bo_sung_120b.md](experiments/thi_nghiem_bo_sung_120b.md) | Kiểm tra lại kết luận với gpt-oss-120b |
| | [cau_hinh_khoa_c_gated.md](experiments/cau_hinh_khoa_c_gated.md) | Khóa C-gated (chỉ dùng prior khi kNN tự tin) trước khi chạy test 301–600 |
| | [ket_qua_c_gated.md](experiments/ket_qua_c_gated.md) | Kết quả C-gated trên test 301–600 |
| | [nhan_nhieu_lop_normal.md](experiments/nhan_nhieu_lop_normal.md) | Phân tích nhãn nhiễu ở lớp Normal |
| | [cau_hinh_khoa_cai_tien.md](experiments/cau_hinh_khoa_cai_tien.md) | Khóa vòng cải tiến C trước khi chạy tập test mới |
| | [cai_tien_pipeline_c.md](experiments/cai_tien_pipeline_c.md) | **Báo cáo vòng cải tiến C**: 6 phương pháp đã công bố, tập test mới, gộp 900 câu |
| `plan/` | [ke_hoach_2_nguoi_11_10_den_14_11.md](plan/ke_hoach_2_nguoi_11_10_den_14_11.md) | Kế hoạch và phân công 11/10–14/11/2026 |
| `midterm/` | [bao_cao_giua_ky.md](midterm/bao_cao_giua_ky.md) | Báo cáo giữa kỳ (Markdown); bản Word/PDF theo mẫu Khoa nằm cùng thư mục |
| `references/` | [link_papers.md](references/link_papers.md) | Danh sách bài báo tham khảo (kèm PDF) |
| `word/` | `build_bao_cao_giua_ky.py`, `export_word.py` | Script dựng file Word theo mẫu Khoa và xuất PDF ([cài thư viện](word/requirements.txt)) |

Hình dùng trong báo cáo: [`dataset/figures/`](dataset/figures/) (hình dữ liệu) và [`word/figures/`](word/figures/) (sơ đồ pipeline, confusion matrix).

Kết quả thực nghiệm dạng bảng nằm cạnh code, trong [`src/artifacts/reports/`](../src/artifacts/reports/): `validation/`, `test/`, `test_120b/`, `test_301_600/`, `validation_improve/`, `test_fresh/`, `pooled/`.

**Dựng lại báo cáo Word** (Windows, cần Microsoft Word để cập nhật mục lục và xuất PDF):

```bash
pip install -r reports/word/requirements.txt
python reports/word/build_bao_cao_giua_ky.py
python reports/word/export_word.py reports/midterm/Bao_cao_giua_ky_LabelAware.docx
```
