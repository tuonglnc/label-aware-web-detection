# Báo cáo Nghiên cứu: Truy xuất Nhận biết Nhãn phục vụ Phát hiện Tấn công Web dựa trên Mô hình Ngôn ngữ Lớn

## Chương 1: Giới thiệu Tổng quan đề tài

### 1.1. Bối cảnh và Động lực nghiên cứu

Các ứng dụng web hiện giữ vai trò quan trọng trong nhiều hoạt động như cung cấp dịch vụ trực tuyến, quản lý dữ liệu, thương mại điện tử và vận hành nội bộ. Phần lớn tương tác giữa máy khách và máy chủ web được thực hiện thông qua các yêu cầu HTTP. Vì vậy, việc phân tích nội dung và cấu trúc của HTTP request là một hướng tiếp cận có ý nghĩa trong việc nhận diện các dấu hiệu bất thường hoặc tấn công vào ứng dụng web [1][2]. Kẻ tấn công có thể đưa payload vào nhiều thành phần khác nhau của request, chẳng hạn như URI, tham số truy vấn, header hoặc body. Payload có thể biểu diễn dưới dạng chuỗi lệnh, ký tự đặc biệt, đường dẫn bất thường hoặc dữ liệu đã được mã hóa nhằm khai thác cách ứng dụng xử lý đầu vào không tin cậy.

Một số hướng tấn công thuộc phạm vi nghiên cứu, chẳng hạn SQL Injection, Path Traversal, Code Injection và OS Command Injection, đều khai thác khả năng ứng dụng diễn giải dữ liệu đầu vào như một phần của truy vấn, đường dẫn hoặc câu lệnh. Bên cạnh đó, HTTP Response Splitting có thể liên quan đến việc đưa các ký tự điều khiển vào dữ liệu request để ảnh hưởng đến cách máy chủ tạo phản hồi. OWASP tiếp tục xếp Injection vào nhóm rủi ro quan trọng trong an ninh ứng dụng web, cho thấy nhu cầu phát hiện và phân loại các dấu hiệu tấn công từ dữ liệu HTTP vẫn có ý nghĩa thực tiễn [3].

Các hệ thống phát hiện truyền thống thường sử dụng luật hoặc chữ ký để đối chiếu request với những mẫu tấn công đã biết. Cách tiếp cận này có ưu điểm là dễ kiểm tra và giải thích theo từng luật, nhưng hiệu quả phụ thuộc vào độ bao phủ của tập luật và công sức tinh chỉnh. Trong thực tế, một yêu cầu hợp lệ vẫn có thể chứa chuỗi giống payload tấn công, ví dụ nội dung HTML hoặc chuỗi ký tự đặc biệt được người dùng gửi hợp pháp. Hiện tượng này có thể làm tăng số lượng cảnh báo nhầm, đặc biệt khi hệ thống ưu tiên độ nhạy mà không có đủ ngữ cảnh để phân biệt nội dung hợp lệ với hành vi khai thác [4].

Các mô hình học máy và học sâu cung cấp khả năng học biểu diễn từ dữ liệu, nhưng thường cần một quy trình huấn luyện hoặc tinh chỉnh dành riêng cho bộ dữ liệu và nhiệm vụ. Trong khi đó, các Mô hình Ngôn ngữ Lớn (Large Language Models — LLMs) có thể xử lý request được biểu diễn dưới dạng văn bản theo hướng dẫn trong prompt. Kỹ thuật Học trong ngữ cảnh (In-Context Learning — ICL) cho phép cung cấp một số ví dụ minh họa gồm request và nhãn ngay trong prompt mà không cần cập nhật trọng số của LLM [5]. Đây là một hướng phù hợp với đề tài vì nhóm sử dụng các mô hình có sẵn và tập trung kiểm chứng ảnh hưởng của cách chọn ví dụ, thay vì huấn luyện một mô hình phân loại mới.

Tuy nhiên, hiệu quả của ICL phụ thuộc đáng kể vào chất lượng và mức độ phù hợp của các demonstrations. Một cách phổ biến là truy xuất những request có embedding gần query nhất, sau đó đưa các request này cùng nhãn vào prompt. Độ tương đồng về hình thức hoặc biểu diễn không bảo đảm rằng hai request có cùng bản chất nhãn. Hai request có thể chứa các token tương tự, có cấu trúc URI gần giống hoặc cùng sử dụng ký tự đặc biệt, nhưng một request là hợp lệ còn request kia chứa dấu hiệu tấn công. Khi đó, nếu các ví dụ gần nhất có nhãn không nhất quán với query, LLM có thể nhận được một ngữ cảnh gây nhiễu [6][7].

Động lực trực tiếp của đề tài là kiểm chứng liệu thông tin nhãn dự đoán ban đầu, được gọi là **prior**, có thể được sử dụng để xếp hạng lại các ứng viên truy xuất hay không. Thay vì thay thế hoàn toàn độ tương đồng embedding, phương pháp của nhóm giữ lại một tập ứng viên có độ tương đồng cao rồi cộng thêm một hệ số ưu tiên cho các ứng viên có nhãn trùng với prior. Cách thiết kế này cho phép khảo sát riêng tác động của thông tin nhãn trong bước chọn demonstrations, đồng thời không đòi hỏi huấn luyện hoặc fine-tune embedding model và LLM.

### 1.2. Phát biểu bài toán và Mục tiêu

#### 1.2.1. Phát biểu bài toán

Cho một HTTP request cần phân loại, ký hiệu là query \(q\), hệ thống cần dự đoán một trong sáu lớp đơn nhãn:

- `Normal`;
- `SQL Injection`;
- `Path Traversal`;
- `Code Injection`;
- `HTTP Response Splitting`;
- `OS Command Injection`.

Mỗi request trong kho ví dụ có một nhãn nguồn đi kèm. Nhãn nguồn là nhãn được cung cấp trong bộ dữ liệu sau khi lọc phạm vi nghiên cứu; nó được dùng làm nhãn tham chiếu trong đánh giá và làm nhãn của demonstrations. Nhãn nguồn không được đồng nhất với prior. **Prior** là nhãn dự đoán sơ bộ cho query, có thể được tạo bằng bỏ phiếu có trọng số của kNN hoặc bằng kết quả LLM zero-shot. Sau khi chọn demonstrations, LLM thực hiện dự đoán cuối cùng cho query. Như vậy, quy trình có ba loại thông tin cần phân biệt:

1. **Nhãn nguồn** của request trong dữ liệu;
2. **Prior** được tạo trước bước lựa chọn demonstrations;
3. **Nhãn dự đoán cuối cùng** do LLM hoặc cấu hình kNN trả về.

