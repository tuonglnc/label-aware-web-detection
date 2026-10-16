# Research Brief --- Label-Aware Retrieval for LLM-Based Web Attack Detection

## 0. Mục đích của tài liệu

Tài liệu này cung cấp context ban đầu cho một AI agent hỗ trợ xây dựng
**Research Proposal / Research Outline** cho đề tài:

> **Label-Aware Retrieval for LLM-Based Web Attack Detection**

Đây là research direction dành cho sinh viên năm 4 ngành **Mạng máy
tính**, định hướng **An toàn thông tin / Web Security / LLM for
Security**.

Agent cần dùng tài liệu này như **hypothesis/context ban đầu**, không
mặc định rằng mọi thiết kế bên dưới đã đúng. Cần tiếp tục kiểm chứng
literature, xác định research gap, thu hẹp scope và đề xuất experimental
methodology phù hợp.

------------------------------------------------------------------------

# 1. Ý tưởng đề tài

## 1.1. Tên đề tài

**Label-Aware Retrieval for LLM-Based Web Attack Detection**

Có thể hiểu là:

> **Truy hồi nhận biết nhãn cho phát hiện tấn công Web dựa trên LLM**

Đề tài nghiên cứu việc sử dụng thông tin **attack label** trong quá
trình retrieval để lựa chọn các examples/demonstrations phù hợp hơn cho
LLM khi phân loại Web Attack.

Ý tưởng cốt lõi:

> Thay vì chỉ retrieve các HTTP request có nội dung/semantic similarity
> cao với request cần phân loại, hệ thống sử dụng thêm thông tin về
> **label của các examples** để lựa chọn hoặc rerank demonstrations
> trước khi đưa vào LLM.

------------------------------------------------------------------------

# 2. Vấn đề nghiên cứu dự kiến

LLM có thể được sử dụng cho Web Attack Detection bằng cách cung cấp HTTP
requests/payloads và yêu cầu LLM phân loại:

-   Benign
-   SQL Injection
-   Cross-Site Scripting (XSS)
-   Path Traversal
-   Command Injection
-   v.v.

Một hướng có thể dùng **In-Context Learning (ICL)**:

``` text
Target HTTP Request
        +
Relevant labeled examples
        ↓
       LLM
        ↓
Attack Classification
```

Tuy nhiên, chất lượng ICL phụ thuộc vào việc chọn demonstrations.

Standard semantic retrieval thường làm:

``` text
Query
  ↓
Embedding
  ↓
Similarity Search
  ↓
Top-k examples
  ↓
LLM
```

Vấn đề:

> Hai examples có semantic similarity cao với query nhưng có thể có
> **label khác nhau**.

Ví dụ:

``` text
Query:
GET /search?q=select+from+users

Candidate A:
SELECT username FROM users
Label: Benign

Candidate B:
' UNION SELECT username,password FROM users--
Label: SQL Injection
```

Do đó, chỉ dựa vào semantic similarity có thể chọn demonstrations không
tối ưu.

Đề tài đặt câu hỏi liệu việc đưa **label information** vào
retrieval/reranking có giúp LLM phân loại Web Attack hiệu quả hơn hay
không.

------------------------------------------------------------------------

# 3. Research Question dự kiến

## Main Research Question

> **RQ: Does incorporating attack-label information into the retrieval
> process improve the effectiveness of LLM-based Web Attack Detection
> compared with conventional semantic retrieval?**

Diễn giải:

> Việc sử dụng thông tin nhãn tấn công trong quá trình retrieval có cải
> thiện hiệu quả phát hiện/phân loại Web Attack bằng LLM so với semantic
> retrieval thông thường hay không?

## Sub-questions có thể nghiên cứu

### RQ1

How does standard semantic retrieval perform for LLM-based Web Attack
Detection?

### RQ2

Can attack-label information improve the selection/ranking of in-context
demonstrations?

### RQ3

How does Label-Aware Retrieval affect different attack classes,
especially classes that are semantically similar to benign traffic or
other attack types?

