# So sánh pipeline trên `validation` (200 query)

Tự sinh bởi `src/analysis/compare.py`. Run có kind `mock` dùng LLM giả: chỉ để kiểm tra luồng, không phải kết quả thực nghiệm.

| Run | Pipeline | Kind | Macro-F1 | Accuracy | FPR Normal | Coverage | LCR@k | Lượt LLM/query | Token TB |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A0_zero_shot | A0 | llm | 0.835 | 0.835 | 0.273 | 1.000 | – | 1 | 637 |
| A1_fixed_k4 | A1 | llm | 0.814 | 0.815 | 0.273 | 1.000 | 0.166 | 1 | 1436 |
| BAL_class_balanced_k4 | BAL | llm | 0.869 | 0.870 | 0.333 | 1.000 | 0.400 | 1 | 1496 |
| B_cll_w1.0_k4 | B | llm | 0.809 | 0.815 | 0.273 | 1.000 | 0.430 | 1 | 1505 |
| B_enn_k4 | B | llm | 0.869 | 0.870 | 0.303 | 1.000 | 0.724 | 1 | 1501 |
| B_semantic_k4 | B | llm | 0.893 | 0.895 | 0.303 | 1.000 | 0.726 | 1 | 1497 |
| B_mmr_lambda0.5_k4 | B | llm | 0.857 | 0.860 | 0.333 | 1.000 | 0.640 | 1 | 1499 |
| C_gated_knn_prior_k4_lambda0.1_share0.7 | C | llm | 0.888 | 0.890 | 0.273 | 1.000 | 0.752 | 1 | 1497 |
| C_iter_Bprior_k4_lambda0.1 | C | llm | 0.868 | 0.870 | 0.333 | 1.000 | 0.889 | 2 | 1496 |
| C_knn_prior_enn_k4_lambda0.1 | C | llm | 0.849 | 0.850 | 0.303 | 1.000 | 0.771 | 1 | 1505 |
| C_knn_prior_k4_lambda0.1 | C | llm | 0.882 | 0.885 | 0.273 | 1.000 | 0.809 | 1 | 1498 |
| C_llm_prior_k4_lambda0.1 | C | llm | 0.874 | 0.875 | 0.273 | 1.000 | 0.860 | 2 | 1499 |
| C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY | C | llm_oracle_analysis | 0.888 | 0.890 | 0.303 | 1.000 | 0.963 | 1 | 1496 |
| ENS_vote_B_BAL_Cknn | ENS | llm | 0.893 | 0.895 | 0.303 | 1.000 | – | 3 | 4491 |

## Chênh lệch Macro-F1 so với `B_semantic_k4`

| Run | Δ Macro-F1 | CI 95% (bootstrap) | Chỉ run đúng | Chỉ tham chiếu đúng | p McNemar |
| --- | ---: | --- | ---: | ---: | ---: |
| A0_zero_shot | -0.057 | [-0.098; -0.018] | 3 | 15 | 0.008 |
| A1_fixed_k4 | -0.078 | [-0.124; -0.038] | 2 | 18 | 0.000 |
| BAL_class_balanced_k4 | -0.024 | [-0.048; -0.004] | 0 | 5 | 0.062 |
| B_cll_w1.0_k4 | -0.084 | [-0.129; -0.046] | 2 | 18 | 0.000 |
| B_enn_k4 | -0.024 | [-0.051; +0.001] | 1 | 6 | 0.125 |
| B_mmr_lambda0.5_k4 | -0.036 | [-0.068; -0.008] | 1 | 8 | 0.039 |
| C_gated_knn_prior_k4_lambda0.1_share0.7 | -0.005 | [-0.024; +0.011] | 1 | 2 | 1.000 |
| C_iter_Bprior_k4_lambda0.1 | -0.025 | [-0.050; -0.006] | 0 | 5 | 0.062 |
| C_knn_prior_enn_k4_lambda0.1 | -0.044 | [-0.078; -0.014] | 1 | 10 | 0.012 |
| C_knn_prior_k4_lambda0.1 | -0.010 | [-0.034; +0.009] | 1 | 3 | 0.625 |
| C_llm_prior_k4_lambda0.1 | -0.019 | [-0.047; +0.008] | 2 | 6 | 0.289 |
| C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY | -0.005 | [-0.032; +0.022] | 3 | 4 | 1.000 |
| ENS_vote_B_BAL_Cknn | -0.000 | [-0.003; +0.002] | 0 | 0 | 1.000 |