Bài toán trọng tâm không phải là huấn luyện một embedding space mới có chứa nhãn, mà là đánh giá một cơ chế **reranking nhận biết nhãn** trên các ứng viên đã được truy xuất bằng embedding có sẵn. Cụ thể, hệ thống truy xuất top-N ứng viên gần query từ retrieval pool đã được mã hóa, rồi chọn k demonstrations bằng một chiến lược đối chứng hoặc bằng công thức reranking dựa trên prior. Nhãn nguồn của query được giữ riêng cho đánh giá; chỉ cấu hình oracle dùng nhãn này làm prior để phân tích offline.

#### 1.2.2. Dữ liệu và phạm vi thực nghiệm

Đề tài sử dụng bộ dữ liệu **SR-BH 2020, phiên bản 1.2**. Dữ liệu gốc gồm các HTTP request được thu thập từ một website WordPress được đưa lên Internet trong 12 ngày vào tháng 7 năm 2020 [18]. Dữ liệu ban đầu có nhiều nhãn và có thể chứa request đa nhãn. Nhóm chỉ giữ các request có đúng một nhãn hoạt động trên toàn bộ taxonomy nguồn và nhãn đó thuộc sáu lớp đã chọn. Các lớp ngoài phạm vi bị loại, không được gộp thành `Normal`. Sau khi kiểm tra dữ liệu thiếu, cách ly request trùng nội dung nhưng mâu thuẫn nhãn và loại trùng, tập dữ liệu còn **466.267 request duy nhất** [19]. Con số này là quy mô dữ liệu sau tiền xử lý, không phải số request được đưa vào mỗi lần thực nghiệm LLM. Retrieval pool, validation và test được chia theo nhóm để hạn chế rò rỉ dữ liệu; nhãn test không được dùng để chọn cấu hình.

Đề tài đánh giá dấu hiệu tấn công dựa trên nội dung request và nhãn nguồn của dữ liệu. Kết quả phân loại không được diễn giải như một bằng chứng rằng payload đã khai thác thành công hệ thống đích. Nói cách khác, hệ thống đang giải quyết bài toán nhận diện và phân loại request theo nhãn dữ liệu, không thực hiện kiểm thử xâm nhập hoặc xác minh khả năng khai thác thực tế.

Biểu diễn phục vụ embedding ưu tiên `method`, `URI`, `protocol`, `body`, sau đó đến các header không rỗng. Biểu diễn trong prompt giữ các trường request dưới dạng JSON với thứ tự ưu tiên tương ứng. Cả hai giữ nguyên encoding của payload; các phép biến đổi dùng để gom nhóm dữ liệu không được áp dụng lên nội dung đưa vào model [19].

#### 1.2.3. Mục tiêu nghiên cứu

**Mục tiêu tổng quát** của đề tài là xây dựng và đánh giá một phương pháp lựa chọn demonstrations có sử dụng thông tin nhãn dự đoán ban đầu để hỗ trợ LLM phân loại HTTP request.

Các mục tiêu cụ thể gồm:

1. Nghiên cứu cấu trúc HTTP request, các nhóm tấn công trong phạm vi sáu lớp, phương pháp phát hiện tấn công web, LLM, ICL và truy xuất ví dụ dựa trên embedding.
2. Xây dựng pipeline xử lý request và retrieval pool trên bộ dữ liệu SR-BH 2020 đã lọc.
3. Sử dụng `all-MiniLM-L6-v2` để tạo embedding cho query và request trong pool mà không huấn luyện hoặc fine-tune encoder.
4. Truy xuất top-30 ứng viên theo cosine similarity, sau đó chọn bốn demonstrations để đưa vào prompt.
5. Tạo prior bằng hai hướng: bỏ phiếu có trọng số trên năm láng giềng gần nhất đối với cấu hình `C-kNN`, và dự đoán zero-shot từ cấu hình `A0` đối với cấu hình `C-LLM`.
6. Thiết kế cơ chế xếp hạng lại dựa trên độ tương đồng và mức trùng khớp giữa nhãn ứng viên với prior.
7. So sánh phương pháp đề xuất với các cấu hình zero-shot, ví dụ cố định, truy xuất thuần túy theo similarity, lựa chọn cân bằng giữa các lớp và kNN không dùng LLM.
8. Đánh giá đồng thời chất lượng phân loại, tính nhất quán của demonstrations, chi phí gọi LLM, số token và độ trễ.
9. Phân tích ảnh hưởng của prior đúng, prior sai và prior oracle để xác định điều kiện hoạt động cũng như giới hạn của cơ chế reranking.

Đề tài sử dụng mô hình có sẵn và không thực hiện huấn luyện hoặc fine-tune embedding model hay LLM. Vì vậy, đóng góp của đề tài nằm ở thiết kế pipeline truy xuất, tạo prior, reranking và đánh giá thực nghiệm có đối chứng, không phải ở việc đề xuất một kiến trúc neural mới.

#### 1.2.4. Câu hỏi nghiên cứu

Đề tài tập trung vào ba câu hỏi nghiên cứu sau:

- **RQ1:** Khi truy xuất theo embedding, mức độ xuất hiện của các ví dụ gần nhất nhưng khác nhãn nguồn với query là bao nhiêu, và hiện tượng này phân bố như thế nào giữa các lớp?
- **RQ2:** Việc xếp hạng lại bằng prior có cải thiện Macro-F1 và giảm tỷ lệ báo nhầm trên lớp `Normal` so với truy xuất theo similarity và lựa chọn luân phiên giữa các lớp hay không? Chi phí suy luận thay đổi như thế nào?
- **RQ3:** Prior đúng và prior sai ảnh hưởng như thế nào đến số lỗi được sửa, số lỗi mới phát sinh và kết quả theo từng lớp? Ngay cả khi dùng nhãn nguồn làm prior trong phân tích `C-oracle`, cơ chế reranking còn gặp hạn chế nào?

Các câu hỏi này giúp tách ba khía cạnh của phương pháp. RQ1 khảo sát bản thân vấn đề không nhất quán nhãn trong retrieval; RQ2 đánh giá hiệu quả tổng thể và chi phí của cơ chế reranking; RQ3 phân tích kết quả theo chất lượng prior, thông qua số lỗi được sửa và số lỗi mới phát sinh so với baseline. Các nhóm prior đúng và prior sai có thể khác nhau về độ khó của query, nên sự khác biệt giữa hai nhóm chưa đủ để kết luận quan hệ nhân quả độc lập của chất lượng prior.

### 1.3. Đóng góp của đề tài

#### 1.3.1. Khoảng trống nghiên cứu

