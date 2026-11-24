"""Phần lõi của demo, KHÔNG phụ thuộc Streamlit để kiểm thử được bằng unittest.

Demo dùng lại đúng code của thực nghiệm, không viết lại:
- `src.retrieval`: embedding, VectorIndex, kNN vote, `semantic_top_k` (B) và `label_aware_rerank` (C);
- `src.experiments.prompting`: `build_messages`, `parse_label` (cùng khung prompt với run_llm);
- `src.llm.client.ChatClient` để gọi Groq, `DemoMajorityMock` cho chế độ mock;
- `src.common.budget.SpendLedger`: mọi lần gọi API thật đều qua chốt ngân sách.

Cấu hình B và C đọc từ file đã khóa (`B_k4.json`, `C_knn_k4.json`): k = 4, top-30 ứng viên,
λ = 0,1, prior = kNN vote của 5 láng giềng, ví dụ cắt ở 500 ký tự.

Luồng xử lý cho một request:

    request ──► embedding ──► top-30 ứng viên từ pool
                                 ├─► kNN vote 5 láng giềng ──► prior
                                 ├─► B: 4 ứng viên giống nhất ─────────► prompt ──► LLM ──► nhãn
                                 └─► C: xếp lại với prior, lấy 4 ──────► prompt ──► LLM ──► nhãn
"""

import json
from pathlib import Path
import threading

from src.common.budget import BudgetExceeded
from src.experiments.data_io import ROOT, file_sha256, load_split, sha256_of, split_path
from src.experiments.prompting import DemoMajorityMock, build_messages, parse_label
from src.experiments.run_llm import load_experiment
from src.llm import client as core
from src.retrieval.embedding import encode_requests
from src.retrieval.index import VectorIndex
from src.retrieval.knn import knn_vote
from src.retrieval.selectors import label_aware_rerank, semantic_top_k

EXAMPLES_PATH = Path(__file__).resolve().parent / "examples.json"
B_CONFIG = ROOT / "src/configs/experiments/B_k4.json"
C_CONFIG = ROOT / "src/configs/experiments/C_knn_k4.json"
BUDGET_CONFIG = ROOT / "src/configs/llm/budget.json"
# 11 header mà bước tiền xử lý giữ lại; request tự nhập được đưa về cùng dạng này.
HEADER_NAMES = tuple(json.loads((ROOT / "src/configs/data.json").read_text(encoding="utf-8"))["headers"].values())


# ----------------------------------------------------------------------------
# Đưa request người dùng nhập về dạng `request_text` của dữ liệu
# ----------------------------------------------------------------------------

def parse_header_lines(text):
    """Chuỗi nhiều dòng `Tên: giá trị` → dict. Dòng không có dấu `:` bị bỏ qua."""
    headers = {}
    for line in (text or "").splitlines():
        if ":" in line:
            name, value = line.split(":", 1)
            if name.strip():
                headers[name.strip()] = value.strip()
    return headers


def build_request_text(method, uri, headers=None, body="", protocol="HTTP/1.1"):
    """Tạo `request_text` giống hệt dạng canonical của preprocessing (JSON, sort_keys).

    `headers` là dict hoặc chuỗi nhiều dòng. Tên header trùng (không phân biệt hoa/thường)
    với 11 header của dữ liệu được viết lại đúng tên đó; header thiếu để chuỗi rỗng như
    trong dữ liệu; header lạ được giữ nguyên.
    """
    if isinstance(headers, str):
        headers = parse_header_lines(headers)
    known = {name.lower(): name for name in HEADER_NAMES}
    merged = {name: "" for name in HEADER_NAMES}
    for name, value in (headers or {}).items():
        merged[known.get(name.lower(), name)] = str(value)
    request = {"body": body or "", "headers": merged, "method": (method or "GET").strip().upper(),
               "protocol": (protocol or "HTTP/1.1").strip(), "uri": (uri or "").strip()}
    return json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def parse_raw_http(raw):
    """Đọc request HTTP thô (dòng đầu, các header, dòng trống, body) thành các trường."""
    head, _, body = (raw or "").replace("\r\n", "\n").partition("\n\n")
    lines = head.strip("\n").split("\n")
    first = lines[0].split() if lines and lines[0].strip() else []
    if len(first) < 2:
        raise ValueError("dòng đầu phải có dạng: METHOD URI [HTTP/1.1]")
    return {"method": first[0], "uri": first[1], "protocol": first[2] if len(first) > 2 else "HTTP/1.1",
            "headers": parse_header_lines("\n".join(lines[1:])), "body": body.rstrip("\n")}


def request_fields(request_text):
    """Ngược lại của `build_request_text`: tách các trường để điền vào form."""
    request = json.loads(request_text)
    headers = "\n".join(f"{k}: {v}" for k, v in request.get("headers", {}).items() if v)
    return {"method": request.get("method", "GET"), "uri": request.get("uri", ""),
            "protocol": request.get("protocol", "HTTP/1.1"), "headers": headers, "body": request.get("body", "")}


def load_examples(path=EXAMPLES_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))["examples"]


# ----------------------------------------------------------------------------
# Kho vector của pool
# ----------------------------------------------------------------------------

