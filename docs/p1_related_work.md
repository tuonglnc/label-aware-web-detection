# P1: Literature Review — Label-Aware Retrieval for LLM-Based Web Attack Detection

> **Loại tài liệu:** Kết quả Phase 1 — Literature Review (v2)
> **Trạng thái:** ✅ Hoàn tất — 11 papers reviewed, gap xác nhận qua systematic search (29/09/2026)
> **Phân biệt:** 🔵 THỰC TẾ từ paper | 🟢 Ý NGHĨA với đề tài
> **Tham chiếu:** Search log chi tiết → `p1_systematic_search_log.md`

---

## 1. Tổng Quan Papers Đã Đọc

---

### [1] CyberRAG: An Agentic RAG Cyber Attack Classification and Reporting Tool

- **Tác giả:** Francesco Blefari, Cristian Cosentino, Francesco Aurelio Pironti, Angelo Furfaro, Fabrizio Marozzo
- **Năm/Venue:** July 2025 — arXiv:2507.02424 [cs.CR] / Future Generation Computer Systems
- **Dataset:** SQL Injection, XSS, SSTI payloads (web attack logs)

#### Abstract (tóm tắt)
Framework RAG dạng agentic cho phân loại và báo cáo tấn công mạng theo thời gian thực. LLM trung tâm điều phối: (i) các classifier fine-tuned chuyên biệt theo attack family; (ii) tool adapters cho enrichment/alerting; (iii) vòng lặp iterative retrieval-and-reason truy vấn knowledge base cho đến khi evidence đủ nhất quán để sinh báo cáo.

#### Method
- **Kiến trúc Agentic RAG:**
  1. *Central LLM Agent*: Điều phối toàn bộ pipeline, giao task cho các module.
  2. *Fine-tuned Specialist Classifiers* (BERT-family): Phân loại theo attack family (SQLi, XSS, SSTI).
  3. *Tool Adapters*: Enrichment và alerting.
  4. *Iterative Retrieval-and-Reason Loop*: Truy vấn domain-specific knowledge base lặp đi lặp lại cho đến khi evidence relevant và self-consistent.
- **Thiết kế:** Agentic (dynamic control flow + adaptive reasoning) — khác biệt với standard RAG pipeline.
- **Extensibility:** Thêm attack type mới chỉ cần thêm classifier, không cần retrain core agent.

#### 🔵 Label-Awareness
**Implicitly Label-Aware.** Specialist classifiers (BERT-family) xác định attack family (SQLi/XSS/SSTI) trước, kết quả đó condition toàn bộ iterative retrieval-and-reason loop. Retrieval loop chỉ tiếp tục cho đến khi evidence self-consistent với nhãn được phân loại — label awareness được thực hiện qua agentic control flow, không phải hard metadata filter.

#### Domain & Kết quả
- **Domain:** Web Attack Detection (SQL Injection, XSS, SSTI) từ HTTP payloads — **có liên quan trực tiếp đến đề tài**.
- **Metrics:** Accuracy >94% per class, final classification accuracy 94.92%; BERTScore 0.94; Expert score (GPT-4) 4.9/5.0.

#### Limitations (từ paper)
- Lỗi từ specialist classifier propagate xuống retrieval (error cascade).
- Chưa đánh giá trên các attack type ngoài SQLi/XSS/SSTI.
- Iterative retrieval loop tốn kém computation hơn single-pass RAG.

#### 🟢 Ý nghĩa với đề tài
- **Bằng chứng trực tiếp và gần nhất** với đề tài: CyberRAG cũng làm Web Attack (SQLi/XSS/SSTI) + RAG + LLM.
- CyberRAG dùng specialist classifier để label trước, sau đó iterative retrieval được condition theo label — một dạng label-aware retrieval.
- **Khác biệt quan trọng:** CyberRAG dùng ICL-style demonstration selection không được đề cập — tập trung vào *report generation* hơn là *few-shot classification*. Không có ablation so sánh label-aware vs vanilla retrieval để đo impact của label-awareness.

---

### [2] From Detection to Response: A Deep Learning and Retrieval-Augmented Generation Framework for Network Intrusion Mitigation

- **Tác giả:** Md Navid Bin Islam, Sajal Saha
- **Năm/Venue:** May 2026 — arXiv:2605.17960 [cs.CR]
- **Dataset:** CICIDS2018, UNSW-NB15