Truy xuất demonstrations theo nội dung và sử dụng thông tin nhãn đã được nghiên cứu trong ICL [5][6]. Vì vậy, đề tài không đặt tính mới ở ý tưởng chung “đưa nhãn vào retrieval”. Khoảng trống thực nghiệm mà nhóm tập trung kiểm chứng là: **trên bài toán HTTP request sáu lớp, prior-based reranking với encoder và LLM cố định thay đổi chất lượng demonstrations, kết quả phân loại và chi phí như thế nào, đặc biệt khi prior sai?**

**Tương đồng biểu diễn và tính nhất quán nhãn.** Request gần nhau về cấu trúc hoặc token có thể thuộc các nhãn nguồn khác nhau. Đề tài đo hiện tượng này trên dữ liệu nghiên cứu trước khi đánh giá reranking. Một demonstration khác nhãn query vẫn có thể cung cấp ví dụ đối chiếu hữu ích; vì vậy, tỷ lệ trùng nhãn là chỉ số mô tả retrieval, chưa phải bằng chứng trực tiếp về lợi ích phân loại.

**Vai trò của prior trong một thiết kế inference-only.** CLL-RetICL kết hợp tương đồng câu–query với tương đồng câu–nhãn mà không thay đổi tham số mô hình [6]. Các hướng khác khai thác nhãn khi học biểu diễn hoặc huấn luyện retriever [8][9]. Đề tài kiểm chứng một lựa chọn cụ thể: giữ nguyên embedding, tạo một nhãn prior rời rạc bằng kNN hoặc LLM zero-shot, rồi cộng điểm cho các ứng viên trùng prior. Sự khác biệt này cần được đánh giá trên cùng dữ liệu và các baseline đã xác định, thay vì suy ra hiệu quả từ công trình khác.

**Lợi ích và lỗi phát sinh do ưu tiên prior.** Đề tài đối chiếu prior đúng, prior sai và oracle để phân tích khi nào reranking sửa lỗi hoặc tạo lỗi mới. Kết quả được diễn giải trong phạm vi encoder, tập ứng viên, số demonstrations và LLM đang xét; không mặc định rằng nhãn nhất quán hơn luôn cho kết quả tốt hơn.

**Đánh giá chất lượng đi cùng chi phí.** Hai nguồn prior có chi phí suy luận khác nhau. Vì vậy, bên cạnh Macro-F1 và FPR Normal, cần đối chiếu LCR@k, số lượt gọi LLM, token và độ trễ. Các tiêu chí này xác định liệu một thay đổi về chất lượng có đi kèm chi phí hợp lý trong thiết lập thực nghiệm hay không.

#### 1.3.2. Đóng góp của đề tài

Trong phạm vi báo cáo, các đóng góp chính được xác định như sau:

1. **Định nghĩa một bài toán kiểm chứng rõ ràng cho truy xuất nhận biết nhãn.** Đề tài khảo sát việc sử dụng prior để lựa chọn bốn demonstrations cho phân loại HTTP request sáu lớp trên SR-BH 2020 sau lọc.
2. **Xây dựng pipeline reranking không cần huấn luyện.** Pipeline kết hợp encoder có sẵn, cosine similarity và công thức cộng điểm theo prior. Đây là cơ chế hậu xử lý trên ứng viên truy xuất, không phải một mô hình embedding được fine-tune.
3. **So sánh hai nguồn prior.** `C-kNN` dùng prior từ bỏ phiếu có trọng số của năm láng giềng gần nhất; `C-LLM` dùng prior từ kết quả zero-shot của `A0`. Cách tách này cho phép đánh giá ảnh hưởng của một prior nhẹ, không dùng LLM, và một prior do LLM tạo ra.
4. **Thiết lập các cấu hình đối chứng có cùng bối cảnh đánh giá.** Các cấu hình `A0`, `A1`, `B`, `BAL`, `C-kNN`, `C-LLM` và `C-oracle` được sử dụng để phân biệt ảnh hưởng của zero-shot, demonstrations cố định, similarity, cân bằng nhãn, prior dự đoán và prior lý tưởng.
5. **Đánh giá cả chất lượng và chi phí.** Ngoài Macro-F1, precision, recall và F1 theo lớp, đề tài theo dõi FPR của lớp `Normal`, LCR@4, số lượt gọi LLM, số token và độ trễ.
6. **Phân tích rủi ro của prior.** Đề tài không chỉ tìm kiếm trường hợp reranking sửa được lỗi mà còn xem xét trường hợp reranking tạo lỗi mới, cũng như giới hạn còn tồn tại khi prior được giả định đúng trong phân tích oracle.

Những đóng góp trên cần được hiểu là đóng góp về thiết kế thực nghiệm và phân tích phương pháp. Báo cáo không tuyên bố đã tạo ra mô hình embedding mới, không tuyên bố đã huấn luyện LLM, và không xem các công trình multi-agent hoặc adversarial fine-tuning là thành phần của hệ thống đề xuất.

### 1.4. Cấu trúc báo cáo

Báo cáo đầy đủ được chia thành các chương như sau:

- **Chương 1 — Giới thiệu Tổng quan đề tài:** Trình bày bối cảnh phát hiện tấn công web, động lực sử dụng LLM và ICL, bài toán, phạm vi dữ liệu, mục tiêu, câu hỏi nghiên cứu, khoảng trống và đóng góp của đề tài.
- **Chương 2 — Cơ sở Lý thuyết:** Trình bày HTTP request và payload, LLM và ICL, lựa chọn demonstrations, quan hệ giữa retrieval-based ICL và RAG, reranking nhận biết nhãn, nguyên tắc đánh giá và các nghiên cứu liên quan.
- **Chương 3 — Thiết kế hệ thống và Phương pháp nghiên cứu:** Mô tả chi tiết bộ dữ liệu, tiền xử lý, embedding, retrieval pool, top-30, cách tạo prior, các cấu hình thực nghiệm, prompt và công thức reranking.
- **Chương 4 — Thực nghiệm và Đánh giá:** Trình bày thiết lập validation/test, các chỉ số Macro-F1, precision, recall, F1 theo lớp, FPR Normal, LCR@4, chi phí và độ trễ; sau đó phân tích RQ1–RQ3.
- **Chương 5 — Kết luận và Hướng phát triển:** Tóm tắt phát hiện chính, giới hạn của thiết kế và các hướng phát triển như hiệu chỉnh prior, mở rộng lớp, thử nghiệm nhiều encoder hoặc học trọng số reranking.

---

## Chương 2: Cơ sở Lý thuyết

### 2.1. Tổng quan về các phương pháp phát hiện Tấn công Web

Phát hiện tấn công web là quá trình phân tích dữ liệu liên quan đến hoạt động của ứng dụng web để nhận diện dấu hiệu độc hại. Dữ liệu có thể gồm HTTP request, HTTP response, access log, sự kiện máy chủ hoặc các dấu vết ứng dụng. Trong đề tài này, đơn vị phân tích là HTTP request và hệ thống thực hiện phân loại request theo sáu nhãn nguồn đã xác định.