### RQ4

How sensitive is the approach to retrieval parameters such as `k`, class
distribution, and label imbalance?

Các RQ trên chỉ là đề xuất ban đầu; agent cần xem literature và scope để
tinh chỉnh.

------------------------------------------------------------------------

# 4. Dataset đóng vai trò gì?

Dataset là thành phần nền tảng của đề tài, không chỉ dùng để test.

Mỗi record tối thiểu nên có:

``` text
HTTP Request / URL / Payload
+
Attack Label
```

Ví dụ:

  Request                                     Label
  ------------------------------------------- ----------------
  `GET /index?id=1`                           Benign
  `GET /index?id=1' OR 1=1--`                 SQLi
  `GET /search?q=<script>alert(1)</script>`   XSS
  `GET /file?name=../../etc/passwd`           Path Traversal

Dataset có 4 vai trò chính:

## 4.1. Retrieval Knowledge / Example Base

Dataset cung cấp các examples để retriever tìm demonstrations tương tự
query.

``` text
Dataset
   ↓
Embedding
   ↓
Vector Database
   ↓
Top-k examples
```

## 4.2. Label Source

Dataset cung cấp label cho từng example.

``` text
Example → SQLi
Example → XSS
Example → Benign
```

Thông tin này là nền tảng để xây dựng **Label-Aware Retrieval**.

## 4.3. ICL Demonstration Pool

Các examples được retrieve có thể được đưa vào prompt:

``` text
Example 1:
Request: ...
Label: SQL Injection

Example 2:
Request: ...
Label: SQL Injection

Example 3:
Request: ...
Label: XSS

Target:
Request: ...
```

LLM sau đó dự đoán label của target.

## 4.4. Ground Truth cho Evaluation

Test set cung cấp label thật để so sánh:

``` text
Ground Truth
     vs
Prediction
```

và tính:

-   Accuracy
-   Precision
-   Recall
-   F1
-   Macro-F1
-   Confusion Matrix
-   Per-class performance

------------------------------------------------------------------------

# 5. Dataset split dự kiến

Một thiết kế ban đầu:

``` text
                 Dataset
                    |
          +---------+---------+
          |                   |
          v                   v
 Retrieval Database        Test Set
          |                   |
          v                   |
   Demonstration Pool         |
          |                   |
          v                   |
         LLM <----------------+
                  |
                  v
             Prediction
                  |
                  v
         Compare with Label
```

Ví dụ:

``` text
80% → Retrieval / Demonstration Database
20% → Test Set
```

Tuy nhiên, tỷ lệ 80/20 chỉ là ví dụ. Agent cần xác định split hợp lý dựa
trên dataset cụ thể.

**Quan trọng: tránh data leakage.**

Test examples không được vô tình xuất hiện trong retrieval database dưới
dạng duplicate hoặc near-duplicate nếu điều đó làm evaluation không công
bằng.

------------------------------------------------------------------------

# 6. Pipeline đề xuất

Nên xây dựng ít nhất 3 experimental pipelines.

------------------------------------------------------------------------

## 6.1. Pipeline A --- LLM Baseline

Mục đích: đo khả năng của LLM khi không có retrieval.

``` text
HTTP Request
     ↓
    LLM
     ↓
Attack Label
```

Ví dụ output:

``` json
{
  "prediction": "SQL Injection"
}
```

------------------------------------------------------------------------

## 6.2. Pipeline B --- Standard Semantic RAG / Retrieval-ICL

Mục đích: baseline cho retrieval thông thường.

``` text
HTTP Request
     ↓
Embedding
     ↓
Vector Database
     ↓
Top-k semantic examples
     ↓
Prompt Construction
     ↓
LLM
     ↓
Attack Label
```

Retriever chỉ dựa trên semantic similarity.

------------------------------------------------------------------------

## 6.3. Pipeline C --- Label-Aware Retrieval

Đây là proposed method.

