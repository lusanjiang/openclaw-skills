---
name: templar-fund-analyzer
description: TEMPLAR-003458 基金量化交易分析系统 - 基于周五效应的智能交易策略
---

# TEMPLAR-003458 基金量化分析 Skill

基于1年历史数据，自动分析基金周五效应、周内规律，生成每日交易建议。

## 核心策略

### 周五效应 (假设H1)
- **发现**: 周五下跌概率 > 60%
- **验证**: 通过1年242个交易日数据验证 ✅
- **操作**: 周五开盘减仓至30%

### 周内规律
| 星期 | 策略 | 仓位建议 |
|:---:|:---|:---:|
| 周一 | 若低开加仓 | 70% |
| 周二 | 持有观望 | 维持 |
| 周三 | 减仓准备 | 50% |
| 周四 | 观望 | 维持 |
| 周五 | **开盘减仓** | **30%** |

## 使用方法

### 命令行

```bash
# 生成今日交易建议
python3 /root/.openclaw/workspace/templar_skill_complete.py

# 查看建议
cat /root/.openclaw/workspace/daily_advice.txt
```

### Python导入

```python
from templar_skill_complete import TemplarFundAnalyzer

analyzer = TemplarFundAnalyzer("017612")
advice = analyzer.get_today_advice()
print(advice)
```

### 定时任务

每天10:00自动执行：
```bash
# 查看定时任务
crontab -l | grep templar

# 手动执行
cd /root/.openclaw/workspace && python3 templar_skill_complete.py
```

## 文件结构

```
/root/.openclaw/workspace/
├── templar_skill_complete.py    # 核心分析脚本
├── fund_data.py                 # 数据获取脚本
├── fund_final.py                # 备用分析脚本
├── daily_advice.txt             # 每日建议输出
└── TEMPLAR-003458-FINAL-COMPLETE.md  # 完整报告

/root/.openclaw/scripts/
└── templar_daily_cron.sh        # 定时任务脚本

/root/.openclaw/skills/templar-fund-analyzer/
├── SKILL.md                     # 本文件
└── templar_analyzer.py          # 备用分析器
```

## 交易策略规则

### 买入条件
- 周一低开 ≥ 2%
- 单次加仓 ≤ 2500元
- 目标仓位 ≤ 70%

### 卖出条件
- 周五开盘减仓至30%
- 硬止损线 -3%
- 禁止买入时间: 14:55后

## 数据来源

- **平台**: 东方财富天天基金网
- **接口**: https://api.fund.eastmoney.com/f10/LSJZChart
- **频率**: 每日更新
- **范围**: 最近1年（约242个交易日）

## 日志

```bash
# 查看执行日志
tail -f /root/.openclaw/logs/templar_daily.log
```

## 版本

- v1.0 (2026-03-08): 初始版本
- 支持基金: 宏利复兴伟业灵活配置混合C (017612)
- 创建者: Kimi Claw

## 相关任务

- 任务书: TEMPLAR-003458-任务书.md
- 分析报告: TEMPLAR-003458-FINAL-COMPLETE.md
