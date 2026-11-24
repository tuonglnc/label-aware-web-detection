"""Chương 5 (Kết luận) và danh mục tài liệu tham khảo của báo cáo cuối kỳ."""


def write_chapter5(r):
    r.h1("KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN")
    r.box("Đề tài không tìm ra một cách chọn ví dụ “thần kỳ”, nhưng trả lời được rõ ràng: ví dụ phải giống yêu cầu; "
          "dùng thêm nhãn chỉ có lợi khi nhãn dự đoán đủ chính xác; và mọi kết luận đều được kiểm chứng bằng quy trình "
          "khóa cấu hình trước, tập test độc lập và kiểm định thống kê.")

    r.h2("Kết luận")
    r.p("Đề tài trả lời một câu hỏi thực tế: khi nhờ LLM phân loại một yêu cầu HTTP (bình thường hay thuộc loại tấn công "
        "nào), nên đưa cho LLM xem những ví dụ mẫu nào để nó đoán đúng nhất. Nhóm so sánh ba cách chọn ví dụ: chọn những "
        "ví dụ giống yêu cầu nhất (B), chọn ví dụ đủ các loại (BAL), và chọn ví dụ giống nhất nhưng ưu tiên những ví dụ "
        "cùng loại với một dự đoán sơ bộ (C). Cả ba chạy trên cùng bộ dữ liệu SR-BH 2020 và cùng một LLM. Kết luận dưới "
        "đây chỉ đúng trong phạm vi bộ dữ liệu và cấu hình này.")
    r.p("Câu hỏi nghiên cứu thứ nhất: ví dụ giống nhất có hay thuộc loại khác không? Có. Khoảng 1 trong 4 yêu cầu (23–24%) "
        "có ví dụ giống nhất mang nhãn khác. Hiện tượng này hay gặp nhất ở Normal (38–45%) và SQL Injection (36–40%), vì hai "
        "loại này nhiều khi chỉ khác nhau vài ký tự trong URL (mục 4.3).")
    r.p("Câu hỏi nghiên cứu thứ hai: ưu tiên ví dụ theo dự đoán sơ bộ (C) có giúp LLM đoán đúng hơn B và BAL không? Chưa. Với "
        "dự đoán sơ bộ lấy từ kNN hoặc từ LLM, C chỉ ngang B. Trên 900 yêu cầu gộp, hai bên gần như hòa (20 yêu cầu chỉ C "
        "đúng, 19 yêu cầu chỉ B đúng). C-LLM còn tốn thêm một lượt gọi LLM cho mỗi yêu cầu, và tỷ lệ báo nhầm Normal cũng "
        "không giảm (32% so với 30% ở B). Sáu phương pháp chọn ví dụ đã được công bố cũng không hơn B một cách đáng tin "
        "(mục 4.6).")
    r.p("Điều chắc chắn hơn là B tốt hơn hẳn việc không đưa ví dụ nào và việc đưa ví dụ cố định: trên 600 yêu cầu gộp, B cao "
        "hơn 0,058 và 0,052 điểm Macro-F1 (p < 0,001). Kết quả này lặp lại trên bốn tập đánh giá và hai cỡ mô hình (mục "
        "4.4, 4.5, 4.7). Nói cách khác, điều quan trọng nhất là ví dụ phải giống yêu cầu cần phân loại.")
    r.p("Câu hỏi nghiên cứu thứ ba: dự đoán sơ bộ đúng hay sai thì ảnh hưởng thế nào? Khi dự đoán sơ bộ đúng, C sửa được một ít "
        "lỗi của B. Khi dự đoán sơ bộ sai, C làm hỏng nhiều yêu cầu mà B vốn đoán đúng (trên tập test 1–300, C-kNN làm hỏng "
        "11 yêu cầu và chỉ sửa được 2). Nếu giả sử dự đoán sơ bộ luôn đúng (C-oracle, chỉ là thí nghiệm phân tích vì ngoài "
        "thực tế không biết trước đáp án), C hơn B rõ ràng: +0,026 Macro-F1, p = 0,004 trên 600 yêu cầu. Như vậy chỗ yếu của "
        "C không phải công thức cộng điểm, mà là dự đoán sơ bộ của kNN chỉ đúng khoảng 75–81%. Lưu ý thêm: những yêu cầu mà "
        "dự đoán sơ bộ sai có thể vốn đã khó đoán, nên chưa thể khẳng định dự đoán sai là nguyên nhân gây ra lỗi (mục 4.4, "
        "4.7).")

    r.h2("Đóng góp của đề tài")
    r.p("Các ý tưởng nền gồm truy xuất ví dụ theo độ tương đồng, dùng nhãn dự đoán để chọn ví dụ và hiện tượng LLM không tất "
        "định đã có trong các nghiên cứu về văn bản. Theo khảo sát của nhóm, chưa có công trình nào so sánh có đối chứng các "
        "cách chọn ví dụ này cho LLM phân loại yêu cầu HTTP. Đóng góp của đề tài là kiểm chứng chúng trong miền mới này.")
    r.p("Thứ nhất, đề tài cung cấp bằng chứng thực nghiệm rằng ví dụ cần giống yêu cầu cần phân loại: B cao hơn không dùng ví "
        "dụ và ví dụ cố định trên bốn tập đánh giá và hai cỡ mô hình, kèm số đo hiện tượng “giống nhưng khác nhãn” trên dữ "
        "liệu HTTP thực. Về thực tiễn, truy xuất theo độ tương đồng có thể là cấu hình mặc định khi dùng LLM phân loại yêu "
        "cầu mà không huấn luyện.")
    r.p("Thứ hai, đề tài chỉ ra khi nào thông tin nhãn có lợi và khi nào gây hại: tách được hai trường hợp là nhãn dự đoán thực "
        "tế (ngang B) và nhãn dự đoán hoàn hảo (cao hơn B có ý nghĩa thống kê). Kết quả này bổ sung bằng chứng cho tranh luận "
        "về vai trò của nhãn trong học trong ngữ cảnh (Min và cộng sự, 2022; Yoo và cộng sự, 2022) và cho thấy các phương pháp "
        "hiệu quả trên văn bản như CLL-RetICL không tự động chuyển sang được dữ liệu HTTP.")
    r.p("Thứ ba, đề tài xây dựng một quy trình đánh giá có thể tái lập cho phân loại an ninh bằng LLM qua API: chia dữ liệu "
        "theo nhóm để chống rò rỉ, khóa cấu hình và giả thuyết trước mỗi lần chạy tập test, dùng tập test độc lập, "
        "gộp nhiều tập, hiệu chỉnh khi so sánh nhiều phương án và đo độ dao động của chính LLM (khoảng 0,01 Macro-F1). Kèm "
        "theo là phát hiện nhãn nhiễu ở lớp Normal của SR-BH 2020, một lưu ý cho những người sử dụng lại bộ dữ liệu này.")
    r.p("Đề tài không đề xuất một mô hình mới và không khẳng định phương pháp dựa trên nhãn cao hơn truy xuất theo độ tương "
        "đồng. Các kết quả âm tính có kiểm định vẫn có giá trị vì chỉ ra những hướng chưa mang lại cải thiện đáng tin trong "
        "phạm vi đã khảo sát.")

    r.h2("Hạn chế")
    r.p("Phạm vi dữ liệu còn hẹp. Thực nghiệm chỉ dùng bộ SR-BH 2020 với sáu lớp tấn công cổ điển, thu thập năm 2020, chưa có "
        "các dạng tấn công mới như Log4Shell, SSTI, SSRF hay tấn công vào API JSON. Nhóm đã khảo sát CSIC 2010, ECML/PKDD "
        "2007 và một số bộ mới hơn, nhưng chưa có bộ nào đồng thời mới, là lưu lượng thực, có nhãn theo loại tấn công và có "
        "lớp Normal. Kết quả vì vậy chưa cho phép suy rộng sang các loại tấn công hoặc nguồn lưu lượng khác.")
    r.p("Quy mô và cách lấy mẫu của tập đánh giá cũng là một giới hạn. Mỗi tập có 200–300 yêu cầu, khoảng tin cậy rộng cỡ "
        "±0,03, nên chỉ phân biệt được các chênh lệch lớn; việc gộp các tập thu hẹp được phần nào khoảng tin cậy. Các tập "
        "đánh giá cân bằng 50 yêu cầu mỗi lớp, không giống tỷ lệ của lưu lượng thực, nên điểm số tuyệt đối không phản ánh hiệu "
        "năng khi triển khai.")
    r.p("Nhãn nguồn có nhiễu, nhất là ở lớp Normal (mục 4.8). Điểm số trong Chương 4 vì vậy đo mức khớp với nhãn của bộ dữ liệu "
        "hơn là khả năng phát hiện mọi mã tấn công. Bộ quy tắc dùng để đánh dấu Normal đáng ngờ được viết sau khi xem lỗi của "
        "B và chưa được chuyên gia bảo mật xác nhận; thí nghiệm bỏ ví dụ Normal sai nhãn khỏi kho cũng chỉ bắt được các "
        "payload phổ biến.")
    r.p("Về mô hình và cách chạy, đề tài chỉ dùng một họ mô hình (gpt-oss-20b và gpt-oss-120b) và mỗi phương án chỉ chạy một "
        "lần; riêng B được chạy hai lần để đo độ dao động. Một số phương pháp đã công bố phải được điều chỉnh khác bài gốc để "
        "so sánh công bằng (giữ 4 ví dụ, dùng bỏ phiếu thay cho xác suất), nên kết luận về chúng chỉ áp dụng cho cách triển "
        "khai trong đề tài.")
    r.p("Cuối cùng, chưa có đánh giá trên lưu lượng thực với tỷ lệ tấn công thấp, nơi mức báo nhầm Normal khoảng 30% có thể tạo "
        "ra rất nhiều cảnh báo cần xử lý. Chi phí và độ trễ cũng mới được đo ở mức gọi API đơn lẻ.")

    r.h2("Hướng phát triển")
    r.p("Thứ nhất, cần nâng chất lượng nhãn dự đoán, vì kết quả với C-oracle cho thấy đây là điểm nghẽn của cơ chế. Có thể "
        "kết hợp nhiều nguồn dự đoán (kNN và LLM), hoặc chỉ dùng nhãn dự đoán khi đủ tự tin như C-gated, rồi kiểm chứng "
        "trên tập lớn hơn (khoảng 1.000–2.000 yêu cầu) để kiểm định có đủ độ nhạy.")
    r.p("Thứ hai, cần mở rộng dữ liệu: dùng một bộ thứ hai (ví dụ CSIC 2010 với nhãn bán tự động có kiểm tra thủ công) và một "
        "bộ thử payload hiện đại, ghép từ lưu lượng hợp lệ thực với payload công khai theo từng loại.")
    r.p("Thứ ba, cần làm sạch nhãn: rà soát thủ công các yêu cầu Normal đáng ngờ và đánh giá lại các phương án trên nhãn đã "
        "sửa, để tách khả năng phát hiện khỏi khả năng tái hiện nhãn của bộ dữ liệu.")
    r.p("Cuối cùng, trước khi xem xét triển khai, cần phát triển ứng dụng minh họa thành dịch vụ phân loại yêu cầu theo thời "
        "gian thực, đo độ trễ và chi phí trên lưu lượng thực, đồng thời đánh giá ở các mức báo nhầm thấp hơn.")