``` text
                         HTTP Request
                              |
                              v
                        Query Embedding
                              |
                    +---------+---------+
                    |                   |
                    v                   v
             Semantic Score       Label Information
                    |                   |
                    +---------+---------+
                              |
                              v
                    Label-Aware Ranking
                              |
                              v
                           Top-k
                              |
                              v
                             LLM
                              |
                              v
                       Attack Label
```

Một cách triển khai đơn giản có thể là:

``` text
FinalScore =
    α × SemanticSimilarity
  + β × LabelRelevance
```

Nhưng đây chỉ là **một hypothesis/design option**, không phải công thức
bắt buộc.

Agent cần nghiên cứu các phương án:

1.  Label filtering
2.  Label-aware reranking
3.  Label-aware scoring
4.  Label-aware embedding / representation learning

Trong scope của sinh viên năm 4, **label-aware reranking/scoring** có
thể là hướng thực tế hơn so với tự train một encoder phức tạp.

------------------------------------------------------------------------

# 7. Research comparison

Một experimental story tương đối rõ:

``` text
             Same Dataset
                   |
        +----------+----------+
        |          |          |
        v          v          v
      LLM       Standard    Label-Aware
    Baseline      RAG          RAG
        |          |            |
        v          v            v
     Metrics    Metrics      Metrics
        |          |            |
        +----------+------------+
                   |
                   v
              Comparison
```

Có thể so sánh:

  --------------------------------------------------------------------------
  Method         Retrieval      Label-aware    LLM            Metrics
  -------------- -------------- -------------- -------------- --------------
  LLM baseline   No             No             Yes            F1, Precision,
                                                              Recall

  Standard RAG   Semantic       No             Yes            F1, Precision,
                                                              Recall

  Proposed       Semantic +     Yes            Yes            F1, Precision,
                 label-aware                                  Recall
  --------------------------------------------------------------------------

Không nên chỉ báo cáo Accuracy vì Web Attack datasets có thể bị class
imbalance.

Ưu tiên:

-   Macro-F1
-   Per-class Precision / Recall / F1
-   Confusion Matrix
-   Accuracy
-   Micro-F1 nếu phù hợp

------------------------------------------------------------------------

# 8. Output của đề tài

Output không nhất thiết là một LLM mới.

Output dự kiến gồm:

## 8.1. Label-Aware Retrieval Module

Ví dụ:

``` text
retriever/
├── embedding.py
├── vector_store.py
├── label_aware.py
└── reranker.py
```

## 8.2. LLM-based Web Attack Detection Prototype

``` text
HTTP Request
     ↓
Retriever
     ↓
Top-k labeled demonstrations
     ↓
LLM
     ↓
Predicted Attack Type
```

## 8.3. Experimental Results

So sánh:

``` text
LLM
vs
Standard Retrieval + LLM
vs
Label-Aware Retrieval + LLM
```

## 8.4. Research Analysis

Phân tích:

-   Khi nào Label-Aware Retrieval cải thiện kết quả?
-   Khi nào không cải thiện?
-   Attack classes nào hưởng lợi?
-   Attack classes nào dễ bị nhầm?
-   `k` ảnh hưởng thế nào?
-   Class imbalance ảnh hưởng thế nào?
-   Semantic similarity và label relevance có quan hệ thế nào?

------------------------------------------------------------------------

# 9. Hard Cases --- phần quan trọng của dataset

Đề tài sẽ thuyết phục hơn nếu dataset có các trường hợp mà semantic
similarity đơn thuần dễ nhầm.

Ví dụ:

``` text
Query:
GET /search?q=select+from+users

Candidate A:
SELECT username FROM users
Label: Benign

Candidate B:
' UNION SELECT username,password FROM users--
Label: SQLi
```

Hoặc:

``` text
Query:
GET /search?q=<script>

Candidate A:
GET /search?q=<script>
Label: XSS

Candidate B:
GET /search?q=<script>
Label: Benign
```

