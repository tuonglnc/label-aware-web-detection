# So sánh pipeline trên `test` (300 query)

Tự sinh bởi `src/analysis/compare.py`. Run có kind `mock` dùng LLM giả: chỉ để kiểm tra luồng, không phải kết quả thực nghiệm.

| Run | Pipeline | Kind | Macro-F1 | Accuracy | FPR Normal | Coverage | LCR@k | Lượt LLM/query | Token TB |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A0_zero_shot | A0 | llm | 0.834 | 0.833 | 0.340 | 1.000 | – | 1 | 630 |
| A1_fixed_k4 | A1 | llm | 0.797 | 0.797 | 0.400 | 1.000 | 0.167 | 1 | 1431 |
| BAL_class_balanced_k4 | BAL | llm | 0.865 | 0.863 | 0.280 | 1.000 | 0.416 | 1 | 1486 |
| B_semantic_k4 | B | llm | 0.881 | 0.880 | 0.300 | 1.000 | 0.692 | 1 | 1487 |
| C_knn_prior_k4_lambda0.1 | C | llm | 0.862 | 0.860 | 0.320 | 1.000 | 0.745 | 1 | 1488 |
| C_llm_prior_k4_lambda0.1 | C | llm | 0.861 | 0.860 | 0.320 | 1.000 | 0.845 | 2 | 1490 |
| C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY | C | llm_oracle_analysis | 0.900 | 0.900 | 0.280 | 1.000 | 0.943 | 1 | 1487 |

## Chênh lệch Macro-F1 so với `B_semantic_k4`

| Run | Δ Macro-F1 | CI 95% (bootstrap) | Chỉ run đúng | Chỉ tham chiếu đúng | p McNemar |
| --- | ---: | --- | ---: | ---: | ---: |
| A0_zero_shot | -0.047 | [-0.081; -0.016] | 5 | 19 | 0.007 |
| A1_fixed_k4 | -0.084 | [-0.118; -0.051] | 2 | 27 | 0.000 |
| BAL_class_balanced_k4 | -0.016 | [-0.041; +0.008] | 5 | 10 | 0.302 |
| C_knn_prior_k4_lambda0.1 | -0.019 | [-0.047; +0.008] | 7 | 13 | 0.263 |
| C_llm_prior_k4_lambda0.1 | -0.020 | [-0.042; -0.002] | 2 | 8 | 0.109 |
| C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY | +0.019 | [-0.003; +0.043] | 10 | 4 | 0.180 |

## Prior đúng/sai: `C_knn_prior_k4_lambda0.1` so với `B_semantic_k4`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 224 | 5 | 2 | 209 | 8 |
| prior_wrong | 76 | 2 | 11 | 42 | 21 |

## Prior đúng/sai: `C_llm_prior_k4_lambda0.1` so với `B_semantic_k4`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 250 | 1 | 1 | 244 | 4 |
| prior_wrong | 50 | 1 | 7 | 12 | 30 |

## Prior đúng/sai: `C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY` so với `B_semantic_k4`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 300 | 10 | 4 | 260 | 26 |

## F1 từng lớp

| Run | NORMAL | SQL_INJECTION | PATH_TRAVERSAL | CODE_INJECTION | HTTP_RESPONSE_SPLITTING | OS_COMMAND_INJECTION |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A0_zero_shot | 0.73 | 0.93 | 0.91 | 0.94 | 0.81 | 0.68 |
| A1_fixed_k4 | 0.61 | 0.92 | 0.86 | 0.89 | 0.83 | 0.67 |
| BAL_class_balanced_k4 | 0.76 | 0.92 | 0.94 | 0.92 | 0.89 | 0.76 |
| B_semantic_k4 | 0.77 | 0.94 | 0.94 | 0.96 | 0.89 | 0.79 |
| C_knn_prior_k4_lambda0.1 | 0.73 | 0.93 | 0.91 | 0.94 | 0.88 | 0.78 |
| C_llm_prior_k4_lambda0.1 | 0.76 | 0.93 | 0.92 | 0.96 | 0.84 | 0.76 |
| C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY | 0.78 | 0.96 | 0.94 | 0.97 | 0.92 | 0.83 |
