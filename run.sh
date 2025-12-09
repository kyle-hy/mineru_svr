#!/bin/bash
# run.sh

APP_MODULE="main:app"
PORT=8090
WORKERS=8
LOG_FILE="uvicorn.log"
PID_FILE="uvicorn.pid"

# 启动前清理进程
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        # 校验进程是否真的是我们的 uvicorn 主进程（防 PID reuse）
        # 注意：/proc/$OLD_PID/cmdline 是 null 分隔，需 tr '\0' '\n'
        CMDLINE=$(tr '\0' ' ' < "/proc/$OLD_PID/cmdline" 2>/dev/null)
        if echo "$CMDLINE" | grep -q "uvicorn.*$APP_MODULE"; then
            echo "Stopping old process (PID: $OLD_PID) ..."
            kill "$OLD_PID"
            # ...后续等待逻辑同原脚本...
        else
            echo "⚠️ PID $OLD_PID exists but is NOT our uvicorn process (cmd: ${CMDLINE:0:50}...). Skipping kill."
            # 不 kill，但建议清理 stale PID file
            rm -f "$PID_FILE"
        fi
    else
        # PID 不存在，清理 stale 文件
        rm -f "$PID_FILE"
    fi
fi


# ===== 启动新实例 =====
echo "Starting Uvicorn ($APP_MODULE) on :$PORT with $WORKERS workers..."
nohup uvicorn "$APP_MODULE" \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers $WORKERS \
    --log-level info \
    > "$LOG_FILE" 2>&1 &

NEW_PID=$!
echo $NEW_PID > "$PID_FILE"
echo "✅ Started with PID $NEW_PID, logs → $LOG_FILE"