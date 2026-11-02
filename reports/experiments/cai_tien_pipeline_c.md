# Vòng cải tiến Pipeline C: thử các phương pháp đã công bố

Ngày thực hiện: 02/11/2026. Nhánh: `test/c-improvements`. Model: `openai/gpt-oss-20b` qua Groq; k = 4, N = 30, mỗi ví dụ tối đa 500 ký tự, giống thí nghiệm chính.

## Tóm tắt

- Thử **6 cách chọn ví dụ đã được công bố** (MMR, CLL-RetICL, Wilson-ENN cho B và cho C, vòng lặp kiểu IDS, bỏ phiếu đa số) cùng C-gated. Tham số lấy đúng giá trị mặc định của bài gốc, không chỉnh trên test.
- Đánh giá cuối trên **một tập test mới 300 request** (`test_fresh`), chưa từng dùng. Toàn bộ pipeline cũ được **chạy lại** trên tập này. Cấu hình và giả thuyết được khóa và đẩy lên GitHub **trước** khi chạy (commit `7391294`).
- **Không phương pháp nào vượt B có ý nghĩa thống kê** sau hiệu chỉnh Holm. B-MMR cao nhất trên tập mới (+0,025, p Holm = 1,0), nhưng trên validation lại thấp hơn B 0,036, nên không ổn định.
- Gộp 3 tập test độc lập (900 request):
  - **C-kNN ngang B**: C đúng riêng 20 câu, B đúng riêng 19 câu.
  - **C-oracle (prior luôn đúng) hơn B có ý nghĩa**: +0,026, p = 0,004 trên 600 request.
  - Tức là cách cộng điểm theo nhãn **có tác dụng khi nhãn dự đoán đúng**; **nút thắt là chất lượng nhãn dự đoán**.
- **C-gated** nhỉnh hơn B ở cả hai tập test nó được chạy: +0,013 và +0,008; gộp 600 request là +0,010, CI [−0,000; +0,021]. Đây là hướng hứa hẹn nhất nhưng **chưa đủ bằng chứng**.
- **Cùng một prompt, chạy lại cho câu trả lời khác** (6/200 và 5/300 câu); Macro-F1 lệch khoảng 0,011. Chênh lệch dưới mức này không nên diễn giải.

## 1. Mục tiêu và nguyên tắc

Pipeline C (cộng điểm cho ví dụ trùng nhãn dự đoán sơ bộ) chưa vượt B trên tập test chính. Vòng này thử các cách chọn ví dụ **đã được công bố** ở hội nghị/tạp chí, xem có cách nào cải thiện được C hoặc B không.

1. **Chỉ dùng phương pháp có nguồn rõ ràng.** Ghi rõ bài gốc, nơi công bố, phần nào nhóm làm khác.
2. **Không chỉnh tham số trên test.** Bài gốc có giá trị mặc định thì dùng đúng giá trị đó.
3. **Đánh giá cuối trên tập test mới** `test_fresh`: 300 request, 50/lớp, lấy từ `test.jsonl`, không trùng request hay nhóm với 600 request test cũ, mỗi nhóm tối đa 1 request (`src/preprocessing/make_fresh_test.py`).
4. **Chạy lại toàn bộ** pipeline cũ trên `test_fresh`, để mọi phương pháp được so trên cùng dữ liệu.
5. **Hiệu chỉnh Holm** khi so nhiều phương pháp với B. Kế hoạch đánh giá được khóa trước: [cau_hinh_khoa_cai_tien.md](cau_hinh_khoa_cai_tien.md).

## 2. Các phương pháp và nguồn

