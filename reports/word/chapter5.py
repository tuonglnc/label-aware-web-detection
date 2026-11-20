"""Chương 5 (Kết luận) và danh mục tài liệu tham khảo của báo cáo cuối kỳ."""


def write_chapter5(r):
    r.h1("KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN")
    r.box("Đề tài không tìm ra một cách chọn ví dụ “thần kỳ”, nhưng trả lời được rõ ràng: ví dụ phải giống yêu cầu; "
          "dùng thêm nhãn chỉ có lợi khi nhãn dự đoán đủ chính xác; và mọi kết luận đều được kiểm chứng bằng quy trình "
          "khóa cấu hình trước, tập test độc lập và kiểm định thống kê.")

    r.h2("Trả lời ba câu hỏi nghiên cứu")
    r.p("[b]RQ1: Ví dụ giống nhất có hay khác nhãn không?[/b] Có. Khoảng 23–24% yêu cầu có ví dụ giống nhất mang nhãn "
        "khác, lặp lại trên validation và hai tập test. Hiện tượng tập trung ở Normal (38–45%) và SQL Injection (36–40%), "
        "hai lớp thường chỉ khác nhau vài ký tự trong URL.")
    r.p("[b]RQ2: Xếp hạng lại theo nhãn dự đoán có giúp không, và tốn thêm bao nhiêu?[/b] Với nhãn dự đoán thực tế thì "
        "không: C-kNN ngang B trên 900 yêu cầu gộp, C-LLM ngang B trên 600 yêu cầu và còn tốn thêm một lượt gọi LLM. Tỷ "
        "lệ báo nhầm Normal cũng không cải thiện rõ. Cả sáu phương pháp chọn ví dụ đã công bố cũng không vượt B sau hiệu "
        "chỉnh Holm.")
    r.p("[b]RQ3: Nhãn dự đoán đúng và sai ảnh hưởng thế nào?[/b] Khi đúng, C sửa được lỗi của B; khi sai, C làm hỏng "
        "nhiều câu B đang đúng (C-kNN trên test 1–300: hỏng 11, sửa 2). Khi nhãn dự đoán luôn đúng (C-oracle), C hơn B "
        "có ý nghĩa thống kê (+0,026, p = 0,004 trên 600 yêu cầu). Như vậy giới hạn chính của cơ chế không nằm ở công "
        "thức cộng điểm, mà ở độ chính xác của nhãn dự đoán (khoảng 75–81% với kNN).")

    r.h2("Đóng góp của đề tài")
    r.p("Các ý tưởng nền (truy xuất ví dụ theo độ giống, dùng nhãn dự đoán để chọn ví dụ, LLM không tất định) đã có "
        "trong các nghiên cứu về văn bản. Theo khảo sát của nhóm, chưa có công trình nào so sánh có đối chứng các cách "
        "chọn ví dụ này cho LLM phân loại yêu cầu HTTP. Đóng góp của đề tài là kiểm chứng chúng trong miền mới này:")
    r.bullets([
        "[b]Bằng chứng thực nghiệm rằng ví dụ phải giống yêu cầu mới có ích[/b]: B hơn không dùng ví dụ và ví dụ cố định "
        "trên bốn tập đánh giá và hai cỡ model; kèm số đo hiện tượng “giống nhưng khác nhãn” trên dữ liệu HTTP thật. Ý "
        "nghĩa thực tế: truy xuất theo độ giống nên là cấu hình mặc định khi dùng LLM phân loại yêu cầu mà không huấn "
        "luyện.",
        "[b]Chỉ ra khi nào thông tin nhãn giúp và khi nào gây hại[/b]: tách được hai trường hợp nhãn dự đoán thực tế (ngang "
        "B) và nhãn dự đoán hoàn hảo (hơn B có ý nghĩa). Đây là bằng chứng bổ sung cho tranh luận về vai trò của nhãn "
        "trong ICL (Min và cộng sự, 2022; Yoo và cộng sự, 2022), và cho thấy các phương pháp hiệu quả trên văn bản như "
        "CLL-RetICL không tự động chuyển sang được dữ liệu HTTP.",
        "[b]Một quy trình đánh giá tái lập được[/b] cho phân loại an ninh bằng LLM qua API: chia theo nhóm chống rò rỉ, "
        "khóa cấu hình và giả thuyết trước mỗi lần chạy test, tập test độc lập, gộp nhiều tập, hiệu chỉnh nhiều phép so, "
        "và đo độ dao động của chính LLM (khoảng 0,01 Macro-F1). Kèm theo là phát hiện nhãn nhiễu ở lớp Normal của "
        "SR-BH 2020, một cảnh báo hữu ích cho người dùng bộ dữ liệu này.",
    ])
    r.p("Đề tài không đề xuất một mô hình mới và không khẳng định phương pháp label-aware tốt hơn truy xuất theo độ "
        "giống. Kết quả âm tính có kiểm định vẫn có giá trị: nó cho người làm sau biết nên đầu tư vào đâu.")

    r.h2("Hạn chế")
    r.bullets([
        "[b]Một bộ dữ liệu[/b]: SR-BH 2020 với sáu lớp tấn công cổ điển, thu năm 2020. Chưa có các dạng tấn công mới "
        "(Log4Shell, SSTI, SSRF, tấn công vào API JSON). Nhóm đã khảo sát CSIC 2010, ECML/PKDD 2007 và một số bộ mới hơn "
        "nhưng chưa có bộ nào vừa mới, vừa là lưu lượng thật, vừa có nhãn theo loại tấn công và có lớp Normal.",
        "[b]Tập đánh giá nhỏ[/b]: 200–300 yêu cầu mỗi tập, khoảng tin cậy rộng cỡ ±0,03, nên chỉ phân biệt được chênh "
        "lệch lớn. Việc gộp các tập giúp thu hẹp phần nào.",
        "[b]Tập con cân bằng[/b] 50 yêu cầu mỗi lớp, không giống tỷ lệ của lưu lượng thật; điểm số tuyệt đối không phản "
        "ánh hiệu năng khi triển khai.",
        "[b]Nhãn nguồn có nhiễu[/b], nhất là lớp Normal; điểm số đo mức khớp với nhãn của dataset.",
        "[b]Một họ model[/b] (gpt-oss 20b và 120b) và mỗi phương án chỉ chạy một lần (riêng B chạy hai lần để đo dao "
        "động).",
        "[b]Một số phương pháp phải làm khác bài gốc[/b] để so sánh công bằng (giữ 4 ví dụ, dùng bỏ phiếu thay cho xác "
        "suất), nên kết luận về chúng chỉ nói về cách áp dụng trong đề tài.",
    ])

    r.h2("Hướng phát triển")
    r.bullets([
        "[b]Nâng chất lượng nhãn dự đoán[/b]: kết hợp nhiều nguồn (kNN và LLM), hoặc chỉ dùng nhãn dự đoán khi đủ tự tin "
        "như C-gated, rồi kiểm chứng trên tập lớn hơn (khoảng 1.000–2.000 yêu cầu) để có đủ sức kiểm định.",
        "[b]Thêm dữ liệu[/b]: một bộ thứ hai (ví dụ CSIC 2010 với nhãn bán tự động có kiểm tra thủ công), và một bộ thử "
        "payload hiện đại ghép từ lưu lượng hợp lệ thật với payload công khai theo loại.",
        "[b]Làm sạch nhãn[/b]: rà soát thủ công các yêu cầu Normal đáng ngờ và đánh giá lại trên nhãn đã sửa.",
        "[b]Đưa vào ứng dụng[/b]: phát triển demo thành dịch vụ phân loại yêu cầu theo thời gian thực, đo độ trễ và chi "
        "phí trên lưu lượng thật.",
    ])


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


def write_references(r):
    r.h1("TÀI LIỆU THAM KHẢO", numbered=False)
    for ref in REFERENCES:
        par = r.p(ref, indent=False)
        fmt = par.paragraph_format
        from docx.shared import Cm
        fmt.left_indent = Cm(1.0)
        fmt.first_line_indent = Cm(-1.0)
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        par.alignment = WD_ALIGN_PARAGRAPH.LEFT