## Prior đúng/sai: `C_gated_knn_prior_k4_lambda0.1_share0.7` so với `B_semantic_k4`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 162 | 1 | 1 | 152 | 8 |
| prior_wrong | 38 | 0 | 1 | 25 | 12 |

## Prior đúng/sai: `C_iter_Bprior_k4_lambda0.1` so với `B_semantic_k4`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 179 | 0 | 5 | 174 | 0 |
| prior_wrong | 21 | 0 | 0 | 0 | 21 |

## Prior đúng/sai: `C_knn_prior_enn_k4_lambda0.1` so với `B_semantic_k4`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 154 | 1 | 4 | 144 | 5 |
| prior_wrong | 46 | 0 | 6 | 25 | 15 |

## Prior đúng/sai: `C_knn_prior_k4_lambda0.1` so với `B_semantic_k4`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 162 | 1 | 0 | 153 | 8 |
| prior_wrong | 38 | 0 | 3 | 23 | 12 |

## Prior đúng/sai: `C_llm_prior_k4_lambda0.1` so với `B_semantic_k4`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 167 | 0 | 2 | 162 | 3 |
| prior_wrong | 33 | 2 | 4 | 11 | 16 |

## Prior đúng/sai: `C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY` so với `B_semantic_k4`

| Nhóm | n | C sửa lỗi của B | C làm hỏng | Cả hai đúng | Cả hai sai |
| --- | ---: | ---: | ---: | ---: | ---: |
| prior_correct | 200 | 3 | 4 | 175 | 18 |

## F1 từng lớp

| Run | NORMAL | SQL_INJECTION | PATH_TRAVERSAL | CODE_INJECTION | HTTP_RESPONSE_SPLITTING | OS_COMMAND_INJECTION |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A0_zero_shot | 0.73 | 0.81 | 0.92 | 0.96 | 0.89 | 0.72 |
| A1_fixed_k4 | 0.71 | 0.78 | 0.92 | 0.89 | 0.92 | 0.68 |
| BAL_class_balanced_k4 | 0.75 | 0.84 | 0.96 | 0.94 | 0.97 | 0.75 |
| B_cll_w1.0_k4 | 0.72 | 0.72 | 0.97 | 0.88 | 0.96 | 0.61 |
| B_enn_k4 | 0.73 | 0.81 | 0.99 | 0.96 | 0.97 | 0.76 |
| B_semantic_k4 | 0.73 | 0.87 | 0.97 | 0.99 | 0.97 | 0.83 |
| B_mmr_lambda0.5_k4 | 0.73 | 0.79 | 0.96 | 0.93 | 0.94 | 0.79 |
| C_gated_knn_prior_k4_lambda0.1_share0.7 | 0.77 | 0.85 | 0.99 | 0.94 | 0.97 | 0.80 |
| C_iter_Bprior_k4_lambda0.1 | 0.71 | 0.85 | 0.94 | 0.96 | 0.95 | 0.79 |
| C_knn_prior_enn_k4_lambda0.1 | 0.73 | 0.81 | 0.96 | 0.93 | 0.92 | 0.75 |
| C_knn_prior_k4_lambda0.1 | 0.75 | 0.83 | 0.97 | 0.94 | 0.99 | 0.82 |
| C_llm_prior_k4_lambda0.1 | 0.76 | 0.84 | 0.96 | 0.94 | 0.95 | 0.78 |
| C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY | 0.73 | 0.87 | 0.97 | 0.97 | 0.99 | 0.81 |
| ENS_vote_B_BAL_Cknn | 0.75 | 0.87 | 0.97 | 0.97 | 0.97 | 0.82 |