| Mã | Phương pháp | Nguồn | Cách nhóm áp dụng | Khác bài gốc |
| --- | --- | --- | --- | --- |
| C-gated | Chỉ dùng nhãn dự đoán khi đủ tự tin, ngược lại dùng B | Selective classification (Geifman & El-Yaniv, NeurIPS 2017) | Độ tự tin = tỷ lệ phiếu kNN; ngưỡng 0,7 khóa trên validation | Bài gốc từ chối trả lời; ở đây quay về B |
| B-MMR | Maximal Marginal Relevance: vừa giống query vừa đa dạng | Carbonell & Goldstein (SIGIR 1998); dùng cho chọn ví dụ ICL bởi Ye và cộng sự (Findings of ACL 2023, phương trình 1) | λ = 0,5 như Ye và cộng sự | Bài gốc đo độ giống bằng BERTScore; nhóm dùng cosine MiniLM |
| B-CLL | CLL-RetICL: cộng điểm ví dụ giống tên nhãn của nó hơn tên các nhãn khác | Lin và cộng sự (Findings of IJCNLP-AACL 2025, phương trình 2) | w1 = 1,0 (mặc định của bài), cùng MiniLM và cosine | Bài gốc chọn N-way K-shot; nhóm giữ k = 4 cho công bằng |
| B-ENN | Bỏ ví dụ pool nghi sai nhãn | Edited Nearest Neighbor (Wilson, IEEE Trans. SMC 1972); động cơ: nhãn nhiễu làm ICL kém (Kang và cộng sự, 2024) | Bỏ ví dụ mà luật 3-NN trong pool đoán khác nhãn; 724/3.000 bị bỏ | Không |
| C-kNN-ENN | C-kNN trên pool đã làm sạch | Wilson (1972) | Prior kNN và ví dụ đều lấy từ ứng viên đã làm sạch | Không |
| C-iter | Lấy câu trả lời của B làm nhãn dự đoán cho C | Ý tưởng lặp của IDS (Qin và cộng sự, Findings of EMNLP 2024) | Vòng 1 = B, vòng 2 = C với prior = nhãn B trả về | Bài gốc dùng chain-of-thought, nhiều vòng, bỏ phiếu |
| ENS | Bỏ phiếu đa số giữa nhiều bộ ví dụ | Dietterich (MCS 2000); Khalifa và cộng sự (ME-FoMo @ ICLR 2023); Wang và cộng sự (ICLR 2023) | Đa số của B, BAL, C-kNN; hòa theo B | Groq không trả xác suất nhãn nên dùng bỏ phiếu |

Code: `src/retrieval/selectors.py` (`mmr_select`, `label_term_rerank`, `drop_flagged`), `src/retrieval/pool_aux.py` (ENN, số hạng CLL), `src/analysis/ensemble.py`, cấu hình trong `src/configs/experiments/`.

## 3. Validation (200 request), dùng để chọn trước khi khóa

| Run | Macro-F1 | LCR@4 |
| --- | ---: | ---: |
| B (tham chiếu) | **0,893** | 0,726 |
| ENS | 0,893 | – |
| C-gated | 0,888 | 0,752 |
| C-kNN | 0,882 | 0,809 |
| **B chạy lại, cùng prompt** | **0,882** | 0,726 |
| B-ENN | 0,869 | 0,724 |
| C-iter | 0,868 | 0,889 |
| B-MMR | 0,857 | 0,640 |
| C-kNN-ENN | 0,849 | 0,771 |
| B-CLL | 0,809 | 0,430 |

Trên validation không phương pháp nào vượt B. Chạy lại B với đúng prompt cũ thì 6/200 câu trả lời khác và Macro-F1 giảm 0,011: dù temperature = 0, LLM qua API vẫn không hoàn toàn tất định. Bảng đầy đủ: `src/artifacts/reports/validation_improve/comparison.md`.

Riêng CLL-RetICL, quét w1 không cần LLM cho thấy LCR@4 chỉ giảm khi w1 tăng (0,726 ở w1 = 0 xuống 0,430 ở w1 = 1). Nghĩa là tên nhãn ("SQL Injection"…) không phải điểm neo tốt cho nội dung HTTP. Nhóm vẫn chạy w1 = 1,0 để tái hiện đúng bài gốc.

## 4. Tập test mới `test_fresh` (300 request, chạy sau khi khóa)

### 4.1. Toàn bộ pipeline