HTTP là giao thức tầng ứng dụng sử dụng cơ chế trao đổi request–response giữa client và server [1]. Theo HTTP semantics, request thể hiện thao tác mà client muốn thực hiện trên một tài nguyên, cùng với các metadata cần thiết để server xử lý [2]. Với HTTP/1.1, request thường gồm request-line, các header, dòng trống phân cách và body nếu phương thức hoặc ứng dụng cần truyền dữ liệu [1].

Các thành phần này có thể chứa dữ liệu do người dùng kiểm soát. Query string và URI thường chứa tham số; body có thể chứa form data, JSON hoặc nội dung tải lên; header có thể chứa thông tin điều khiển hoặc metadata. Nếu ứng dụng xử lý dữ liệu đầu vào không an toàn, kẻ tấn công có thể đưa payload vào một hoặc nhiều thành phần nhằm thay đổi ngữ nghĩa xử lý của ứng dụng.

Trong nghiên cứu này, cần phân biệt hai khái niệm. **Payload** là phần dữ liệu có thể mang dấu hiệu phục vụ hành vi khai thác. **Nhãn nguồn** là lớp được gán cho toàn bộ request trong bộ dữ liệu. Một request được gán `SQL Injection` không có nghĩa rằng hệ thống đích chắc chắn đã bị khai thác thành công; nó chỉ cho biết request được ghi nhận hoặc phân loại theo lớp đó trong dữ liệu nghiên cứu [15].

#### 2.1.1. Các đặc trưng của Payload HTTP

HTTP request có thể được mô tả ở nhiều mức khác nhau. Việc lựa chọn cách biểu diễn ảnh hưởng trực tiếp đến khả năng truy xuất request tương tự.

**Đặc trưng cấu trúc HTTP.** Các thành phần cơ bản gồm method, URI, protocol, header và body. Method cho biết loại thao tác ở mức giao thức; URI và query có thể chứa đường dẫn hoặc tham số; header cung cấp metadata; body chứa dữ liệu được gửi trong request. Khi encoder giới hạn độ dài đầu vào, thứ tự trình bày có thể quyết định phần nào của request được giữ lại. Ưu tiên URI và body giúp giảm nguy cơ payload ở các trường này bị cắt, nhưng không bảo đảm toàn bộ request được mã hóa.

**Đặc trưng ký tự và token.** Payload web thường chứa các ký tự như dấu nháy, dấu ngoặc, dấu gạch chéo, dấu chấm, dấu bằng hoặc chuỗi mã hóa phần trăm. Các token cục bộ như `../`, `SELECT`, dấu phân cách câu lệnh hoặc chuỗi thẻ HTML có thể cung cấp tín hiệu để phân biệt các lớp. Tuy nhiên, cùng một ký tự hoặc token có thể xuất hiện trong cả request hợp lệ và request tấn công. Vì vậy, sự xuất hiện của token đơn lẻ không đủ để quyết định nhãn.

**Đặc trưng làm mờ và mã hóa.** Payload có thể được biểu diễn qua URL encoding, Unicode encoding, chuỗi escape hoặc nhiều lớp mã hóa. Nếu tiền xử lý tự động thay thế hoặc xóa các chuỗi này, hệ thống có thể làm mất tín hiệu quan trọng. Do đó, đề tài giữ nguyên các chuỗi đã mã hóa trong đầu vào dùng để phân loại, thay vì áp dụng quy tắc biến đổi phục vụ mục đích gom nhóm dữ liệu [15].

**Đặc trưng thống kê và thủ công.** Các đặc trưng thống kê và biểu diễn văn bản như TF-IDF, n-gram được sử dụng trong nghiên cứu phân loại payload [14]. Các đặc trưng này có thể hữu ích cho mô hình học máy chuyên biệt, nhưng đề tài hiện tại không xây dựng bộ đặc trưng thủ công để huấn luyện một classifier mới. Đề tài dùng encoder có sẵn để tạo vector phục vụ truy xuất ví dụ; lượng nội dung thực sự được mã hóa phụ thuộc vào giới hạn đầu vào của encoder.

**Sáu lớp trong phạm vi nghiên cứu.** Bảng dưới đây mô tả ý nghĩa vận hành của các lớp theo phạm vi phân loại của đề tài.

| Lớp | Mô tả khái quát trong bài toán |
|---|---|
| `Normal` | Request có nhãn nguồn duy nhất là `Normal`; nhãn này không bảo đảm request hoàn toàn không chứa dấu hiệu đáng nghi. |
| `SQL Injection` | Request có dấu hiệu đưa thành phần truy vấn hoặc biểu thức SQL vào dữ liệu đầu vào. |
| `Path Traversal` | Request có dấu hiệu truy cập đường dẫn ngoài phạm vi dự kiến, thường liên quan đến thao tác di chuyển qua thư mục. |
| `Code Injection` | Request có dấu hiệu đưa mã hoặc biểu thức cần được thông dịch vào đầu vào ứng dụng. |
| `HTTP Response Splitting` | Request có dấu hiệu sử dụng dữ liệu điều khiển dòng hoặc header để ảnh hưởng đến phản hồi HTTP. |
| `OS Command Injection` | Request có dấu hiệu đưa lệnh hệ điều hành vào dữ liệu được ứng dụng chuyển tiếp cho trình thực thi lệnh. |

Bảng trên chỉ mô tả nhãn phục vụ phân loại trong dữ liệu; nó không thay thế định nghĩa đầy đủ của từng lỗ hổng và không được dùng để kết luận khả năng khai thác trên một hệ thống cụ thể.

#### 2.1.2. Các hướng phát hiện tấn công web

Có thể chia các hệ thống phát hiện tấn công web thành một số hướng chính.

**Phát hiện dựa trên luật và chữ ký.** Hệ thống so sánh request với các mẫu hoặc điều kiện đã được định nghĩa. OWASP Core Rule Set là ví dụ về một tập luật được sử dụng trong WAF. Ưu điểm của hướng này là quyết định có thể truy vết đến từng luật. Hạn chế là tập luật có thể không bao phủ biến thể mới, và những nội dung hợp lệ nhưng có hình thức giống payload có thể tạo false positive [4].

**Phát hiện bất thường.** Hệ thống xây dựng mô tả về hoạt động bình thường và xem sai lệch so với mô tả đó là tín hiệu cần kiểm tra. Sai lệch không đồng nghĩa với tấn công, vì các ứng dụng thực tế có thể tạo ra nhiều request hợp lệ nhưng hiếm gặp. Do đó, phát hiện bất thường thường cần một bước điều tra hoặc phân loại bổ sung.

