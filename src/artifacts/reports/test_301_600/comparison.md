# So sánh pipeline trên `test` (300 query)

Tự sinh bởi `src/analysis/compare.py`. Run có kind `mock` dùng LLM giả: chỉ để kiểm tra luồng, không phải kết quả thực nghiệm.

| Run | Pipeline | Kind | Macro-F1 | Accuracy | FPR Normal | Coverage | LCR@k | Lượt LLM/query | Token TB |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B_semantic_k4 | B | llm | 0.869 | 0.870 | 0.320 | 1.000 | 0.727 | 1 | 1487 |
| C_gated_knn_prior_k4_lambda0.1_share0.7 | C | llm | 0.882 | 0.883 | 0.300 | 1.000 | 0.741 | 1 | 1489 |
| C_knn_prior_k4_lambda0.1 | C | llm | 0.873 | 0.873 | 0.300 | 1.000 | 0.782 | 1 | 1489 |

## Chênh lệch Macro-F1 so với `B_semantic_k4`

| Run | Δ Macro-F1 | CI 95% (bootstrap) | Chỉ run đúng | Chỉ tham chiếu đúng | p McNemar |
| --- | ---: | --- | ---: | ---: | ---: |
| C_gated_knn_prior_k4_lambda0.1_share0.7 | +0.013 | [-0.002; +0.030] | 5 | 1 | 0.219 |
| C_knn_prior_k4_lambda0.1 | +0.004 | [-0.015; +0.025] | 5 | 4 | 1.000 |

## Prior đúng/sai: `C_gated_knn_prior_k4_lambda0.1_share0.7` so với `B_semantic_k4`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 235 | 4 | 0 | 215 | 16 |
| prior_wrong | 65 | 1 | 1 | 45 | 18 |

## Prior đúng/sai: `C_knn_prior_k4_lambda0.1` so với `B_semantic_k4`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 235 | 4 | 0 | 215 | 16 |
| prior_wrong | 65 | 1 | 4 | 42 | 18 |

## F1 từng lớp

| Run | NORMAL | SQL_INJECTION | PATH_TRAVERSAL | CODE_INJECTION | HTTP_RESPONSE_SPLITTING | OS_COMMAND_INJECTION |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| B_semantic_k4 | 0.71 | 0.93 | 0.88 | 0.96 | 0.93 | 0.81 |
| C_gated_knn_prior_k4_lambda0.1_share0.7 | 0.74 | 0.93 | 0.90 | 0.95 | 0.94 | 0.84 |
| C_knn_prior_k4_lambda0.1 | 0.71 | 0.92 | 0.87 | 0.96 | 0.93 | 0.85 |
