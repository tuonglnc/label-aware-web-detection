"""Nội dung Chương 4 (Thực nghiệm) của báo cáo cuối kỳ. Mọi số liệu lấy từ src/artifacts/.

Giọng văn theo báo cáo mẫu: câu văn trang trọng, đoạn văn liền mạch, mỗi nhận định kèm số liệu và phạm vi áp dụng.
Các ô tóm tắt (r.box) chỉ xuất hiện ở bản tham khảo dựng bằng KEEP_BOXES=1.
"""

W = 15.5  # bề rộng vùng chữ (cm)


def write_chapter4(r, FIG, ART):
    r.h1("THỰC NGHIỆM")
    r.box("Chương này trả lời ba câu hỏi nghiên cứu bằng số liệu: [b]RQ1[/b] ví dụ giống nhất có hay khác nhãn không "
          "(mục 4.3); [b]RQ2[/b] xếp hạng lại ví dụ theo nhãn dự đoán có cải thiện Macro-F1 và giảm báo nhầm Normal so với "
          "B và BAL không, và tốn thêm gì (mục 4.4–4.7); [b]RQ3[/b] nhãn dự đoán đúng hay sai thì ảnh hưởng thế nào "
          "(mục 4.4, 4.7, 4.8). Đọc nhanh: mục 4.4 (kết quả chính), 4.7 (kết quả có đáng tin không) và 4.10 (tóm tắt).")

    # ------------------------------------------------------------------ 4.1
    r.h2("Dữ liệu thực nghiệm")
    r.h3("Bộ dữ liệu và kết quả lọc")
    r.p("Thực nghiệm sử dụng bộ dữ liệu SR-BH 2020, phiên bản 1.2 (Sureda Riera và cộng sự, 2022). Nhóm tác giả bộ dữ "
        "liệu đưa một website WordPress lên Internet trong 12 ngày của tháng 7/2020, ghi lại mọi yêu cầu HTTP gửi tới bằng "
        "tường lửa ModSecurity rồi gán nhãn thủ công hoặc bán tự động. Tệp gốc có 907.815 bản ghi, 38 cột và 14 cột nhãn; "
        "một yêu cầu có thể mang nhiều nhãn cùng lúc.")
    r.fig("dist", ROOT_DATASET_FIG(FIG) / "sr_bh_class_distribution.png",
          "Phân bố 14 nhãn của SR-BH 2020 (trục ngang thang logarit)", width_cm=14)
    r.p("<<dist>> cho thấy số yêu cầu của từng nhãn, với trục ngang dùng thang logarit. Normal có khoảng 525 nghìn yêu "
        "cầu, còn HTTP Request Smuggling chỉ có khoảng 1 nghìn, tức chênh nhau khoảng 500 lần. Dữ liệu vì vậy mất cân bằng "
        "rất nặng: nếu lấy mẫu ngẫu nhiên, gần như chỉ thu được Normal và SQL Injection. Do đó các tập đánh giá trong đề "
        "tài được lấy cân bằng giữa các lớp.")
    r.p("Quy trình lọc chỉ giữ các yêu cầu có đúng một nhãn thuộc sáu lớp: Normal, SQL Injection, Path Traversal, Code "
        "Injection, HTTP Response Splitting và OS Command Injection. Các yêu cầu trùng bị loại, các yêu cầu có nội dung "
        "giống hệt nhau nhưng mâu thuẫn nhãn được đưa vào diện cách ly. Sau bước này còn 466.267 yêu cầu. Những yêu cầu gần "
        "như giống hệt nhau (ví dụ chỉ khác một con số trong URL) được gom thành một nhóm, và mỗi nhóm phải nằm trọn trong "
        "một tập. Cách chia này nhằm ngăn rò rỉ dữ liệu, tức tình huống LLM nhìn thấy trong kho ví dụ một yêu cầu gần như "
        "trùng với yêu cầu cần phân loại.")
    r.table("sets", "Các tập dữ liệu dùng trong thực nghiệm",
            ["Tập", "Số yêu cầu", "Mục đích sử dụng"],
            [["Pool (kho ví dụ)", "3.000 (500/lớp)", "Nguồn chọn ví dụ có đáp án đưa vào câu lệnh; không dùng để huấn luyện"],
             ["Validation", "200 (33–34/lớp)", "Chọn tham số và so sánh sơ bộ (giữa kỳ)"],
             ["Test 1–300", "300 (50/lớp)", "Kết quả chính, chạy một lần sau khi khóa cấu hình ngày 20/10/2026"],
             ["Test 301–600", "300 (50/lớp)", "Kiểm tra C-gated, khóa cấu hình riêng trước khi chạy"],
             ["Test mới", "300 (50/lớp)", "Đánh giá vòng cải tiến; không trùng yêu cầu hay nhóm với 600 yêu cầu test cũ"]],
            [3.4, 3.3, 8.8], aligns=["left", "center", "left"])
    r.p("Các tập đánh giá cân bằng giúp lớp nhỏ có đủ mẫu để chấm điểm, nhưng không phản ánh tỷ lệ của lưu lượng thực, "
        "nơi phần lớn yêu cầu là bình thường. Ngoài ra, nhãn của SR-BH 2020 có nhiễu: khoảng một phần tư đến gần một phần "
        "ba yêu cầu mang nhãn Normal thực chất chứa mã tấn công (mục 4.8). Điểm số trong chương này vì vậy đo mức khớp với "
        "nhãn của bộ dữ liệu, chưa phải khả năng phát hiện tấn công thực tế.")

    # ------------------------------------------------------------------ 4.2
    r.h2("Cài đặt thực nghiệm")
    r.h3("Cấu hình chung")
    r.p("Mọi phương án dùng chung một LLM, một câu lệnh hướng dẫn và cùng số ví dụ; các phương án chỉ khác nhau ở cách "
        "chọn ví dụ. Nhờ vậy, chênh lệch về kết quả có thể được quy cho cách chọn ví dụ chứ không phải các yếu tố khác. "
        "<<cfg>> tóm tắt cấu hình chính.")
    r.table("cfg", "Cấu hình chính của thí nghiệm",
            ["Thành phần", "Thiết lập"],
            [["LLM", "openai/gpt-oss-20b qua Groq; temperature = 0; reasoning_effort = low; tối đa 1.024 token trả lời. "
                     "Kiểm tra bổ sung với openai/gpt-oss-120b"],
             ["Embedding", "all-MiniLM-L6-v2 (chạy cục bộ, không huấn luyện); vector 384 chiều; đọc tối đa 256 token"],
             ["Chọn ví dụ", "Lấy 30 ứng viên giống nhất trong pool 3.000, chọn 4 ví dụ; mỗi ví dụ cắt ở 500 ký tự"],
             ["Pipeline C", "điểm = độ giống + 0,1 × [nhãn ví dụ trùng nhãn dự đoán]; nhãn dự đoán lấy từ kNN (5 láng "
                            "giềng) hoặc từ A0"],
             ["Đăng ký trước", "Cấu hình và giả thuyết được ghi vào tệp khóa và đẩy lên GitHub trước mỗi lần chạy tập "
                               "test (commit làm bằng chứng); không điều chỉnh sau khi xem kết quả"],
             ["Ngân sách", "Một tài khoản Groq; chương trình tự dừng trước khi chi phí ước tính (tính theo giá gấp đôi) "
                           "vượt 4,5 USD"]],
            [3.6, 11.9], aligns=["left", "left"])
    r.h3("Phương án so sánh và chỉ số đánh giá")
    r.p("Các phương án được mô tả ở Bảng 3.2 (Chương 3). A0 không dùng ví dụ; A1 luôn dùng cùng 4 ví dụ cố định; B chọn "
        "4 ví dụ giống yêu cầu nhất theo độ tương đồng; BAL chọn ví dụ luân phiên giữa các lớp; C xếp hạng lại danh sách "
        "ứng viên có cộng điểm cho ví dụ cùng nhãn với nhãn dự đoán, với nhãn dự đoán lấy từ kNN (C-kNN) hoặc từ LLM "
        "(C-LLM). C-oracle dùng nhãn thật làm nhãn dự đoán; vì ngoài thực tế không biết nhãn thật, phương án này chỉ phục "
        "vụ phân tích.")
    r.p("Macro-F1 là chỉ số chính, nhận giá trị từ 0 đến 1 và càng cao càng tốt. Với mỗi lớp, F1 kết hợp độ chính xác "
        "(trong các yêu cầu được dự đoán là lớp đó, bao nhiêu phần đúng) và độ bao phủ (trong các yêu cầu thực sự thuộc lớp "
        "đó, bao nhiêu phần được phát hiện); Macro-F1 là trung bình của sáu giá trị F1, mỗi lớp có trọng số như nhau nên "
        "lớp bị bỏ sót nhiều sẽ kéo điểm xuống. FPR Normal là tỷ lệ yêu cầu Normal bị dự đoán là tấn công, càng thấp càng "
        "tốt. LCR@4 là số ví dụ cùng nhãn thật với yêu cầu trong 4 ví dụ được chọn; đây chỉ là chỉ số chẩn đoán vì ví dụ cùng "
        "nhãn nhiều hơn chưa chắc làm LLM dự đoán đúng hơn.")
    r.p("Chênh lệch giữa hai phương án được đánh giá bằng hai công cụ. Khoảng tin cậy 95% theo bootstrap ghép cặp, với "
        "2.000 lần lấy mẫu lại tập đánh giá, cho biết chênh lệch Macro-F1 dao động trong khoảng nào; nếu khoảng này chứa "
        "số 0 thì chưa đủ bằng chứng để khẳng định hai phương án khác nhau (Efron & Tibshirani, 1993). Kiểm định McNemar "
        "chỉ xét những yêu cầu mà hai phương án cho kết quả khác nhau, nhằm đánh giá chênh lệch đó có thể do ngẫu nhiên hay "
        "không (McNemar, 1947). Khi so sánh nhiều phương án với cùng một mốc, giá trị p được hiệu chỉnh theo phương pháp "
        "Holm (Holm, 1979).")

    # ------------------------------------------------------------------ 4.3
    r.h2("Nhãn của ví dụ truy xuất gần nhất (RQ1)")
    r.p("Mục này trả lời RQ1. Trước khi gọi LLM, phần truy xuất được kiểm tra riêng: ví dụ giống yêu cầu nhất có mang cùng "
        "nhãn với yêu cầu hay không. Trên tập test 1–300, 24,3% yêu cầu có ví dụ giống nhất mang nhãn khác, dù độ "
        "tương đồng trung bình rất cao (0,956 trên thang tối đa 1). Tỷ lệ này là 23,0% trên tập validation và 24,3% trên tập "
        "test mới, tức gần như không đổi giữa các tập.")
    r.fig("rq1", ART / "retrieval/minilm/eval_validation/retrieval_overview.png",
          "(a) Tỷ lệ yêu cầu có ví dụ giống nhất khác nhãn, theo lớp; (b) tỷ lệ ví dụ cùng nhãn trong 4 ví dụ được chọn "
          "(tập validation)", width_cm=15.5)
    r.p("Ở phần (a) của <<rq1>>, Normal (45,5%) và SQL Injection (39,4%) có tỷ lệ cao nhất. Một yêu cầu SQL Injection "
        "thường chỉ là yêu cầu bình thường được thêm vài ký tự như “+AND+1%3D1”, nên trong không gian embedding hai loại "
        "yêu cầu này nằm gần nhau. Phần (b) cho thấy B chọn được khoảng 0,8 ví dụ cùng nhãn ở các lớp tấn công có đặc trưng "
        "rõ, nhưng chỉ khoảng 0,5 ở Normal và SQL Injection. C-kNN nâng tỷ lệ này lên, còn BAL thấp ở mọi lớp do chủ ý lấy "
        "đủ các lớp.")
    r.box("Hiện tượng “giống nhau nhưng khác nhãn” có thật, chiếm khoảng một phần tư số yêu cầu, tập trung ở Normal và "
          "SQL Injection. Đây là lý do đề tài thử ưu tiên ví dụ theo nhãn.", title="Điều rút ra")

    # ------------------------------------------------------------------ 4.4
    r.h2("Kết quả chính trên tập test (RQ2, RQ3)")
    r.p("Mục này trả lời RQ2 và RQ3. RQ2 hỏi xếp hạng lại theo nhãn dự đoán (C) có cải thiện Macro-F1 và giảm tỷ lệ báo "
        "nhầm Normal so với B và BAL hay không, và chi phí thêm là gì; RQ3 hỏi nhãn dự đoán đúng hay sai ảnh hưởng thế nào "
        "đến kết quả. Số liệu dùng 300 yêu cầu của tập test 1–300, chạy một lần sau khi cấu hình đã được khóa.")
    r.h3("Hiệu quả phân loại và chi phí")
    r.table("main", "Kết quả trên tập test 1–300 (gpt-oss-20b)",
            ["Phương án", "Macro-F1", "FPR Normal", "Coverage", "LCR@4", "Lượt LLM/yêu cầu", "Token TB"],
            [["A0: không ví dụ", "0,834", "34,0%", "1,000", "–", "1", "630"],
             ["A1: ví dụ cố định", "0,797", "40,0%", "1,000", "0,167", "1", "1.431"],
             ["BAL: cân bằng lớp", "0,865", "28,0%", "1,000", "0,416", "1", "1.486"],
             ["[b]B: 4 ví dụ giống nhất[/b]", "[b]0,881[/b]", "30,0%", "1,000", "0,692", "1", "1.487"],
             ["C-kNN", "0,862", "32,0%", "1,000", "0,745", "1", "1.488"],
             ["C-LLM", "0,861", "32,0%", "1,000", "0,845", "2", "1.490"],
             ["C-oracle (chỉ phân tích)", "0,900", "28,0%", "1,000", "0,943", "1", "1.487"]],
            [3.9, 1.8, 2.0, 1.9, 1.6, 2.4, 1.9], aligns=["left"] + ["center"] * 6, size=10.5)
    r.p("<<main>> cho thấy mọi phương án đều trả lời được toàn bộ yêu cầu (coverage 1,000) và dùng số token gần như nhau, "
        "trừ A0 không có ví dụ; chênh lệch điểm số vì vậy không đến từ độ dài câu lệnh. C-LLM cần thêm một lượt gọi LLM cho "
        "mỗi yêu cầu. LCR@4 tăng dần từ B (0,692) đến C-oracle (0,943), nhưng Macro-F1 không tăng theo, và FPR Normal của "
        "C-kNN và C-LLM (32%) không thấp hơn B (30%). Mức nhất quán nhãn cao hơn do đó chưa dẫn đến phân loại đúng hơn, "
        "phù hợp với cách diễn giải LCR ở mục 2.5.")
    r.table("maindiff", "So sánh từng phương án với B trên tập test 1–300",
            ["Phương án", "Macro-F1", "So với B (CI 95%)", "Chỉ PA đúng / chỉ B đúng", "p McNemar"],
            [["kNN (không LLM)", "0,742", "–", "–", "–"],
             ["A0: không ví dụ", "0,834", "−0,047 [−0,081; −0,016]", "5 / 19", "0,007"],
             ["A1: ví dụ cố định", "0,797", "−0,084 [−0,118; −0,051]", "2 / 27", "< 0,001"],
             ["[b]B: 4 ví dụ giống nhất[/b]", "[b]0,881[/b]", "–", "–", "–"],
             ["BAL: luân phiên lớp", "0,865", "−0,016 [−0,041; +0,008]", "5 / 10", "0,302"],
             ["C-kNN", "0,862", "−0,019 [−0,047; +0,008]", "7 / 13", "0,263"],
             ["C-LLM", "0,861", "−0,020 [−0,042; −0,002]", "2 / 8", "0,109"],
             ["C-oracle (phân tích)", "0,900", "+0,019 [−0,003; +0,043]", "10 / 4", "0,180"]],
            [3.9, 1.8, 4.4, 3.0, 2.4], aligns=["left", "center", "center", "center", "center"], size=11)
    r.p("Cột “Chỉ PA đúng / chỉ B đúng” đếm số yêu cầu mà một bên dự đoán đúng còn bên kia dự đoán sai. A0 đúng riêng 5 "
        "yêu cầu, còn B đúng riêng 19 yêu cầu, nên B cao hơn A0 có ý nghĩa thống kê (p = 0,007); A1 thấp hơn B với p < "
        "0,001. BAL, C-kNN và C-LLM đều thấp hơn B một chút, nhưng khoảng tin cậy chứa 0 (riêng C-LLM chạm sát 0) và p "
        "lần lượt là 0,302, 0,263 và 0,109, nên chưa phân biệt được với B. C-kNN đúng riêng 7 yêu cầu và B đúng riêng 13 "
        "yêu cầu; chênh lệch này nhỏ so với mức dao động giữa các lần chạy (mục 4.7). C-oracle cao hơn B 0,019 nhưng chưa "
        "có ý nghĩa thống kê trên 300 yêu cầu; kết quả gộp nhiều tập được trình bày ở mục 4.7.")
    r.p("Kết quả của A1 thấp hơn cả A0 cho thấy ví dụ không liên quan đến yêu cầu có thể làm LLM phân loại kém đi so với "
        "không có ví dụ. Đối với RQ2, trên tập test này việc xếp hạng lại theo nhãn dự đoán chưa cải thiện Macro-F1 "
        "và chưa giảm FPR Normal so với B và BAL.")
    r.h3("Nhãn dự đoán đúng, sai và kết quả theo lớp")
    r.table("prior", "C so với B, tách theo nhãn dự đoán đúng hay sai (tập test 1–300)",
            ["Phương án", "Nhãn dự đoán", "Số yêu cầu", "C sửa lỗi của B", "C làm hỏng câu B đúng"],
            [["C-kNN", "Đúng", "224", "5", "2"], ["C-kNN", "Sai", "76", "2", "11"],
             ["C-LLM", "Đúng", "250", "1", "1"], ["C-LLM", "Sai", "50", "1", "7"]],
            [2.6, 2.8, 2.6, 3.6, 3.9], size=11)
    r.p("<<prior>> tách các yêu cầu theo việc nhãn dự đoán đúng hay sai. Khi nhãn dự đoán đúng, C sửa được một số lỗi của "
        "B (C-kNN sửa 5, làm hỏng 2). Khi nhãn dự đoán sai, C làm hỏng nhiều yêu cầu mà B đang dự đoán đúng hơn số lỗi sửa "
        "được (C-kNN làm hỏng 11, sửa 2; C-LLM làm hỏng 7, sửa 1). Nhãn dự đoán của kNN đúng khoảng 75% trên tập kiểm "
        "thử, nên phần thiệt hại ở nhóm nhãn dự đoán sai triệt tiêu phần lợi ở nhóm nhãn dự đoán đúng.")
    r.p("Cơ chế có thể giải thích kết quả này là khi nhãn dự đoán sai, C đưa các ví dụ sai lớp lên đầu danh sách. Tuy "
        "nhiên nhóm yêu cầu có nhãn dự đoán sai có thể gồm những yêu cầu vốn khó, nên số liệu chưa đủ để kết luận quan hệ "
        "nhân quả. C-oracle, dù luôn có nhãn dự đoán đúng, vẫn có 26 yêu cầu mà cả B lẫn C-oracle cùng dự đoán sai; một phần "
        "lỗi còn lại vì vậy không do nhãn dự đoán. C-oracle chỉ là phân tích ngoại tuyến, không phải giới hạn toán học của "
        "phương pháp.")
    r.table("perclass", "F1 theo từng lớp trên tập test 1–300",
            ["Phương án", "Normal", "SQL Inj.", "Path Trav.", "Code Inj.", "HTTP Resp. Split.", "OS Cmd Inj."],
            [["A0: không ví dụ", "0,73", "0,93", "0,91", "0,94", "0,81", "0,68"],
             ["A1: ví dụ cố định", "0,61", "0,92", "0,86", "0,89", "0,83", "0,67"],
             ["BAL", "0,76", "0,92", "0,94", "0,92", "0,89", "0,76"],
             ["[b]B[/b]", "[b]0,77[/b]", "[b]0,94[/b]", "[b]0,94[/b]", "[b]0,96[/b]", "[b]0,89[/b]", "[b]0,79[/b]"],
             ["C-kNN", "0,73", "0,93", "0,91", "0,94", "0,88", "0,78"],
             ["C-LLM", "0,76", "0,93", "0,92", "0,96", "0,84", "0,76"],
             ["C-oracle (chỉ phân tích)", "0,78", "0,96", "0,94", "0,97", "0,92", "0,83"]],
            [3.9, 1.7, 1.8, 1.9, 1.8, 2.4, 2.0], aligns=["left"] + ["center"] * 6, size=10.5)
    r.p("Theo <<perclass>>, Normal và OS Command Injection là hai lớp có F1 thấp nhất ở mọi phương án (với B lần lượt là "
        "0,77 và 0,79), còn bốn lớp tấn công còn lại đều đạt từ 0,89 trở lên. C-kNN thấp hơn B ở Normal (0,73 so với 0,77) "
        "và Path Traversal (0,91 so với 0,94). Với C-oracle, lớp được cải thiện nhiều nhất so với B là OS Command Injection "
        "(+0,04) và HTTP Response Splitting (+0,03). Mỗi lớp chỉ có 50 yêu cầu nên các chênh lệch theo lớp chỉ mang tính "
        "mô tả.")
    r.fig("f1sets", FIG / "final_f1_across_sets.png",
          "Macro-F1 của các phương án trên bốn tập đánh giá (dấu * : chỉ để phân tích)", width_cm=15.5)
    r.p("<<f1sets>> đặt kết quả của cả bốn tập cạnh nhau. Điểm tuyệt đối thay đổi giữa các tập (tập test mới khó hơn), "
        "nhưng thứ tự chung được giữ nguyên: B và các biến thể C ở nhóm trên, A0 và A1 ở nhóm dưới, còn kNN không dùng LLM "
        "thấp nhất.")
    r.box("Ví dụ phải giống yêu cầu mới giúp LLM. Ưu tiên ví dụ theo nhãn dự đoán (C) chưa hơn B, vì khi đoán sai nó "
          "gây hại nhiều hơn phần lợi khi đoán đúng.", title="Điều rút ra")

    # ------------------------------------------------------------------ 4.5
    r.h2("Kiểm tra với mô hình lớn hơn")
    r.p("Mục này kiểm tra độ vững của câu trả lời cho RQ2 theo cỡ mô hình. Nhóm chạy lại các phương án chính trên tập kiểm "
        "thử 1–300 với gpt-oss-120b, có quy mô lớn hơn khoảng 6 lần. Đây là thí nghiệm bổ sung, được quyết định sau khi đã "
        "có kết quả của gpt-oss-20b.")
    r.table("big", "So sánh gpt-oss-20b và gpt-oss-120b trên tập test 1–300 (Macro-F1)",
            ["Phương án", "gpt-oss-20b", "gpt-oss-120b"],
            [["A0: không ví dụ", "0,834", "0,793"], ["[b]B: 4 ví dụ giống nhất[/b]", "[b]0,881[/b]", "[b]0,869[/b]"],
             ["BAL", "0,865", "0,862"], ["C-kNN", "0,862", "0,866"], ["C-LLM", "0,861", "0,854"],
             ["C-oracle (phân tích)", "0,900", "0,880"]],
            [6.0, 3.5, 3.5])
    r.p("Kết luận giữ nguyên khi đổi mô hình. B vẫn có Macro-F1 cao nhất trong các phương án dùng được ngoài thực tế "
        "(0,869), C-kNN (0,866) và BAL (0,862) ở mức ngang B, và C không vượt B. Điểm đáng chú ý là mô hình lớn hơn có điểm "
        "thấp hơn khi không có ví dụ (0,793 so với 0,834).")
    r.p("Nguyên nhân chính được ghi nhận là gpt-oss-120b gán các payload như “;sleep 15;” vào SQL Injection, trong khi bộ "
        "dữ liệu gán nhãn OS Command Injection. Khi câu lệnh có ví dụ, mô hình tiếp nhận được quy ước gán nhãn của bộ dữ "
        "liệu, nên điểm của B ở hai mô hình gần nhau. Kết quả cho thấy mô hình lớn hơn không tự động cho điểm cao hơn trên "
        "bài toán có quy ước nhãn riêng, và ví dụ truy xuất giúp đưa mô hình về đúng quy ước đó. Kết luận này mới được kiểm "
        "tra với một họ mô hình.")

    # ------------------------------------------------------------------ 4.6
    r.h2("Vòng cải tiến Pipeline C (RQ2, RQ3)")
    r.p("Mục này bổ sung bằng chứng cho RQ2 và RQ3 bằng cách thử cải tiến C trên dữ liệu mới. Do C chưa vượt B, nhóm thử "
        "hai hướng cải tiến theo các nguyên tắc sau: chỉ dùng phương pháp có nguồn công bố rõ ràng, dùng đúng tham số mặc "
        "định của bài gốc, khóa cấu hình trước khi chạy tập test và đánh giá trên dữ liệu chưa từng được xem.")
    r.h3("C-gated")
    r.p("Hướng thứ nhất là C-gated (mô tả ở Chương 3), chỉ dùng nhãn dự đoán khi kNN đủ tự tin. Trên tập test 301–600, "
        "C-gated đạt 0,882 so với 0,869 của B (+0,013; CI [−0,002; +0,030]; chỉ C-gated đúng 5 yêu cầu, chỉ B đúng 1 yêu "
        "cầu). C-gated làm hỏng 1 yêu cầu mà B đang đúng, trong khi C-kNN làm hỏng 4. Kết quả đi theo hướng mong đợi nhưng "
        "chưa đủ bằng chứng thống kê.")
    r.h3("Các phương pháp chọn ví dụ đã công bố")
    r.p("Hướng thứ hai là thử sáu cách chọn ví dụ đã được công bố, tóm tắt ở <<pub>>. Các phương án này được chạy trên tập xác "
        "thực, khóa cấu hình, rồi chạy cùng toàn bộ phương án cũ trên tập test mới gồm 300 yêu cầu.")
    r.table("pub", "Các phương pháp chọn ví dụ đã công bố được thử",
            ["Mã", "Ý tưởng chính", "Nguồn", "Tham số"],
            [["B-MMR", "Chọn ví dụ vừa giống yêu cầu vừa khác nhau, tránh 4 ví dụ gần như trùng nhau",
              "Carbonell & Goldstein (1998); Ye và cộng sự (2023)", "λ = 0,5 (mặc định của bài)"],
             ["B-CLL", "Cộng điểm cho ví dụ có nội dung gần với tên nhãn của chính nó hơn tên các nhãn khác",
              "Lin và cộng sự (2025), phương trình 2", "w1 = 1,0 (mặc định)"],
             ["B-ENN", "Bỏ khỏi kho các ví dụ có nhãn trái với láng giềng (nghi sai nhãn)",
              "Wilson (1972); động cơ từ Kang và cộng sự (2024)", "3 láng giềng; bỏ 724/3.000"],
             ["C-kNN-ENN", "C-kNN trên kho đã làm sạch bằng ENN", "Wilson (1972)", "như trên"],
             ["C-iter", "Lấy câu trả lời của B làm nhãn dự đoán cho C (hai vòng)",
              "Qin và cộng sự (2024)", "2 vòng"],
             ["ENS", "Bỏ phiếu đa số giữa B, BAL và C-kNN",
              "Dietterich (2000); Khalifa và cộng sự (2023); Wang và cộng sự (2023)", "hòa phiếu theo B"]],
            [2.2, 5.6, 4.8, 2.9], aligns=["left", "left", "left", "left"], size=10.5)
    r.fig("fresh", FIG / "final_fresh_forest.png",
          "Tập test mới (300 yêu cầu): chênh lệch Macro-F1 của từng phương án so với B, kèm khoảng tin cậy 95%",
          width_cm=14.5)
    r.p("Trong <<fresh>>, mỗi dòng là một phương án, chấm tròn là chênh lệch Macro-F1 so với B và vạch ngang là khoảng "
        "tin cậy 95%. Vạch nằm hoàn toàn bên phải số 0 cho thấy phương án cao hơn B có ý nghĩa; vạch cắt qua 0 cho thấy "
        "chưa phân biệt được với B. Dải màu vàng biểu thị mức dao động khi chạy lại cùng một câu lệnh (mục 4.7); chênh "
        "lệch nằm trong dải này chưa thể xem là khác biệt thật.")
    r.table("holm", "Kiểm định đã đăng ký trước trên tập test mới (McNemar, hiệu chỉnh Holm cho 7 phép so)",
            ["Phương án", "Macro-F1", "So với B", "Chỉ PA đúng / chỉ B đúng", "p Holm"],
            [["B (tham chiếu)", "0,833", "–", "–", "–"],
             ["B-MMR", "0,858", "+0,025", "13 / 6", "1,000"], ["B-ENN", "0,847", "+0,014", "7 / 3", "1,000"],
             ["C-gated", "0,841", "+0,008", "3 / 1", "1,000"], ["C-iter", "0,838", "+0,005", "3 / 2", "1,000"],
             ["B-CLL", "0,834", "+0,001", "13 / 13", "1,000"], ["C-kNN-ENN", "0,834", "+0,001", "3 / 3", "1,000"],
             ["ENS", "0,833", "+0,000", "0 / 0", "1,000"]],
            [3.6, 2.4, 2.4, 4.0, 2.4], size=11)
    r.p("Theo <<holm>>, không phương án cải tiến nào cao hơn B có ý nghĩa thống kê, vì mọi giá trị p sau hiệu chỉnh Holm "
        "đều bằng 1. Trong ba giả thuyết đã ghi trước khi chạy, hai giả thuyết được ủng hộ (không phương án nào vượt B; B "
        "cao hơn A0 rõ ràng, −0,070, p < 0,001) và một giả thuyết không được ủng hộ: nhóm dự đoán B-CLL thấp hơn B, "
        "nhưng trên tập test mới hai phương án bằng nhau. Kết quả không khớp giả thuyết vẫn được báo cáo đầy đủ.")
    r.p("B-MMR đổi chiều giữa hai tập: thấp hơn B 0,036 trên tập validation nhưng cao hơn 0,025 trên tập test mới, nên "
        "chưa thể kết luận. Ye và cộng sự (2023) áp dụng MMR cho bài toán suy luận nhiều bước, nơi sự đa dạng về kỹ năng có vai "
        "trò quan trọng; với phân loại yêu cầu HTTP, lợi ích của sự đa dạng chưa rõ. B-CLL dựa trên độ giống giữa ví dụ và "
        "tên nhãn (“SQL Injection”,…). Cách này phù hợp với văn bản tự nhiên mà bài gốc thử nghiệm (đánh giá phim, tin tức), "
        "nhưng nội dung HTTP không gần tên nhãn trong không gian embedding, nên B-CLL chủ yếu tạo thiên lệch theo lớp.")
    r.p("B-ENN bỏ 24% kho ví dụ, trong đó có cả những ví dụ khó nhưng đúng nhãn ở ranh giới Normal và SQL Injection. C-iter "
        "lấy nhãn dự đoán từ câu trả lời của B, nên khi B sai thì nhãn dự đoán cũng sai và vòng thứ hai hầu như không sửa "
        "được lỗi. ENS chỉ khác B khi BAL và C-kNN cùng bất đồng với B, tình huống hiếm (2/300 yêu cầu), nên kết quả gần như "
        "trùng B trong khi chi phí gấp ba.")
    r.box("Các cách chọn ví dụ đã công bố, áp dụng đúng tham số gốc, không vượt được B một cách đáng tin trên dữ liệu "
          "HTTP. C-gated là hướng hứa hẹn nhất nhưng cần thêm dữ liệu để khẳng định.", title="Điều rút ra")

    # ------------------------------------------------------------------ 4.7
    r.h2("Độ tin cậy của kết quả (RQ2, RQ3)")
    r.p("Mục này xác định chênh lệch nào giữa các phương án đủ tin cậy để rút ra kết luận cho RQ2 và RQ3, và chênh lệch "
        "nào nằm trong mức dao động của chính hệ thống.")
    r.h3("Độ dao động giữa các lần chạy")
    r.p("LLM gọi qua API không trả lời hoàn toàn giống nhau giữa các lần chạy dù temperature bằng 0. Nhóm chạy lại B lần thứ "
        "hai với đúng câu lệnh cũ. Trên tập validation, 6/200 câu trả lời thay đổi và Macro-F1 lệch 0,011; trên tập kiểm "
        "thử mới, 5/300 câu trả lời thay đổi và Macro-F1 cũng lệch 0,011. Hiện tượng này phù hợp với các nghiên cứu đã công "
        "bố (Ouyang và cộng sự, 2025; Atil và cộng sự, 2024). Do đó, các chênh lệch nhỏ hơn khoảng 0,01 giữa các phương án "
        "chỉ được xem là ngang nhau.")
    r.h3("Gộp các tập test độc lập")
    r.p("Mỗi tập có 300 yêu cầu cho khoảng tin cậy rộng cỡ ±0,03, nên một phương án có thể cao hơn ở tập này và thấp hơn "
        "ở tập khác chỉ do ngẫu nhiên. Khi gộp các tập test không trùng nhau, khoảng tin cậy hẹp lại. Việc gộp chỉ dùng "
        "các kết quả đã có, không điều chỉnh thêm cấu hình nào.")
    r.fig("pooled", FIG / "final_pooled_forest.png",
          "Gộp các tập test độc lập: chênh lệch Macro-F1 so với B (số yêu cầu trong ngoặc)", width_cm=15)
    r.table("pooltbl", "Kết quả gộp các tập test độc lập",
            ["So với B", "Số yêu cầu", "Chênh lệch (CI 95%)", "Chỉ PA đúng / chỉ B đúng", "p McNemar"],
            [["C-kNN", "900", "+0,002 [−0,012; +0,016]", "20 / 19", "1,000"],
             ["C-gated", "600", "+0,010 [−0,000; +0,021]", "8 / 2", "0,109"],
             ["C-LLM", "600", "−0,006 [−0,021; +0,007]", "8 / 12", "0,503"],
             ["[b]C-oracle (phân tích)[/b]", "600", "[b]+0,026 [+0,009; +0,044][/b]", "22 / 6", "[b]0,004[/b]"],
             ["BAL", "600", "−0,008 [−0,027; +0,009]", "12 / 17", "0,458"],
             ["A1: ví dụ cố định", "600", "−0,052 [−0,075; −0,030]", "9 / 41", "< 0,001"],
             ["A0: không ví dụ", "600", "−0,058 [−0,084; −0,034]", "10 / 44", "< 0,001"]],
            [3.9, 1.9, 4.4, 2.9, 2.4], size=11)
    r.p("<<pooltbl>> là kết quả quan trọng nhất của đề tài. Trên 900 yêu cầu, C-kNN và B gần như hòa tuyệt đối (20 so với "
        "19 yêu cầu đúng riêng). Khi nhãn dự đoán luôn đúng, C-oracle cao hơn B có ý nghĩa thống kê (+0,026; CI "
        "[+0,009; +0,044]; p = 0,004 trên 600 yêu cầu). C-gated cao hơn B ở cả hai tập được chạy, nhưng chênh lệch gộp "
        "(+0,010, p = 0,109) chưa vượt ngưỡng ý nghĩa.")
    r.p("Kết quả cho thấy cách cộng điểm theo nhãn có tác dụng khi nhãn dự đoán đúng, và điều kiện còn thiếu là nhãn dự "
        "đoán đủ chính xác. C-gated là cách tránh dùng nhãn dự đoán khi kNN không chắc chắn. Các kết luận định tính (B cao "
        "hơn zero-shot và ví dụ cố định; C chỉ có lợi khi nhãn dự đoán đúng) lặp lại trên nhiều tập độc lập và có kiểm "
        "định, trong khi các chênh lệch cỡ 0,01–0,02 giữa các phương án chưa đủ cơ sở để kết luận.")
    r.box("Kết luận định tính (B hơn zero-shot; C chỉ có lợi khi nhãn dự đoán đúng) lặp lại trên nhiều tập độc lập và có "
          "kiểm định, nên đáng tin. Chênh lệch nhỏ cỡ 0,01–0,02 giữa các phương án thì không đủ để kết luận.",
          title="Điều rút ra")

    # ------------------------------------------------------------------ 4.8
    r.h2("Phân tích lỗi: nhãn nhiễu ở lớp Normal")
    r.p("Mục này giải thích vì sao điểm tuyệt đối thấp và kiểm tra nhãn nhiễu có làm lệch kết luận cho RQ2 và RQ3 hay "
        "không.")
    r.h3("Yêu cầu Normal mang mã tấn công")
    r.p("Ở mọi phương án, Normal là lớp có kết quả thấp nhất: khoảng 30% yêu cầu Normal bị dự đoán là tấn công. Khi đọc "
        "từng yêu cầu bị báo nhầm, phần lớn chứa mã tấn công rõ ràng, ví dụ “/blog/wp-content/themes';cat /etc/passwd;'/...” "
        "hoặc “/blog/index.php/'\"<script>alert(1);</script>/oembed”. Với những yêu cầu này, dự đoán của LLM là hợp lý, "
        "còn nhãn Normal của bộ dữ liệu có khả năng sai.")
    r.fig("cmb", ART / "reports/test/confusion_B_semantic_k4.png",
          "Ma trận nhầm lẫn của B trên tập test 1–300 (hàng: nhãn của bộ dữ liệu; cột: nhãn LLM dự đoán)", width_cm=12)
    r.p("Trong <<cmb>>, đường chéo là các yêu cầu được dự đoán đúng. Phần lớn lỗi nằm ở hàng NORMAL, chủ yếu bị dự đoán "
        "thành OS Command Injection, đúng loại mã tấn công thường gặp trong các yêu cầu Normal sai nhãn.")
    r.p("Nhóm dùng một bộ quy tắc cố định, chỉ xét nội dung yêu cầu (ví dụ có “sleep(”, “/etc/passwd”, thẻ script hoặc lệnh "
        "shell), để đánh dấu các yêu cầu Normal đáng ngờ. Kết quả là 139/500 ví dụ Normal trong kho (27,8%), 15/50 yêu cầu "
        "Normal ở tập test 1–300 và 14/50 ở tập test 301–600 bị đánh dấu. Cả 15/15 lần B báo nhầm Normal trên tập "
        "test 1–300 đều rơi vào nhóm đáng ngờ này.")
    r.table("noise", "Kết quả khi bỏ các yêu cầu Normal đáng ngờ khỏi tập đánh giá",
            ["Tập", "Phương án", "Macro-F1 gốc → khi bỏ", "FPR Normal gốc → khi bỏ"],
            [["Test 1–300", "A0", "0,834 → 0,873", "34,0% → 8,6%"],
             ["Test 1–300", "B", "0,881 → 0,927", "30,0% → 0,0%"],
             ["Test 1–300", "C-kNN", "0,862 → 0,901", "32,0% → 5,7%"],
             ["Test 301–600", "B", "0,869 → 0,910", "32,0% → 5,6%"],
             ["Test 301–600", "C-gated", "0,882 → 0,925", "30,0% → 2,8%"]],
            [3.4, 2.8, 4.6, 4.7], size=11)
    r.p("Khi bỏ các yêu cầu Normal đáng ngờ, Macro-F1 của mọi phương án tăng khoảng 0,04 và tỷ lệ báo nhầm Normal của B "
        "giảm từ 30% xuống còn 0–6%. Thứ hạng giữa các phương án không thay đổi, nên nhãn nhiễu không làm đổi kết luận so "
        "sánh; nó chỉ cho thấy các con số tuyệt đối bị kéo thấp bởi nhãn sai của bộ dữ liệu. Hạn chế của phân tích này là "
        "bộ quy tắc được viết sau khi đã xem lỗi của B, và 36 yêu cầu đáng ngờ được đọc kiểm tra chưa được chuyên gia bảo "
        "mật xác nhận.")
    r.h3("Thử bỏ ví dụ Normal sai nhãn khỏi kho ví dụ")
    r.p("Nhãn nhiễu cũng có mặt trong kho ví dụ. Nhóm vì vậy thử cách đơn giản nhất là bỏ các ví dụ Normal đáng ngờ khỏi "
        "kho (loại 139/500 ví dụ Normal) rồi chọn 4 ví dụ như B; phương án này được gọi là B-cleanpool. Giả thuyết và tiêu "
        "chí đánh giá được ghi vào tệp khóa và đẩy lên GitHub trước khi chạy. Thí nghiệm chạy trên tập test mới và tập "
        "test 301–600, gộp 600 yêu cầu.")
    r.table("cleanpool", "B-cleanpool so với B (gpt-oss-20b)",
            ["Tập", "Số yêu cầu", "B", "B-cleanpool", "Chênh lệch (CI 95%)", "p McNemar"],
            [["Test mới", "300", "0,833", "0,841", "+0,008 [−0,011; +0,027]", "0,727"],
             ["Test 301–600", "300", "0,869", "0,884", "+0,014 [−0,003; +0,034]", "0,289"],
             ["[b]Gộp[/b]", "[b]600[/b]", "[b]0,852[/b]", "[b]0,863[/b]", "[b]+0,011 [−0,002; +0,025][/b]",
              "[b]0,210[/b]"]],
            [3.2, 1.9, 1.4, 2.3, 4.2, 2.5], aligns=["left"] + ["center"] * 5, size=10.5)
    r.p("Theo <<cleanpool>>, chênh lệch gộp là +0,011, khoảng tin cậy chứa 0 và p = 0,21, nên việc bỏ ví dụ Normal sai "
        "nhãn không cải thiện kết quả có ý nghĩa thống kê. Cả ba giả thuyết đã ghi trước đều được ủng hộ: phương án không "
        "làm hại (cận dưới của CI là −0,002, lớn hơn −0,02); số yêu cầu tấn công bị dự đoán thành Normal không tăng (23 so "
        "với 25); và chênh lệch nằm trong khoảng dự đoán [−0,01; +0,02] mà không có ý nghĩa thống kê.")
    r.p("Bộ lọc chỉ làm đổi ví dụ ở 110/600 yêu cầu (18%). Trong nhóm này có 5 yêu cầu được sửa và 4 yêu cầu bị làm hỏng, "
        "gần như hòa. Ở 490 yêu cầu còn lại, câu lệnh giống hệt B nhưng vẫn có 10 yêu cầu đổi đáp án (6 được sửa, 1 bị làm "
        "hỏng so với B), tức là do LLM dao động giữa hai lần chạy. Phần lớn mức +0,011 vì vậy nhiều khả năng là nhiễu chứ "
        "chưa phải lợi ích của việc làm sạch kho. Bộ quy tắc chỉ bắt được các payload phổ biến, và mỗi tập chỉ có 300 yêu "
        "cầu nên kiểm định chưa đủ độ nhạy để phát hiện chênh lệch dưới khoảng 0,02.")
    r.box("Nhãn Normal bị nhiễu làm điểm tuyệt đối thấp nhưng không làm đổi thứ hạng, và bỏ ví dụ sai nhãn khỏi kho "
          "không giúp được B đáng kể. Điều này khớp với các kết quả âm khác của đề tài: B là baseline mạnh, các thay đổi ở "
          "khâu chọn ví dụ chỉ chạm tới khoảng 16–18% câu lệnh nên khó vượt nhiễu cỡ 0,01.", title="Điều rút ra")

    # ------------------------------------------------------------------ 4.9
    r.h2("Chi phí và sản phẩm")
    r.p("Toàn bộ thực nghiệm gồm hơn 12.000 lượt gọi LLM được ghi trong sổ chi phí, trên cả hai mô hình, tốn khoảng "
        "1,5–1,7 USD theo giá tham khảo. Sổ chi phí tính theo giá gấp đôi nên ghi khoảng 2,4 USD cho gpt-oss-20b và 0,9 USD "
        "cho gpt-oss-120b, đều dưới giới hạn nhóm tự đặt (4,5 và 3,0 USD). Một yêu cầu với B dùng khoảng 1.500 token, A0 "
        "khoảng 630 token; C-LLM và C-iter cần hai lượt gọi. Thời gian trả lời trung vị khoảng 0,6–0,8 giây mỗi lượt gọi.")
    r.p("Sản phẩm đi kèm gồm mã nguồn mở trên GitHub với 94 bài kiểm thử tự động; chương trình có thể chạy tiếp khi bị "
        "gián đoạn và tự dừng khi chạm ngân sách; các tệp khóa cấu hình kèm commit làm bằng chứng; và một ứng dụng minh "
        "họa (Streamlit). Trong ứng dụng, người dùng nhập một yêu cầu HTTP và xem cạnh nhau cách B và C chọn 4 ví dụ, nhãn "
        "dự đoán sơ bộ và nhãn LLM trả về. Ứng dụng có chế độ không cần API để trình diễn khi không có kết nối mạng.")

    # ------------------------------------------------------------------ 4.10
    r.h2("Tóm tắt chương")
    r.p("Về RQ1, khoảng 24% yêu cầu có ví dụ giống nhất mang nhãn khác, nặng nhất ở Normal và SQL Injection. Về RQ2, chọn "
        "ví dụ giống yêu cầu (B) cho kết quả cao hơn rõ rệt so với không có ví dụ hay ví dụ cố định, lặp lại trên bốn tập "
        "và hai cỡ mô hình; xếp hạng lại theo nhãn dự đoán thực tế (C) ở mức ngang B. Về RQ3, C hơn B có ý nghĩa thống kê "
        "khi nhãn dự đoán luôn đúng và làm hỏng nhiều yêu cầu hơn số lỗi sửa được khi nhãn dự đoán sai, nên chất lượng nhãn "
        "dự đoán là điều kiện then chốt.")
    r.p("Sáu phương pháp chọn ví dụ đã công bố không vượt B một cách đáng tin; C-gated cho kết quả đi theo hướng mong đợi "
        "nhưng chưa đủ bằng chứng. LLM dao động khoảng 0,01 Macro-F1 giữa hai lần chạy. Nhãn Normal của bộ dữ liệu có nhiễu "
        "đáng kể nhưng không làm đổi thứ hạng các phương án, và việc bỏ ví dụ Normal sai nhãn khỏi kho ví dụ không cải "
        "thiện kết quả có ý nghĩa thống kê (+0,011; p = 0,21).")


def ROOT_DATASET_FIG(FIG):
    return FIG.parents[1] / "dataset" / "figures"
