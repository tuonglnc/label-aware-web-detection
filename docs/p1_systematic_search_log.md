# P1: Systematic Literature Search Log

> **Ngày thực hiện:** 29/09/2026
> **Mục đích:** Xác nhận/bác bỏ Research Gap bằng systematic search
> **Trạng thái:** ✅ Hoàn tất — Gap CẦN ĐIỀU CHỈNH (xem Section 4)

---

## 1. Search Queries & Kết Quả

### Query 1: `"label-aware retrieval" "in-context learning"`
- **Kết quả:** Có nhiều papers về label-aware demonstration selection cho ICL trong NLP
- **Papers relevant:**
  - **CLL-RetICL** (Lin et al., IJCNLP-AACL 2025) — label-aware retrieval cho text classification
  - **RDES** (arXiv:2412.03966, ICML 2025) — RL-based demo selection, label distribution diversity
  - **L2D** (arXiv:2511.10675) — Label Distribution Divergence cho demo selection
- **⚠️ Nhận định:** Label-aware retrieval cho ICL text classification đã được nghiên cứu trong NLP! Gap cần thu hẹp lại vào domain Web Attack.

### Query 2: `LLM web attack detection HTTP payload classification SQL injection XSS`
- **Kết quả:** Nhiều papers về ML/DL for Web Attack, một số dùng LLM
- **Xu hướng chính:**
  - Fine-tuning (BERT, Llama-3, DistilBERT) for SQLi/XSS classification → accuracy ~98%
  - Hybrid: LLM + traditional ML/WAF
  - LLM-generated WAF rules
- **⚠️ Nhận định:** Chưa tìm thấy paper nào kết hợp **ICL + retrieval-based demo selection + Web Attack HTTP payload** → Gap vẫn đứng cho domain cụ thể này.

### Query 3: `"demonstration selection" cybersecurity classification "in-context learning"`
- **Kết quả:** Paper quan trọng tìm được:
  - **BFAD** (arXiv:2504.13811, COLM 2025) — Behavioral Function-Aware Detection for WebShell
    - Dùng function-level behavioral profiling để chọn ICL demonstrations
    - Cải thiện F1 trung bình 13.82%
    - **Rất gần đề tài:** Cybersecurity + ICL demo selection + label-awareness (qua behavior profiling)
- **⚠️ Nhận định:** BFAD là paper closest competitor trong cybersecurity ICL demo selection. Cần phân biệt rõ: BFAD làm WebShell (PHP code), đề tài làm Web Attack (HTTP request payloads).

### Query 4: `RAG "in-context learning" "web application attack"`
- **Kết quả:** Chủ yếu về RAG security (prompt injection, data poisoning) và RAG cho cybersecurity reporting
- **Papers liên quan:** Vẫn là [1] CyberRAG và [2] Detection-to-Response
- **⚠️ Nhận định:** Không tìm thấy paper mới nào kết hợp RAG + ICL cho Web Attack classification.

### Query 5: `GPT "SQL injection" "XSS" classification few-shot in-context learning 2024 2025`
- **Kết quả:** Có papers về few-shot prompting cho SQLi/XSS detection
- **Xu hướng:**
  - Zero/few-shot prompting với LLM (GPT, Llama) cho web attack detection
  - Fine-tuning transformers cho payload classification
  - **Prompt injection as "new SQLi/XSS"** (hướng nghiên cứu mới)
- **⚠️ Nhận định:** Few-shot ICL cho web attack detection tồn tại, NHƯNG không có paper nào focus vào **retrieval-based demonstration selection** (tức chọn demo thông minh thay vì random/manual few-shot).

### Query 6: `"label-conditioned retrieval" OR "class-aware retrieval" "text classification"`
- **Kết quả:** Ít kết quả cụ thể — thuật ngữ chưa phổ biến
- **⚠️ Nhận định:** "Label-aware retrieval" là term đúng hơn trong literature.

---

## 2. Papers Mới Tìm Được (Cần Thêm Vào Related Work)

### [5] CLL-RetICL — Label-Aware Retrieval cho Text Classification ⭐

> Lin, C., Wu, K., Xiang, P., Wu, Y., & Bai, O. (2025). *CLL-RetICL: Contrastive Linguistic Label Retrieval-based In-Context Learning for Text Classification via Large Language Models.* Findings of IJCNLP-AACL 2025.

| Thuộc tính | Chi tiết |
|---|---|
| **Focus** | Label-aware ICL demo retrieval cho text classification |
| **Method** | Kết hợp sentence-query similarity + sentence-label similarity |
| **Domain** | NLP text classification chung |
| **Label-Aware?** | ✓ **Explicit** — dùng linguistic label semantics |
| **Key Innovation** | Tích hợp label similarity vào retrieval scoring, không cần fine-tune |
| **Kết quả** | Outperforms standard retrieval methods trên multiple datasets |
| **Relevance cho đề tài** | ⭐ **CAO** — cùng ý tưởng label-aware retrieval cho ICL classification, nhưng domain NLP chung, không phải cybersecurity |
| **Gap so với đề tài** | Không áp dụng cho Web Attack, không đo LCR@k, không có hard case analysis cho security payloads |