#### Abstract (tóm tắt)
Framework 2 tầng: (1) Ensemble DNN phân loại lưu lượng mạng (Benign/DoS/DDoS) + SHAP attribution, (2) Hybrid RAG pipeline (BM25 + Dense + Cross-Encoder reranker) truy xuất tài liệu chuẩn NIST/MITRE để sinh báo cáo ứng phó bằng LLaMA-3 8B.

#### Method
- **Stage 1:** 3 mạng DNN nhị phân (One-vs-Rest): Benign-vs-Rest, DoS-vs-Rest, DDoS-vs-Rest. Top-5 SHAP features được trích xuất.
- **Stage 2 — Hybrid RAG:**
  - BM25 (lexical) + `bge-small-en-v1.5` FAISS (semantic).
  - Score fusion: 0.60×Semantic + 0.40×BM25.
  - Cross-Encoder reranker (`ms-marco-MiniLM-L-6-v2`).
  - Knowledge base: 5,234 chunks từ NIST SP 800-61, SP 800-94, MITRE ATT&CK, CIS Controls.

#### 🔵 Label-Awareness
**Explicitly Label-Conditioned (implicit, không phải hard filter).** Query đưa vào RAG là chuỗi ghép:
`"Attack class: DoS | Anomalous features: Flow Bytes/s = ... | Flow Duration = ..."` — predicted label được embed vào query string. Chunks trong KB có metadata `traffic_relevance_label`. Khi query có chứa từ "DoS", retriever tự nhiên ưu tiên chunks tagged "DoS" thông qua BM25 term matching.

**Nhưng KHÔNG có hard filter:** Retriever tìm trên toàn bộ 5,234 chunks, không filter theo label trước. Không có chỉ số đo Label Consistency Rate.

#### Domain & Kết quả
- **Domain:** Network Intrusion Detection (CICIDS2018, UNSW-NB15) — **không phải Web Attack (HTTP request)**.
- **Attack classes:** Chỉ Benign/DoS/DDoS, không có SQLi/XSS/Path Traversal.
- **Detection:** 99.84% (CICIDS2018), 95.30% (UNSW-NB15).
- **Retrieval:** Precision@5 = 0.91, Recall@5 = 0.84, MRR = 0.87.
- **Generation so với Vanilla LLM:** ROUGE-1 +32.5%, BLEU +244.1%, BERTScore +4.4%.

#### Limitations (từ paper)
- Chỉ cover DoS/DDoS, chưa cover multi-stage APT hay web application attacks.
- SHAP features nhạy cảm với high correlation.

#### 🟢 Ý nghĩa với đề tài
- Framework gần nhất với ý tưởng đề tài về kiến trúc.
- **Quan trọng:** Retrieval của [2] là **label-conditioned nhưng KHÔNG label-aware thuần tuý** — nhãn được embed vào query string, không có filtering/reranking explicit theo label.
- **Research gap:** [2] không đo đạc xem label conditioning có thực sự giúp ích không (không có ablation: "with vs without label in query"). Không thực nghiệm trên Web Attack (HTTP payload).
- **Đề tài có thể kế thừa:** Hybrid retrieval architecture, nhưng áp dụng cho Web Attack + đo đạc impact của label-aware selection một cách có kiểm soát.

---

### [3] In-Context Learning with Noisy Labels

- **Tác giả:** Junyong Kang, Donghyun Son, Hwanjun Song, Buru Chang
- **Năm/Venue:** November 2024 — arXiv:2411.19581 [cs.CL]
- **Dataset:** MRPC (paraphrase), SST-5 (sentiment), Tweet (hate speech). Models: GPT-2-Neo (2.7B), Llama2-7B, Mistral-7B.

#### Abstract (tóm tắt)
Nghiên cứu và giải quyết hiện tượng suy giảm hiệu năng LLM ICL khi các demonstrations trong prompt chứa nhãn sai/nhiễu. Đề xuất phương pháp **Rectification**: fine-tune GPT-2 nhỏ bằng LoRA để nhìn chuỗi K demonstrations và sinh ra chuỗi K nhãn đã hiệu chỉnh trước khi đưa vào LLM chính.