**Học máy truyền thống.** Các mô hình như logistic regression, random forest hoặc XGBoost có thể sử dụng TF-IDF, n-gram và đặc trưng thống kê để phân loại. Ưu điểm là dễ kiểm soát chi phí và có thể phù hợp với dữ liệu dạng chuỗi. Hạn chế là hiệu quả phụ thuộc vào cách thiết kế đặc trưng và chất lượng dữ liệu huấn luyện.

**Học sâu và mô hình Transformer.** CNN, RNN, BiLSTM hoặc Transformer có thể học biểu diễn phức tạp hơn từ chuỗi ký tự hoặc văn bản. Các mô hình này có khả năng nắm bắt quan hệ cục bộ và ngữ cảnh, nhưng thường cần huấn luyện hoặc tinh chỉnh theo nhiệm vụ. WAMM là một nghiên cứu liên quan về tinh lọc dữ liệu SR-BH và đánh giá các mô hình học máy, học sâu cho phân loại payload [14].

**LLM và phân loại theo prompt.** LLM có thể nhận request dưới dạng văn bản và đưa ra nhãn theo hướng dẫn. Trong thiết kế của đề tài, LLM không được fine-tune. Việc cải thiện ngữ cảnh được thực hiện thông qua chọn demonstrations, vì vậy câu hỏi chính chuyển từ “mô hình học bộ phân loại nào” sang “nên đưa ví dụ nào vào prompt”.

Các hướng trên có thể kết hợp với nhau. Đề tài sử dụng kNN như một baseline không LLM và dùng embedding retrieval như bước chuẩn bị demonstrations cho LLM. Đây không phải là một hệ thống WAF hoàn chỉnh, cũng không thay thế cơ chế thực thi luật hoặc quy trình xác minh an ninh.

### 2.2. LLM và Học trong ngữ cảnh (In-Context Learning)

LLM là các mô hình ngôn ngữ được huấn luyện trên lượng dữ liệu lớn và có khả năng xử lý chuỗi văn bản theo hướng dẫn. Trong an ninh mạng, LLM được nghiên cứu cho nhiều nhiệm vụ như phân tích log, giải thích cảnh báo, phân loại nội dung độc hại, hỗ trợ điều tra và phát hiện lưu lượng đáng ngờ. Lợi thế của LLM là có thể kết hợp nhiều tín hiệu trong một ngữ cảnh và sinh ra quyết định theo định dạng được yêu cầu.

Tuy nhiên, LLM không tự động bảo đảm rằng kết quả phân loại là đúng. Mô hình có thể chịu ảnh hưởng của prompt, ví dụ minh họa, giới hạn token, cách biểu diễn request và những sai lệch trong dữ liệu. Trong phát hiện tấn công web, request là dữ liệu không tin cậy; vì vậy prompt phải phân biệt rõ hướng dẫn hệ thống với nội dung request cần phân tích. Prompt của đề tài yêu cầu LLM coi HTTP request là dữ liệu không tin cậy, định nghĩa rõ sáu nhãn và trả về JSON có khóa `label`.

#### 2.2.1. Phân loại bằng demonstrations

Trong ICL, một demonstration là cặp đầu vào–nhãn được đặt trong prompt để minh họa nhiệm vụ. Với tập ví dụ \(D_q=\{(x_i,y_i)\}_{i=1}^{k}\), dự đoán có thể biểu diễn khái quát là:

\[
\hat{y}_q=f_{\theta}\big(\text{hướng dẫn},D_q,q\big).
\]

Tham số \(\theta\) của LLM được giữ nguyên. Các ví dụ cung cấp ngữ cảnh về cách ánh xạ nội dung request sang nhãn; mô hình vẫn phải đánh giá query theo nội dung của nó. Dự đoán của LLM không được định nghĩa bằng việc sao chép nhãn của ví dụ gần nhất hay lấy nhãn đa số.

Zero-shot không cung cấp demonstrations. Fixed few-shot dùng cùng một bộ ví dụ cho mọi query. Retrieval-based ICL chọn ví dụ riêng theo query từ một kho có nhãn. Nghiên cứu của Liu và cộng sự cho thấy lựa chọn ví dụ theo tương đồng có thể hữu ích trên các tác vụ NLP đã khảo sát [5]; kết quả đó là động lực kiểm chứng, không bảo đảm cùng mức lợi ích trên HTTP request.

#### 2.2.2. Chất lượng, thành phần và thứ tự ví dụ

Chất lượng demonstrations có nhiều khía cạnh: mức liên quan đến query, độ tin cậy của nhãn, lượng nội dung được giữ lại và thành phần các lớp. Tập ví dụ cùng nhãn có thể cung cấp tín hiệu nhất quán, nhưng ví dụ khác nhãn cũng có thể giúp làm rõ ranh giới phân loại. Do đó, cần đo chất lượng phân loại cùng với tỷ lệ nhất quán nhãn và sử dụng baseline cân bằng lớp để đối chiếu.

Thứ tự ví dụ cũng có thể ảnh hưởng đến kết quả ICL [17]. Trong thiết kế của đề tài, danh sách ví dụ được trình bày theo quy tắc cố định: ứng viên được chiến lược lựa chọn xếp hạng cao hơn được đặt gần query hơn. Quy tắc này không được coi là thứ tự tối ưu cho mọi mô hình. Vì reranking có thể thay đổi cả thành phần và thứ tự demonstrations, chênh lệch kết quả phản ánh tác động tổng hợp của chiến lược lựa chọn; chưa tách riêng hai yếu tố này nếu không có ablation tương ứng.

Khi so sánh các cấu hình, nhóm giữ chung LLM, hướng dẫn, định dạng đầu ra và quy tắc trình bày. Các cấu hình few-shot dùng cùng số ví dụ và giới hạn độ dài; zero-shot là đối chứng không có ví dụ. Các kiểm soát này giúp việc so sánh tập trung vào chiến lược lựa chọn demonstrations.

### 2.3. Truy xuất ví dụ cho ICL và quan hệ với RAG

#### 2.3.1. Kho truy xuất và cosine similarity

Retrieval pool là tập các cặp request–nhãn được phép sử dụng làm ví dụ. Nội dung request được đưa vào encoder để tạo vector; nhãn được lưu riêng và chỉ tham gia các bước lựa chọn có xét nhãn. Embedding của pool được tính trước và tái sử dụng. Với query mới, hệ thống tạo embedding của query rồi tìm các ứng viên gần nhất trong pool.

Nếu các vector được L2-normalize, cosine similarity được tính bằng tích vô hướng:

\[
\operatorname{sim}(q,d)=\mathbf{e}_q^{\mathsf{T}}\mathbf{e}_d.
\]

