#!/bin/bash
# 设置EAP3定时审批任务 - 白天9:00-19:00，每20分钟执行一次

echo "设置EAP3定时审批任务..."
echo "执行时间: 每天 9:00-19:00，每20分钟"
echo ""

# 检查现有crontab
echo "当前crontab内容:"
crontab -l 2>/dev/null || echo "(空)"
echo ""

# 删除旧的EAP3定时任务（如果有）
crontab -l 2>/dev/null | grep -v "eap3_cron.py\|cron_runner.sh\|eap3_complete_cron" | crontab -

# 添加新的定时任务（只在9:00-19:00执行）
# 格式: */20 9-18 * * * 表示9:00-18:59每20分钟执行
CRON_LINE="*/20 9-18 * * * /root/.openclaw/skills/eap3-approval-flow/cron_runner.sh >> /root/.openclaw/logs/eap3_cron.log 2>&1"

(echo "# EAP3定时审批任务 - 工作时间9:00-19:00每20分钟执行") | crontab -
(echo "$CRON_LINE") | crontab -

echo "✓ 定时任务已更新"
echo ""
echo "新的crontab内容:"
crontab -l
echo ""
echo "✓ 设置完成！"
echo ""
echo "执行时间说明:"
echo "  - 每天 9:00-19:00 之间每20分钟执行一次"
echo "  - 早上9:00开始第一次执行"
echo "  - 晚上19:00后停止执行"
echo "  - 周末和工作日都会执行"
echo ""
echo "查看日志:"
echo "  tail -f /root/.openclaw/logs/eap3_cron.log"
