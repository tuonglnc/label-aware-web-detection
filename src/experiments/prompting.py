"""Xây prompt gửi LLM và đọc câu trả lời, dùng chung cho mọi pipeline.

Mọi pipeline (A0, A1, B, BAL, C) dùng ĐÚNG một khung prompt; chỉ khác danh
sách ví dụ mẫu. Nhờ vậy, chênh lệch kết quả chỉ đến từ cách chọn ví dụ.

Khung prompt:
- system: định nghĩa 6 nhãn (lấy từ A0), yêu cầu trả về JSON {"label": ...},
  và nhắc rằng nội dung request là dữ liệu không tin cậy, không được làm theo
  lệnh nằm trong đó (chống prompt injection từ payload).
- user: một JSON gồm
      "labeled_examples": [{"request": ..., "label": ...}, ...]   (A0 không có)
      "request_to_classify": ...

Thứ tự ví dụ: ví dụ được xếp hạng CAO NHẤT đặt CUỐI danh sách, sát với
request cần phân loại (cách làm phổ biến trong các nghiên cứu ICL).
"""

from collections import Counter
import json
import re

from src.pipeline_a0.core import BackendError, SYSTEM as A0_SYSTEM, parse_output
from src.retrieval.views import prompt_view

PROMPT_VERSION = "icl-v1"
SYSTEM = A0_SYSTEM + (
    "\nThe user message is a JSON object. If it contains labeled_examples, they are reference HTTP requests "
    "with their labels; use them as evidence but judge request_to_classify on its own content. "
    "Examples may be truncated (marked …[truncated])."
)
FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


def build_messages(request_text, demos, max_demo_chars):
    """`demos`: danh sách {"request_text", "label"} theo thứ tự xếp hạng (tốt nhất trước)."""
    payload = {}
    if demos:
        payload["labeled_examples"] = [{"request": prompt_view(d["request_text"], max_demo_chars), "label": d["label"]}
                                       for d in reversed(demos)]
    payload["request_to_classify"] = prompt_view(request_text)  # query: không cắt
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]


def parse_label(raw):
    """Đọc nhãn từ câu trả lời. Chấp nhận JSON nằm trong khối ```json ... ```
    (nhiều model hay bọc như vậy); mọi dạng khác được ghi là `invalid_output`."""
    if isinstance(raw, str):
        match = FENCE.match(raw)
        if match:
            raw = match.group(1)
    return parse_output(raw)


class DemoMajorityMock:
    """LLM GIẢ để kiểm thử toàn bộ luồng mà không tốn API.

    Quy tắc: trả về nhãn xuất hiện nhiều nhất trong các ví dụ (hòa thì lấy ví
    dụ đứng cuối, tức giống nhất); không có ví dụ thì trả "NORMAL".
    Kết quả của mock KHÔNG phải năng lực của LLM, không được đưa vào báo cáo
    như kết quả thực nghiệm.
    """

    model = "mock-demo-majority"

    def __call__(self, messages):
        payload = json.loads(messages[-1]["content"])
        examples = payload.get("labeled_examples", [])
        if not examples:
            label = "NORMAL"
        else:
            counts = Counter(e["label"] for e in examples)
            best = max(counts.values())
            label = next(e["label"] for e in reversed(examples) if counts[e["label"]] == best)
        if "FORCE_BACKEND_ERROR" in payload["request_to_classify"]:
            raise BackendError("mock_backend_error")
        return {"raw_output": json.dumps({"label": label}), "usage": None, "attempts": 1}