Hai vector được tạo bởi cùng encoder và có cùng số chiều. Similarity phản ánh độ gần trong không gian biểu diễn, không phải xác suất hai request có cùng nhãn. Với payload chứa token ngắn, chuỗi mã hóa hoặc cấu trúc bất thường, mức gần embedding cần được kiểm chứng bằng đánh giá retrieval và phân loại thực tế.

Hệ thống trước hết lấy top-N theo similarity, sau đó chọn k demonstrations. Reranking chỉ thay đổi thứ tự và thành phần được chọn trong tập ứng viên này; nó không thể bổ sung một ví dụ hữu ích đã nằm ngoài top-N.

#### 2.3.2. Phân biệt retrieval-based ICL và RAG truy hồi tài liệu

Công trình RAG của Lewis và cộng sự kết hợp mô hình sinh với truy xuất từ một kho tri thức cho các tác vụ NLP cần kiến thức [16]. Retrieval-based ICL dùng cùng ý tưởng tổng quát là bổ sung ngữ cảnh từ một kho bên ngoài, nhưng các đơn vị được truy xuất trong đề tài là **ví dụ request–nhãn** nhằm minh họa quyết định phân loại.

| Khía cạnh | RAG truy hồi tài liệu | Retrieval-based ICL trong đề tài |
|---|---|---|
| Đơn vị truy xuất | Tài liệu hoặc đoạn văn bản | Cặp HTTP request–nhãn nguồn |
| Vai trò của ngữ cảnh | Cung cấp thông tin, bằng chứng phục vụ câu trả lời | Cung cấp ví dụ về ánh xạ request sang nhãn |
| Đầu ra đang xét | Câu trả lời hoặc nội dung sinh theo tác vụ | Một nhãn trong taxonomy đã xác định |
| Cách dùng nhãn trong đề tài | Không phải đặc trưng định nghĩa chung của RAG | Nhãn ví dụ được đưa vào prompt; prior tham gia reranking |

Vì vậy, mô tả chính xác trọng tâm phương pháp là **retrieval-based ICL với prior-based label-aware reranking**. Thuật ngữ RAG được dùng để đặt phương pháp trong bối cảnh truy xuất bổ sung ngữ cảnh, không hàm ý hệ thống triển khai toàn bộ kiến trúc huấn luyện của công trình RAG gốc.

### 2.4. Truy hồi nhận biết nhãn (Label-Aware Retrieval)

Truy hồi nhận biết nhãn là hướng truy hồi sử dụng thông tin nhãn trong bước lựa chọn hoặc xếp hạng ví dụ, thay vì chỉ dựa trên tương đồng giữa đầu vào và ứng viên. Cần phân biệt ba mức độ sử dụng nhãn:

- **Truy hồi thuần similarity:** chỉ dùng độ tương đồng embedding, không xét nhãn ứng viên.
- **Truy hồi hoặc reranking có nhãn:** dùng nhãn ứng viên và một tín hiệu nhãn của query để ưu tiên hoặc loại bỏ ứng viên.
- **Huấn luyện biểu diễn có nhãn:** đưa nhãn vào quá trình học embedding hoặc hàm mất mát để thay đổi không gian vector.

Đề tài thuộc mức thứ hai. Nhãn nguồn của ứng viên được dùng ở bước reranking, còn prior của query được tạo trước bằng kNN hoặc LLM zero-shot. Encoder không nhận nhãn làm đầu vào và không được cập nhật trọng số. Đây là điểm cần nêu rõ để tránh nhầm lẫn giữa “label-aware retrieval” trong đề tài với “label-aware contrastive fine-tuning” của một số công trình liên quan.

**Prior và nhãn nguồn.** Prior của query được định nghĩa là nhãn dự đoán sơ bộ, không phải nhãn thật, không phải xác suất đã hiệu chỉnh và không mặc nhiên đúng. Nhãn nguồn \(y_d\) của ứng viên là thông tin có sẵn trong kho tham khảo. Cơ chế reranking kiểm tra điều kiện \(y_d=\operatorname{prior}(q)\). Nếu prior sai, phần thưởng nhãn có thể làm thứ hạng lệch khỏi nhóm đúng. Đây là lý do đề tài cần cấu hình `C-oracle` để phân tích giới hạn trong điều kiện prior được cung cấp bằng nhãn nguồn của query.

#### 2.4.1. Cơ chế reranking và vai trò của prior

Công thức ở mục 1.2.5 cộng \(\lambda\) cho ứng viên có nhãn nguồn trùng prior. Với \(\lambda=0\), thứ tự trở về baseline similarity. Với \(\lambda>0\), ứng viên trùng prior có thể vượt qua ứng viên khác nhãn nếu mức cộng bù được chênh lệch similarity. Đây là ưu tiên mềm, không bảo đảm toàn bộ k ví dụ đều có nhãn trùng prior. Nếu không có prior hợp lệ, triển khai quay về cách chọn theo similarity.

Prior kNN tổng hợp phiếu của các láng giềng, với trọng số dựa trên similarity. Prior LLM là dự đoán zero-shot được tạo trước khi lựa chọn demonstrations. Hai nguồn prior có kiểu lỗi và chi phí khác nhau; độ chính xác prior cao hơn chưa đủ bảo đảm Macro-F1 cuối cùng cao hơn, vì hiệu quả còn phụ thuộc vào những query bị sai và các ví dụ được chọn.

Cấu hình `C-oracle` thay prior dự đoán bằng nhãn nguồn của query để khảo sát điều kiện không có lỗi prior so với nhãn tham chiếu. Đây là phân tích offline có sử dụng thông tin không sẵn có khi suy luận thực tế. Kết quả oracle không phải cận trên toán học của mọi phương pháp lựa chọn ví dụ, cũng không bảo đảm cao hơn baseline trên mọi query.

#### 2.4.2. Đối chiếu với các hướng khai thác nhãn trong biểu diễn

Thông tin nhãn có thể tham gia retrieval theo nhiều cách. CLL-RetICL khai thác tương đồng câu–query và câu–nhãn mà không cập nhật tham số mô hình [6]. LaPR xây dựng biểu diễn chung ảnh–nhãn cho visual ICL, kết hợp các chuyên gia và bộ định tuyến theo query [9]. *Small Model, Big Retrieval* sử dụng nhãn trong fine-tuning tương phản để loại các ứng viên trùng nhãn khỏi tập mẫu âm khi phù hợp [8].

Các công trình này cung cấp cơ sở so sánh về vị trí sử dụng nhãn. Phương pháp của đề tài giữ nguyên encoder, không nối nhãn vào đầu vào embedding và chỉ cộng điểm sau truy xuất dựa trên một prior rời rạc. Thiết kế này thuận tiện cho so sánh có đối chứng, nhưng không làm thay đổi những hạn chế của không gian embedding ban đầu.

### 2.5. Nguyên tắc đánh giá và giới hạn diễn giải

