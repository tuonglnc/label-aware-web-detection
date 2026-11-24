"""Demo Streamlit: so sánh Pipeline B (top-4) và C (label-aware, prior kNN, λ = 0,1) cho một HTTP request.

Chạy từ thư mục gốc repo (cần `pip install -r requirements-demo.txt`):

    streamlit run src/demo/app.py

- Chế độ **mock** (mặc định): không gọi API, không cần key. Nhãn "LLM" chỉ là nhãn đa số của
  4 ví dụ (DemoMajorityMock), KHÔNG phải năng lực của LLM.
- Chế độ **Groq thật**: đọc A0_API_KEY từ file `.env` (cơ chế `load_env_file` của run_llm), mọi lần
  gọi đều qua chốt ngân sách `src/configs/llm/budget.json`, câu trả lời được cache theo prompt.

Phần xử lý nằm trong `src/demo/core.py`; file này chỉ vẽ giao diện.
"""

import json
from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:  # `streamlit run` chỉ thêm thư mục src/demo vào sys.path
    sys.path.insert(0, str(ROOT))

from src.common.budget import SpendLedger  # noqa: E402
from src.demo.core import (BUDGET_CONFIG, DemoEngine, build_request_text, load_examples,  # noqa: E402
                           load_retrieval, parse_raw_http, request_fields)
from src.experiments.run_llm import load_env_file, load_llm  # noqa: E402
from src.retrieval.embedding import SentenceTransformerEncoder  # noqa: E402

RETRIEVAL_DIR = ROOT / "src/artifacts/retrieval/minilm"
LLM_CONFIGS = {"mock": ROOT / "src/configs/llm/mock.json", "groq": ROOT / "src/configs/llm/groq.json"}
CUSTOM = "(Tự nhập request)"
STATUS_TEXT = {"ok": "", "invalid_output": "LLM trả lời sai định dạng", "backend_error": "lỗi API",
               "budget_exhausted": "dừng vì chốt ngân sách"}


@st.cache_resource(show_spinner="Đang nạp model embedding và kho 3.000 ví dụ (lần đầu ~1 phút)…")
def get_retrieval():
    manifest = json.loads((RETRIEVAL_DIR / "manifest.json").read_text(encoding="utf-8"))["encoder"]
    encoder = SentenceTransformerEncoder(manifest["model"], manifest["max_seq_length"])
    pool, index = load_retrieval(encoder, RETRIEVAL_DIR)
    return encoder, pool, index


@st.cache_resource(show_spinner=False)
def get_engine(mode, env_file):
    """Một engine (kèm cache câu trả lời) cho mỗi chế độ; giữ suốt thời gian server chạy."""
    encoder, pool, index = get_retrieval()
    if mode == "groq":
        load_env_file(ROOT / env_file)
    budget = lambda: SpendLedger.from_config(BUDGET_CONFIG, ROOT)
    return DemoEngine(encoder, pool, index, load_llm(LLM_CONFIGS[mode]), budget=budget)


def fill_from_example():
    """Chọn ví dụ có sẵn → điền vào form."""
    choice = st.session_state.example
    if choice == CUSTOM:
        return
    example = next(e for e in load_examples() if e["title"] == choice)
    for field, value in request_fields(example["request_text"]).items():
        st.session_state[field] = value
    st.session_state.raw = ""
    st.session_state.result = None


def mark_custom():
    """Người dùng sửa form → request không còn là ví dụ có sẵn (không hiện nhãn thật nữa)."""
    st.session_state.example = CUSTOM


def show_label(column, title, answer):
    column.markdown(f"**{title}**")
    if answer["status"] == "ok":
        column.success(f"### {answer['label']}")
    else:
        column.error(f"Không có nhãn: {STATUS_TEXT.get(answer['status'], answer['status'])} ({answer['error']})")
    note = "lấy từ cache, không tốn thêm" if answer["cached"] else "vừa gọi LLM"
    if answer.get("usage"):
        note += f" · {answer['usage'].get('total_tokens', '?')} token"
    column.caption(note)


def show_demos(column, answer, other_ids):
    rows = [{"nhãn": d["label"] + (" ✱" if d["request_id"] not in other_ids else ""),
             "sim": round(d["similarity"], 4), "điểm": round(d["score"], 4), "rank": d["rank"]}
            for d in answer["demos"]]
    column.dataframe(rows, hide_index=True, width="stretch")
    column.caption("sim = độ giống với request · điểm = điểm dùng để xếp hạng · rank = thứ hạng theo sim "
                   "trong top-30 · ✱ = ví dụ pipeline bên kia không chọn")
    with column.expander("Xem nội dung 4 ví dụ và prompt gửi LLM"):
        for i, d in enumerate(answer["demos"]):
            st.markdown(f"**Ví dụ {i + 1}** · `{d['label']}` · `{d['request_id'][:12]}`")
            st.code(json.loads(d["request_text"]).get("uri", ""), language=None, wrap_lines=True)
        st.markdown("**Prompt (phần user)**")
        st.code(answer["messages"][-1]["content"], language="json", wrap_lines=True)


def budget_caption():
    ledger = SpendLedger.from_config(BUDGET_CONFIG, ROOT)
    return f"Sổ chi phí: ~{ledger.spent_usd:.4f} / {ledger.limit_usd:.2f} USD (ước tính giá cố ý đặt cao)"


