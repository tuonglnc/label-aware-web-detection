# So sánh pipeline trên `test_fresh` (300 query)

Tự sinh bởi `src/analysis/compare.py`. Run có kind `mock` dùng LLM giả: chỉ để kiểm tra luồng, không phải kết quả thực nghiệm.

| Run | Pipeline | Kind | Macro-F1 | Accuracy | FPR Normal | Coverage | LCR@k | Lượt LLM/query | Token TB |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A0_zero_shot | A0 | llm | 0.763 | 0.770 | 0.500 | 1.000 | – | 1 | 632 |
| A1_fixed_k4 | A1 | llm | 0.811 | 0.813 | 0.420 | 1.000 | 0.167 | 1 | 1433 |
| BAL_class_balanced_k4 | BAL | llm | 0.833 | 0.837 | 0.440 | 1.000 | 0.399 | 1 | 1492 |
| B_cll_w1.0_k4 | B | llm | 0.834 | 0.837 | 0.340 | 1.000 | 0.445 | 1 | 1505 |
| B_enn_k4 | B | llm | 0.847 | 0.850 | 0.400 | 1.000 | 0.698 | 1 | 1501 |
| B_semantic_k4 | B | llm | 0.833 | 0.837 | 0.460 | 1.000 | 0.691 | 1 | 1494 |
| B_mmr_lambda0.5_k4 | B | llm | 0.858 | 0.860 | 0.400 | 1.000 | 0.648 | 1 | 1497 |
| C_gated_knn_prior_k4_lambda0.1_share0.7 | C | llm | 0.841 | 0.843 | 0.420 | 1.000 | 0.715 | 1 | 1495 |
| C_iter_Bprior_k4_lambda0.1 | C | llm | 0.838 | 0.840 | 0.420 | 1.000 | 0.835 | 2 | 1496 |
| C_knn_prior_enn_k4_lambda0.1 | C | llm | 0.834 | 0.837 | 0.440 | 1.000 | 0.710 | 1 | 1501 |
| C_knn_prior_k4_lambda0.1 | C | llm | 0.854 | 0.857 | 0.380 | 1.000 | 0.756 | 1 | 1495 |
| C_llm_prior_k4_lambda0.1 | C | llm | 0.840 | 0.843 | 0.400 | 1.000 | 0.797 | 2 | 1497 |
| C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY | C | llm_oracle_analysis | 0.866 | 0.870 | 0.440 | 1.000 | 0.950 | 1 | 1492 |
| ENS_vote_B_BAL_Cknn | ENS | llm | 0.833 | 0.837 | 0.460 | 1.000 | – | 3 | 4482 |

## Chênh lệch Macro-F1 so với `B_semantic_k4`

| Run | Δ Macro-F1 | CI 95% (bootstrap) | Chỉ run đúng | Chỉ tham chiếu đúng | p McNemar |
| --- | ---: | --- | ---: | ---: | ---: |
| A0_zero_shot | -0.070 | [-0.106; -0.036] | 5 | 25 | 0.000 |
| A1_fixed_k4 | -0.022 | [-0.051; +0.008] | 7 | 14 | 0.189 |
| BAL_class_balanced_k4 | +0.000 | [-0.027; +0.027] | 7 | 7 | 1.000 |
| B_cll_w1.0_k4 | +0.001 | [-0.032; +0.034] | 13 | 13 | 1.000 |
| B_enn_k4 | +0.014 | [-0.006; +0.035] | 7 | 3 | 0.344 |
| B_mmr_lambda0.5_k4 | +0.025 | [-0.003; +0.053] | 13 | 6 | 0.167 |
| C_gated_knn_prior_k4_lambda0.1_share0.7 | +0.008 | [-0.004; +0.022] | 3 | 1 | 0.625 |
| C_iter_Bprior_k4_lambda0.1 | +0.005 | [-0.010; +0.020] | 3 | 2 | 1.000 |
| C_knn_prior_enn_k4_lambda0.1 | +0.001 | [-0.015; +0.017] | 3 | 3 | 1.000 |
| C_knn_prior_k4_lambda0.1 | +0.021 | [+0.002; +0.042] | 8 | 2 | 0.109 |
| C_llm_prior_k4_lambda0.1 | +0.007 | [-0.014; +0.029] | 6 | 4 | 0.754 |
| C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY | +0.033 | [+0.009; +0.057] | 12 | 2 | 0.013 |
| ENS_vote_B_BAL_Cknn | +0.000 | [-0.000; +0.002] | 0 | 0 | 1.000 |