#### Method
- **Vấn đề được formalize:** Có r% demonstrations trong prompt bị flip label. ICL performance drops khi r tăng.
- **Proposed Method — Rectification:**
  - Auxiliary GPT-2 (LoRA) nhận chuỗi K demonstrations làm input, output là chuỗi K corrected labels.
  - Chỉ cần 10% clean data để train.
  - Hoạt động trước khi LLM chính nhận prompt.
- **Baselines so sánh:** Weighting (gắn confidence score), Reordering (đặt low-confidence lên trước), Selection (loại bỏ dưới ngưỡng).

#### 🔵 Label-Awareness
**Có — theo hướng noise correction.** Phương pháp không dùng label để *select* demonstrations, mà dùng để *correct* labels của demonstrations đã được retrieved. Label information được dùng **sau** retrieval.

#### Kết quả
- GPT-2-Neo trên MRPC: không có Rectification → accuracy từ 78.4% → 47.8% khi noise 50%; **với Rectification → 76.2%** (gần như không sụt).
- Data efficiency: 10% clean data đủ để đạt kết quả tương đương 100% clean data.

#### 🟢 Ý nghĩa với đề tài
- **Nền tảng lý thuyết quan trọng nhất:** Chứng minh quantitatively rằng noisy labels trong demonstrations gây ra accuracy drop + instability.
- **Áp dụng cho đề tài:** Nếu Vanilla Retrieval kéo về demonstrations có label sai (cross-class contamination — lấy Benign khi cần SQLi), đây là lý do label-aware selection cần thiết.
- **Điểm khác biệt với đề tài:** [3] giải quyết noise *sau* retrieval (correction). Đề tài muốn ngăn noise ngay từ *trong* quá trình retrieval (prevention = label-aware selection).
- **Hạn chế áp dụng:** [3] chỉ test trên NLP tasks chung (sentiment, paraphrase), chưa test trên Web Attack/cybersecurity domain.

---

### [4] DemoShapley: Valuation of Demonstrations for In-Context Learning

- **Tác giả:** Shan Xie, Man Luo, Chadly Daniel Stern, Mengnan Du, Lu Cheng
- **Năm/Venue:** October 2024 — arXiv:2410.07523 [cs.CL]
- **Dataset:** BoolQ, FinancialPhraseBank, Adult (fairness), Toxi-text-3M. Models: GPT-J-6B, ChatGPT-3.5, Llama3, Mistral-7B.

#### Abstract (tóm tắt)
Áp dụng game-theoretic Shapley value để đo lường đóng góp của từng demonstration trong tập prompt vào hiệu năng của LLM. DemoShapley tính Shapley value cho mỗi candidate demonstration, từ đó: (1) chọn demonstrations có giá trị cao nhất, (2) tự động phát hiện mislabeled data (Shapley âm/thấp), (3) giảm demographic bias.

#### Method
- **Core:** Mỗi demonstration `i` có Shapley value = expected marginal contribution khi thêm vào prompt `P`: `V(P∪{i}, f) - V(P, f)`.
- **Beta-DemoShapley:** Weighted version ưu tiên cardinality nhỏ → tối ưu cho low-shot ICL.
- **Monte Carlo estimation** với Gelman-Rubin convergence diagnostics.
- **Vai trò trong pipeline:** Post-retrieval valuation layer — đánh giá và lọc demonstrations đã được retrieved bởi kNN/BM25/dense.

#### 🔵 Label-Awareness
**Gián tiếp — qua Shapley.** Demonstrations có nhãn sai sẽ có Shapley value âm/thấp → tự động bị loại. Không explicitly dùng label để filter, nhưng label quality ảnh hưởng gián tiếp qua performance metric.

#### Kết quả
- Outperforms LOO, Influence Functions, CondAcc. Ví dụ: BoolQ (16-shot) Beta-DemoShapley 0.574 vs LOO 0.535.
- **Noise detection:** Xác định đúng 3/3 flipped labels trong top-10 candidates thấp nhất.
- **Fairness:** Giảm đáng kể Demographic Parity Difference.

#### 🟢 Ý nghĩa với đề tài
- **Cung cấp góc nhìn lý thuyết:** Demonstration chất lượng kém (sai nhãn) có thể có Shapley âm (harmful cho LLM).
- **Áp dụng tiềm năng:** DemoShapley có thể dùng như metric để *validate* chất lượng của Label-Aware Retrieval offline (so sánh Shapley distribution của demonstrations từ Vanilla vs Label-Aware).
- **Limitation cho scope đề tài:** Monte Carlo tốn kém. Không phù hợp dùng trong inference pipeline real-time. Dùng offline để phân tích là hợp lý.

