# Kết quả retrieval và kNN trên `test` (300 query)

Số liệu tự sinh bởi `src/experiments/eval_retrieval.py`; không gọi LLM.

## RQ1: ví dụ giống nhất có khác nhãn không?

- Tỷ lệ query có ví dụ top-1 KHÁC nhãn: **24.3%**
- Similarity trung bình của top-1: 0.956

| Lớp | Top-1 khác nhãn |
| --- | ---: |
| CODE_INJECTION | 18.0% |
| HTTP_RESPONSE_SPLITTING | 28.0% |
| NORMAL | 38.0% |
| OS_COMMAND_INJECTION | 6.0% |
| PATH_TRAVERSAL | 16.0% |
| SQL_INJECTION | 40.0% |

## Baseline kNN vote (không dùng LLM)

| k | Macro-F1 | Accuracy | FPR Normal |
| ---: | ---: | ---: | ---: |
| 1 | 0.758 | 0.757 | 38.0% |
| 3 | 0.727 | 0.730 | 44.0% |
| 5 | 0.742 | 0.747 | 52.0% |
| 7 | 0.754 | 0.760 | 54.0% |
| 10 | 0.753 | 0.757 | 48.0% |

## LCR@4 của các chiến lược chọn ví dụ (N = 30, λ = 0.1)

Prior kNN (k=5) đúng 74.7% số query.

| Chiến lược | LCR@k trung bình | % query không có ví dụ nào cùng nhãn |
| --- | ---: | ---: |
| B_semantic | 0.692 | 8.3% |
| BAL_class_balanced | 0.416 | 2.0% |
| C_knn_prior | 0.745 | 23.3% |
| C_oracle_prior (analysis only) | 0.943 | 1.0% |

## Quét λ cho C (prior kNN), k = 4

| λ | LCR@k trung bình | % query không có ví dụ nào cùng nhãn |
| ---: | ---: | ---: |
| 0.0 | 0.692 | 8.3% |
| 0.02 | 0.726 | 15.7% |
| 0.05 | 0.746 | 19.7% |
| 0.1 | 0.745 | 23.3% |
| 0.25 | 0.748 | 24.7% |
| 0.5 | 0.748 | 24.7% |
| 1.0 | 0.748 | 24.7% |

LCR@k chỉ là chỉ số chẩn đoán: ví dụ cùng nhãn nhiều hơn chưa chắc giúp LLM đoán đúng hơn.