### [6] BFAD — Behavioral Function-Aware Detection for WebShell ⭐⭐

> (2025). *Can LLMs Handle WebShell Detection? Overcoming Detection Challenges with Behavioral Function-Aware Framework.* arXiv:2504.13811, COLM 2025.

| Thuộc tính | Chi tiết |
|---|---|
| **Focus** | LLM + ICL cho WebShell detection |
| **Method** | 3 components: Critical Function Filter, Context-Aware Code Extraction, Weighted Behavioral Function Profiling (WBFP) |
| **Domain** | Cybersecurity — WebShell (PHP code analysis) |
| **Label-Aware?** | ✓ **Implicit** — behavior-weighted function profiling để chọn demos |
| **Key Innovation** | Domain-specific demo selection dựa trên behavioral function similarity |
| **Kết quả** | F1 improvement +13.82% trung bình, GPT-4 + BFAD vượt SOTA |
| **Relevance cho đề tài** | ⭐⭐ **RẤT CAO** — cybersecurity + ICL demo selection + domain-specific awareness |
| **Gap so với đề tài** | WebShell ≠ Web Attack HTTP payload; BFAD dùng function-level similarity (code), đề tài cần payload-level similarity (HTTP request); không đo label consistency; không có ablation label-aware vs vanilla retrieval |

### [7] RDES — RL-based Demonstration Selection

> (2025). *Demonstration Selection for In-Context Learning via Reinforcement Learning.* arXiv:2412.03966, ICML 2025.

| Thuộc tính | Chi tiết |
|---|---|
| **Focus** | RL-optimized demo selection cho ICL, diversity via label distribution |
| **Method** | Q-learning/PPO framework chọn demos maximize relevance + label diversity |
| **Domain** | NLP chung — text classification, reasoning |
| **Label-Aware?** | ✓ **Explicit** — diversity quantified by label distribution |
| **Kết quả** | Outperforms 10 baselines on 14 LLMs |
| **Relevance cho đề tài** | 🟡 **TRUNG BÌNH** — RL approach quá phức tạp cho scope khoá luận, nhưng confirm rằng label diversity matters |

### [8] L2D — Label Distribution Divergence

> (2025). *Learn to Select: Exploring Label Distribution Divergence for In-Context Demonstration Selection in Text Classification.* arXiv:2511.10675.

| Thuộc tính | Chi tiết |
|---|---|
| **Focus** | Label distribution alignment cho demo selection |
| **Method** | 2-stage: TopK semantic + Label Distribution Divergence (via fine-tuned SLM) |
| **Domain** | NLP text classification — 7 benchmarks |
| **Label-Aware?** | ✓ **Explicit** — minimize label distribution divergence |
| **Relevance cho đề tài** | 🟡 **TRUNG BÌNH** — cùng NLP domain, nhưng method (fine-tune SLM) khác approach đề tài |

### [9] Comparative Analysis of Demonstration Selection Algorithms

> (2024). *Comparative Analysis of Demonstration Selection Algorithms for LLM In-Context Learning.* arXiv:2410.23099.

| Thuộc tính | Chi tiết |
|---|---|
| **Focus** | Systematic evaluation 6 demo selection algorithms |
| **Kết quả chính** | Performance varies significantly across tasks; some methods fail to beat random; more demos ≠ better performance |
| **Relevance cho đề tài** | 🟢 **Methodological reference** — cung cấp framework so sánh, cite khi justify experimental design |

### [10] Liu et al. 2022 — What Makes Good In-Context Examples

> Liu, J., et al. (2022). *What Makes Good In-Context Examples for GPT-3?* DeeLIO Workshop, ACL 2022.

| Thuộc tính | Chi tiết |
|---|---|
| **Focus** | Retrieval-based ICL demo selection |
| **Method** | KNN-based: chọn demos semantically similar nhất |
| **Key finding** | Semantic similarity is a strong heuristic cho demo quality |
| **Relevance** | 🟢 **Foundational** — baseline approach (vanilla semantic retrieval) cho đề tài |

### [11] Rubin et al. 2022 — EPR

> Rubin, O., Herzig, J., & Berant, J. (2022). *Learning To Retrieve Prompts for In-Context Learning.* NAACL 2022.

| Thuộc tính | Chi tiết |
|---|---|
| **Focus** | Train dense retriever cho ICL demo selection |
| **Method** | LLM probability as signal → train retriever |
| **Key finding** | Trained retriever >> BM25/generic dense retrievers |
| **Relevance** | 🟢 **Foundational** — established retrieval-for-ICL paradigm |

---

## 3. Bảng So Sánh Mở Rộng (8 papers)