---

### [5] CLL-RetICL: Contrastive Linguistic Label Retrieval-based ICL for Text Classification ⭐

- **Tác giả:** Chaohao Lin, Kaida Wu, Peihao Xiang, Yanzhao Wu, Ou Bai
- **Năm/Venue:** 2025 — Findings of IJCNLP-AACL 2025
- **Dataset:** Multiple NLP text classification benchmarks

#### Abstract (tóm tắt)
Framework retrieval-based ICL cho text classification tích hợp linguistic label information vào quá trình chọn demonstrations. Kết hợp sentence-query similarity + sentence-label similarity để đảm bảo demonstrations phù hợp cả về ngữ nghĩa lẫn nhãn.

#### Method
- **Integrated Similarity:** Score = f(sentence-query similarity, sentence-label similarity)
- **No Parameter Tuning:** Không cần fine-tune embedding model hay LLM
- **Contrastive approach:** Dùng linguistic label semantics (tên nhãn) để tính similarity

#### 🔵 Label-Awareness
**Explicitly Label-Aware.** Tích hợp label similarity trực tiếp vào retrieval scoring — demonstrations được chọn phải relevant cả về nội dung lẫn nhãn.

#### 🟢 Ý nghĩa với đề tài
- **⭐ Paper gần nhất về phương pháp** — cùng ý tưởng label-aware retrieval cho ICL classification
- **Khác biệt quan trọng:**
  - CLL-RetICL làm NLP text classification chung, **không phải cybersecurity/Web Attack**
  - Không có **ablation tường minh** so sánh label-aware vs vanilla retrieval
  - Không đo **Label Consistency@k**
  - Không có **hard case analysis** cho security payloads có semantic overlap cao
- **Đề tài kế thừa:** Ý tưởng tích hợp label info vào scoring, áp dụng cho domain Web Attack

---

### [6] BFAD: Behavioral Function-Aware Detection for WebShell ⭐⭐

- **Tác giả:** (2025)
- **Năm/Venue:** 2025 — arXiv:2504.13811 / COLM 2025
- **Dataset:** WebShell benchmarks (PHP code)

#### Abstract (tóm tắt)
Framework cải thiện LLM detection WebShell bằng 3 components: Critical Function Filter, Context-Aware Code Extraction, và Weighted Behavioral Function Profiling (WBFP) để chọn ICL demonstrations dựa trên behavioral function similarity.

#### Method
- **Critical Function Filter:** Lọc PHP functions liên quan security (command execution, file manipulation)
- **Context-Aware Code Extraction (CACE):** Trích xuất code segments quan trọng nhất, phù hợp context window
- **Weighted Behavioral Function Profiling (WBFP):** Chọn demonstrations dựa trên behavior-weighted, function-level similarity score

#### 🔵 Label-Awareness
**Implicitly Label-Aware qua behavior profiling.** Demonstrations được chọn theo behavioral function similarity — gián tiếp ưu tiên examples cùng loại attack behavior.

#### Domain & Kết quả
- **Domain:** Cybersecurity — **WebShell detection** (PHP code analysis), **không phải Web Attack HTTP payload**
- **Metrics:** F1 improvement +13.82% trung bình; GPT-4 + BFAD vượt SOTA
- **LLMs tested:** GPT-4, LLaMA-3.1-70B, Qwen-2.5-Coder-14B, Qwen-2.5-Coder-3B

#### 🟢 Ý nghĩa với đề tài
- **⭐⭐ Paper gần nhất về domain** — cybersecurity + ICL demo selection + domain-specific awareness
- **Khác biệt quan trọng:**
  - BFAD phân tích **PHP code** (function-level), đề tài phân tích **HTTP request payloads** (payload-level)
  - BFAD dùng **function profiling** để chọn demos, đề tài dùng **label information** trực tiếp
  - BFAD **không có ablation** so sánh với vanilla retrieval (không có Pipeline B baseline)
  - BFAD **không đo Label Consistency@k**
- **Đề tài bổ sung:** Mang ý tưởng domain-specific demo selection từ PHP WebShell sang HTTP Web Attack

---

### [7] RDES: Demonstration Selection via Reinforcement Learning