| Run | Macro-F1 | Δ so với B | CI 95% | FPR Normal | Lượt LLM/query |
| --- | ---: | ---: | --- | ---: | ---: |
| kNN (không LLM, k = 5) | 0,747 | – | – | 48,0% | 0 |
| A0 zero-shot | 0,763 | −0,070 | [−0,106; −0,036] | 50,0% | 1 |
| A1 ví dụ cố định | 0,811 | −0,022 | [−0,051; +0,008] | 42,0% | 1 |
| **B** (tham chiếu) | **0,833** | – | – | 46,0% | 1 |
| B chạy lại, cùng prompt | 0,844 | +0,011 | – | – | 1 |
| BAL | 0,833 | +0,000 | [−0,027; +0,027] | 44,0% | 1 |
| C-kNN | 0,854 | +0,021 | [+0,002; +0,042] | 38,0% | 1 |
| C-LLM | 0,840 | +0,007 | [−0,014; +0,029] | 40,0% | 2 |
| C-oracle (phân tích) | 0,866 | +0,033 | [+0,009; +0,057] | 44,0% | 1 |
| C-gated | 0,841 | +0,008 | [−0,004; +0,022] | 42,0% | 1 |
| B-MMR | 0,858 | +0,025 | [−0,003; +0,053] | 40,0% | 1 |
| B-CLL | 0,834 | +0,001 | [−0,032; +0,034] | 34,0% | 1 |
| B-ENN | 0,847 | +0,014 | [−0,006; +0,035] | 40,0% | 1 |
| C-kNN-ENN | 0,834 | +0,001 | [−0,015; +0,017] | 44,0% | 1 |
| C-iter | 0,838 | +0,005 | [−0,010; +0,020] | 42,0% | 2 |
| ENS | 0,833 | +0,000 | [−0,000; +0,002] | 46,0% | 3 |

Nguồn: `src/artifacts/reports/test_fresh/comparison.md` (kèm F1 từng lớp, bảng nhãn dự đoán đúng/sai, ma trận nhầm lẫn).

### 4.2. Kiểm định đã đăng ký trước (McNemar, hiệu chỉnh Holm cho 7 phép so)

| Phương pháp | Δ Macro-F1 | Chỉ PP đúng | Chỉ B đúng | p McNemar | p Holm |
| --- | ---: | ---: | ---: | ---: | ---: |
| C-gated | +0,008 | 3 | 1 | 0,625 | 1,000 |
| B-MMR | +0,025 | 13 | 6 | 0,167 | 1,000 |
| B-CLL | +0,001 | 13 | 13 | 1,000 | 1,000 |
| B-ENN | +0,014 | 7 | 3 | 0,344 | 1,000 |
| C-kNN-ENN | +0,001 | 3 | 3 | 1,000 | 1,000 |
| C-iter | +0,005 | 3 | 2 | 1,000 | 1,000 |
| ENS | +0,000 | 0 | 0 | 1,000 | 1,000 |

### 4.3. Đối chiếu với giả thuyết đã khóa

| Giả thuyết | Kết quả |
| --- | --- |
| H1: không phương pháp cải tiến nào vượt B có ý nghĩa sau Holm | **Đúng**: mọi p Holm = 1,000 |
| H2: B-CLL kém B | **Sai**: trên `test_fresh` B-CLL bằng B (+0,001; 13 câu mỗi bên). Validation thấp hơn 0,084 nhưng không lặp lại |
| H3: B hơn A0 có ý nghĩa | **Đúng**: −0,070, CI [−0,106; −0,036], p < 0,001 |

## 5. Gộp các tập test độc lập

Mỗi tập 300 request cho khoảng tin cậy rộng cỡ ±0,03. Gộp các tập không trùng nhau giúp thấy xu hướng thật. Chỉ gộp các run đã có, không chỉnh gì (`src/analysis/pooled.py`, kết quả `src/artifacts/reports/pooled/`).

| Phương pháp so với B | Các tập (Δ từng tập) | n | Δ gộp | CI 95% | Chỉ PP đúng / chỉ B đúng | p McNemar |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| C-kNN | test 1–300 (−0,019), test 301–600 (+0,004), test_fresh (+0,021) | 900 | +0,002 | [−0,012; +0,016] | 20 / 19 | 1,000 |
| C-gated | test 301–600 (+0,013), test_fresh (+0,008) | 600 | +0,010 | [−0,000; +0,021] | 8 / 2 | 0,109 |
| C-LLM | test 1–300 (−0,020), test_fresh (+0,007) | 600 | −0,006 | [−0,021; +0,007] | 8 / 12 | 0,503 |
| **C-oracle** | test 1–300 (+0,019), test_fresh (+0,033) | 600 | **+0,026** | **[+0,009; +0,044]** | 22 / 6 | **0,004** |
| BAL | test 1–300 (−0,016), test_fresh (0,000) | 600 | −0,008 | [−0,027; +0,009] | 12 / 17 | 0,458 |
| A1 | test 1–300 (−0,084), test_fresh (−0,022) | 600 | −0,052 | [−0,075; −0,030] | 9 / 41 | < 0,001 |
| A0 | test 1–300 (−0,047), test_fresh (−0,070) | 600 | −0,058 | [−0,084; −0,034] | 10 / 44 | < 0,001 |

