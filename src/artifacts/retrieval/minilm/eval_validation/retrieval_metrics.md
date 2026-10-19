# Kết quả retrieval và kNN trên `validation` (200 query)

Số liệu tự sinh bởi `src/experiments/eval_retrieval.py`; không gọi LLM.

## RQ1: ví dụ giống nhất có khác nhãn không?

- Tỷ lệ query có ví dụ top-1 KHÁC nhãn: **23.0%**
- Similarity trung bình của top-1: 0.956

| Lớp | Top-1 khác nhãn |
| --- | ---: |
| CODE_INJECTION | 11.8% |
| HTTP_RESPONSE_SPLITTING | 14.7% |
| NORMAL | 45.5% |
| OS_COMMAND_INJECTION | 6.1% |
| PATH_TRAVERSAL | 21.2% |
| SQL_INJECTION | 39.4% |

## Baseline kNN vote (không dùng LLM)

| k | Macro-F1 | Accuracy | FPR Normal |
| ---: | ---: | ---: | ---: |
| 1 | 0.768 | 0.770 | 45.5% |
| 3 | 0.805 | 0.815 | 42.4% |
| 5 | 0.800 | 0.810 | 45.5% |
| 7 | 0.801 | 0.810 | 42.4% |
| 10 | 0.800 | 0.810 | 45.5% |

## LCR@4 của các chiến lược chọn ví dụ (N = 30, λ = 0.1)

Prior kNN (k=5) đúng 81.0% số query.

| Chiến lược | LCR@k trung bình | % query không có ví dụ nào cùng nhãn |
| --- | ---: | ---: |
| B_semantic | 0.726 | 7.0% |
| BAL_class_balanced | 0.400 | 0.0% |
| C_knn_prior | 0.809 | 16.5% |
| C_oracle_prior (analysis only) | 0.963 | 0.0% |

## Quét λ cho C (prior kNN), k = 4

| λ | LCR@k trung bình | % query không có ví dụ nào cùng nhãn |
| ---: | ---: | ---: |
| 0.0 | 0.726 | 7.0% |
| 0.02 | 0.779 | 10.5% |
| 0.05 | 0.795 | 14.0% |
| 0.1 | 0.809 | 16.5% |
| 0.25 | 0.814 | 17.5% |
| 0.5 | 0.814 | 17.5% |
| 1.0 | 0.814 | 17.5% |

LCR@k chỉ là chỉ số chẩn đoán: ví dụ cùng nhãn nhiều hơn chưa chắc giúp LLM đoán đúng hơn.
