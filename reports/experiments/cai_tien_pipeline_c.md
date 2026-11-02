# Vòng cải tiến Pipeline C: thử các phương pháp đã công bố

> Bản nháp đang chạy thí nghiệm. Phần kết quả được điền sau khi chạy xong.

## 1. Mục tiêu và nguyên tắc

Pipeline C (cộng điểm cho ví dụ trùng nhãn dự đoán sơ bộ) chưa vượt B trên tập test chính. Vòng này thử các cách chọn ví dụ **đã được công bố** ở hội nghị/tạp chí, để xem có cách nào cải thiện được C hoặc B hay không.

Nguyên tắc để kết quả đáng tin:

1. **Chỉ dùng phương pháp có nguồn rõ ràng.** Mỗi phương pháp ghi rõ bài báo gốc, nơi công bố, và phần nào nhóm làm khác bài gốc.
2. **Chỉnh tham số trên validation, không bao giờ trên test.** Ở đâu bài gốc có giá trị mặc định, nhóm dùng đúng giá trị đó.
3. **Đánh giá cuối trên một tập test mới** (`test_fresh`, 300 request, 50/lớp): lấy từ `test.jsonl`, không trùng request và không trùng nhóm với 600 request test đã dùng trước đó. Danh sách phương pháp và giả thuyết được ghi lại (mục 4) **trước** khi chạy tập này.
4. **Chạy lại toàn bộ** các pipeline cũ (A0, A1, B, BAL, C-kNN, C-LLM, C-oracle, kNN) trên cùng tập test mới, để mọi phương pháp được so trên cùng dữ liệu.
5. **Hiệu chỉnh cho nhiều phép so sánh** (Holm): so nhiều phương pháp với B thì xác suất "may mắn thắng" tăng, nên p-value được hiệu chỉnh.

## 2. Các phương pháp thử và nguồn

| Mã | Phương pháp | Nguồn | Cách nhóm áp dụng | Khác bài gốc |
| --- | --- | --- | --- | --- |
| C-gated | Chỉ dùng prior khi đủ tự tin, ngược lại dùng B | Selective classification (Geifman & El-Yaniv, NeurIPS 2017): chỉ quyết định khi độ tự tin vượt ngưỡng | Độ tự tin = tỷ lệ phiếu kNN của nhãn thắng; ngưỡng 0,7 đã khóa trên validation (`cau_hinh_khoa_c_gated.md`) | Bài gốc dùng softmax của mạng nơ-ron và từ chối trả lời; ở đây "từ chối" nghĩa là quay về B |
| B-MMR | Maximal Marginal Relevance: vừa giống query vừa đa dạng | Carbonell & Goldstein (SIGIR 1998); áp dụng cho chọn ví dụ ICL bởi Ye và cộng sự (Findings of ACL 2023), λ = 0,5 | λ = 0,5 như bài của Ye và cộng sự, chọn 4 ví dụ trong top-30 | Bài gốc đo độ giống bằng BERTScore; nhóm dùng cosine của MiniLM |
| B-CLL | CLL-RetICL: cộng điểm ví dụ giống TÊN nhãn của nó hơn các nhãn khác | Lin và cộng sự (Findings of IJCNLP-AACL 2025), phương trình 2, w1 = 1,0 | Đúng công thức và w1 = 1,0 mặc định của bài; cùng encoder MiniLM và cosine | Bài gốc chọn N-way K-shot (K ví dụ mỗi lớp); nhóm giữ k = 4 để so công bằng với các pipeline khác |
| B-ENN | Bỏ ví dụ pool nghi sai nhãn | Edited Nearest Neighbor (Wilson, IEEE Trans. SMC 1972); động cơ: nhãn nhiễu trong ví dụ làm ICL kém đi (Kang và cộng sự, 2024) | Ví dụ pool bị bỏ nếu luật 3-NN trong pool đoán khác nhãn của nó; chọn top-4 như B trên phần còn lại | Không |
| C-kNN-ENN | Như C-kNN nhưng trên pool đã làm sạch bằng ENN | Wilson (1972) | Prior kNN và ví dụ đều lấy từ ứng viên đã bỏ ví dụ nghi nhiễu | Không |
| C-iter | Lấy câu trả lời của B làm prior cho C | Ý tưởng lặp của IDS (Qin và cộng sự, Findings of EMNLP 2024): dùng kết quả vòng trước để chọn ví dụ vòng sau | Vòng 1 = B, vòng 2 = C với prior = nhãn B trả về | Bài gốc dùng zero-shot chain-of-thought, nhiều vòng và bỏ phiếu; nhóm chỉ chạy 2 vòng, không CoT |
| ENS | Bỏ phiếu đa số giữa nhiều bộ ví dụ | Ensemble (Dietterich, MCS 2000); ensemble theo nhóm ví dụ (Khalifa và cộng sự, ME-FoMo @ ICLR 2023); bỏ phiếu đa số (Wang và cộng sự, ICLR 2023) | Đa số của B, BAL, C-kNN; hòa thì theo B | Groq không trả xác suất nhãn nên dùng bỏ phiếu thay cho gộp xác suất |

## 3. Kết quả trên validation (200 request)

(đang chạy)