Ghi chú: C-gated trên test 1–300 chỉ có phân tích ghép kết quả (không phải run thật) nên không gộp; C-oracle là phép phân tích, không phải phương pháp dùng được ngoài thực tế.

## 6. Giải thích từng phương pháp

- **C-kNN**: thua ở tập này, thắng ở tập kia. Gộp 900 câu thì ngang B: số câu sửa được gần bằng số câu làm hỏng. Lợi ích khi prior đúng bị triệt tiêu bởi tác hại khi prior sai (prior kNN đúng khoảng 75%).
- **C-oracle**: khi nhãn dự đoán luôn đúng thì C hơn B rõ ràng, p = 0,004 trên 600 câu. Đây là bằng chứng mạnh nhất rằng **ý tưởng label-aware có giá trị, nhưng cần nhãn dự đoán tốt hơn kNN hay LLM zero-shot hiện tại**.
- **C-gated**: chỉ dùng prior khi kNN đủ tự tin, nên giữ phần lợi và tránh phần lớn tác hại. Hai tập test đều dương, nhưng mức +0,01 vẫn nằm trong vùng dao động. Cần thêm dữ liệu mới kết luận được.
- **B-MMR**: trên validation kém B 0,036, trên `test_fresh` hơn B 0,025. Kết quả đổi chiều giữa hai tập nên không thể kết luận. Ye và cộng sự áp dụng MMR cho bài toán suy luận nhiều bước, nơi đa dạng kỹ năng quan trọng; với phân loại HTTP thì lợi ích chưa rõ.
- **B-CLL**: tên nhãn bằng tiếng Anh không gần với nội dung HTTP trong không gian embedding, nên số hạng nhãn chủ yếu tạo thiên lệch theo lớp (ví dụ HTTP Response Splitting luôn được cộng điểm). Bài gốc thử trên văn bản tự nhiên (SST-2, CARER, BBC News), nơi tên nhãn có nghĩa gần với câu.
- **ENN**: bỏ 24% pool, gồm cả ví dụ "khó" nhưng đúng nhãn ở ranh giới Normal/SQLi, nên không giúp ổn định (validation −0,024, test_fresh +0,014).
- **C-iter**: prior lấy từ chính câu trả lời của B. Khi B sai thì prior cũng sai (46/49 câu prior sai thì cả hai cùng sai), nên vòng 2 hầu như không sửa được gì.
- **ENS**: bỏ phiếu chỉ khác B khi BAL và C-kNN cùng không đồng ý với B; điều này hiếm (2/300 câu), nên ENS gần như trùng B mà tốn gấp 3 lần.

## 7. Kết luận cho đồ án

1. **B (chọn ví dụ giống nhất) là lựa chọn tốt và ổn định.** Nó hơn zero-shot và ví dụ cố định có ý nghĩa trên mọi tập.
2. Các cách chọn ví dụ đã công bố, áp dụng đúng tham số gốc, **không vượt B một cách đáng tin** trên dữ liệu HTTP này.
3. **Thông tin nhãn có giá trị nếu nhãn dự đoán đúng** (C-oracle +0,026, có ý nghĩa). Vì vậy hướng phát triển đúng là **nâng chất lượng nhãn dự đoán**, hoặc chỉ dùng nó khi đủ tự tin (C-gated), thay vì thay công thức chọn ví dụ.
4. Với 300 câu mỗi tập và độ dao động khoảng 0,01 giữa các lần chạy, chỉ nên tin chênh lệch lớn và lặp lại trên nhiều tập.

## 8. Chi phí

Sổ chi phí (giá đặt gấp đôi để an toàn): model 20b ước tính 2,24 USD, model 120b ước tính 0,85 USD. Tiền thật vào khoảng một nửa, tức **khoảng 1,5 USD tổng cộng**, dưới giới hạn 5 USD. Vòng này dùng khoảng 5.600 lượt gọi: 1.400 trên validation và 4.200 trên `test_fresh`, gồm cả lần chạy lại B. Có 2 lượt gọi không được ghi vào sổ do lỗi khóa file trên Windows; lỗi này đã được sửa (`src/common/budget.py`).

