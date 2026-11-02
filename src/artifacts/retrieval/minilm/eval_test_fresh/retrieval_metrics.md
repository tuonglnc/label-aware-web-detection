# Kết quả retrieval và kNN trên `test_fresh` (300 query)

Số liệu tự sinh bởi `src/experiments/eval_retrieval.py`; không gọi LLM.

## RQ1: ví dụ giống nhất có khác nhãn không?

- Tỷ lệ query có ví dụ top-1 KHÁC nhãn: **24.3%**
- Similarity trung bình của top-1: 0.956

| Lớp | Top-1 khác nhãn |
| --- | ---: |
| CODE_INJECTION | 18.0% |
| HTTP_RESPONSE_SPLITTING | 30.0% |
| NORMAL | 44.0% |
| OS_COMMAND_INJECTION | 10.0% |
| PATH_TRAVERSAL | 8.0% |
| SQL_INJECTION | 36.0% |

## Baseline kNN vote (không dùng LLM)

| k | Macro-F1 | Accuracy | FPR Normal |
| ---: | ---: | ---: | ---: |
| 1 | 0.753 | 0.757 | 44.0% |
| 3 | 0.747 | 0.753 | 50.0% |
| 5 | 0.747 | 0.753 | 48.0% |
| 7 | 0.746 | 0.753 | 48.0% |
| 10 | 0.739 | 0.747 | 50.0% |

## LCR@4 của các chiến lược chọn ví dụ (N = 30, λ = 0.1)

Prior kNN (k=5) đúng 75.3% số query.

| Chiến lược | LCR@k trung bình | % query không có ví dụ nào cùng nhãn |
| --- | ---: | ---: |
| B_semantic | 0.691 | 10.3% |
| BAL_class_balanced | 0.399 | 1.7% |
| C_knn_prior | 0.756 | 22.0% |
| C_oracle_prior (analysis only) | 0.950 | 0.7% |

## Quét λ cho C (prior kNN), k = 4

| λ | LCR@k trung bình | % query không có ví dụ nào cùng nhãn |
| ---: | ---: | ---: |
| 0.0 | 0.691 | 10.3% |
| 0.02 | 0.735 | 15.7% |
| 0.05 | 0.752 | 18.3% |
| 0.1 | 0.756 | 22.0% |
| 0.25 | 0.754 | 24.3% |
| 0.5 | 0.754 | 24.3% |
| 1.0 | 0.754 | 24.3% |

LCR@k chỉ là chỉ số chẩn đoán: ví dụ cùng nhãn nhiều hơn chưa chắc giúp LLM đoán đúng hơn.
