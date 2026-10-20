#!/usr/bin/env bash
# Chạy bộ thí nghiệm chính trên một split bằng MỘT tài khoản Groq (Git Bash / Linux).
#
#   bash src/experiments/run_suite.sh validation
#   bash src/experiments/run_suite.sh test --locked      # CHỈ sau khi đã khóa cấu hình (300 mẫu đầu, 50/lớp)
#   EXTRA=1 bash src/experiments/run_suite.sh validation # thêm C-oracle và A1
#   ENV_FILE=.env.khac bash src/experiments/run_suite.sh validation   # dùng file key khác (mặc định .env)
#
# Key đặt trong file .env ở thư mục gốc repo (theo mẫu env.example). Điều khoản của Groq cấm
# vượt giới hạn bằng cách dùng nhiều tài khoản, nên script chỉ dùng đúng một key.
# - Bị giới hạn theo phút (HTTP 429 ngắn): runner tự chờ rồi chạy tiếp.
# - Hết quota/giới hạn dài: run đang chạy dừng gọn, không ghi lỗi; chạy lại ĐÚNG lệnh cũ để tiếp tục.
# - Run đã xong được bỏ qua; lỗi API lẻ được gọi lại nhờ --retry-errors.
# - Chốt ngân sách (src/configs/llm/budget.json): dừng TRƯỚC khi tổng chi phí ước tính có thể vượt ngưỡng.
set -u
SPLIT="${1:-validation}"
BUDGET="${BUDGET:-src/configs/llm/budget.json}"
EXTRA_ARGS="--retry-errors --budget $BUDGET"
if [ "$SPLIT" = "test" ]; then
  if [ "${2:-}" != "--locked" ]; then
    echo "Tập test chỉ chạy sau khi khóa cấu hình: bash src/experiments/run_suite.sh test --locked"
    exit 1
  fi
  EXTRA_ARGS="$EXTRA_ARGS --allow-test --limit 300"
fi
PY="${PYTHON:-python}"
ENV_FILE="${ENV_FILE:-.env}"
export PYTHONIOENCODING=utf-8

if [ ! -f "$ENV_FILE" ] || ! grep -q "^A0_API_KEY=.\+" "$ENV_FILE" || grep -q "^A0_API_KEY=''" "$ENV_FILE"; then
  echo "Không tìm thấy key trong $ENV_FILE (tạo từ env.example và điền A0_API_KEY)."
  exit 1
fi
echo "File key: $ENV_FILE"

# Bộ chính. A0 phải chạy trước vì C_llm dùng dự đoán của A0 làm prior.
CONFIGS="A0 B_k4 BAL_k4 C_knn_k4 C_llm_k4"
[ "${EXTRA:-0}" = "1" ] && CONFIGS="$CONFIGS C_oracle_k4 A1_k4"

FAILED=""
for c in $CONFIGS; do
  echo "=== $c | $(date +%H:%M:%S) ==="
  out=$("$PY" -m src.experiments.run_llm --config "src/configs/experiments/$c.json" \
      --llm src/configs/llm/groq.json --env-file "$ENV_FILE" --split "$SPLIT" \
      --output "src/artifacts/runs/$SPLIT/$c" $EXTRA_ARGS 2>&1)
  echo "$out"
  if echo "$out" | grep -q "budget_exhausted"; then
    echo "=== ĐÃ CHẠM NGÂN SÁCH (xem $BUDGET và src/artifacts/api_spend_ledger.json): dừng, không gọi API nữa. ==="
    exit 0
  fi
  if echo "$out" | grep -q "quota_exhausted"; then
    [ -n "$FAILED" ] && echo "=== CÁC RUN BỊ CHẶN:$FAILED. Gửi thông báo lỗi ở trên cho người phụ trách code. ==="
    echo "=== Hết quota/giới hạn: dừng. Chạy lại đúng lệnh này sau để tiếp tục. ==="
    exit 0
  fi
  if echo "$out" | grep -q "run_llm stopped"; then
    # Lỗi không phải do quota (ví dụ cấu hình/code đã đổi): ghi lại, chạy tiếp các run khác.
    echo "!!! $c BỊ CHẶN, cần xử lý trước lần chạy sau (xem thông báo ở trên) !!!"
    FAILED="$FAILED $c"
  fi
done
if [ -n "$FAILED" ]; then
  echo "=== CÁC RUN BỊ CHẶN:$FAILED. Gửi thông báo lỗi ở trên cho người phụ trách code. ==="
fi
echo "=== Xong bộ thí nghiệm trên $SPLIT ($(date +%H:%M:%S)) ==="
