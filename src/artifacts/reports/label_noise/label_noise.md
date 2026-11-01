# Nhãn nhiễu ở lớp Normal: phân tích độ nhạy

Số liệu tự sinh bởi `src/analysis/label_noise.py`; không gọi LLM, không sửa nhãn.

"Normal đáng ngờ" = request mang nhãn NORMAL nhưng khớp ít nhất một quy tắc payload tấn công (xem `SUSPICIOUS_RULES`). Danh sách để kiểm tra tay: `flagged_normal.jsonl`.

## 1. Tỷ lệ khớp quy tắc theo lớp

| Tập | NORMAL | SQL_INJECTION | PATH_TRAVERSAL | CODE_INJECTION | HTTP_RESPONSE_SPLITTING | OS_COMMAND_INJECTION |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| pool | 139/500 (27.8%) | 294/500 (58.8%) | 475/500 (95.0%) | 11/500 (2.2%) | 500/500 (100.0%) | 141/500 (28.2%) |
| validation | 7/33 (21.2%) | 20/33 (60.6%) | 31/33 (93.9%) | 1/34 (2.9%) | 34/34 (100.0%) | 7/33 (21.2%) |
| test 1-300 | 15/50 (30.0%) | 34/50 (68.0%) | 49/50 (98.0%) | 0/50 (0.0%) | 50/50 (100.0%) | 16/50 (32.0%) |
| test 301-600 | 14/50 (28.0%) | 35/50 (70.0%) | 46/50 (92.0%) | 1/50 (2.0%) | 50/50 (100.0%) | 10/50 (20.0%) |

Với NORMAL, đây là ước lượng số nhãn sai. Với các lớp tấn công, đây chỉ cho biết quy tắc bắt được bao nhiêu payload (quy tắc hẹp, nên không bắt hết).

Quy tắc khớp nhiều nhất ở Normal trong pool: `shell_command` 95, `sensitive_file` 94, `time_delay` 13, `path_traversal` 7, `header_injection` 4, `script_tag` 3, `sql_keywords` 1.

## 2. Metrics gốc và khi bỏ Normal đáng ngờ

### validation (200 request, 7/33 Normal đáng ngờ bị bỏ)

| Run | Macro-F1 gốc | FPR Normal gốc | F1 Normal gốc | Normal bị báo nhầm (đáng ngờ) | Macro-F1 khi bỏ | FPR khi bỏ | F1 Normal khi bỏ | So với tham chiếu khi bỏ [CI 95%] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| A0_zero_shot | 0.835 | 27.3% | 0.73 | 9 (7) | 0.863 | 7.7% | 0.81 | -0.060 [-0.106; -0.019] |
| A1_fixed_k4 | 0.814 | 27.3% | 0.71 | 9 (7) | 0.841 | 7.7% | 0.79 | -0.082 [-0.133; -0.040] |
| B_semantic_k4 | 0.893 | 30.3% | 0.73 | 10 (7) | 0.923 | 11.5% | 0.82 | (tham chiếu) |
| BAL_class_balanced_k4 | 0.869 | 33.3% | 0.75 | 11 (7) | 0.898 | 15.4% | 0.85 | -0.025 [-0.051; -0.004] |
| C_knn_prior_k4_lambda0.1 | 0.882 | 27.3% | 0.75 | 9 (7) | 0.913 | 7.7% | 0.84 | -0.010 [-0.034; +0.011] |
| C_llm_prior_k4_lambda0.1 | 0.874 | 27.3% | 0.76 | 9 (6) | 0.898 | 11.5% | 0.84 | -0.025 [-0.058; +0.002] |
| C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY | 0.888 | 30.3% | 0.73 | 10 (7) | 0.919 | 11.5% | 0.82 | -0.005 [-0.032; +0.023] |

### test 1-300 (300 request, 15/50 Normal đáng ngờ bị bỏ)

| Run | Macro-F1 gốc | FPR Normal gốc | F1 Normal gốc | Normal bị báo nhầm (đáng ngờ) | Macro-F1 khi bỏ | FPR khi bỏ | F1 Normal khi bỏ | So với tham chiếu khi bỏ [CI 95%] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| A0_zero_shot | 0.834 | 34.0% | 0.73 | 17 (14) | 0.873 | 8.6% | 0.86 | -0.054 [-0.091; -0.021] |
| A1_fixed_k4 | 0.797 | 40.0% | 0.61 | 20 (15) | 0.835 | 14.3% | 0.72 | -0.092 [-0.129; -0.058] |
| B_semantic_k4 | 0.881 | 30.0% | 0.77 | 15 (15) | 0.927 | 0.0% | 0.92 | (tham chiếu) |
| BAL_class_balanced_k4 | 0.865 | 28.0% | 0.76 | 14 (13) | 0.902 | 2.9% | 0.87 | -0.025 [-0.049; -0.002] |
| C_knn_prior_k4_lambda0.1 | 0.862 | 32.0% | 0.73 | 16 (14) | 0.901 | 5.7% | 0.86 | -0.025 [-0.055; +0.001] |
| C_llm_prior_k4_lambda0.1 | 0.861 | 32.0% | 0.76 | 16 (15) | 0.906 | 2.9% | 0.91 | -0.021 [-0.045; +0.001] |
| C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY | 0.900 | 28.0% | 0.78 | 14 (14) | 0.943 | 0.0% | 0.92 | +0.016 [-0.007; +0.039] |

### test 301-600 (300 request, 14/50 Normal đáng ngờ bị bỏ)

