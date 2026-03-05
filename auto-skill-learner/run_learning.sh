#!/bin/bash
# GitHub Skill自动学习定时任务
# 每30分钟执行一次

cd ~/.openclaw/skills/auto-skill-learner
python3 github_skill_learner.py >> /tmp/skill_learning.log 2>&1