Trong trường hợp thứ hai, cần xem xét context, annotation quality và
duplicate/near-duplicate issues.

Mục tiêu là tìm những trường hợp:

> **Semantic similarity cao nhưng attack labels khác nhau.**

Đây là loại dữ liệu có khả năng làm nổi bật lý do cần Label-Aware
Retrieval.

------------------------------------------------------------------------

# 10. Attack taxonomy dự kiến

Không nên bắt đầu với quá nhiều loại attack.

Một scope ban đầu có thể là:

``` text
Benign
SQL Injection
XSS
Path Traversal
Command Injection
```

Sau khi khảo sát dataset và literature, có thể điều chỉnh taxonomy.

Agent cần kiểm tra:

-   Dataset nào có các class này?
-   Label quality ra sao?
-   Class distribution thế nào?
-   Có duplicate/near-duplicate không?
-   HTTP request có đầy đủ context không?
-   Dataset có phù hợp với LLM input không?

Không nên tự động giả định rằng tất cả dataset Web Attack đều có
taxonomy giống nhau.

------------------------------------------------------------------------

# 11. Một số dataset candidate cần khảo sát

Agent nên tìm và đánh giá các dataset Web Attack phù hợp thay vì chọn
ngay một dataset.

Có thể khảo sát:

-   HTTP request / payload datasets
-   Web application attack datasets
-   SQLi/XSS datasets
-   OWASP-related datasets
-   CIC / Canadian Institute for Cybersecurity datasets nếu phù hợp
-   Các public dataset có labeled HTTP requests

Tiêu chí chọn:

1.  Có label rõ ràng.
2.  Có HTTP request/payload đủ thông tin.
3.  Có nhiều attack classes.
4.  Có đủ sample cho từng class.
5.  Có thể phân chia train/retrieval/test hợp lý.
6.  Có giấy phép sử dụng phù hợp.
7.  Có khả năng kiểm tra duplicate/data leakage.
8.  Có đủ hard cases cho nghiên cứu retrieval.

------------------------------------------------------------------------

# 12. Literature direction

Đề tài nằm tại giao điểm của ít nhất 3 hướng:

``` text
Web Attack Detection
        +
Retrieval / RAG / ICL
        +
Label-Aware Retrieval
```

Một số hướng literature cần khảo sát:

## 12.1. Retrieval-style In-Context Learning

Ý tưởng:

``` text
Query
 ↓
Retrieve demonstrations
 ↓
LLM
 ↓
Classification
```

Có các nghiên cứu về retrieval-style ICL cho classification.

## 12.2. Label-aware Retrieval / Label-aware ICL

Một số nghiên cứu gần đây nghiên cứu việc đưa label information vào
retrieval/ranking để lựa chọn demonstrations tốt hơn.

## 12.3. LLM-based Cybersecurity / Intrusion Detection

Khảo sát:

-   LLM for intrusion detection
-   LLM for Web Attack Detection
-   LLM + ICL for cybersecurity classification
-   RAG for cybersecurity
-   CyberRAG
-   LLM-based attack classification

## 12.4. Web Attack Detection

Khảo sát:

-   ML-based HTTP attack detection
-   Deep Learning for Web Attack Detection
-   Transformer-based Web Attack Detection
-   SQLi/XSS classification
-   Dataset limitations

------------------------------------------------------------------------

# 13. Research Gap cần chứng minh

Không nên viết ngay:

> "Chưa có ai làm Label-Aware Retrieval cho Web Attack Detection."

Phải kiểm tra literature trước.

Một research gap có thể tồn tại theo dạng:

> Existing work has explored LLM-based cybersecurity classification and
> retrieval-based in-context learning, while label-aware retrieval has
> been investigated in general text classification. However, the
> effectiveness of incorporating attack-label information into retrieval
> for LLM-based Web Attack Detection may not have been sufficiently
> evaluated.

Đây chỉ là **hypothesis về research gap**.

Agent phải:

