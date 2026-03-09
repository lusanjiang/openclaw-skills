#!/bin/bash
# #审批 标签触发脚本
# 放置在触发器目录中

cd /root/.openclaw/skills/eap3-approval-flow
python3 eap3_tag_approval.py "$@"
