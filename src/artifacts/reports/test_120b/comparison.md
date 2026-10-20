# So sánh pipeline trên `test` (300 query)

Tự sinh bởi `src/analysis/compare.py`. Run có kind `mock` dùng LLM giả: chỉ để kiểm tra luồng, không phải kết quả thực nghiệm.

| Run | Pipeline | Kind | Macro-F1 | Accuracy | FPR Normal | Coverage | LCR@k | Lượt LLM/query | Token TB |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A0_zero_shot_120b | A0 | llm | 0.793 | 0.800 | 0.360 | 1.000 | – | 1 | 642 |
| BAL_class_balanced_k4_120b | BAL | llm | 0.862 | 0.863 | 0.340 | 1.000 | 0.416 | 1 | 1503 |
| B_semantic_k4_120b | B | llm | 0.869 | 0.870 | 0.340 | 1.000 | 0.692 | 1 | 1497 |
| C_knn_prior_k4_lambda0.1_120b | C | llm | 0.866 | 0.867 | 0.340 | 1.000 | 0.745 | 1 | 1508 |
| C_llm_prior_k4_lambda0.1_120b | C | llm | 0.854 | 0.857 | 0.360 | 1.000 | 0.828 | 2 | 1502 |
| C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY_120b | C | llm_oracle_analysis | 0.880 | 0.883 | 0.360 | 1.000 | 0.943 | 1 | 1507 |

## Chênh lệch Macro-F1 so với `B_semantic_k4_120b`

| Run | Δ Macro-F1 | CI 95% (bootstrap) | Chỉ run đúng | Chỉ tham chiếu đúng | p McNemar |
| --- | ---: | --- | ---: | ---: | ---: |
| A0_zero_shot_120b | -0.076 | [-0.113; -0.040] | 6 | 27 | 0.000 |
| BAL_class_balanced_k4_120b | -0.006 | [-0.027; +0.013] | 4 | 6 | 0.754 |
| C_knn_prior_k4_lambda0.1_120b | -0.003 | [-0.027; +0.022] | 6 | 7 | 1.000 |
| C_llm_prior_k4_lambda0.1_120b | -0.015 | [-0.041; +0.010] | 5 | 9 | 0.424 |
| C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY_120b | +0.011 | [-0.014; +0.037] | 9 | 5 | 0.424 |

## Prior đúng/sai: `C_knn_prior_k4_lambda0.1_120b` so với `B_semantic_k4_120b`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 224 | 4 | 3 | 207 | 10 |
| prior_wrong | 76 | 2 | 4 | 47 | 23 |

## Prior đúng/sai: `C_llm_prior_k4_lambda0.1_120b` so với `B_semantic_k4_120b`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 240 | 3 | 3 | 231 | 3 |
| prior_wrong | 60 | 2 | 6 | 21 | 31 |

## Prior đúng/sai: `C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY_120b` so với `B_semantic_k4_120b`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 300 | 9 | 5 | 256 | 30 |

## F1 từng lớp

| Run | NORMAL | SQL_INJECTION | PATH_TRAVERSAL | CODE_INJECTION | HTTP_RESPONSE_SPLITTING | OS_COMMAND_INJECTION |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A0_zero_shot_120b | 0.74 | 0.75 | 0.91 | 0.94 | 0.87 | 0.53 |
| BAL_class_balanced_k4_120b | 0.76 | 0.90 | 0.94 | 0.95 | 0.84 | 0.78 |
| B_semantic_k4_120b | 0.76 | 0.90 | 0.94 | 0.93 | 0.88 | 0.80 |
| C_knn_prior_k4_lambda0.1_120b | 0.76 | 0.94 | 0.94 | 0.94 | 0.83 | 0.79 |
| C_llm_prior_k4_lambda0.1_120b | 0.74 | 0.88 | 0.93 | 0.95 | 0.84 | 0.78 |
| C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY_120b | 0.75 | 0.94 | 0.93 | 0.94 | 0.87 | 0.84 |