- **Tác giả:** (2025)
- **Năm/Venue:** 2025 — arXiv:2412.03966 / ICML 2025
- **Dataset:** Multiple NLP benchmarks, 14 LLMs

#### Abstract (tóm tắt)
RL-based framework (Q-learning, PPO) tối ưu hoá chọn demonstrations cho ICL, maximize relevance + label diversity.

#### 🔵 Label-Awareness
**Explicitly Label-Aware via diversity.** Label distribution được dùng trực tiếp để quantify diversity — RL agent tối ưu balanced representation.

#### 🟢 Ý nghĩa với đề tài
- **Confirm:** Label diversity/distribution matters cho ICL demo selection
- **Limitation cho scope:** RL approach quá phức tạp cho khoá luận — cite as theoretical motivation, không replicate

---

### [8] L2D: Label Distribution Divergence for Demo Selection

- **Tác giả:** (2025)
- **Năm/Venue:** 2025 — arXiv:2511.10675

#### Abstract (tóm tắt)
2-stage demo selection: TopK semantic retrieval + Label Distribution Divergence minimization (via fine-tuned BERT-like SLM).

#### 🔵 Label-Awareness
**Explicitly Label-Aware.** Fine-tune SLM để estimate label distributions → chọn demos có label distribution gần nhất với test input.

#### 🟢 Ý nghĩa với đề tài
- Confirm rằng label distribution alignment cải thiện ICL
- Method (fine-tune SLM) khác approach đề tài (simpler label filtering/reranking)

---

### [9] Comparative Analysis of Demo Selection Algorithms

- **Tác giả:** (2024)
- **Năm/Venue:** 2024 — arXiv:2410.23099

#### Abstract (tóm tắt)
Systematic evaluation 6 demo selection algorithms trên 5 datasets. Findings: performance varies significantly; some methods fail to beat random; more demos ≠ better.

#### 🟢 Ý nghĩa với đề tài
- **Methodological reference:** Justify experimental design choices
- Important finding: random selection là baseline mạnh — đề tài cần beat random convincingly

---

### [10] Liu et al. 2022 — What Makes Good In-Context Examples

- **Tác giả:** Jiachang Liu, Dinghan Shen, Yizhe Zhang, Bill Dolan, Lawrence Carin, Weizhu Chen
- **Năm/Venue:** 2022 — DeeLIO Workshop, ACL 2022 / arXiv:2101.06804

#### Key finding
Semantic similarity (KNN retrieval) là strong heuristic cho demo quality. Encoder fine-tuned trên task-related data → better retrieval.

#### 🟢 Ý nghĩa với đề tài
- **Foundational paper** — established retrieval-based ICL paradigm
- **Vanilla semantic retrieval = Pipeline B baseline** của đề tài

---

### [11] Rubin et al. 2022 — EPR (Learning To Retrieve Prompts)

- **Tác giả:** Ohad Rubin, Jonathan Herzig, Jonathan Berant
- **Năm/Venue:** 2022 — NAACL 2022

#### Key finding
Train dense retriever bằng LLM probability signal → significantly outperforms BM25 và generic dense retrievers.

#### 🟢 Ý nghĩa với đề tài
- **Foundational paper** — established trained-retriever-for-ICL paradigm
- Đề tài không train retriever (quá scope), nhưng cite as reference for retrieval-ICL pipeline

---

## 2. Bảng So Sánh Tổng Hợp (Related Work Comparison Matrix — Updated 29/09/2026)

