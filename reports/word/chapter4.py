"""Nội dung Chương 4 (Thực nghiệm) của báo cáo cuối kỳ. Mọi số liệu lấy từ src/artifacts/."""

W = 15.5  # bề rộng vùng chữ (cm)


def write_chapter4(r, FIG, ART):
    r.h1("THỰC NGHIỆM")
    r.box("Chương này trả lời ba câu hỏi bằng số liệu: (1) ví dụ giống nhất có hay khác nhãn không; (2) chọn ví dụ "
          "theo nhãn dự đoán có giúp LLM đoán đúng hơn không; (3) khi nào thì có, khi nào thì không. Đọc nhanh: mục 4.4 "
          "(kết quả chính), 4.7 (kết quả có đáng tin không) và 4.10 (tóm tắt).")

    # ------------------------------------------------------------------ 4.1
    r.h2("Dữ liệu thực nghiệm")
    r.p("Đề tài dùng bộ dữ liệu SR-BH 2020, phiên bản 1.2 (Sureda Riera và cộng sự, 2022). Nhóm tác giả đưa một website "
        "WordPress lên Internet trong 12 ngày của tháng 7/2020 và ghi lại mọi yêu cầu HTTP gửi tới bằng tường lửa "
        "ModSecurity, rồi gán nhãn thủ công hoặc bán tự động. File gốc có 907.815 bản ghi, 38 cột, 14 cột nhãn; một yêu "
        "cầu có thể mang nhiều nhãn cùng lúc.")
    r.fig("dist", ROOT_DATASET_FIG(FIG) / "sr_bh_class_distribution.png",
          "Phân bố 14 nhãn của SR-BH 2020 (trục ngang thang logarit)", width_cm=14)
    r.p("Cách đọc <<dist>>: mỗi thanh là một nhãn, con số cuối thanh là số yêu cầu mang nhãn đó. Trục ngang dùng thang "
        "logarit: mỗi vạch lớn gấp 10 lần vạch trước, nên Normal (525 nghìn) và HTTP Request Smuggling (1 nghìn) chênh "
        "nhau 500 lần dù thanh chỉ dài gấp khoảng hai lần. Hình cho thấy dữ liệu mất cân bằng rất nặng: nếu lấy mẫu "
        "ngẫu nhiên, gần như chỉ có Normal và SQL Injection. Vì thế các tập đánh giá được lấy cân bằng giữa các lớp.")
    r.p("[b]Lọc và chia dữ liệu.[/b] Nhóm chỉ giữ yêu cầu có đúng một nhãn thuộc sáu lớp: Normal, SQL Injection, Path "
        "Traversal, Code Injection, HTTP Response Splitting và OS Command Injection; bỏ yêu cầu trùng và cách ly những "
        "yêu cầu giống hệt nhau nhưng mâu thuẫn nhãn. Còn lại 466.267 yêu cầu. Những yêu cầu gần như giống hệt nhau (ví "
        "dụ chỉ khác một con số trong URL) được gom thành một nhóm, và cả nhóm phải nằm trọn trong một tập. Làm vậy để "
        "LLM không thể “chép đáp án” từ một yêu cầu sinh đôi nằm trong kho ví dụ (rò rỉ dữ liệu).")
    r.table("sets", "Các tập dữ liệu dùng trong thực nghiệm",
            ["Tập", "Số yêu cầu", "Dùng để làm gì"],
            [["Pool (kho ví dụ)", "3.000 (500/lớp)", "Nơi chọn ví dụ có đáp án đưa vào câu lệnh; không dùng để huấn luyện"],
             ["Validation", "200 (33–34/lớp)", "Chọn tham số và so sánh sơ bộ (giữa kỳ)"],
             ["Test 1–300", "300 (50/lớp)", "Kết quả chính, chạy một lần sau khi khóa cấu hình ngày 20/10/2026"],
             ["Test 301–600", "300 (50/lớp)", "Kiểm tra C-gated, khóa cấu hình riêng trước khi chạy"],
             ["Test mới", "300 (50/lớp)", "Đánh giá vòng cải tiến; không trùng yêu cầu hay nhóm với 600 yêu cầu test cũ"]],
            [3.2, 3.3, 9.0], aligns=["left", "center", "left"])
    r.p("[b]Lưu ý về nhãn.[/b] Tập con cân bằng giúp lớp nhỏ có đủ mẫu để chấm điểm, nhưng không giống tỷ lệ của lưu "
        "lượng thật (ngoài đời phần lớn yêu cầu là bình thường). Ngoài ra, nhãn của SR-BH 2020 có nhiễu: khoảng một "
        "phần tư đến gần một phần ba yêu cầu mang nhãn Normal thật ra chứa mã tấn công (phân tích ở mục 4.8). Vì vậy "
        "điểm số trong chương này đo mức khớp với nhãn của dataset, không phải khả năng phát hiện tấn công thật.")

    # ------------------------------------------------------------------ 4.2
    r.h2("Cài đặt thực nghiệm")
    r.p("Mọi phương án dùng chung một LLM, một câu lệnh hướng dẫn và cùng số ví dụ; chỉ khác cách chọn ví dụ. Nhờ vậy, "
        "nếu kết quả khác nhau thì nguyên nhân nằm ở cách chọn ví dụ chứ không phải yếu tố khác.")
    r.table("cfg", "Cấu hình chính của thí nghiệm",
            ["Thành phần", "Thiết lập"],
            [["LLM", "openai/gpt-oss-20b qua Groq; temperature = 0; reasoning_effort = low; tối đa 1.024 token trả lời. "
                     "Kiểm tra thêm với openai/gpt-oss-120b"],
             ["Embedding", "all-MiniLM-L6-v2 (chạy trên máy, không huấn luyện); vector 384 chiều; đọc tối đa 256 token"],
             ["Chọn ví dụ", "Lấy 30 ứng viên giống nhất trong pool 3.000, chọn 4 ví dụ; mỗi ví dụ cắt ở 500 ký tự"],
             ["Pipeline C", "điểm = độ giống + 0,1 × [nhãn ví dụ trùng nhãn dự đoán]; nhãn dự đoán từ kNN (5 láng giềng) "
                            "hoặc từ A0"],
             ["Chống “chỉnh cho đẹp số”", "Cấu hình và giả thuyết được ghi vào file khóa và đẩy lên GitHub trước mỗi lần "
                                          "chạy test (commit làm bằng chứng); không sửa gì sau khi xem kết quả test"],
             ["Ngân sách", "Một tài khoản Groq; chương trình tự dừng trước khi chi phí ước tính (tính giá gấp đôi) vượt "
                           "4,5 USD"]],
            [3.6, 11.9], aligns=["left", "left"])
    r.p("[b]Chấm điểm thế nào?[/b] Phần này giải thích các chỉ số bằng lời đơn giản.")
    r.bullets([
        "[b]Macro-F1[/b] (chỉ số chính, từ 0 đến 1, càng cao càng tốt): với mỗi lớp, xét hai câu hỏi “khi model nói là "
        "lớp X thì đúng bao nhiêu lần” và “trong các yêu cầu thật sự là X thì model bắt được bao nhiêu”, gộp thành điểm "
        "F1 của lớp; rồi lấy trung bình sáu lớp, mỗi lớp nặng như nhau, để lớp nào bị bỏ bê cũng kéo điểm xuống.",
        "[b]FPR Normal[/b] (càng thấp càng tốt): trong các yêu cầu bình thường, bao nhiêu phần trăm bị báo nhầm là tấn công.",
        "[b]LCR@4[/b]: trong 4 ví dụ được chọn, bao nhiêu cái cùng nhãn thật với yêu cầu. Đây chỉ là chỉ số chẩn đoán; "
        "ví dụ cùng nhãn nhiều hơn chưa chắc làm LLM đoán đúng hơn.",
        "[b]Khoảng tin cậy 95% (bootstrap)[/b]: bốc ngẫu nhiên lại tập đánh giá 2.000 lần để xem chênh lệch giữa hai "
        "phương án dao động trong khoảng nào. Nếu khoảng này chứa số 0 thì chưa đủ bằng chứng để nói hai phương án khác "
        "nhau (Efron & Tibshirani, 1993).",
        "[b]Kiểm định McNemar[/b]: chỉ đếm những yêu cầu mà hai phương án cho kết quả khác nhau, rồi xem sự chênh lệch "
        "có thể do may rủi hay không (McNemar, 1947). Khi so nhiều phương án cùng lúc, p-value được hiệu chỉnh Holm "
        "(Holm, 1979) để tránh một phương án “thắng do may”.",
    ])
    r.p("[b]Các phương án được so sánh[/b] đã mô tả ở Bảng 3.2 (Chương 3). Có thể hình dung LLM như một học "
        "sinh, trước mỗi câu hỏi được xem 4 bài mẫu có lời giải: A0 không được xem bài mẫu nào; A1 luôn xem cùng 4 bài; "
        "B xem 4 bài giống câu hỏi nhất; BAL xem bài mẫu đủ các loại; C đoán trước “câu này chắc là SQL Injection” rồi "
        "ưu tiên bài mẫu SQL Injection; C-oracle là phép thử “nếu đoán trước luôn đúng thì sao”, chỉ để phân tích vì "
        "ngoài đời không biết đáp án.")

    # ------------------------------------------------------------------ 4.3
    r.h2("Ví dụ giống nhất có cùng nhãn không?")
    r.p("Trước khi hỏi LLM, nhóm kiểm tra phần truy xuất: ví dụ giống yêu cầu nhất có mang cùng nhãn không. Trên tập "
        "test 1–300, [b]24,3%[/b] yêu cầu có ví dụ giống nhất mang nhãn khác, dù độ giống trung bình rất cao (0,956 trên "
        "thang tối đa 1). Con số trên validation (23,0%) và tập test mới (24,3%) gần như y hệt.")
    r.fig("rq1", ART / "retrieval/minilm/eval_validation/retrieval_overview.png",
          "(a) Tỷ lệ yêu cầu có ví dụ giống nhất khác nhãn, theo lớp; (b) tỷ lệ ví dụ cùng nhãn trong 4 ví dụ được chọn "
          "(validation)", width_cm=15.5)
    r.p("Ở phần (a) của <<rq1>>, cột càng cao thì lớp đó càng hay gặp “ví dụ giống nhất mà khác nhãn”. Normal (45,5%) và "
        "SQL Injection (39,4%) cao nhất: một yêu cầu SQL Injection thường chỉ là yêu cầu bình thường thêm vài ký tự như "
        "“+AND+1%3D1”. Phần (b) cho thấy B chọn được khoảng 0,8 ví dụ cùng nhãn ở các lớp tấn công “dễ” nhưng chỉ khoảng "
        "0,5 ở Normal và SQL Injection; C-kNN nâng tỷ lệ này lên; BAL thấp ở mọi lớp vì cố ý lấy đủ các loại.")
    r.box("Hiện tượng “giống nhau nhưng khác nhãn” có thật, chiếm khoảng một phần tư số yêu cầu, tập trung ở Normal và "
          "SQL Injection. Đây là lý do đề tài thử ưu tiên ví dụ theo nhãn.", title="Điều rút ra")

    # ------------------------------------------------------------------ 4.4
    r.h2("Kết quả chính trên tập test")
    r.p("Kết quả chính là 300 yêu cầu test đầu tiên, chạy một lần sau khi cấu hình đã khóa. <<main>> so mỗi phương án "
        "với B, phương án tốt nhất trên validation.")
    r.table("main", "Kết quả trên test 1–300 (gpt-oss-20b)",
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
    r.p("Cách đọc: cột “Chỉ PA đúng / chỉ B đúng” đếm những yêu cầu mà một bên đúng còn bên kia sai. Ví dụ A0 chỉ đúng "
        "riêng 5 câu, còn B đúng riêng 19 câu, nên B tốt hơn A0 rõ ràng (p = 0,007). Ngược lại, C-kNN đúng riêng 7 câu và "
        "B đúng riêng 13 câu: chênh lệch nhỏ, khoảng tin cậy chứa 0, nên chưa thể nói bên nào hơn.")
    r.p("Kết quả cho thấy: (1) LLM có ví dụ giống yêu cầu (B) tốt hơn hẳn LLM không có ví dụ (A0) và ví dụ cố định (A1); "
        "A1 thậm chí kém A0, tức ví dụ không liên quan còn làm LLM phân tâm. (2) C-kNN và C-LLM không vượt B. "
        "(3) C-oracle nhỉnh hơn B nhưng chưa có ý nghĩa thống kê trên 300 yêu cầu (mục 4.7 gộp thêm dữ liệu).")
    r.table("prior", "C so với B, tách theo nhãn dự đoán đúng hay sai (test 1–300)",
            ["Phương án", "Nhãn dự đoán", "Số yêu cầu", "C sửa lỗi của B", "C làm hỏng câu B đúng"],
            [["C-kNN", "Đúng", "224", "5", "2"], ["C-kNN", "Sai", "76", "2", "11"],
             ["C-LLM", "Đúng", "250", "1", "1"], ["C-LLM", "Sai", "50", "1", "7"]],
            [2.6, 2.8, 2.6, 3.6, 3.9], size=11)
    r.p("<<prior>> giải thích vì sao C không thắng. Khi nhãn dự đoán đúng, C sửa được vài lỗi của B. Khi nhãn dự đoán "
        "sai, C kéo các ví dụ sai lớp lên đầu và làm hỏng nhiều câu B đang đúng (C-kNN: hỏng 11, chỉ sửa 2). Nhãn dự đoán "
        "của kNN chỉ đúng khoảng 75% trên test, nên phần hại triệt tiêu phần lợi.")
    r.fig("f1sets", FIG / "final_f1_across_sets.png",
          "Macro-F1 của các phương án trên bốn tập đánh giá (dấu * : chỉ để phân tích)", width_cm=15.5)
    r.p("<<f1sets>> đặt kết quả của cả bốn tập cạnh nhau. Điểm tuyệt đối thay đổi giữa các tập (tập test mới khó hơn), "
        "nhưng thứ tự lớn thì giữ nguyên: B và các biến thể C ở nhóm trên, A0 và A1 ở nhóm dưới, kNN không dùng LLM "
        "thấp nhất.")
    r.box("Ví dụ phải giống yêu cầu mới giúp LLM. Ưu tiên ví dụ theo nhãn dự đoán (C) chưa hơn B, vì khi đoán sai nó "
          "gây hại nhiều hơn phần lợi khi đoán đúng.", title="Điều rút ra")

    # ------------------------------------------------------------------ 4.5
    r.h2("Kiểm tra với model lớn hơn")
    r.p("Để xem kết luận có phụ thuộc cỡ model không, nhóm chạy lại các phương án chính trên test 1–300 với "
        "gpt-oss-120b, lớn gấp khoảng 6 lần. Đây là thí nghiệm bổ sung, quyết định sau khi đã có kết quả 20b.")
    r.table("big", "So sánh gpt-oss-20b và gpt-oss-120b trên test 1–300 (Macro-F1)",
            ["Phương án", "gpt-oss-20b", "gpt-oss-120b"],
            [["A0: không ví dụ", "0,834", "0,793"], ["[b]B: 4 ví dụ giống nhất[/b]", "[b]0,881[/b]", "[b]0,869[/b]"],
             ["BAL", "0,865", "0,862"], ["C-kNN", "0,862", "0,866"], ["C-LLM", "0,861", "0,854"],
             ["C-oracle (phân tích)", "0,900", "0,880"]],
            [6.0, 3.5, 3.5])
    r.p("Kết luận giữ nguyên: B vẫn tốt nhất trong các phương án dùng được ngoài thực tế, C không vượt B. Điều bất ngờ là "
        "model lớn hơn lại kém hơn khi không có ví dụ (0,793 so với 0,834). Lý do chính: 120b gọi các payload như "
        "“;sleep 15;” là SQL Injection, trong khi dataset gán OS Command Injection. Khi có ví dụ trong câu lệnh, model "
        "học được quy ước gán nhãn của dataset, nên B của hai model gần ngang nhau. Model lớn hơn không tự động tốt hơn "
        "trên bài toán có quy ước nhãn riêng; ví dụ truy xuất giúp đưa model về đúng quy ước đó.")

    # ------------------------------------------------------------------ 4.6
    r.h2("Vòng cải tiến Pipeline C")
    r.p("Vì C chưa thắng B, nhóm thử hai hướng cải tiến. Nguyên tắc: chỉ dùng phương pháp có nguồn công bố rõ ràng, dùng "
        "đúng tham số mặc định của bài gốc, khóa cấu hình trước khi chạy test, và đánh giá trên dữ liệu chưa ai nhìn thấy.")
    r.p("[b]Hướng 1: C-gated[/b] (mô tả ở Chương 3) chỉ dùng nhãn dự đoán khi kNN đủ tự tin. Trên test 301–600, C-gated "
        "đạt 0,882 so với B 0,869 (+0,013; CI [−0,002; +0,030]; chỉ C-gated đúng 5 câu, chỉ B đúng 1 câu). C-gated làm "
        "hỏng 1 câu B đang đúng, trong khi C-kNN làm hỏng 4. Hướng đi đúng, nhưng chưa đủ bằng chứng thống kê.")
    r.p("[b]Hướng 2: sáu cách chọn ví dụ đã được công bố[/b], tóm tắt ở <<pub>>. Các phương án này được chạy trên "
        "validation, khóa cấu hình, rồi chạy cùng toàn bộ phương án cũ trên tập test mới gồm 300 yêu cầu.")
    r.table("pub", "Các phương pháp chọn ví dụ đã công bố được thử",
            ["Mã", "Ý tưởng (nói đơn giản)", "Nguồn", "Tham số"],
            [["B-MMR", "Chọn ví dụ vừa giống yêu cầu vừa khác nhau, tránh 4 ví dụ na ná nhau",
              "Carbonell & Goldstein (1998); Ye và cộng sự (2023)", "λ = 0,5 (mặc định của bài)"],
             ["B-CLL", "Cộng điểm ví dụ giống tên nhãn của nó hơn tên các nhãn khác",
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
    r.p("Cách đọc <<fresh>>: mỗi dòng là một phương án; chấm tròn là chênh lệch so với B, vạch ngang là khoảng tin cậy "
        "95%. Vạch nằm hẳn bên phải số 0 nghĩa là hơn B chắc chắn; vạch cắt qua 0 nghĩa là chưa phân biệt được với B. "
        "Dải màu vàng là mức dao động khi chạy lại cùng một câu lệnh (mục 4.7): chênh lệch nằm trong dải này không nên "
        "coi là khác biệt thật.")
    r.table("holm", "Kiểm định đã đăng ký trước trên tập test mới (McNemar, hiệu chỉnh Holm cho 7 phép so)",
            ["Phương án", "Macro-F1", "So với B", "Chỉ PA đúng / chỉ B đúng", "p Holm"],
            [["B (tham chiếu)", "0,833", "–", "–", "–"],
             ["B-MMR", "0,858", "+0,025", "13 / 6", "1,000"], ["B-ENN", "0,847", "+0,014", "7 / 3", "1,000"],
             ["C-gated", "0,841", "+0,008", "3 / 1", "1,000"], ["C-iter", "0,838", "+0,005", "3 / 2", "1,000"],
             ["B-CLL", "0,834", "+0,001", "13 / 13", "1,000"], ["C-kNN-ENN", "0,834", "+0,001", "3 / 3", "1,000"],
             ["ENS", "0,833", "+0,000", "0 / 0", "1,000"]],
            [3.6, 2.4, 2.4, 4.0, 2.4], size=11)
    r.p("Không phương án cải tiến nào hơn B có ý nghĩa thống kê (mọi p Holm đều bằng 1). Trong ba giả thuyết đã ghi trước "
        "khi chạy, hai giả thuyết đúng (không phương án nào vượt B; B hơn A0 rõ ràng, −0,070, p < 0,001), một giả thuyết "
        "sai: nhóm dự đoán B-CLL kém B, nhưng trên tập test mới hai bên bằng nhau. Kết quả sai giả thuyết vẫn được báo "
        "cáo đầy đủ.")
    r.p("Lý do từng phương pháp không giúp được nhiều:")
    r.bullets([
        "[b]B-MMR[/b] đổi chiều giữa hai tập: thấp hơn B 0,036 trên validation nhưng cao hơn 0,025 trên tập test mới, nên "
        "không thể kết luận. Ye và cộng sự áp dụng MMR cho bài toán suy luận nhiều bước, nơi đa dạng kỹ năng quan trọng; "
        "với phân loại yêu cầu HTTP, lợi ích chưa rõ.",
        "[b]B-CLL[/b] dựa vào độ giống giữa ví dụ và tên nhãn (“SQL Injection”…). Cách này hợp với văn bản tự nhiên mà "
        "bài gốc thử (đánh giá phim, tin tức), nhưng nội dung HTTP không gần với tên nhãn trong không gian embedding, "
        "nên chỉ tạo thiên lệch theo lớp.",
        "[b]ENN[/b] bỏ 24% kho ví dụ, kể cả những ví dụ khó nhưng đúng nhãn ở ranh giới Normal/SQL Injection.",
        "[b]C-iter[/b] lấy nhãn dự đoán từ chính câu trả lời của B: khi B sai thì nhãn dự đoán cũng sai, nên vòng hai "
        "hầu như không sửa được gì.",
        "[b]ENS[/b] chỉ khác B khi BAL và C-kNN cùng không đồng ý với B, điều rất hiếm (2/300 câu), nên gần như trùng B "
        "mà tốn gấp ba.",
    ])
    r.box("Các cách chọn ví dụ đã công bố, áp dụng đúng tham số gốc, không vượt được B một cách đáng tin trên dữ liệu "
          "HTTP. C-gated là hướng hứa hẹn nhất nhưng cần thêm dữ liệu để khẳng định.", title="Điều rút ra")

    # ------------------------------------------------------------------ 4.7
    r.h2("Kết quả có đáng tin không?")
    r.p("[b]LLM không trả lời hoàn toàn giống nhau giữa các lần chạy.[/b] Nhóm chạy lại B lần hai với đúng câu lệnh cũ. "
        "Trên validation, 6/200 câu trả lời đổi và Macro-F1 lệch 0,011; trên tập test mới, 5/300 câu đổi, Macro-F1 lệch "
        "0,011. Hiện tượng này đã được ghi nhận ở các nghiên cứu khác (Ouyang và cộng sự, 2025; Atil và cộng sự, 2024). "
        "Hệ quả: mọi chênh lệch nhỏ hơn khoảng 0,01 giữa các phương án chỉ nên xem là ngang nhau.")
    r.p("[b]Gộp nhiều tập để thấy xu hướng thật.[/b] Mỗi tập 300 yêu cầu cho khoảng tin cậy rộng cỡ ±0,03, nên một "
        "phương án có thể thắng ở tập này, thua ở tập kia chỉ do may rủi. Khi gộp các tập test không trùng nhau, khoảng "
        "tin cậy hẹp lại. Việc gộp chỉ dùng các kết quả đã có, không chỉnh gì thêm.")
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
    r.p("<<pooltbl>> là kết quả quan trọng nhất của đề tài. Trên 900 yêu cầu, C-kNN và B gần như hòa tuyệt đối (20 so "
        "với 19 câu). Nhưng khi nhãn dự đoán luôn đúng, C-oracle hơn B rõ ràng (+0,026, p = 0,004). Nghĩa là cách cộng "
        "điểm theo nhãn [b]có tác dụng[/b]; thứ đang thiếu là [b]nhãn dự đoán đủ chính xác[/b]. C-gated, cách tránh "
        "dùng nhãn dự đoán khi không chắc, nhỉnh hơn B ở cả hai tập nó được chạy, nhưng chưa vượt ngưỡng có ý nghĩa.")
    r.box("Kết luận định tính (B hơn zero-shot; C chỉ có lợi khi nhãn dự đoán đúng) lặp lại trên nhiều tập độc lập và có "
          "kiểm định, nên đáng tin. Chênh lệch nhỏ cỡ 0,01–0,02 giữa các phương án thì không đủ để kết luận.",
          title="Điều rút ra")

    # ------------------------------------------------------------------ 4.8
    r.h2("Phân tích lỗi: nhãn nhiễu ở lớp Normal")
    r.p("Ở mọi phương án, Normal là lớp yếu nhất: khoảng 30% yêu cầu “bình thường” bị báo là tấn công. Khi đọc từng yêu "
        "cầu bị báo nhầm, phần lớn lại chứa mã tấn công rõ ràng, ví dụ “/blog/wp-content/themes';cat /etc/passwd;'/...” "
        "hay “/blog/index.php/'\"<script>alert(1);</script>/oembed”. Với những câu này, LLM đoán đúng; nhãn Normal của "
        "dataset mới sai.")
    r.fig("cmb", ART / "reports/test/confusion_B_semantic_k4.png",
          "Ma trận nhầm lẫn của B trên test 1–300 (hàng: nhãn của dataset; cột: nhãn LLM dự đoán)", width_cm=12)
    r.p("Cách đọc <<cmb>>: mỗi hàng là nhãn của dataset, mỗi cột là nhãn LLM dự đoán; đường chéo là các câu đoán đúng. "
        "Phần lớn lỗi nằm ở hàng NORMAL, chủ yếu bị đoán thành OS Command Injection, đúng loại mã tấn công hay gặp trong "
        "các yêu cầu Normal sai nhãn.")
    r.p("Nhóm dùng một bộ quy tắc cố định chỉ nhìn nội dung yêu cầu (ví dụ có “sleep(”, “/etc/passwd”, thẻ script, lệnh "
        "shell) để đánh dấu “Normal đáng ngờ”. Kết quả: 139/500 ví dụ Normal trong kho (27,8%), 15/50 Normal ở test 1–300 "
        "và 14/50 ở test 301–600 là đáng ngờ. Đáng chú ý, cả 15/15 lần B báo nhầm Normal trên test 1–300 đều rơi vào "
        "nhóm đáng ngờ này.")
    r.table("noise", "Kết quả khi bỏ các yêu cầu Normal đáng ngờ khỏi tập đánh giá",
            ["Tập", "Phương án", "Macro-F1 gốc → khi bỏ", "FPR Normal gốc → khi bỏ"],
            [["Test 1–300", "A0", "0,834 → 0,873", "34,0% → 8,6%"],
             ["Test 1–300", "B", "0,881 → 0,927", "30,0% → 0,0%"],
             ["Test 1–300", "C-kNN", "0,862 → 0,901", "32,0% → 5,7%"],
             ["Test 301–600", "B", "0,869 → 0,910", "32,0% → 5,6%"],
             ["Test 301–600", "C-gated", "0,882 → 0,925", "30,0% → 2,8%"]],
            [3.2, 3.0, 4.6, 4.7], size=11)
    r.p("Bỏ các Normal đáng ngờ, Macro-F1 của mọi phương án tăng khoảng 0,04 và tỷ lệ báo nhầm Normal của B giảm từ 30% "
        "xuống 0–6%. [b]Thứ hạng giữa các phương án không đổi[/b], nên nhãn nhiễu không làm thay đổi kết luận so sánh; "
        "nó chỉ cho thấy con số tuyệt đối bị kéo thấp bởi nhãn sai của dataset. Hạn chế: bộ quy tắc được viết sau khi "
        "đã xem lỗi của B, và việc đọc kiểm tra 36 yêu cầu đáng ngờ chưa được chuyên gia bảo mật xác nhận.")

    # ------------------------------------------------------------------ 4.9
    r.h2("Chi phí và sản phẩm")
    r.p("Toàn bộ thực nghiệm (hơn 11.000 lượt gọi LLM được ghi trong sổ chi phí, trên cả hai model) tốn khoảng 1,5 USD thật, dưới giới hạn 5 USD "
        "nhóm tự đặt. Một yêu cầu với B dùng khoảng 1.500 token; A0 khoảng 630 token; C-LLM và C-iter cần hai lượt gọi. "
        "Thời gian trả lời trung vị khoảng 0,6–0,8 giây mỗi lượt gọi.")
    r.p("Sản phẩm đi kèm gồm: mã nguồn mở trên GitHub với 93 bài kiểm thử tự động; chương trình chạy tiếp được khi bị "
        "gián đoạn và tự dừng khi chạm ngân sách; các file khóa cấu hình kèm commit làm bằng chứng; và một ứng dụng demo "
        "(Streamlit). Trong demo, người dùng dán một yêu cầu HTTP và thấy cạnh nhau cách B và C chọn 4 ví dụ, nhãn dự "
        "đoán sơ bộ và nhãn LLM trả về. Demo có chế độ không cần API để trình diễn khi không có mạng.")

    # ------------------------------------------------------------------ 4.10
    r.h2("Tóm tắt chương")
    r.bullets([
        "Khoảng 24% yêu cầu có ví dụ giống nhất mang nhãn khác; nặng nhất ở Normal và SQL Injection.",
        "Ví dụ giống yêu cầu (B) giúp LLM rõ rệt so với không có ví dụ hay ví dụ cố định; kết quả lặp lại trên bốn tập và "
        "hai cỡ model.",
        "Ưu tiên ví dụ theo nhãn dự đoán (C) ngang B với nhãn dự đoán thực tế, nhưng hơn B có ý nghĩa khi nhãn dự đoán "
        "đúng: nút thắt là chất lượng nhãn dự đoán.",
        "Sáu phương pháp chọn ví dụ đã công bố không vượt B một cách đáng tin; C-gated hứa hẹn nhưng chưa đủ bằng chứng.",
        "LLM dao động khoảng 0,01 Macro-F1 giữa hai lần chạy; nhãn Normal của dataset có nhiễu đáng kể nhưng không đổi "
        "thứ hạng các phương án.",
    ])


def ROOT_DATASET_FIG(FIG):
    return FIG.parents[1] / "dataset" / "figures"
