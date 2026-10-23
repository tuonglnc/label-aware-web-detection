# C-gated: kiểm tra phản thực tế trên test 301-600

Số liệu tự sinh bởi `src/experiments/analyze_gating.py`; không gọi LLM.

300 query, k = 4, N = 30, λ = 0.1, prior kNN k = 5 (đúng 78.3%).

Độ tự tin = tỷ lệ phiếu (có trọng số similarity) dồn cho nhãn thắng trong 5 hàng xóm.

## 1. Retrieval (không cần LLM)

| Ngưỡng | Gate vào | Prior đúng (gate vào) | Prior đúng (gate ra) | Bộ ví dụ khác B | Prior đúng (ở câu khác B) | LCR@k | Không ví dụ nào cùng nhãn |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 (= C prior kNN) | 100.0% | 78.3% | – | 45.0% (135) | 57.8% | 0.782 | 19.7% |
| 0.5 | 85.3% | 84.0% | 45.5% | 31.0% (93) | 64.5% | 0.767 | 15.0% |
| 0.6 | 77.0% | 88.7% | 43.5% | 22.7% (68) | 73.5% | 0.762 | 11.3% |
| 0.7 | 64.0% | 92.7% | 52.8% | 10.0% (30) | 76.7% | 0.741 | 8.7% |
| 0.8 | 58.0% | 94.8% | 55.6% | 4.0% (12) | 83.3% | 0.733 | 7.3% |
| 0.9 | 47.7% | 95.8% | 62.4% | 0.0% (0) | – | 0.727 | 6.7% |
| 1.0 (5/5 cùng nhãn) | 47.7% | 95.8% | 62.4% | 0.0% (0) | – | 0.727 | 6.7% |
| > 1 (= B) | 0.0% | – | 78.3% | 0.0% (0) | – | 0.727 | 6.7% |

## 2. Phản thực tế từ các run LLM đã có (B cho câu gate ra, C prior kNN cho câu gate vào)

B: Macro-F1 = 0.869.

| Ngưỡng | Macro-F1 | Chênh lệch so với B | CI 95% bootstrap | Sửa được lỗi của B | Làm hỏng câu B đúng |
| --- | ---: | ---: | --- | ---: | ---: |
| 0 (= C prior kNN) | 0.873 | +0.004 | [-0.016; +0.024] | 5 | 4 |
| 0.5 | 0.873 | +0.004 | [-0.013; +0.022] | 4 | 3 |
| 0.6 | 0.870 | +0.000 | [-0.013; +0.015] | 2 | 2 |
| 0.7 | 0.873 | +0.003 | [-0.007; +0.017] | 2 | 1 |
| 0.8 | 0.873 | +0.003 | [+0.000; +0.011] | 1 | 0 |
| 0.9 | 0.869 | +0.000 | [+0.000; +0.000] | 0 | 0 |
| 1.0 (5/5 cùng nhãn) | 0.869 | +0.000 | [+0.000; +0.000] | 0 | 0 |
| > 1 (= B) | 0.869 | +0.000 | [+0.000; +0.000] | 0 | 0 |

Ghi chú: khi 5/5 hàng xóm cùng nhãn thì 4 ví dụ của B đã cùng nhãn prior, nên C không đổi gì; C chỉ thay ví dụ ở những query mà hàng xóm bất đồng.
