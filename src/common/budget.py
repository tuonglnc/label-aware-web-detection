"""Chốt ngân sách API: dừng chạy TRƯỚC khi tổng chi phí có thể vượt ngưỡng.

Cách hoạt động:
- Sổ ghi chi phí (ledger, file JSON) lưu tổng token đầu vào/đầu ra đã dùng, cộng dồn qua MỌI lần chạy.
- Trước mỗi request, ước tính chi phí xấu nhất của request đó:
      token đầu vào ước tính (số ký tự prompt / 3) + toàn bộ max_tokens đầu ra.
  Nếu chi phí đã dùng + chi phí xấu nhất > ngưỡng thì KHÔNG gọi API nữa.
- Sau mỗi request, cộng token thực tế (lấy từ trường usage của API) vào sổ.

Giá trong file cấu hình nên đặt CAO HƠN giá thật (ví dụ gấp đôi) để có khoảng an toàn.
Đây là lớp bảo vệ thứ hai; lớp thứ nhất là giới hạn chi tiêu đặt trong console của nhà cung cấp.
"""

import json
import os
from pathlib import Path

CHARS_PER_TOKEN = 3.0  # đo thực tế khoảng 3,2 ký tự/token; dùng 3,0 để ước tính dư
SAFETY = 1.2           # ước tính token đầu vào thêm 20% cho chắc


class BudgetExceeded(Exception):
    pass


class SpendLedger:
    def __init__(self, ledger_path, limit_usd, price_input_per_million, price_output_per_million):
        if limit_usd <= 0 or price_input_per_million <= 0 or price_output_per_million <= 0:
            raise ValueError("budget limit and prices must be positive")
        self.path = Path(ledger_path)
        self.limit_usd = float(limit_usd)
        self.price_in = float(price_input_per_million) / 1_000_000
        self.price_out = float(price_output_per_million) / 1_000_000
        # max_tokens_per_char: tỷ lệ token/ký tự LỚN NHẤT từng thấy, để ước tính không bao giờ thấp hơn thực tế đã gặp.
        self.state = {"input_tokens": 0, "output_tokens": 0, "calls": 0, "estimated_calls": 0,
                      "max_tokens_per_char": 1 / CHARS_PER_TOKEN}
        if self.path.exists():
            self.state.update(json.loads(self.path.read_text(encoding="utf-8")))

    @classmethod
    def from_config(cls, path, root=None):
        cfg = json.loads(Path(path).read_text(encoding="utf-8"))
        ledger = Path(cfg["ledger"])
        if root is not None and not ledger.is_absolute():
            ledger = Path(root) / ledger
        return cls(ledger, cfg["limit_usd"], cfg["price_input_per_million"], cfg["price_output_per_million"])

    @property
    def spent_usd(self):
        return self.state["input_tokens"] * self.price_in + self.state["output_tokens"] * self.price_out

    def estimated_input_tokens(self, prompt_chars):
        return prompt_chars * self.state["max_tokens_per_char"] * SAFETY

    def worst_case_usd(self, prompt_chars, max_output_tokens):
        return self.estimated_input_tokens(prompt_chars) * self.price_in + max_output_tokens * self.price_out

    def check(self, prompt_chars, max_output_tokens):
        """Ném BudgetExceeded nếu request tiếp theo có thể làm tổng vượt ngưỡng."""
        if self.spent_usd + self.worst_case_usd(prompt_chars, max_output_tokens) > self.limit_usd:
            raise BudgetExceeded(f"spent ~{self.spent_usd:.4f} USD of {self.limit_usd:.2f} USD limit")

    def record(self, usage, prompt_chars, max_output_tokens):
        """Cộng token thực tế. Nếu API không trả usage, cộng ước tính xấu nhất để an toàn."""
        if usage and "prompt_tokens" in usage and "completion_tokens" in usage:
            self.state["input_tokens"] += int(usage["prompt_tokens"])
            self.state["output_tokens"] += int(usage["completion_tokens"])
            if prompt_chars > 0:
                self.state["max_tokens_per_char"] = max(self.state["max_tokens_per_char"],
                                                        int(usage["prompt_tokens"]) / prompt_chars)
        else:
            self.state["input_tokens"] += int(self.estimated_input_tokens(prompt_chars)) + 1
            self.state["output_tokens"] += int(max_output_tokens)
            self.state["estimated_calls"] += 1
        self.state["calls"] += 1
        self._save()

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = dict(self.state, spent_usd_estimate=round(self.spent_usd, 6), limit_usd=self.limit_usd,
                    note="Estimated with the (deliberately high) prices in the budget config; real cost is lower.")
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        tmp.replace(self.path)