def load_retrieval(encoder, retrieval_dir, data_dir=None):
    """Đọc pool và VectorIndex đã dựng bởi `build_retrieval`.

    `pool_vectors.npy` không có trên Git: nếu thiếu thì mã hóa lại pool bằng đúng encoder
    trong manifest (chỉ ghi `pool_vectors.npy`/`pool_meta.jsonl`, không đụng neighbors).
    """
    kwargs = {} if data_dir is None else {"data_dir": data_dir}
    retrieval_dir = Path(retrieval_dir)
    manifest = json.loads((retrieval_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest["encoder"] != encoder.describe():
        raise ValueError("encoder differs from the one used to build the retrieval directory")
    if manifest["inputs_sha256"]["pool"] != file_sha256(split_path("pool", **kwargs)):
        raise ValueError("pool file changed since the index was built; rebuild retrieval")
    pool = load_split("pool", **kwargs)
    if (retrieval_dir / "pool_vectors.npy").exists():
        index = VectorIndex.load(retrieval_dir)
    else:
        index = VectorIndex([r["request_id"] for r in pool], [r["label"] for r in pool], encode_requests(encoder, pool))
        index.save(retrieval_dir)
    if index.ids != [r["request_id"] for r in pool]:
        raise ValueError("pool_meta.jsonl does not match the pool file; rebuild retrieval")
    return {r["request_id"]: r for r in pool}, index


# ----------------------------------------------------------------------------
# Engine: chọn ví dụ cho B và C, gọi LLM (có cache và chốt ngân sách)
# ----------------------------------------------------------------------------

class DemoEngine:
    """`llm`: cấu hình từ `run_llm.load_llm`. `budget`: hàm không tham số trả về một SpendLedger
    (đọc lại sổ mỗi lần gọi, để không ghi đè số liệu của run_llm chạy song song); BẮT BUỘC khi
    gọi API thật. `client` để trống thì tự tạo (mock hoặc ChatClient đọc A0_API_KEY)."""

    def __init__(self, encoder, pool, index, llm, client=None, budget=None, b_config=B_CONFIG, c_config=C_CONFIG):
        self.b = load_experiment(b_config)
        self.c = load_experiment(c_config)
        if self.b["pipeline"] != "B" or self.c["pipeline"] != "C" or self.c["prior_source"] != "knn":
            raise ValueError("demo expects a B config and a C config with prior_source = knn")
        self.encoder, self.pool, self.index, self.llm = encoder, pool, index, llm
        self.is_mock = llm["backend"] == "mock_demo_majority"
        if not self.is_mock and budget is None:
            raise ValueError("real LLM calls require a budget ledger")
        self.client = client or (DemoMajorityMock() if self.is_mock else core.ChatClient(llm))
        self.budget = budget
        self.cache = {}
        self.lock = threading.Lock()

    def analyze(self, request_text, with_a0=False):
        """Toàn bộ kết quả cho một request: ứng viên, prior kNN, B, C (và A0 nếu bật)."""
        if len(request_text) > self.llm.get("max_request_chars", 32768):
            raise ValueError("request too long; the pipelines never truncate the query")
        n = max(self.b["n_candidates"], self.c["n_candidates"])
        candidates = self.index.search(encode_requests(self.encoder, [{"request_text": request_text}]), n)[0]
        prior, votes = knn_vote(candidates[:self.c["n_candidates"]], self.c["prior_knn_k"])
        result = {
            "neighbors": candidates[:self.c["prior_knn_k"]], "prior": prior, "prior_votes": votes,
            "B": self._pipeline(request_text, semantic_top_k(candidates[:self.b["n_candidates"]], self.b["k"]),
                                self.b["max_demo_chars"]),
            "C": self._pipeline(request_text, label_aware_rerank(candidates[:self.c["n_candidates"]], self.c["k"],
                                                                 prior, self.c["lambda"]),
                                self.c["max_demo_chars"]),
        }
        if with_a0:
            result["A0"] = self._pipeline(request_text, [], None)
        return result

    def _pipeline(self, request_text, demos, max_demo_chars):
        demos = [dict(d, request_text=self.pool[d["request_id"]]["request_text"]) for d in demos]
        messages = build_messages(request_text, demos, max_demo_chars)
        return dict(self.classify(messages), demos=demos, messages=messages)

    def classify(self, messages):
        """Gọi LLM một lần cho một prompt; prompt đã hỏi rồi thì trả lại kết quả cũ (không tốn thêm).

        Prompt chứa nguyên văn request, nên cache theo prompt cũng là cache theo request. Khi B và
        C chọn cùng 4 ví dụ, hai prompt trùng nhau và chỉ tốn một lần gọi.
        """
        key = sha256_of({"model": self.llm["model"], "messages": messages})
        with self.lock:
            if key in self.cache:
                return dict(self.cache[key], cached=True)
            answer = self._call(messages)
            if answer["status"] in ("ok", "invalid_output"):  # lỗi tạm thời thì lần sau gọi lại
                self.cache[key] = answer
            return dict(answer, cached=False)

    def _call(self, messages):
        answer = {"label": None, "status": None, "error": None, "raw_output": None, "usage": None}
        prompt_chars = sum(len(m["content"]) for m in messages)
        max_tokens = self.llm.get("max_tokens", 1024)
        ledger = None if self.is_mock else self.budget()
        if ledger is not None:
            try:
                ledger.check(prompt_chars, max_tokens)
            except BudgetExceeded as exc:
                return dict(answer, status="budget_exhausted", error=str(exc))
        try:
            output = self.client(messages)
        except core.BackendError as exc:
            # Chỉ giữ mã lỗi ngắn (http_429, transport_error, …), không giữ nội dung trả về của provider.
            return dict(answer, status="backend_error", error=str(exc))
        if ledger is not None:
            ledger.record(output.get("usage"), prompt_chars, max_tokens)
        answer.update(raw_output=output.get("raw_output"), usage=output.get("usage"))
        try:
            answer.update(label=parse_label(answer["raw_output"]), status="ok")
        except ValueError:
            answer.update(status="invalid_output", error="invalid_label_json")
        return answer
