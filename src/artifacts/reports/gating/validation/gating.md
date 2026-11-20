# C-gated: chọn ngưỡng trên validation (200 query)

Số liệu tự sinh bởi `src/experiments/analyze_gating.py`; không gọi LLM.

200 query, k = 4, N = 30, λ = 0.1, prior kNN k = 5 (đúng 81.0%).

Độ tự tin = tỷ lệ phiếu (có trọng số similarity) dồn cho nhãn thắng trong 5 hàng xóm.

## 1. Retrieval (không cần LLM)

| Ngưỡng | Gate vào | Prior đúng (gate vào) | Prior đúng (gate ra) | Bộ ví dụ khác B | Prior đúng (ở câu khác B) | LCR@k | Không ví dụ nào cùng nhãn |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 (= C prior kNN) | 100.0% | 81.0% | – | 49.0% (98) | 65.3% | 0.809 | 16.5% |
| 0.5 | 85.0% | 84.7% | 60.0% | 34.5% (69) | 68.1% | 0.777 | 13.0% |
| 0.6 | 74.5% | 90.6% | 52.9% | 24.0% (48) | 79.2% | 0.774 | 9.5% |
| 0.7 | 63.5% | 93.7% | 58.9% | 13.0% (26) | 84.6% | 0.752 | 7.5% |
| 0.8 | 56.5% | 96.5% | 60.9% | 6.0% (12) | 100.0% | 0.741 | 7.0% |
| 0.9 | 45.5% | 97.8% | 67.0% | 0.0% (0) | – | 0.726 | 7.0% |
| 1.0 (5/5 cùng nhãn) | 45.5% | 97.8% | 67.0% | 0.0% (0) | – | 0.726 | 7.0% |
| > 1 (= B) | 0.0% | – | 81.0% | 0.0% (0) | – | 0.726 | 7.0% |

## 2. Phản thực tế từ các run LLM đã có (B cho câu gate ra, C prior kNN cho câu gate vào)

B: Macro-F1 = 0.893.

| Ngưỡng | Macro-F1 | Chênh lệch so với B | CI 95% bootstrap | Sửa được lỗi của B | Làm hỏng câu B đúng |
| --- | ---: | ---: | --- | ---: | ---: |
| 0 (= C prior kNN) | 0.882 | -0.010 | [-0.033; +0.009] | 1 | 3 |
| 0.5 | 0.893 | -0.000 | [-0.015; +0.015] | 1 | 1 |
| 0.6 | 0.898 | +0.006 | [-0.002; +0.019] | 1 | 0 |
| 0.7 | 0.899 | +0.006 | [-0.001; +0.019] | 1 | 0 |
| 0.8 | 0.899 | +0.006 | [+0.000; +0.019] | 1 | 0 |
| 0.9 | 0.893 | +0.000 | [+0.000; +0.000] | 0 | 0 |
| 1.0 (5/5 cùng nhãn) | 0.893 | +0.000 | [+0.000; +0.000] | 0 | 0 |
| > 1 (= B) | 0.893 | +0.000 | [+0.000; +0.000] | 0 | 0 |

Ghi chú: khi 5/5 hàng xóm cùng nhãn thì 4 ví dụ của B đã cùng nhãn prior, nên C không đổi gì; C chỉ thay ví dụ ở những query mà hàng xóm bất đồng.
