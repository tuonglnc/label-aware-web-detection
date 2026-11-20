# C-gated trên test 1-300: CHỈ THAM KHẢO (tập này đã được xem, không dùng để chọn ngưỡng)

Số liệu tự sinh bởi `src/experiments/analyze_gating.py`; không gọi LLM.

300 query, k = 4, N = 30, λ = 0.1, prior kNN k = 5 (đúng 74.7%).

Độ tự tin = tỷ lệ phiếu (có trọng số similarity) dồn cho nhãn thắng trong 5 hàng xóm.

## 1. Retrieval (không cần LLM)

| Ngưỡng | Gate vào | Prior đúng (gate vào) | Prior đúng (gate ra) | Bộ ví dụ khác B | Prior đúng (ở câu khác B) | LCR@k | Không ví dụ nào cùng nhãn |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 (= C prior kNN) | 100.0% | 74.7% | – | 46.3% (139) | 53.2% | 0.745 | 23.3% |
| 0.5 | 83.7% | 78.9% | 53.1% | 30.7% (92) | 53.3% | 0.715 | 19.0% |
| 0.6 | 72.7% | 85.3% | 46.3% | 19.7% (59) | 62.7% | 0.718 | 13.0% |
| 0.7 | 61.0% | 91.8% | 47.9% | 8.0% (24) | 79.2% | 0.705 | 9.3% |
| 0.8 | 57.0% | 93.0% | 50.4% | 4.0% (12) | 83.3% | 0.699 | 8.7% |
| 0.9 | 48.7% | 95.2% | 55.2% | 0.0% (0) | – | 0.692 | 8.3% |
| 1.0 (5/5 cùng nhãn) | 48.7% | 95.2% | 55.2% | 0.0% (0) | – | 0.692 | 8.3% |
| > 1 (= B) | 0.0% | – | 74.7% | 0.0% (0) | – | 0.692 | 8.3% |

## 2. Phản thực tế từ các run LLM đã có (B cho câu gate ra, C prior kNN cho câu gate vào)

B: Macro-F1 = 0.881.

| Ngưỡng | Macro-F1 | Chênh lệch so với B | CI 95% bootstrap | Sửa được lỗi của B | Làm hỏng câu B đúng |
| --- | ---: | ---: | --- | ---: | ---: |
| 0 (= C prior kNN) | 0.862 | -0.019 | [-0.051; +0.011] | 7 | 13 |
| 0.5 | 0.867 | -0.014 | [-0.039; +0.010] | 5 | 9 |
| 0.6 | 0.878 | -0.003 | [-0.022; +0.013] | 3 | 4 |
| 0.7 | 0.878 | -0.003 | [-0.018; +0.010] | 2 | 3 |
| 0.8 | 0.875 | -0.006 | [-0.016; +0.000] | 0 | 2 |
| 0.9 | 0.878 | -0.003 | [-0.010; +0.000] | 0 | 1 |
| 1.0 (5/5 cùng nhãn) | 0.878 | -0.003 | [-0.010; +0.000] | 0 | 1 |
| > 1 (= B) | 0.881 | +0.000 | [+0.000; +0.000] | 0 | 0 |

Ghi chú: khi 5/5 hàng xóm cùng nhãn thì 4 ví dụ của B đã cùng nhãn prior, nên C không đổi gì; C chỉ thay ví dụ ở những query mà hàng xóm bất đồng.