#### 2.5.1. Chất lượng phân loại và nhất quán nhãn

Macro-F1 là trung bình F1 của sáu lớp, giúp các lớp có trọng số ngang nhau trong chỉ số tổng hợp. Cần đọc cùng precision, recall, F1 từng lớp và ma trận nhầm lẫn để nhận diện kiểu lỗi cụ thể. FPR Normal trong đề tài là tỷ lệ request mang nhãn nguồn `Normal` bị dự đoán thành một trong các lớp tấn công. Đây là báo nhầm so với nhãn dữ liệu, không phải kết quả xác minh request thực sự vô hại trên hệ thống đích.

Với tập demonstrations \(D_q\) gồm k phần tử, tỷ lệ nhất quán nhãn được định nghĩa:

\[
\operatorname{LCR@k}(q)=\frac{1}{k}\sum_{d\in D_q} I(y_d=y_q).
\]

Ở đây \(y_q\) là nhãn nguồn của query, chỉ dùng để tính chỉ số offline. LCR@k của một tập query là trung bình các giá trị trên tập đó. Trong cấu hình chính, chỉ số này được báo cáo tại k = 4. LCR cao không tự chứng minh demonstrations hữu ích hơn; cần đối chiếu với Macro-F1 và số lỗi được sửa hoặc tạo thêm.

Dự đoán lỗi API hoặc sai định dạng phải được giữ trong đánh giá và tính là sai, đồng thời báo cáo coverage. Trong triển khai, FPR Normal chỉ đếm dự đoán thành nhãn tấn công, không đếm đầu ra lỗi là một nhãn tấn công; vì vậy FPR thấp cần được đọc cùng coverage để tránh diễn giải sai khi hệ thống không trả lời được.

#### 2.5.2. Nhãn nguồn, prior và oracle

Nhiễu nhãn trong demonstrations và prior sai là hai hiện tượng khác nhau. Hiện tượng thứ nhất liên quan đến chất lượng annotation trong pool [7]; hiện tượng thứ hai là lỗi của bước dự đoán sơ bộ cho query. Nhóm giữ nhãn nguồn làm tham chiếu đánh giá, đồng thời ghi nhận giới hạn annotation và không coi mọi bất đồng giữa mô hình với dữ liệu là bằng chứng mô hình sai về ngữ nghĩa an ninh.

Phân tích prior đúng/sai đếm số trường hợp C sửa lỗi của B và số trường hợp C làm sai một query mà B dự đoán đúng. Đây là đối chiếu theo cùng query và theo nhóm chất lượng prior. Sự khác biệt giữa các nhóm có thể đồng thời phản ánh độ khó của query; không diễn giải nó như ước lượng nhân quả độc lập của prior.

Oracle giúp khảo sát khi thay prior bằng nhãn tham chiếu nhưng giữ nguyên các thành phần khác. Nếu oracle vẫn mắc lỗi, cần xem xét nội dung query, tập ứng viên, ví dụ được chọn, phần nội dung bị cắt và cách LLM sử dụng ngữ cảnh. Kết quả tổng hợp chưa tự xác định được nguyên nhân nào chi phối.

#### 2.5.3. Chi phí suy luận và đối chứng

| Cấu hình | Vai trò hoặc cách chọn ví dụ | Lượt gọi LLM logic/query |
|---|---|---:|
| `kNN` | Bỏ phiếu có trọng số từ các láng giềng; baseline không LLM | 0 |
| `A0` | Zero-shot; nguồn prior LLM | 1 |
| `A1` | Cùng một bộ demonstrations cố định cho mọi query | 1 |
| `B` | Top-k theo cosine similarity | 1 |
| `BAL` | Chọn luân phiên theo các lớp có mặt trong top-N | 1 |
| `C-kNN` | Reranking bằng prior kNN rồi phân loại | 1 |
| `C-LLM` | Zero-shot tạo prior, rồi reranking và phân loại | 2 |
| `C-oracle` | Reranking bằng nhãn nguồn của query; chỉ phân tích offline | 1 |

Số lượt gọi logic mô tả các bước cần thiết của phương pháp. Số yêu cầu API thực gửi có thể khác do cache hoặc retry. Khi đánh giá tổng chi phí `C-LLM`, cần cộng chi phí tạo prior A0 với lượt phân loại sau retrieval; nếu bảng chỉ báo token hoặc latency của lượt phân loại cuối thì phải ghi rõ phạm vi. kNN không gọi LLM nhưng vẫn có chi phí embedding và tìm láng giềng.

Giới hạn độ dài demonstrations giúp kiểm soát token nhưng có thể làm mất ngữ cảnh hoặc payload ở cuối request. Query được giữ nguyên trong prompt theo quy tắc triển khai, trong khi encoder vẫn có giới hạn độ dài riêng. Các thông số giới hạn, model và ngân sách được trình bày trong thiết lập phương pháp; không đồng nhất độ dài chuỗi với số token.

#### 2.5.4. So sánh trên cùng tập query

Các cấu hình được đối chiếu trên cùng tập query và nhãn tham chiếu. Paired bootstrap ước lượng khoảng tin cậy cho chênh lệch Macro-F1, còn kiểm định McNemar xét các cặp bất đồng đúng–sai giữa hai cấu hình. Hai cách đánh giá này xét các đại lượng khác nhau, nên cần báo cáo riêng và tránh diễn giải p-value McNemar như kiểm định trực tiếp cho chênh lệch Macro-F1.

Việc khóa cấu hình trước khi xem kết quả test và chia dữ liệu theo nhóm giúp hạn chế chọn cấu hình theo test và rò rỉ mẫu gần trùng [19][20]. Kết quả trên một dataset và các subset đã chọn chỉ hỗ trợ kết luận trong thiết lập đó; khả năng khái quát sang website, phân bố lớp hoặc họ payload khác cần được kiểm chứng riêng.

### 2.6. Các nghiên cứu liên quan và vị trí của đề tài

Nhóm công trình gần nhất về phương pháp là lựa chọn demonstrations bằng retrieval [5], khai thác thông tin nhãn trong retrieval [6][8][9] và ICL khi nhãn ví dụ bị nhiễu [7]. WAMM liên quan trực tiếp đến dữ liệu và phân loại payload web, nhưng hướng nghiên cứu tập trung vào tinh lọc dữ liệu và đánh giá mô hình [14]. Những khác biệt này giúp xác định đối tượng so sánh về ý tưởng, không thay thế các baseline được chạy trên cùng protocol.