REFERENCES = [
    "Ambati, R. B., Lester, J., Srivastava, S., & Chaturvedi, S. (2025). [i]MarginSel: Max-margin demonstration selection for LLMs[/i] [Preprint]. arXiv. https://arxiv.org/abs/2506.06699",
    "Atil, B., Aykent, S., Chittams, A., Fu, L., Passonneau, R. J., Radcliffe, E., Rajagopal, G. R., Sloan, A., Tudrej, T., Ture, F., Wu, Z., Xu, L., & Baldwin, B. (2024). [i]Non-determinism of “deterministic” LLM settings[/i] [Preprint]. arXiv. https://arxiv.org/abs/2408.04667",
    "Blefari, F., Cosentino, C., Pironti, F. A., Furfaro, A., & Marozzo, F. (2025). [i]CyberRAG: An agentic RAG cyber attack classification and reporting tool[/i] [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2507.02424",
    "Carbonell, J., & Goldstein, J. (1998). The use of MMR, diversity-based reranking for reordering documents and producing summaries. In [i]Proceedings of the 21st Annual International ACM SIGIR Conference on Research and Development in Information Retrieval[/i] (pp. 335–336). https://doi.org/10.1145/290941.291025",
    "Dietterich, T. G. (2000). Ensemble methods in machine learning. In [i]Multiple Classifier Systems[/i] (pp. 1–15). Springer. https://doi.org/10.1007/3-540-45014-9_1",
    "Efron, B., & Tibshirani, R. J. (1993). [i]An introduction to the bootstrap[/i]. Chapman & Hall/CRC. https://doi.org/10.1201/9780429246593",
    "Fielding, R., Nottingham, M., & Reschke, J. (Eds.). (2022a). [i]HTTP semantics (RFC 9110)[/i]. RFC Editor. https://doi.org/10.17487/RFC9110",
    "Fielding, R., Nottingham, M., & Reschke, J. (Eds.). (2022b). [i]HTTP/1.1 (RFC 9112)[/i]. RFC Editor. https://doi.org/10.17487/RFC9112",
    "Gao, L., Chaudhary, A., Srinivasan, K., Hashimoto, K., Raman, K., & Bendersky, M. (2023). [i]Ambiguity-aware in-context learning with large language models[/i] [Preprint]. arXiv. https://arxiv.org/abs/2309.07900",
    "Geifman, Y., & El-Yaniv, R. (2017). Selective classification for deep neural networks. In [i]Advances in Neural Information Processing Systems 30[/i] (pp. 4878–4887). https://arxiv.org/abs/1705.08500",
    "Holm, S. (1979). A simple sequentially rejective multiple test procedure. [i]Scandinavian Journal of Statistics, 6[/i](2), 65–70.",
    "Islam, M. N. B., & Saha, S. (2026). [i]From detection to response: A deep learning and retrieval-augmented generation framework for network intrusion mitigation[/i] [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2605.17960",
    "Kang, J., Son, D., Song, H., & Chang, B. (2024). [i]In-context learning with noisy labels[/i] [Preprint]. arXiv. https://doi.org/10.48550/arXiv.2411.19581",
    "Khalifa, M., Logeswaran, L., Lee, M., Lee, H., & Wang, L. (2023). [i]Exploring demonstration ensembling for in-context learning[/i]. ME-FoMo Workshop at ICLR 2023. https://arxiv.org/abs/2308.08780",
    "Lin, C., Wu, K., Xiang, P., Wu, Y., & Bai, O. (2025). CLL-RetICL: Contrastive linguistic label retrieval-based in-context learning for text classification via large language models. In [i]Proceedings of the 14th International Joint Conference on Natural Language Processing and the 4th Conference of the Asia-Pacific Chapter of the Association for Computational Linguistics[/i] (pp. 1575–1590). The Asian Federation of Natural Language Processing and the Association for Computational Linguistics. https://doi.org/10.18653/v1/2025.findings-ijcnlp.97",
    "Liu, J., Shen, D., Zhang, Y., Dolan, B., Carin, L., & Chen, W. (2022). What makes good in-context examples for GPT-3? In [i]Proceedings of Deep Learning Inside Out (DeeLIO 2022)[/i] (pp. 100–114). Association for Computational Linguistics. https://doi.org/10.18653/v1/2022.deelio-1.10",
    "McNemar, Q. (1947). Note on the sampling error of the difference between correlated proportions or percentages. [i]Psychometrika, 12[/i](2), 153–157. https://doi.org/10.1007/BF02295996",
    "Min, S., Lyu, X., Holtzman, A., Artetxe, M., Lewis, M., Hajishirzi, H., & Zettlemoyer, L. (2022). Rethinking the role of demonstrations: What makes in-context learning work? In [i]Proceedings of the 2022 Conference on Empirical Methods in Natural Language Processing[/i] (pp. 11048–11064). https://aclanthology.org/2022.emnlp-main.759",
    "Ouyang, S., Zhang, J. M., Harman, M., & Wang, M. (2025). An empirical study of the non-determinism of ChatGPT in code generation. [i]ACM Transactions on Software Engineering and Methodology, 34[/i](2), 1–28. https://doi.org/10.1145/3697010",
    "OWASP CRS Project. (n.d.). [i]False positives and tuning[/i]. CRS Documentation. https://coreruleset.org/docs/2-how-crs-works/2-3-false-positives-and-tuning/",
    "OWASP Foundation. (n.d.). [i]Code injection[/i]. OWASP Community. https://owasp.org/www-community/attacks/Code_Injection",
    "OWASP Foundation. (2025). [i]A05:2025 injection[/i]. OWASP Top 10:2025. https://top10.owasp.org/2025/A05_2025-Injection/",
    "Qin, C., Zhang, A., Chen, C., Dagar, A., & Ye, W. (2024). In-context learning with iterative demonstration selection. In [i]Findings of the Association for Computational Linguistics: EMNLP 2024[/i]. https://arxiv.org/abs/2310.09881",
    "Scarfone, K., & Mell, P. (2007). [i]Guide to intrusion detection and prevention systems (IDPS)[/i] (NIST Special Publication 800-94). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-94",
    "Sureda Riera, T., Bermejo Higuera, J.-R., Bermejo Higuera, J., Martínez Herraiz, J.-J., & Sicilia Montalvo, J.-A. (2022). A new multi-label dataset for Web attacks CAPEC classification using machine learning techniques. [i]Computers & Security, 120[/i], 102788. https://doi.org/10.1016/j.cose.2022.102788",
    "Wang, X., Wei, J., Schuurmans, D., Le, Q., Chi, E., Narang, S., Chowdhery, A., & Zhou, D. (2023). Self-consistency improves chain of thought reasoning in language models. In [i]International Conference on Learning Representations (ICLR 2023)[/i]. https://arxiv.org/abs/2203.11171",
    "Wilson, D. L. (1972). Asymptotic properties of nearest neighbor rules using edited data. [i]IEEE Transactions on Systems, Man, and Cybernetics, SMC-2[/i](3), 408–421. https://doi.org/10.1109/TSMC.1972.4309137",
    "Xie, S., Luo, M., Stern, C. D., Du, M., & Cheng, L. (2025). [i]DemoShapley: Valuation of demonstrations for in-context learning[/i] (Version 3) [Preprint]. arXiv. https://arxiv.org/abs/2410.07523v3",
    "Ye, X., Iyer, S., Celikyilmaz, A., Stoyanov, V., Durrett, G., & Pasunuru, R. (2023). Complementary explanations for effective in-context learning. In [i]Findings of the Association for Computational Linguistics: ACL 2023[/i] (pp. 4469–4484). https://aclanthology.org/2023.findings-acl.273/",
    "Yoo, K. M., Kim, J., Kim, H. J., Cho, H., Jo, H., Lee, S.-W., Lee, S., & Kim, T. (2022). Ground-truth labels matter: A deeper look into input-label demonstrations. In [i]Proceedings of the 2022 Conference on Empirical Methods in Natural Language Processing[/i] (pp. 2422–2437). https://doi.org/10.18653/v1/2022.emnlp-main.155",
]


def write_references(r, order=None, unused=()):
    """Danh mục tham khảo đánh số [n] theo thứ tự trích dẫn đầu tiên, như báo cáo mẫu."""
    from citations import format_reference
    r.h1("TÀI LIỆU THAM KHẢO", numbered=False)
    sequence = list(order) + list(unused) if order is not None else range(len(REFERENCES))
    for n, i in enumerate(sequence, 1):
        par = r.p(f"[{n}]\t{format_reference(REFERENCES[i])}", indent=False)
        fmt = par.paragraph_format
        from docx.shared import Cm
        fmt.left_indent = Cm(1.0)
        fmt.first_line_indent = Cm(-1.0)
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        par.alignment = WD_ALIGN_PARAGRAPH.LEFT
