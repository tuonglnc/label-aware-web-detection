# Kết quả retrieval và kNN trên `test` (300 query)

Số liệu tự sinh bởi `src/experiments/eval_retrieval.py`; không gọi LLM.

## RQ1: ví dụ giống nhất có khác nhãn không?

- Tỷ lệ query có ví dụ top-1 KHÁC nhãn: **22.0%**
- Similarity trung bình của top-1: 0.957

| Lớp | Top-1 khác nhãn |
| --- | ---: |
| CODE_INJECTION | 22.0% |
| HTTP_RESPONSE_SPLITTING | 18.0% |
| NORMAL | 42.0% |
| OS_COMMAND_INJECTION | 14.0% |
| PATH_TRAVERSAL | 12.0% |
| SQL_INJECTION | 24.0% |

## Baseline kNN vote (không dùng LLM)

| k | Macro-F1 | Accuracy | FPR Normal |
| ---: | ---: | ---: | ---: |
| 1 | 0.778 | 0.780 | 42.0% |
| 3 | 0.768 | 0.770 | 42.0% |
| 5 | 0.780 | 0.783 | 44.0% |
| 7 | 0.766 | 0.770 | 46.0% |
| 10 | 0.774 | 0.780 | 48.0% |

## LCR@4 của các chiến lược chọn ví dụ (N = 30, λ = 0.1)

Prior kNN (k=5) đúng 78.3% số query.

| Chiến lược | LCR@k trung bình | % query không có ví dụ nào cùng nhãn |
| --- | ---: | ---: |
| B_semantic | 0.727 | 6.7% |
| BAL_class_balanced | 0.410 | 1.3% |
| C_knn_prior | 0.782 | 19.7% |
| C_oracle_prior (analysis only) | 0.956 | 1.0% |

## Quét λ cho C (prior kNN), k = 4

| λ | LCR@k trung bình | % query không có ví dụ nào cùng nhãn |
| ---: | ---: | ---: |
| 0.0 | 0.727 | 6.7% |
| 0.02 | 0.755 | 12.7% |
| 0.05 | 0.775 | 16.3% |
| 0.1 | 0.782 | 19.7% |
| 0.25 | 0.783 | 21.0% |
| 0.5 | 0.783 | 21.0% |
| 1.0 | 0.783 | 21.0% |

LCR@k chỉ là chỉ số chẩn đoán: ví dụ cùng nhãn nhiều hơn chưa chắc giúp LLM đoán đúng hơn.