Trong phạm vi an ninh mạng rộng hơn, MalRAG nghiên cứu truy xuất hỗ trợ nhận dạng lưu lượng độc hại tập mở [11]; PhishDebate dùng nhiều agent phân tích website lừa đảo [10]; CyberSleuth hỗ trợ điều tra sau sự cố [13]; ADRAG nghiên cứu phát hiện truy vấn có ý định độc hại với huấn luyện đối kháng và chưng cất [12]. Đây là các bối cảnh tham khảo, không phải các thành phần của pipeline phân loại HTTP request hiện tại. Hai lượt gọi ở `C-LLM` lần lượt phục vụ tạo prior và phân loại, không tạo thành hệ thống tranh luận đa tác nhân.

Các hướng học biểu diễn ở nhiều kích thước như Matryoshka có thể được khảo sát khi mở rộng nghiên cứu về chi phí embedding. Bản thực nghiệm hiện tại giữ cố định biểu diễn và không đánh giá hướng này. Trọng tâm của đề tài là đo tác động của lựa chọn demonstrations và reranking theo prior, với các đối chứng về chất lượng, lỗi phát sinh và chi phí suy luận.

---

## Tài liệu tham khảo

[1] R. Fielding, M. Nottingham và J. Reschke (Eds.), “HTTP/1.1,” RFC 9112, 2022. [RFC Editor](https://www.rfc-editor.org/rfc/rfc9112).

[2] R. Fielding, M. Nottingham và J. Reschke (Eds.), “HTTP Semantics,” RFC 9110, 2022. [RFC Editor](https://www.rfc-editor.org/rfc/rfc9110).

[3] OWASP Foundation, “A05:2025 Injection,” *OWASP Top 10:2025*. [OWASP](https://top10.owasp.org/2025/A05_2025-Injection/).

[4] OWASP CRS Project, “False Positives and Tuning,” *CRS Documentation*. [OWASP CRS](https://coreruleset.org/docs/2-how-crs-works/2-3-false-positives-and-tuning/).

[5] J. Liu, D. Shen, Y. Zhang, B. Dolan, L. Carin và W. Chen, “What Makes Good In-Context Examples for GPT-3?” trong *Proceedings of Deep Learning Inside Out (DeeLIO 2022)*, 2022, tr. 100–114. [ACL Anthology](https://aclanthology.org/2022.deelio-1.10/).

[6] C. Lin, K. Wu, P. Xiang, Y. Wu và O. Bai, “CLL-RetICL: Contrastive Linguistic Label Retrieval-based In-Context Learning for Text Classification via Large Language Models,” IJCNLP-AACL 2025, Findings, tr. 1575–1590. [ACL Anthology](https://aclanthology.org/2025.findings-ijcnlp.97/).

[7] J. Kang, D. Son, H. Song và B. Chang, “In-Context Learning with Noisy Labels,” *arXiv:2411.19581*, 2024. [arXiv](https://arxiv.org/abs/2411.19581).

[8] S. Jiang, D. Liu, F. Gonzalez, P. Herrero-Vidal, Y.-L. Chen, X. Chu và P. Sen, “Small Model, Big Retrieval: Unified Heterogeneous Retrieval via Multi-Label-Aware Contrastive Fine-Tuning,” trong *Proceedings of the 2026 Conference on Empirical Methods in Natural Language Processing: Industry Track*, 2026, tr. 2355–2368. [ACL Anthology](https://aclanthology.org/2026.emnlp-industry.140/).

[9] T. Luo, H. Pan, J. Wang, N. Lian, X. Chen, B. Chen, S.-T. Xia và C. Yuan, “Love Me, Love My Label: Rethinking the Role of Labels in Prompt Retrieval for Visual In-Context Learning,” *arXiv:2604.03657*, 2026. [arXiv](https://arxiv.org/abs/2604.03657).

[10] W. Li, S. Manickam, Y.-w. Chong và S. Karuppayah, “PhishDebate: An LLM-Based Multi-Agent Framework for Phishing Website Detection,” *arXiv:2506.15656*, 2025. [arXiv](https://arxiv.org/abs/2506.15656).

[11] X. Luo, C. Liu, G. Xiong, C. Yang, G. Gou, Y. Ren và Z. Li, “MalRAG: A Retrieval-Augmented LLM Framework for Open-set Malicious Traffic Identification,” *arXiv:2511.14129*, 2025. [arXiv](https://arxiv.org/abs/2511.14129).

[12] Y. Guo và cộng sự, “Adversarial Distilled Retrieval-Augmented Guarding Model for Online Malicious Intent Detection,” *arXiv:2509.14622*, 2025. [arXiv](https://arxiv.org/abs/2509.14622).

[13] S. Fumero, K. Huang, M. Boffa, D. Giordano, M. Mellia và D. Rossi, “CyberSleuth: Autonomous Blue-Team LLM Agent for Web Attack Forensics,” *arXiv:2508.20643*, 2025. [arXiv](https://arxiv.org/abs/2508.20643).

[14] H. Osama, O. Elebiary, Y. Qassim, M. Amgad, A. Maghawry, A. Saafan và H. Ghalwash, “Enhanced Web Payload Classification Using WAMM: An AI-Based Framework for Dataset Refinement and Model Evaluation,” *arXiv:2512.23610*, 2025. [arXiv](https://arxiv.org/abs/2512.23610).

[15] Nhóm đề tài, “Label-Aware Retrieval for LLM-Based Web Attack Detection,” *Báo cáo giữa kỳ*, 2026. [Bản lưu trong repository](../reports/progress/bao_cao_giua_ky.md).

[16] P. Lewis và cộng sự, “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” *arXiv:2005.11401*, 2020. [arXiv](https://arxiv.org/abs/2005.11401).

[17] Y. Lu, M. Bartolo, A. Moore, S. Riedel và P. Stenetorp, “Fantastically Ordered Prompts and Where to Find Them: Overcoming Few-Shot Prompt Order Sensitivity,” trong *Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, 2022, tr. 8086–8098. [ACL Anthology](https://aclanthology.org/2022.acl-long.556/).

[18] T. Sureda Riera, J. R. Bermejo Higuera, J. Bermejo Higuera, J. A. Sicilia Montalvo và J. J. Martínez Herráiz, “SR-BH 2020 multi-label dataset,” Harvard Dataverse, phiên bản 1.2, 2022. [DOI: 10.7910/DVN/OGOIXX](https://doi.org/10.7910/DVN/OGOIXX). Metadata nguồn của phiên bản được sử dụng được lưu tại `src/artifacts/data/source_metadata.json`.

[19] Nhóm đề tài, “Báo cáo Task 1 — Dataset và protocol cho Pipeline A,” ngày 19/10/2026. [Báo cáo xử lý dữ liệu và kiểm tra annotation](../reports/progress/task_1_dataset_va_protocol.md).

[20] Nhóm đề tài, “Khóa cấu hình trước khi chạy tập test,” ngày 20/10/2026. [Protocol thực nghiệm](../reports/protocol/cau_hinh_khoa.md).
