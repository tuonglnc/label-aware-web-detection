# Label-Aware Retrieval for LLM-Based Web Attack Detection

## 1. Tổng quan đề tài

Đề tài nghiên cứu **Label-Aware Retrieval** để lựa chọn các ví dụ có nhãn (demonstrations) cho **Large Language Model (LLM)** trong bài toán phát hiện và phân loại **Web Attack** từ **HTTP request**. Phương pháp kết hợp **In-Context Learning (ICL)** với retrieval có sử dụng thông tin nhãn, nhằm lựa chọn demonstrations phù hợp hơn so với **Standard Semantic Retrieval** chỉ dựa trên embedding similarity. Mục tiêu là kiểm chứng tác động của phương pháp đến chất lượng phân loại, đặc biệt với các request có cấu trúc tương tự nhưng thuộc các lớp khác nhau.

## 2. Phương pháp thực hiện

- Khảo sát các nghiên cứu liên quan và lựa chọn dataset HTTP request có nhãn; thực hiện EDA, preprocessing, deduplication và chia retrieval pool, validation set, test set để hạn chế data leakage.
- Xây dựng và so sánh ba pipeline: **LLM baseline** (zero-shot/fixed few-shot), **Standard Semantic Retrieval + LLM** và **Label-Aware Retrieval + LLM**.
- Với pipeline đề xuất, dùng **LLM zero-shot** dự đoán prior label, retrieve top-N candidates rồi rerank theo semantic similarity và thông tin nhãn để chọn top-k demonstrations. Ground-truth test label chỉ dùng để đánh giá.
- Đánh giá bằng **Accuracy, Macro-F1, Precision/Recall/F1 per class** và **Label Consistency Rate@k (LCR@k)**; thực hiện ablation study, phân tích lỗi và chi phí inference.

## 3. Phạm vi nghiên cứu

Đề tài tập trung vào phân loại HTTP request trên dataset có sẵn, ưu tiên khảo sát **SR-BH 2020/CAPEC**. Phạm vi nhãn dự kiến gồm **Normal/Benign, SQL Injection, Path Traversal, Code Injection, HTTP Response Splitting** và **OS Command Injection**; dataset và tập nhãn cuối cùng được lựa chọn sau khi đánh giá chất lượng dữ liệu.

Phương pháp triển khai theo hướng **inference-only**, sử dụng pretrained embedding model và LLM, không train hoặc fine-tune model. Thực nghiệm được thực hiện offline, tập trung vào demonstration selection và label-aware reranking; chưa bao gồm triển khai WAF hoặc hệ thống phát hiện tấn công real-time.