1.  Search literature.
2.  Identify closest works.
3.  Build comparison table.
4.  Verify whether the proposed combination is genuinely underexplored.
5.  Avoid claiming novelty without evidence.

------------------------------------------------------------------------

# 14. Evaluation design

## Primary metrics

-   Macro-F1
-   Precision
-   Recall
-   Accuracy
-   Per-class F1
-   Confusion Matrix

## Retrieval-specific metrics có thể xem xét

-   Recall@k
-   Precision@k
-   Label consistency@k
-   Class coverage@k
-   Similarity distribution

## Ablation studies

Có thể nghiên cứu:

### Ablation A

``` text
Semantic Retrieval
vs
Semantic + Label-aware
```

### Ablation B

Thay đổi `k`:

``` text
k = 1
k = 3
k = 5
k = 10
```

### Ablation C

Thay đổi weight:

``` text
α / β
```

nếu sử dụng scoring function.

### Ablation D

Class imbalance:

``` text
Balanced retrieval
vs
Natural distribution
```

### Ablation E

LLM model:

Nếu resource cho phép, thử nhiều model để xem phương pháp có phụ thuộc
vào một LLM cụ thể hay không.

------------------------------------------------------------------------

# 15. Expected contribution

Một contribution hợp lý cho khóa luận:

> **A label-aware retrieval strategy for selecting in-context
> demonstrations in LLM-based Web Attack Detection.**

Cụ thể:

1.  Xây dựng pipeline Web Attack Detection dựa trên Retrieval + LLM.
2.  Đề xuất cơ chế đưa attack-label information vào retrieval/reranking.
3.  Xây dựng experimental comparison với:
    -   LLM-only
    -   Standard semantic retrieval
    -   Label-aware retrieval
4.  Đánh giá trên labeled Web Attack dataset.
5.  Phân tích ảnh hưởng của label-aware retrieval đối với từng attack
    class và các hard cases.

Không nhất thiết phải claim:

> "Propose a new LLM"

hoặc

> "Achieves state-of-the-art."

Mục tiêu phù hợp hơn là **đánh giá một phương pháp retrieval có kiểm
soát và có thực nghiệm rõ ràng**.

------------------------------------------------------------------------

# 16. Scope phù hợp với sinh viên năm 4 Mạng máy tính

## Có thể làm

-   Python
-   HTTP/Web basics
-   Web Security basics
-   Dataset preprocessing
-   Embeddings
-   Vector database
-   Retrieval
-   Reranking
-   Prompt engineering
-   LLM API/local LLM
-   Classification
-   Evaluation

## Không cần thiết ở giai đoạn đầu

-   Train LLM từ đầu
-   Fine-tune một LLM lớn
-   Xây foundation model
-   Xây SIEM hoàn chỉnh
-   Real-time production WAF
-   Bao phủ toàn bộ OWASP
-   Xây một vector database từ đầu

------------------------------------------------------------------------

# 17. Proposed minimal implementation

Một MVP có thể là:

``` text
Dataset
   ↓
Preprocessing
   ↓
Train/Retrieval/Test split
   ↓
Embedding
   ↓
Vector DB
   ↓
Semantic Retrieval
   ↓
Label-aware Reranking
   ↓
Top-k demonstrations
   ↓
Prompt
   ↓
LLM
   ↓
Attack Label
   ↓
Evaluation
```

Có thể bắt đầu với:

``` text
5 classes
+
1 dataset
+
1 embedding model
+
1 vector DB
+
1 LLM
+
3 pipelines
```

Sau khi MVP hoạt động mới mở rộng.

------------------------------------------------------------------------

# 18. Những câu hỏi agent cần trả lời tiếp

Agent hãy tiếp tục xây dựng Research Proposal bằng cách trả lời có nguồn
các câu hỏi sau:

### A. Problem

