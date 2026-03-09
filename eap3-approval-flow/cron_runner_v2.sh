#!/bin/bash
# EAP3定时审批任务 v2.0 - 区域筛选+确认模式
# 福建/江西：通知用户等待确认
# 其他省份：自动审批

LOG_FILE="/root/.openclaw/logs/eap3_cron.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========== EAP3 v2.0 定时任务启动 ==========" | tee -a $LOG_FILE

# 检查是否已有正在运行的任务
PID_FILE="/tmp/eap3_cron.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 警告: 已有任务在运行 (PID: $OLD_PID)，跳过本次执行" | tee -a $LOG_FILE
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

echo $$ > "$PID_FILE"

cd /root/.openclaw/skills/eap3-approval-flow || exit 1

# 执行检测和自动审批（福建/江西会发送通知但不审批）
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 执行检测任务..." | tee -a $LOG_FILE
timeout 300 python3 eap3_auto_v2.py 2>&1 | tee -a $LOG_FILE
EXIT_CODE=${PIPESTATUS[0]}

# 清理进程
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 清理残留进程..." | tee -a $LOG_FILE
pkill -f "chrome.*--headless" 2>/dev/null || true
pkill -f "chromium.*--headless" 2>/dev/null || true
sleep 2

PIDS=$(pgrep -f "chrome.*eap3" 2>/dev/null)
if [ -n "$PIDS" ]; then
    kill -9 $PIDS 2>/dev/null || true
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 内存使用情况:" | tee -a $LOG_FILE
free -h | tee -a $LOG_FILE

rm -f "$PID_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 任务结束，退出码: $EXIT_CODE" | tee -a $LOG_FILE
echo "---" | tee -a $LOG_FILE

exit $EXIT_CODE
