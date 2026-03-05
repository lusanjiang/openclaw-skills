---
name: web-search-skill
description: 网页搜索技能。使用#搜索标签快速进行网络搜索，获取最新信息。
---

# 网页搜索 Skill

## 快速使用

使用 `#搜索` 标签快速搜索：

```
#搜索 最新AI技术
#搜索 天正电气新闻
#搜索 燃气热水器评测
```

## 搜索工具

### 1. Brave搜索（主力）

```python
web_search(
    query="搜索词",
    count=10,           # 结果数量
    freshness="pd"      # 时间筛选：pd=当天, pw=本周, pm=本月, py=本年
)
```

### 2. DuckDuckGo多引擎（备选）

```bash
# Google引擎
ddgs search "query" --engine google --max 10

# Bing引擎
ddgs search "query" --engine bing --max 10
```

### 3. 网页正文提取

```python
web_fetch(
    url="https://...",
    extractMode="markdown",  # 或 "text"
    maxChars=10000          # 最大字符数
)
```

### 4. arXiv论文搜索

```bash
ddgs arxiv "large language model agents" --max 5
```

## 使用场景

| 场景 | 示例 |
|:---|:---|
| 最新资讯 | `#搜索 美伊战争最新进展` |
| 产品评测 | `#搜索 iPhone 16 评测` |
| 技术文档 | `#搜索 OpenClaw 文档` |
| 学术论文 | `#搜索 arxiv LLM agents` |
| 价格查询 | `#搜索 燃气热水器 价格` |

## 最佳实践

1. **关键词精准** - 使用具体词汇而非笼统描述
2. **时间筛选** - 用 freshness 获取最新信息
3. **多引擎验证** - 交叉验证搜索结果
4. **提取正文** - 用 web_fetch 获取完整内容

## 示例

```
用户：#搜索 天正电气 2024 年报

→ 使用 web_search(query="天正电气 2024 年报", count=5)
→ 提取关键信息
→ 总结回复
```
