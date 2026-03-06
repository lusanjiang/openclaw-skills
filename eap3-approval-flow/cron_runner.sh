#!/bin/bash
# EAP3定时审批任务 - 每20分钟执行一次
# 确保一次做完、及时关闭清理

# 日志
LOG_FILE="/root/.openclaw/logs/eap3_cron.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ========== 启动定时审批任务 ==========" | tee -a $LOG_FILE

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

# 写入当前PID
echo $$ > "$PID_FILE"

# 切换到技能目录
cd /root/.openclaw/skills/eap3-approval-flow || exit 1

# 执行审批任务
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始执行 Python 脚本..." | tee -a $LOG_FILE
timeout 600 python3 eap3_cron.py 2>&1 | tee -a $LOG_FILE
EXIT_CODE=${PIPESTATUS[0]}

# 清理残留的chrome进程
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 清理残留进程..." | tee -a $LOG_FILE
pkill -f "chrome.*--headless" 2>/dev/null || true
pkill -f "chromium.*--headless" 2>/dev/null || true
sleep 2

# 强制清理（如果还有残留）
PIDS=$(pgrep -f "chrome.*eap3" 2>/dev/null)
if [ -n "$PIDS" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 强制清理残留进程: $PIDS" | tee -a $LOG_FILE
    kill -9 $PIDS 2>/dev/null || true
fi

# 显示内存使用情况
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 内存使用情况:" | tee -a $LOG_FILE
free -h | tee -a $LOG_FILE

# 删除PID文件
rm -f "$PID_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 任务结束，退出码: $EXIT_CODE" | tee -a $LOG_FILE
echo "---" | tee -a $LOG_FILE

exit $EXIT_CODE