## Prior đúng/sai: `C_gated_knn_prior_k4_lambda0.1_share0.7` so với `B_semantic_k4`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 226 | 0 | 0 | 209 | 17 |
| prior_wrong | 74 | 3 | 1 | 41 | 29 |

## Prior đúng/sai: `C_iter_Bprior_k4_lambda0.1` so với `B_semantic_k4`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 251 | 0 | 2 | 249 | 0 |
| prior_wrong | 49 | 3 | 0 | 0 | 46 |

## Prior đúng/sai: `C_knn_prior_enn_k4_lambda0.1` so với `B_semantic_k4`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 213 | 1 | 1 | 199 | 12 |
| prior_wrong | 87 | 2 | 2 | 49 | 34 |

## Prior đúng/sai: `C_knn_prior_k4_lambda0.1` so với `B_semantic_k4`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 226 | 3 | 0 | 209 | 14 |
| prior_wrong | 74 | 5 | 2 | 40 | 27 |

## Prior đúng/sai: `C_llm_prior_k4_lambda0.1` so với `B_semantic_k4`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 231 | 1 | 0 | 226 | 4 |
| prior_wrong | 69 | 5 | 4 | 21 | 39 |

## Prior đúng/sai: `C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY` so với `B_semantic_k4`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 300 | 12 | 2 | 249 | 37 |

## F1 từng lớp

| Run | NORMAL | SQL_INJECTION | PATH_TRAVERSAL | CODE_INJECTION | HTTP_RESPONSE_SPLITTING | OS_COMMAND_INJECTION |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A0_zero_shot | 0.59 | 0.76 | 0.81 | 0.87 | 0.91 | 0.65 |
| A1_fixed_k4 | 0.62 | 0.84 | 0.86 | 0.86 | 0.95 | 0.74 |
| BAL_class_balanced_k4 | 0.62 | 0.82 | 0.87 | 0.93 | 0.94 | 0.83 |
| B_cll_w1.0_k4 | 0.66 | 0.79 | 0.92 | 0.95 | 0.96 | 0.73 |
| B_enn_k4 | 0.66 | 0.84 | 0.89 | 0.92 | 0.95 | 0.82 |
| B_semantic_k4 | 0.60 | 0.84 | 0.85 | 0.93 | 0.94 | 0.84 |
| B_mmr_lambda0.5_k4 | 0.67 | 0.88 | 0.90 | 0.94 | 0.93 | 0.83 |
| C_gated_knn_prior_k4_lambda0.1_share0.7 | 0.64 | 0.85 | 0.87 | 0.93 | 0.93 | 0.83 |
| C_iter_Bprior_k4_lambda0.1 | 0.65 | 0.84 | 0.88 | 0.93 | 0.93 | 0.79 |
| C_knn_prior_enn_k4_lambda0.1 | 0.62 | 0.83 | 0.87 | 0.94 | 0.94 | 0.81 |
| C_knn_prior_k4_lambda0.1 | 0.66 | 0.83 | 0.87 | 0.97 | 0.95 | 0.85 |
| C_llm_prior_k4_lambda0.1 | 0.67 | 0.80 | 0.87 | 0.94 | 0.95 | 0.80 |
| C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY | 0.64 | 0.88 | 0.89 | 0.96 | 0.98 | 0.84 |
| ENS_vote_B_BAL_Cknn | 0.59 | 0.84 | 0.85 | 0.94 | 0.94 | 0.84 |
