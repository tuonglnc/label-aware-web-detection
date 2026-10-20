"""Cách "trình bày" một HTTP request trước khi đưa vào embedding hoặc prompt.

`request_text` trong dữ liệu là chuỗi JSON đã sắp xếp khóa theo bảng chữ cái
(body, headers, method, protocol, uri). Thứ tự này đặt 11 header TRƯỚC uri.
Embedding model (ví dụ all-MiniLM-L6-v2) chỉ đọc khoảng 256 token đầu, nên nếu
đưa nguyên chuỗi vào, phần uri, nơi thường chứa payload tấn công, có thể bị
cắt mất.

Vì vậy module này tạo một "view" chứa CÙNG thông tin nhưng xếp lại thứ tự:
method, uri, protocol, body, rồi mới đến headers. Không decode, không sửa
payload; chỉ đổi thứ tự trình bày.
"""

import json

FIELD_ORDER = ("method", "uri", "protocol", "body")


def parse_request(request_text):
    """Đọc `request_text` (chuỗi JSON) thành dict. Nếu không phải JSON (ví dụ
    fixture viết tay dạng HTTP thô) thì trả về dict chỉ có trường `raw`."""
    try:
        value = json.loads(request_text)
    except (TypeError, ValueError):
        return {"raw": request_text}
    return value if isinstance(value, dict) else {"raw": request_text}


def embedding_view(request_text):
    """Chuỗi ngắn gọn dùng cho embedding: phần quan trọng (method, uri, body)
    đứng đầu, headers không rỗng đứng sau."""
    request = parse_request(request_text)
    if "raw" in request:
        return request["raw"]
    parts = [f"{request.get('method', '')} {request.get('uri', '')} {request.get('protocol', '')}".strip()]
    if request.get("body"):
        parts.append("BODY: " + request["body"])
    headers = request.get("headers") or {}
    for name, value in headers.items():
        if value:
            parts.append(f"{name}: {value}")
    return "\n".join(parts)


def prompt_view(request_text, max_chars=None):
    """Chuỗi JSON đưa vào prompt cho LLM, giữ đủ mọi trường nhưng xếp
    method/uri/protocol/body lên trước headers.

    `max_chars` chỉ dùng cho DEMONSTRATIONS (ví dụ mẫu) để prompt không quá dài.
    Request cần phân loại (query) luôn được đưa nguyên vẹn, không cắt.
    """
    request = parse_request(request_text)
    if "raw" in request:
        text = request["raw"]
    else:
        ordered = {key: request[key] for key in FIELD_ORDER if key in request}
        ordered["headers"] = request.get("headers", {})
        ordered.update({k: v for k, v in request.items() if k not in ordered})
        text = json.dumps(ordered, ensure_ascii=False)
    if max_chars is not None and len(text) > max_chars:
        # Đánh dấu rõ là đã cắt để LLM (và người đọc log) biết.
        text = text[:max_chars] + " …[truncated]"
    return text


def endpoint_of(request_text):
    """Endpoint = method + đường dẫn (bỏ phần query sau dấu ?). Dùng để phân tích."""
    request = parse_request(request_text)
    if "raw" in request:
        first_line = request["raw"].split("\n", 1)[0].split(" ")
        return " ".join(first_line[:2]).split("?", 1)[0]
    return f"{request.get('method', '')} {str(request.get('uri', '')).split('?', 1)[0]}"