| Tiêu chí | [1] CyberRAG | [2] Det-to-Resp | [3] Noisy Labels | [4] DemoShapley | **[5] CLL-RetICL** | **[6] BFAD** | **Đề tài** |
|---|---|---|---|---|---|---|---|
| **Focus** | Agentic RAG classification & reporting | End-to-end IDS + RAG response | ICL robustness dưới noisy labels | Demonstration valuation cho ICL | **Label-aware ICL retrieval cho text classification** | **Domain-specific ICL demo selection cho WebShell** | **Label-aware ICL retrieval cho Web Attack** |
| **Domain** | Web Attack (SQLi/XSS/SSTI) | Network Intrusion (DoS/DDoS) | NLP chung | NLP chung | **NLP chung** | **Cybersecurity — WebShell (PHP)** | **Web Attack (HTTP payload)** |
| **Web Attack (HTTP)?** | ✓ (SQLi, XSS, SSTI) | ✗ | ✗ | ✗ | ✗ | ✗ (PHP code) | ✓ |
| **ICL Demo Selection?** | ✗ (report gen) | ✗ (response gen) | ✗ (noise correction) | ✗ (valuation) | **✓ Retrieval** | **✓ WBFP** | ✓ **Retrieval** |
| **Label-Aware?** | Implicit | Soft (query embed) | Post-hoc | Indirect (Shapley) | **✓ Explicit (label sim)** | **✓ Implicit (behavior)** | ✓ **Explicit filter/rerank** |
| **Ablation LA vs Vanilla?** | ✗ | ✗ | N/A | N/A | **✗** | **✗** | ✓ **Core contribution** |
| **LCR@k metric?** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| **Metrics chính** | Acc=94.92%, BERTScore=0.94 | Detection=99.84%, P@5=0.91 | Acc drop: 78%→48% | Noise detection 3/3 | Outperforms standard retrieval | F1 +13.82% | Macro-F1, LCR@k, per-class |

> **Bảng bổ sung** (papers methodology/foundational — không so sánh trực tiếp):
> - **[7] RDES** (ICML 2025) — RL for demo selection, label distribution diversity
> - **[8] L2D** (2025) — Label Distribution Divergence
> - **[9] Comparative Analysis** (2024) — Survey 6 demo selection algorithms
> - **[10] Liu 2022** — Foundational: KNN retrieval for ICL
> - **[11] Rubin 2022 (EPR)** — Foundational: trained retriever for ICL

---

## 3. Phân Tích Research Gap (Xác Nhận Qua Systematic Search 29/09/2026)

### 3.1. Những gì đã được nghiên cứu 🔵

1. **RAG cho Cybersecurity** đã được nghiên cứu ([1], [2]): RAG cải thiện chất lượng phân tích/report trong cybersecurity.
2. **Label conditioning trong Cybersecurity RAG** đã thực hiện — [1] dùng specialist classifier rồi condition iterative retrieval loop; [2] embed label vào query string.
3. **Noisy labels trong ICL** làm giảm accuracy nghiêm trọng, có thể >30% ([3]).
4. **Demonstration quality/valuation** ảnh hưởng ICL performance ([4]).
5. **🆕 Label-aware demo selection cho ICL text classification** đã được nghiên cứu trong NLP ([5] CLL-RetICL, [7] RDES, [8] L2D) — dùng label similarity, label distribution, RL.
6. **🆕 Domain-specific ICL demo selection cho cybersecurity** đã có 1 paper ([6] BFAD — WebShell via behavioral function profiling).
7. **🆕 Retrieval-based ICL** là paradigm đã established ([10] Liu 2022, [11] Rubin 2022 EPR).

### 3.2. Research Gap — XÁC NHẬN ✅

> **Tuyên bố dựa trên:** 11 papers reviewed + systematic search 6 queries trên Google Scholar (29/09/2026).

**Gap 1 — Label-aware retrieval cho ICL chưa áp dụng cho Web Attack HTTP payload:**
- [5] CLL-RetICL, [7] RDES, [8] L2D làm label-aware retrieval, nhưng **chỉ NLP text classification** (sentiment, paraphrase, topic)
- [6] BFAD làm cybersecurity ICL demo selection, nhưng **WebShell PHP code** (khác HTTP request payloads)
- Chưa có paper nào kết hợp **label-aware retrieval + ICL + Web Attack Detection từ HTTP request**

**Gap 2 — Không có controlled ablation Label-Aware vs Vanilla:**
- [1] CyberRAG, [2] Detection-to-Response, [5] CLL-RetICL, [6] BFAD — tất cả dùng label-aware hoặc domain-specific selection nhưng **không so sánh tường minh với vanilla semantic retrieval**
- Chưa có bằng chứng định lượng đo **isolated impact** của label-awareness

**Gap 3 — Label Consistency@k chưa được đo:**
- Không paper nào đo `LCR@k` — metric đo trực tiếp chất lượng demonstration pool về mặt label alignment

**Gap 4 — Hard case analysis cho HTTP payloads chưa có:**
- Web Attack HTTP requests có đặc thù: semantic overlap cao giữa benign/malicious (chia sẻ SQL/HTML syntax)
- Phân tích này chưa được thực hiện trong bất kỳ related work nào

