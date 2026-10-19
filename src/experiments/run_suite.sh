#!/usr/bin/env bash
# Chạy bộ thí nghiệm chính trên một split, luân phiên API key của hai thành viên (Git Bash / Linux).
#
#   bash src/experiments/run_suite.sh validation
#   bash src/experiments/run_suite.sh test --locked      # CHỈ sau khi đã khóa cấu hình (300 mẫu đầu, 50/lớp)
#   EXTRA=1 bash src/experiments/run_suite.sh validation # thêm C-oracle và A1 nếu còn quota
#
# Key: mỗi thành viên tạo một file trong thư mục gốc repo, dạng như env.example:
#   .env       -> key của thành viên 1
#   .env.tv2   -> key của thành viên 2
# Khi key đang dùng hết quota trong ngày, script tự chuyển sang key tiếp theo.
# Khi mọi key đều hết, script dừng; hôm sau chạy lại ĐÚNG lệnh cũ để tiếp tục
# (run đã xong được bỏ qua, run dở chạy tiếp, lỗi API lẻ được gọi lại nhờ --retry-errors).
set -u
SPLIT="${1:-validation}"
EXTRA_ARGS="--sleep 1 --retry-errors"
if [ "$SPLIT" = "test" ]; then
  if [ "${2:-}" != "--locked" ]; then
    echo "Tập test chỉ chạy sau khi khóa cấu hình: bash src/experiments/run_suite.sh test --locked"
    exit 1
  fi
  EXTRA_ARGS="$EXTRA_ARGS --allow-test --limit 300"
fi
PY="${PYTHON:-python}"
export PYTHONIOENCODING=utf-8

# Danh sách file key: .env rồi .env.* (bỏ qua file mẫu và file không có key).
ENV_FILES=()
for f in .env .env.*; do
  [ -f "$f" ] && grep -q "^A0_API_KEY=.\+" "$f" && ! grep -q "^A0_API_KEY=''" "$f" && ENV_FILES+=("$f")
done
if [ ${#ENV_FILES[@]} -eq 0 ]; then echo "Không tìm thấy file key (.env, .env.tv2, ...)."; exit 1; fi
echo "Các file key: ${ENV_FILES[*]}"

# Bộ chính. A0 phải chạy trước vì C_llm dùng dự đoán của A0 làm prior.
CONFIGS="A0 B_k4 BAL_k4 C_knn_k4 C_llm_k4"
[ "${EXTRA:-0}" = "1" ] && CONFIGS="$CONFIGS C_oracle_k4 A1_k4"

key=0
FAILED=""
for c in $CONFIGS; do
  while true; do
    envf="${ENV_FILES[$key]}"
    echo "=== $c | key: $envf | $(date +%H:%M:%S) ==="
    out=$("$PY" -m src.experiments.run_llm --config "src/configs/experiments/$c.json" \
        --llm src/configs/llm/groq.json --env-file "$envf" --split "$SPLIT" \
        --output "src/artifacts/runs/$SPLIT/$c" $EXTRA_ARGS 2>&1)
    echo "$out"
    if echo "$out" | grep -q "quota_exhausted"; then
      key=$((key + 1))
      if [ $key -ge ${#ENV_FILES[@]} ]; then
        [ -n "$FAILED" ] && echo "=== CÁC RUN BỊ CHẶN:$FAILED. Gửi thông báo lỗi ở trên cho người phụ trách code. ==="
        echo "=== Mọi key đã hết quota trong ngày: dừng. Hôm sau chạy lại đúng lệnh này. ==="
        exit 0
      fi
      echo "--- $envf hết quota, chuyển sang ${ENV_FILES[$key]} ---"
      continue
    fi
    if echo "$out" | grep -q "run_llm stopped"; then
      # Lỗi không phải do quota (ví dụ cấu hình/code đã đổi): ghi lại, chạy tiếp các run khác.
      echo "!!! $c BỊ CHẶN, cần xử lý trước lần chạy sau (xem thông báo ở trên) !!!"
      FAILED="$FAILED $c"
    fi
    break
  done
done
if [ -n "$FAILED" ]; then
  echo "=== CÁC RUN BỊ CHẶN:$FAILED. Gửi thông báo lỗi ở trên cho người phụ trách code. ==="
fi
echo "=== Xong bộ thí nghiệm trên $SPLIT ($(date +%H:%M:%S)) ==="
