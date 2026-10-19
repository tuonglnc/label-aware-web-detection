# Kết quả retrieval và kNN trên `development` (30 query)

Số liệu tự sinh bởi `src/experiments/eval_retrieval.py`; không gọi LLM.

## RQ1: ví dụ giống nhất có khác nhãn không?

- Tỷ lệ query có ví dụ top-1 KHÁC nhãn: **6.7%**
- Similarity trung bình của top-1: 0.962

| Lớp | Top-1 khác nhãn |
| --- | ---: |
| CODE_INJECTION | 0.0% |
| HTTP_RESPONSE_SPLITTING | 20.0% |
| NORMAL | 20.0% |
| OS_COMMAND_INJECTION | 0.0% |
| PATH_TRAVERSAL | 0.0% |
| SQL_INJECTION | 0.0% |

## Baseline kNN vote (không dùng LLM)

| k | Macro-F1 | Accuracy | FPR Normal |
| ---: | ---: | ---: | ---: |
| 1 | 0.933 | 0.933 | 20.0% |
| 3 | 0.765 | 0.800 | 40.0% |
| 5 | 0.760 | 0.800 | 40.0% |
| 7 | 0.895 | 0.900 | 20.0% |
| 10 | 0.863 | 0.867 | 20.0% |

## LCR@4 của các chiến lược chọn ví dụ (N = 30, λ = 0.1)

Prior kNN (k=5) đúng 80.0% số query.

| Chiến lược | LCR@k trung bình | % query không có ví dụ nào cùng nhãn |
| --- | ---: | ---: |
| B_semantic | 0.775 | 3.3% |
| BAL_class_balanced | 0.458 | 0.0% |
| C_knn_prior | 0.783 | 16.7% |
| C_oracle_prior (analysis only) | 0.958 | 0.0% |

## Quét λ cho C (prior kNN), k = 4

| λ | LCR@k trung bình | % query không có ví dụ nào cùng nhãn |
| ---: | ---: | ---: |
| 0.0 | 0.775 | 3.3% |
| 0.02 | 0.800 | 6.7% |
| 0.05 | 0.792 | 10.0% |
| 0.1 | 0.783 | 16.7% |
| 0.25 | 0.800 | 20.0% |
| 0.5 | 0.800 | 20.0% |
| 1.0 | 0.800 | 20.0% |

LCR@k chỉ là chỉ số chẩn đoán: ví dụ cùng nhãn nhiều hơn chưa chắc giúp LLM đoán đúng hơn.