### 3.3. Research Gap Statement (FINAL — v2)

> *Label-aware demonstration selection for in-context learning has been explored in NLP text classification (CLL-RetICL, Lin et al. 2025; RDES, 2025; L2D, 2025), and domain-specific ICL demonstration selection has been applied to cybersecurity via behavioral function profiling for WebShell detection (BFAD, 2025). However, based on our systematic literature search, the specific combination of (1) label-aware retrieval for ICL demonstration selection, (2) applied to Web Application Attack classification from HTTP request payloads (SQLi, XSS, Path Traversal, etc.), with (3) a controlled ablation study measuring the isolated impact of label-awareness (Label-Aware vs. Vanilla Retrieval), and (4) Label Consistency Rate as a retrieval quality metric, has not been investigated.*

### 3.4. Positioning Contribution

| Contribution | Novelty basis |
|---|---|
| **Domain application** | Label-aware ICL retrieval → Web Attack HTTP payload (vs NLP text [5][7][8], vs PHP code [6]) |
| **Ablation study** | Controlled comparison LA vs Vanilla vs No-retrieval (missing in [1][2][5][6]) |
| **LCR@k metric** | New metric cho retrieval-ICL quality evaluation (not used in any related work) |
| **Hard case analysis** | HTTP payload-specific semantic overlap analysis (not studied) |

---

## 4. Relevance Map — Vị Trí Đề Tài Trong Literature (Updated)

```
                    CYBERSECURITY DOMAIN
                           ↑
          [1] CyberRAG     |    [2] Detection-to-Response
        (Web Attack,       |   (Network IDS,
         agentic RAG)      |    Hybrid RAG)
                           |
                    [6] BFAD ←── ★ ĐỀ TÀI ★
                  (WebShell,  |  (Web Attack HTTP,
                   PHP code,  |   label-aware retrieval,
                   WBFP)      |   explicit ablation,
                              |   LCR@k metric)
                              |
VANILLA ──────────── LABEL-AWARE ──────────── RETRIEVAL
RETRIEVAL             |                    
[10] Liu 2022         |    [5] CLL-RetICL (NLP, label sim)
[11] Rubin 2022 (EPR) |    [7] RDES (NLP, RL + label diversity)
                      |    [8] L2D (NLP, label dist divergence)
                      |
      [3] ICL Noisy   |    [4] DemoShapley
        Labels        |   (valuation)
      (motivation)    |
                      ↓
                  NLP DOMAIN
```

---

## 5. Kết Luận Phase P1 — Literature Review (Final)

**5 bài học lớn nhất từ 11 papers:**

1. **Từ [1]+[2]:** Label conditioning trong cybersecurity RAG cải thiện retrieval relevance, nhưng chưa có controlled ablation.
2. **Từ [3]:** Noisy labels trong ICL gây accuracy drop >30% — đây là *motivation định lượng* cho label-aware selection.
3. **Từ [4]:** Demonstrations sai nhãn có Shapley value âm (harmful) — framework lý thuyết.
4. **🆕 Từ [5]+[7]+[8]:** Label-aware demo selection đã nghiên cứu cho NLP text classification — ý tưởng không mới trong NLP, nhưng **chưa áp dụng cho Web Attack**.
5. **🆕 Từ [6]:** Domain-specific ICL demo selection cho cybersecurity đã bắt đầu (BFAD) — nhưng chỉ WebShell, không HTTP payload, không ablation.

**Đề tài đứng ở vị trí:** Mang ý tưởng label-aware retrieval từ NLP ([5][7][8]) + domain-specific demo selection từ cybersecurity ([6]) vào **Web Attack Detection từ HTTP request**, với ablation study tường minh và LCR@k metric mới.

**⚠️ Quan trọng — KHÔNG NÊN claim:**
- "Chúng tôi là đầu tiên làm label-aware retrieval cho ICL" ← Sai, CLL-RetICL đã làm
- "Chưa ai nghiên cứu demo selection cho ICL" ← Sai, có nhiều papers

**NÊN claim:**
- "Chúng tôi là đầu tiên áp dụng label-aware ICL retrieval cho **Web Attack HTTP payload** classification"
- "Chúng tôi cung cấp controlled ablation study đo isolated impact của label-awareness"
- "Chúng tôi đề xuất và đo LCR@k — metric chưa được dùng trong related work"