| Run | Macro-F1 gốc | FPR Normal gốc | F1 Normal gốc | Normal bị báo nhầm (đáng ngờ) | Macro-F1 khi bỏ | FPR khi bỏ | F1 Normal khi bỏ | So với tham chiếu khi bỏ [CI 95%] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| B_semantic_k4 | 0.869 | 32.0% | 0.71 | 16 (14) | 0.910 | 5.6% | 0.83 | (tham chiếu) |
| C_gated_knn_prior_k4_lambda0.1_share0.7 | 0.882 | 30.0% | 0.74 | 15 (14) | 0.925 | 2.8% | 0.88 | +0.015 [-0.002; +0.033] |
| C_knn_prior_k4_lambda0.1 | 0.873 | 30.0% | 0.71 | 15 (13) | 0.910 | 5.6% | 0.81 | -0.000 [-0.019; +0.019] |

### test 1-300 (gpt-oss-120b) (300 request, 15/50 Normal đáng ngờ bị bỏ)

| Run | Macro-F1 gốc | FPR Normal gốc | F1 Normal gốc | Normal bị báo nhầm (đáng ngờ) | Macro-F1 khi bỏ | FPR khi bỏ | F1 Normal khi bỏ | So với tham chiếu khi bỏ [CI 95%] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| A0_zero_shot_120b | 0.793 | 36.0% | 0.74 | 18 (15) | 0.838 | 8.6% | 0.90 | -0.079 [-0.117; -0.045] |
| B_semantic_k4_120b | 0.869 | 34.0% | 0.76 | 17 (15) | 0.917 | 5.7% | 0.92 | (tham chiếu) |
| BAL_class_balanced_k4_120b | 0.862 | 34.0% | 0.76 | 17 (15) | 0.910 | 5.7% | 0.92 | -0.007 [-0.028; +0.014] |
| C_knn_prior_k4_lambda0.1_120b | 0.866 | 34.0% | 0.76 | 17 (15) | 0.913 | 5.7% | 0.92 | -0.004 [-0.029; +0.020] |
| C_llm_prior_k4_lambda0.1_120b | 0.854 | 36.0% | 0.74 | 18 (15) | 0.902 | 8.6% | 0.90 | -0.015 [-0.042; +0.011] |
| C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY_120b | 0.880 | 36.0% | 0.75 | 18 (15) | 0.929 | 8.6% | 0.91 | +0.012 [-0.014; +0.036] |

## 3. Nhiễm bẩn ví dụ: prompt có ví dụ "NORMAL" chứa payload

| Tập | Run | Query có ≥ 1 ví dụ Normal đáng ngờ | Câu tấn công bị đoán NORMAL: có ví dụ đó | Không có ví dụ đó |
| --- | --- | ---: | ---: | ---: |
| validation | A1_fixed_k4 | 0.0% | 0/0 (–) | 11/167 (6.6%) |
| validation | B_semantic_k4 | 16.0% | 2/21 (9.5%) | 5/146 (3.4%) |
| validation | BAL_class_balanced_k4 | 32.0% | 1/50 (2.0%) | 3/117 (2.6%) |
| validation | C_knn_prior_k4_lambda0.1 | 7.5% | 1/5 (20.0%) | 6/162 (3.7%) |
| validation | C_llm_prior_k4_lambda0.1 | 14.5% | 2/10 (20.0%) | 4/157 (2.5%) |
| validation | C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY | 12.5% | 1/2 (50.0%) | 6/165 (3.6%) |
| test 1-300 | A1_fixed_k4 | 0.0% | 0/0 (–) | 18/250 (7.2%) |
| test 1-300 | B_semantic_k4 | 15.7% | 0/37 (0.0%) | 6/213 (2.8%) |
| test 1-300 | BAL_class_balanced_k4 | 35.7% | 2/92 (2.2%) | 7/158 (4.4%) |
| test 1-300 | C_knn_prior_k4_lambda0.1 | 7.3% | 1/13 (7.7%) | 8/237 (3.4%) |
| test 1-300 | C_llm_prior_k4_lambda0.1 | 7.7% | 0/8 (0.0%) | 6/242 (2.5%) |
| test 1-300 | C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY | 9.7% | 0/4 (0.0%) | 6/246 (2.4%) |
| test 301-600 | B_semantic_k4 | 18.7% | 4/33 (12.1%) | 8/217 (3.7%) |
| test 301-600 | C_gated_knn_prior_k4_lambda0.1_share0.7 | 16.3% | 3/27 (11.1%) | 6/223 (2.7%) |
| test 301-600 | C_knn_prior_k4_lambda0.1 | 6.7% | 1/7 (14.3%) | 13/243 (5.3%) |
| test 1-300 (gpt-oss-120b) | B_semantic_k4_120b | 15.7% | 1/37 (2.7%) | 3/213 (1.4%) |
| test 1-300 (gpt-oss-120b) | BAL_class_balanced_k4_120b | 35.7% | 1/92 (1.1%) | 3/158 (1.9%) |
| test 1-300 (gpt-oss-120b) | C_knn_prior_k4_lambda0.1_120b | 7.3% | 0/13 (0.0%) | 4/237 (1.7%) |
| test 1-300 (gpt-oss-120b) | C_llm_prior_k4_lambda0.1_120b | 6.7% | 1/6 (16.7%) | 3/244 (1.2%) |
| test 1-300 (gpt-oss-120b) | C_oracle_prior_k4_lambda0.1_ANALYSIS_ONLY_120b | 9.7% | 0/4 (0.0%) | 3/246 (1.2%) |

Kết quả chính của đề tài vẫn tính trên nhãn gốc; bảng trên chỉ là phân tích độ nhạy.