1.  Web Attack Detection hiện đang giải quyết vấn đề gì?
2.  ML/DL-based approaches có hạn chế gì?
3.  LLM-based detection có ưu điểm/hạn chế gì?
4.  Retrieval/ICL giải quyết vấn đề gì?
5.  Standard semantic retrieval có vấn đề gì khi examples có labels khác
    nhau?

### B. Dataset

6.  Dataset Web Attack nào phù hợp nhất với scope?
7.  Dataset có những attack classes nào?
8.  Label quality thế nào?
9.  Class imbalance ra sao?
10. Có duplicate/near-duplicate/data leakage không?
11. Có hard cases để chứng minh giá trị của label-aware retrieval không?

### C. Method

12. Chính xác "Label-Aware Retrieval" sẽ được định nghĩa thế nào?
13. Label information được đưa vào:
    -   filtering?
    -   reranking?
    -   scoring?
    -   embedding?
14. Công thức scoring/ranking nào phù hợp?
15. Có cần train một model mới không?
16. Nếu không train, contribution nằm ở đâu?

### D. Experimental Design

17. Baselines nào cần có?
18. Test split thế nào?
19. Retrieval database thế nào?
20. Metrics nào?
21. Ablation study nào?
22. Có cần nhiều LLM không?
23. Làm sao kiểm soát data leakage?

### E. Novelty / Research Gap

24. Những paper nào gần nhất?
25. Paper nào đã làm Label-Aware Retrieval?
26. Paper nào đã làm LLM + Web Attack Detection?
27. Paper nào đã làm Retrieval + Cybersecurity?
28. Có paper nào đã kết hợp cả ba chưa?
29. Nếu có, đề tài cần điều chỉnh contribution thế nào?

------------------------------------------------------------------------

# 19. Suggested Research Proposal structure

Agent có thể dùng cấu trúc sau để phát triển thành proposal:

``` text
1. Title
2. Background
3. Problem Statement
4. Motivation
5. Research Questions
6. Objectives
7. Related Work
8. Research Gap
9. Proposed Method
10. Dataset
11. Experimental Design
12. Evaluation Metrics
13. Expected Contributions
14. Expected Results
15. Scope and Limitations
16. Research Timeline
17. References
```

------------------------------------------------------------------------

# 20. Important instruction for the research agent

Không được mặc định rằng:

-   Label-aware retrieval chắc chắn tốt hơn standard retrieval.
-   Dataset nào cũng phù hợp.
-   LLM luôn tốt hơn ML/DL.
-   Research gap đã được chứng minh.
-   Phương pháp là novel chỉ vì kết hợp các kỹ thuật.
-   Accuracy cao đồng nghĩa hệ thống tốt.

Agent cần phân biệt rõ:

``` text
FACT
vs
HYPOTHESIS
vs
DESIGN CHOICE
vs
EXPECTED RESULT
vs
ACTUAL EXPERIMENTAL RESULT
```

Đặc biệt:

> **Không được viết kết quả thực nghiệm nếu chưa chạy experiment.**

------------------------------------------------------------------------

# 21. One-sentence research idea

Nếu cần giải thích đề tài trong một câu:

> **This research investigates whether incorporating Web Attack labels
> into the retrieval of in-context demonstrations can improve LLM-based
> Web Attack classification compared with conventional semantic
> retrieval.**

Hoặc đơn giản hơn:

> **"Nếu retriever biết nhãn của các mẫu Web Attack, nó có chọn examples
> tốt hơn cho LLM và từ đó phân loại attack tốt hơn RAG bình thường hay
> không?"**

------------------------------------------------------------------------

# 22. Current status

Đây là **research direction / initial research brief**, chưa phải
Research Proposal hoàn chỉnh.

Các phần cần agent tiếp tục thực hiện:

1.  Literature search.
2.  Related-work comparison.
3.  Dataset survey.
4.  Research-gap verification.
5.  Formal problem definition.
6.  Proposed retrieval formulation.
7.  Experimental methodology.
8.  Proposal draft.
9.  Feasibility check for a fourth-year Computer Networks student.
10. Identify risks and simplify scope if necessary.