## 9. Chạy lại

```bash
python -m src.preprocessing.make_fresh_test
python -m src.experiments.build_retrieval --output src/artifacts/retrieval/minilm --add-split test_fresh
python -m src.experiments.build_pool_aux --retrieval src/artifacts/retrieval/minilm
IMPROVE=1 bash src/experiments/run_suite.sh validation
EXTRA=1 IMPROVE=1 bash src/experiments/run_suite.sh test_fresh --locked
python -m src.analysis.ensemble --split test_fresh --name ENS_vote_B_BAL_Cknn --runs src/artifacts/runs/test_fresh/B_k4 src/artifacts/runs/test_fresh/BAL_k4 src/artifacts/runs/test_fresh/C_knn_k4 --output src/artifacts/runs/test_fresh/ENS_vote
python -m src.analysis.compare --split test_fresh --runs "src/artifacts/runs/test_fresh/*" --output src/artifacts/reports/test_fresh
python -m src.analysis.pooled --method C_knn_k4 --sets test:src/artifacts/runs/test test:src/artifacts/runs/test_301_600 test_fresh:src/artifacts/runs/test_fresh
```

## 10. Hạn chế

- Một dataset (SR-BH 2020) và một họ model. Kết luận về CLL-RetICL và MMR chỉ nói về dữ liệu HTTP này, không phủ nhận kết quả trong bài gốc.
- Một số phương pháp làm khác bài gốc để giữ k = 4 và không dùng xác suất (xem mục 2).
- LLM không hoàn toàn tất định. Mỗi run chỉ chạy một lần, trừ B (chạy hai lần để đo dao động).

## Tài liệu tham khảo

- Carbonell, J., & Goldstein, J. (1998). The use of MMR, diversity-based reranking for reordering documents and producing summaries. *SIGIR '98*, 335–336. https://doi.org/10.1145/290941.291025
- Dietterich, T. G. (2000). Ensemble methods in machine learning. *Multiple Classifier Systems*, LNCS, 1–15. https://doi.org/10.1007/3-540-45014-9_1
- Geifman, Y., & El-Yaniv, R. (2017). Selective classification for deep neural networks. *NeurIPS 2017*. https://arxiv.org/abs/1705.08500
- Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics, 6*(2), 65–70.
- Kang, J., Son, D., Song, H., & Chang, B. (2024). In-context learning with noisy labels. arXiv. https://doi.org/10.48550/arXiv.2411.19581
- Khalifa, M., Logeswaran, L., Lee, M., Lee, H., & Wang, L. (2023). Exploring demonstration ensembling for in-context learning. *ME-FoMo Workshop, ICLR 2023*. https://arxiv.org/abs/2308.08780
- Lin, C., Wu, K., Xiang, P., Wu, Y., & Bai, O. (2025). CLL-RetICL: Contrastive linguistic label retrieval-based in-context learning for text classification via large language models. *Findings of IJCNLP-AACL 2025*, 1575–1590. https://doi.org/10.18653/v1/2025.findings-ijcnlp.97
- Qin, C., Zhang, A., Chen, C., Dagar, A., & Ye, W. (2024). In-context learning with iterative demonstration selection. *Findings of EMNLP 2024*. https://arxiv.org/abs/2310.09881
- Wang, X., Wei, J., Schuurmans, D., Le, Q., Chi, E., Narang, S., Chowdhery, A., & Zhou, D. (2023). Self-consistency improves chain of thought reasoning in language models. *ICLR 2023*. https://arxiv.org/abs/2203.11171
- Wilson, D. L. (1972). Asymptotic properties of nearest neighbor rules using edited data. *IEEE Transactions on Systems, Man, and Cybernetics, SMC-2*(3), 408–421. https://doi.org/10.1109/TSMC.1972.4309137
- Ye, X., Iyer, S., Celikyilmaz, A., Stoyanov, V., Durrett, G., & Pasunuru, R. (2023). Complementary explanations for effective in-context learning. *Findings of ACL 2023*, 4469–4484. https://aclanthology.org/2023.findings-acl.273/