def main():
    st.set_page_config(page_title="Label-aware demo", layout="wide")
    st.title("Phát hiện tấn công web bằng LLM: Pipeline B và C")
    st.caption("Phân loại một HTTP request vào 6 lớp của SR-BH 2020. B lấy 4 ví dụ giống nhất; "
               "C xếp lại top-30 theo similarity + 0,1·1[nhãn = prior], với prior = kNN vote của 5 láng giềng.")
    st.session_state.setdefault("result", None)

    with st.sidebar:
        st.header("Cấu hình")
        mode = st.radio("LLM", ["mock", "groq"], format_func=lambda m: {
            "mock": "Mock (không gọi API, không tốn tiền)", "groq": "Groq thật: openai/gpt-oss-20b"}[m])
        env_file = ".env"
        if mode == "groq":
            env_file = st.text_input("File chứa key", ".env", help="Cần A0_API_KEY; key không bao giờ hiện ra.")
            st.caption(budget_caption())
        else:
            st.info("Ở chế độ mock, nhãn 'LLM' = nhãn xuất hiện nhiều nhất trong 4 ví dụ. "
                    "Đây KHÔNG phải kết quả của LLM.")
        with_a0 = st.toggle("Hiện thêm A0 (zero-shot, +1 lần gọi)", value=False)
        st.divider()
        st.caption("Cấu hình đã khóa: k = 4, top-30 ứng viên, λ = 0,1, prior kNN k = 5, "
                   "ví dụ cắt ở 500 ký tự. Encoder all-MiniLM-L6-v2, pool 3.000 request.")

    examples = load_examples()
    st.selectbox("Ví dụ có sẵn (lấy từ tập validation)", [CUSTOM] + [e["title"] for e in examples],
                 key="example", on_change=fill_from_example)
    true_label = next((e["label"] for e in examples if e["title"] == st.session_state.example), None)

    form_tab, raw_tab = st.tabs(["Điền từng trường", "Dán HTTP thô"])
    with form_tab:
        left, right = st.columns([1, 5])
        left.text_input("Method", key="method", placeholder="GET", on_change=mark_custom)
        right.text_input("URI", key="uri", placeholder="/blog/index.php?id=1", on_change=mark_custom)
        st.text_area("Headers (mỗi dòng `Tên: giá trị`)", key="headers", height=120,
                     placeholder="Host: test-site.com\nUser-Agent: Mozilla/5.0", on_change=mark_custom)
        st.text_area("Body", key="body", height=68, on_change=mark_custom)
    with raw_tab:
        st.text_area("Request HTTP thô (nếu điền ô này thì bỏ qua tab bên cạnh)", key="raw", height=200,
                     placeholder="GET /blog/index.php?id=1 HTTP/1.1\nHost: test-site.com\n\n", on_change=mark_custom)

    if st.button("Phân loại", type="primary"):
        try:
            if (st.session_state.get("raw") or "").strip():
                fields = parse_raw_http(st.session_state.raw)
            else:
                fields = {k: st.session_state.get(k) or "" for k in ("method", "uri", "headers", "body")}
                fields["protocol"] = st.session_state.get("protocol") or "HTTP/1.1"
            if not fields["uri"]:
                raise ValueError("hãy nhập URI")
            request_text = build_request_text(**fields)
            with st.spinner("Đang tìm ví dụ và hỏi LLM…"):
                engine = get_engine(mode, env_file)
                st.session_state.result = {"mode": mode, "true_label": true_label,
                                           "data": engine.analyze(request_text, with_a0)}
        except (ValueError, OSError, KeyError) as exc:
            # Không in chi tiết lỗi của provider hay biến môi trường.
            st.error(f"Không chạy được: {type(exc).__name__}: {str(exc)[:200]}")
            st.session_state.result = None

    result = st.session_state.result
    if not result:
        return
    data = result["data"]
    st.divider()
    if result["true_label"]:
        st.markdown(f"Nhãn thật trong dataset: **`{result['true_label']}`**")
    if result["mode"] == "mock":
        st.warning("Kết quả từ LLM giả (mock). Chọn 'Groq thật' ở thanh bên để hỏi LLM thật.")

    st.subheader(f"1. Prior kNN: `{data['prior']}`")
    left, right = st.columns([3, 2])
    left.dataframe([{"láng giềng": i + 1, "nhãn": c["label"], "similarity": round(c["similarity"], 4)}
                    for i, c in enumerate(data["neighbors"])], hide_index=True, width="stretch")
    right.dataframe([{"nhãn": label, "tổng phiếu": round(score, 4)}
                     for label, score in sorted(data["prior_votes"].items(), key=lambda kv: -kv[1])],
                    hide_index=True, width="stretch")
    right.caption("Mỗi láng giềng bỏ phiếu bằng độ giống của nó. B không dùng prior; C cộng 0,1 cho "
                  "ứng viên có nhãn trùng prior.")

    st.subheader("2. Ví dụ được chọn và nhãn LLM trả về")
    col_b, col_c = st.columns(2)
    ids_b = {d["request_id"] for d in data["B"]["demos"]}
    ids_c = {d["request_id"] for d in data["C"]["demos"]}
    show_label(col_b, "Pipeline B: top-4 giống nhất", data["B"])
    show_label(col_c, f"Pipeline C: label-aware (prior = {data['prior']})", data["C"])
    show_demos(col_b, data["B"], ids_c)
    show_demos(col_c, data["C"], ids_b)
    if ids_b == ids_c:
        st.info("B và C chọn cùng 4 ví dụ, nên prompt giống hệt nhau (chỉ một lần gọi LLM).")

    if "A0" in data:
        st.subheader("3. A0 zero-shot (không có ví dụ)")
        show_label(st, "A0", data["A0"])
    if result["mode"] == "groq":
        st.caption(budget_caption())


main()