| Tiêu chí | [1] CyberRAG | [2] Det-to-Resp | [3] Noisy Labels | [4] DemoShapley | **[5] CLL-RetICL** | **[6] BFAD** | **Đề tài** |
|---|---|---|---|---|---|---|---|
| **Domain** | Web Attack | Network IDS | NLP chung | NLP chung | **NLP chung** | **WebShell (PHP)** | **Web Attack (HTTP)** |
| **ICL Demo Selection?** | ✗ (report gen) | ✗ (response gen) | ✗ (noise correction) | ✗ (valuation) | **✓ Retrieval** | **✓ WBFP** | ✓ **Retrieval** |
| **Label-Aware?** | Implicit | Soft (query embed) | Post-hoc | Indirect | **✓ Explicit (label sim)** | **✓ Implicit (behavior)** | ✓ **Explicit filter/rerank** |
| **Ablation LA vs Vanilla?** | ✗ | ✗ | N/A | N/A | **✗** | **✗** | ✓ **Core contribution** |
| **LCR@k metric?** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| **Web Attack HTTP payload?** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ (PHP code) | ✓ |

---

## 4. Kết Luận Gap Analysis

### ⚠️ Gap CẦN ĐIỀU CHỈNH (không bác bỏ, nhưng thu hẹp)

**Phát hiện quan trọng:**
- Label-aware demo selection cho ICL đã được nghiên cứu trong **NLP text classification** ([5] CLL-RetICL, [7] RDES, [8] L2D)
- Domain-specific demo selection cho **cybersecurity ICL** đã có 1 paper ([6] BFAD — WebShell)
- NHƯNG: Chưa có paper nào kết hợp **label-aware retrieval + ICL + Web Attack Detection từ HTTP request payload**

### Research Gap Statement (REVISED — v2)

> *Label-aware demonstration selection for in-context learning has been explored in NLP text classification (CLL-RetICL, 2025; RDES, 2025; L2D, 2025), and domain-specific ICL has been applied to cybersecurity via behavioral function profiling for WebShell detection (BFAD, 2025). However, based on our systematic search, the specific combination of (1) label-aware retrieval for ICL demonstration selection, (2) applied to Web Application Attack classification from HTTP request payloads (SQLi, XSS, Path Traversal, etc.), with (3) a controlled ablation study measuring the isolated impact of label-awareness (Label-Aware vs. Vanilla Retrieval), and (4) Label Consistency Rate as a retrieval quality metric, has not been investigated.*

### Gap Positioning (điều chỉnh so với ban đầu)

```
Trước (hypothesis): "Chưa ai làm label-aware retrieval cho ICL" ← SAI, quá rộng
Sau  (confirmed):   "Đã có trong NLP, chưa có cho Web Attack HTTP payload
                     + chưa có controlled ablation + chưa đo LCR@k" ← ĐÚNG, hẹp hơn
```

### Implication cho đề tài:
1. **Cần cite [5] CLL-RetICL và [6] BFAD** — đây là related work gần nhất
2. **Contribution chính của đề tài** nên emphasize:
   - **Domain novelty:** Web Attack HTTP payload (khác NLP text, khác PHP code)
   - **Ablation study:** So sánh tường minh label-aware vs vanilla (CLL-RetICL và BFAD không có)
   - **LCR@k metric:** Chưa ai đo trong bất kỳ domain nào
   - **Hard case analysis:** HTTP requests có semantic overlap cao giữa attack types
3. **Không nên claim:** "Chúng tôi là đầu tiên làm label-aware retrieval cho ICL" — vì CLL-RetICL đã làm

---

## 5. Dataset Candidates (Từ Systematic Search)

| Dataset | Nguồn | Samples | Attack Types | HTTP Payload? | Multi-class? |
|---|---|---|---|---|---|
| **CAPEC Multi-label** (đã có) | research | 907K | 13 CAPEC types | ✓ URL path | ✓ |
| **CSIC 2010** | Kaggle/CSIC | 61K (36K normal + 25K anomalous) | SQLi, XSS, Buffer Overflow, etc. | ✓ Full HTTP request | ⚠️ Binary (normal/anomalous) |
| **Web Application Payloads** | Kaggle | ? | SQLi, XSS, SSRF, CMDi | ✓ Payload strings | ✓ |
| **FWAF Dataset** | Kaggle | ? | Mixed WAF blocks | ✓ HTTP queries | ⚠️ Binary |
| **HttpParams** | GitHub | ? | Malicious params | ✓ HTTP params | ⚠️ Binary? |
| **OWASP ModSecurity logs** | Zenodo | 30 days | CRS-blocked traffic | ✓ Full HTTP | ⚠️ Needs labeling |

### Đánh giá sơ bộ:
- **CSIC 2010:** Rất phổ biến, nhưng chỉ binary (normal/anomalous) — không multiclass → cần relabel
- **Web Application Payloads (Kaggle):** Có multiclass (SQLi/XSS/SSRF/CMDi), cần check quality + size
- **CAPEC Multi-label (đã có):** Lớn nhất, multiclass, nhưng nhiều noise + cần heavy preprocessing

> **Bước tiếp:** Task 3 — survey chi tiết 3 dataset candidates (CAPEC, CSIC 2010, Web Application Payloads)
