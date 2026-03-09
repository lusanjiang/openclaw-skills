# OpenClaw Skill 工作流架构 v2.0 开发指南

> 学习自 Coze (扣子) 平台的设计理念，应用于 OpenClaw 的代码优先架构

---

## 架构概述

### 三层 Skill 架构

```
skill-name/
├── metadata.json      ← 第一层：元数据（启动时加载，~100 tokens）
├── SKILL.md           ← 第二层：详细文档（任务相关时加载）
├── workflow.yaml      ← 第三层：工作流定义（执行时加载）
├── workflow_engine.py ← 工作流执行引擎（可引用通用引擎）
└── [其他资源文件]      ← 关联文件（按需加载）
```

### 设计理念

| 层级 | 加载时机 | 内容 | 目的 |
|:---|:---|:---|:---|
| **metadata** | Agent 启动 | 名称、版本、触发器、输入参数 | 快速筛选相关 Skill |
| **SKILL.md** | 任务匹配 | 详细说明、使用示例、规则 | 理解 Skill 功能 |
| **workflow** | 执行时 | 节点编排、流程定义 | 执行业务逻辑 |
| **resources** | 按需 | 脚本、模板、数据文件 | 支持执行 |

**核心优势**：无关 Skill 不占用上下文，大 Skill 也能高效加载。

---

## 第一层：metadata.json

### 作用
Agent 启动时只加载 metadata，用于：
- 判断用户输入是否匹配该 Skill
- 评估资源消耗
- 确定输入参数

### 完整示例

```json
{
  "name": "skill-name",
  "description": "Skill 的简短描述，一句话说明功能",
  "version": "2.0",
  "tags": ["#标签1", "#标签2"],
  
  "trigger": {
    "keywords": ["#触发词1", "#触发词2"],
    "patterns": ["正则.*匹配", "模式.*识别"],
    "cron": "0 9 * * *"
  },
  
  "input_schema": {
    "type": "object",
    "properties": {
      "param1": {
        "type": "string",
        "description": "参数说明"
      },
      "param2": {
        "type": "string",
        "enum": ["option1", "option2"],
        "default": "option1"
      }
    },
    "required": ["param1"]
  },
  
  "workflow": {
    "enabled": true,
    "file": "workflow.yaml"
  },
  
  "cost": {
    "memory": "低/中/高",
    "time": "预计执行时间",
    "api_calls": 3
  },
  
  "requirements": {
    "python_packages": ["requests", "pandas"],
    "system_deps": ["chromium"],
    "network": ["api.example.com"]
  },
  
  "author": "你的名字",
  "created": "2026-03-10",
  "updated": "2026-03-10"
}
```

### 字段详解

| 字段 | 类型 | 必填 | 说明 |
|:---|:---|:---:|:---|
| `name` | string | ✅ | Skill 唯一标识，小写+连字符 |
| `description` | string | ✅ | 一句话描述功能 |
| `version` | string | ✅ | 语义化版本，如 "2.0" |
| `tags` | array | ❌ | 标签列表，用于分类 |
| `trigger.keywords` | array | ❌ | 关键词触发，如 `["#审批"]` |
| `trigger.patterns` | array | ❌ | 正则匹配，如 `["审批.*流程"]` |
| `trigger.cron` | string | ❌ | 定时触发，如 `"0 9 * * *"` |
| `input_schema` | object | ❌ | JSON Schema 定义输入参数 |
| `workflow.enabled` | boolean | ✅ | 是否启用工作流 |
| `workflow.file` | string | ✅ | 工作流文件路径 |
| `cost` | object | ❌ | 资源消耗评估 |
| `requirements` | object | ❌ | 依赖要求 |

---

## 第二层：SKILL.md

### 作用
提供 Skill 的详细说明，包括：
- 功能介绍
- 使用方法
- 示例
- 注意事项

### 模板

```markdown
---
name: skill-name
description: Skill 描述
---

# Skill 名称 v2.0

> 一句话功能概述  
> 🔄 **v2.0 更新**：引入了 xxx 新特性

---

## 快速调用

| 标签 | 用途 | 示例 |
|------|------|------|
| `#标签` | 功能说明 | `#标签 参数` |

---

## 🏗️ 工作流架构 (v2.0)

```
用户输入 → 节点1 → 节点2 → 节点3 → 输出结果
    │         │        │        │
    ▼         ▼        ▼        ▼
  #标签    功能A    功能B    功能C
```

### 节点类型
| 节点 | 功能 | 说明 |
|:---|:---|:---|
| `node1` | 功能A | 详细说明 |
| `node2` | 功能B | 详细说明 |

---

## 使用示例

### 示例1：基础用法
```
#标签 参数
```

### 示例2：高级用法
```
#标签 参数1 参数2
```

---

## 配置文件

- `metadata.json` - Skill 元数据
- `workflow.yaml` - 工作流定义
- `script.py` - 执行脚本

---

## 版本记录

| 版本 | 日期 | 更新内容 |
|:---|:---|:---|
| v1.0 | 2026-03-01 | 基础功能 |
| v2.0 | 2026-03-10 | **引入工作流架构** |

---

## 注意事项

1. 注意事项1
2. 注意事项2
```

---

## 第三层：workflow.yaml

### 作用
定义业务流程，将复杂逻辑拆解为可复用的节点。

### 完整示例

```yaml
name: 审批流程示例
version: "2.0"
description: 演示工作流编排

trigger:
  - keyword: "#审批"
  - pattern: "审批.*流程"

# 输入参数定义
inputs:
  action:
    type: string
    enum: [check, approve]
    default: check
    description: 操作类型

# 工作流节点
nodes:
  # ========== 节点1: API 调用 ==========
  - id: api_login
    type: api_call
    name: 登录系统
    description: 调用API获取Token
    config:
      url: "https://api.example.com/login"
      method: POST
      headers:
        Content-Type: application/json
      body:
        username: "${secrets.USERNAME}"
        password: "${secrets.PASSWORD}"
    output:
      token: "${response.data.token}"
      expires: "${response.data.expires}"
    on_error:
      action: fail
      message: "登录失败"

  # ========== 节点2: 浏览器操作 ==========
  - id: open_page
    type: browser_action
    name: 打开网页
    description: 使用Playwright打开网页并提取数据
    depends_on: [api_login]
    config:
      url: "https://example.com/dashboard"
      actions:
        - wait: 3000
        - click: "button.login"
        - execute_js: |
            return document.querySelector('.data').innerText;
    output:
      page_data: "${js_result}"

  # ========== 节点3: 代码执行 ==========
  - id: process_data
    type: code
    name: 处理数据
    description: 执行Python代码处理数据
    depends_on: [open_page]
    config:
      language: python
      code: |
        data = inputs['open_page']['page_data']
        
        # 数据处理逻辑
        result = data.strip().split('\n')
        
        outputs['processed'] = result
        outputs['count'] = len(result)
    output:
      processed: "${outputs.processed}"
      count: "${outputs.count}"

  # ========== 节点4: 条件分支（选择器）==========
  - id: check_condition
    type: selector
    name: 条件判断
    description: 根据条件执行不同分支
    depends_on: [process_data]
    condition: "${process_data.count} > 0"
    branches:
      # 分支A: 条件为真
      - case: true
        nodes:
          - id: handle_data
            type: python_script
            name: 处理有数据
            script: "handle_data.py"
            args: ["${process_data.processed}"]
      
      # 分支B: 条件为假
      - case: false
        nodes:
          - id: no_data
            type: notify
            message: "没有找到数据"

  # ========== 节点5: LLM 推理 ==========
  - id: llm_analysis
    type: llm_reasoning
    name: AI分析
    description: 调用大模型进行推理
    depends_on: [process_data]
    config:
      model: "kimi-coding/k2p5"
      temperature: 0.3
      system_prompt: "你是专业的分析师..."
      user_prompt: |
        请分析以下数据：
        {{process_data.processed}}
    output:
      analysis: "${response.content}"

  # ========== 节点6: 数据库写入 ==========
  - id: save_to_db
    type: database_write
    name: 保存结果
    description: 写入飞书多维表格
    depends_on: [llm_analysis]
    config:
      provider: feishu_bitable
      app_token: "${secrets.FEISHU_APP_TOKEN}"
      table_id: "${secrets.FEISHU_TABLE_ID}"
      record:
        字段1: "{{process_data.count}}"
        字段2: "{{llm_analysis.analysis}}"
        时间: "{{now()}}"
    output:
      record_id: "${response.record_id}"

  # ========== 节点7: 发送通知 ==========
  - id: notify_user
    type: notify
    name: 通知用户
    description: 发送结果给用户
    depends_on: [save_to_db]
    config:
      channel: feishu
      template: |
        处理完成！
        
        数据条数: {{process_data.count}}
        AI分析: {{llm_analysis.analysis}}
        
        已保存到飞书表格。

# 错误处理
on_error:
  - type: notify
    message: "❌ 流程执行失败: ${error.message}"
  - type: log
    level: error
    message: "${error.stack}"

# 成功处理
on_success:
  - type: notify
    message: "✅ 流程执行完成"
  - type: log
    message: "处理成功"
```

---

## 节点类型详解

### 1. api_call - API 调用
```yaml
- id: api_node
  type: api_call
  config:
    url: "https://api.example.com/endpoint"
    method: GET | POST | PUT | DELETE
    headers:
      Authorization: "Bearer ${secrets.TOKEN}"
    params:  # GET 参数
      key: value
    body:  # POST/PUT 参数
      key: value
  output:
    result: "${response.data}"
```

### 2. browser_action - 浏览器自动化
```yaml
- id: browser_node
  type: browser_action
  config:
    url: "https://example.com"
    actions:
      - wait: 3000                    # 等待毫秒
      - click: "selector"             # 点击元素
      - type:                         # 输入文本
          selector: "#input"
          text: "hello"
      - execute_js: "return document.title;"  # 执行JS
  output:
    title: "${js_result}"
```

### 3. code - 代码执行
```yaml
- id: code_node
  type: code
  config:
    language: python | javascript
    code: |
      # Python 代码
      data = inputs['prev_node']['output_key']
      result = data.strip()
      outputs['result'] = result
  output:
    result: "${outputs.result}"
```

### 4. selector - 条件分支
```yaml
- id: selector_node
  type: selector
  condition: "${prev_node.value} > 10"
  branches:
    - case: true
      nodes:
        - id: true_branch
          type: notify
          message: "值大于10"
    - case: false
      nodes:
        - id: false_branch
          type: notify
          message: "值小于等于10"
```

### 5. llm_reasoning - LLM 推理
```yaml
- id: llm_node
  type: llm_reasoning
  config:
    model: "kimi-coding/k2p5"
    temperature: 0.3
    system_prompt: "你是专业的分析师..."
    user_prompt: |
      请分析：
      {{prev_node.data}}
  output:
    result: "${response.content}"
```

### 6. python_script - 执行外部脚本
```yaml
- id: script_node
  type: python_script
  script: "my_script.py"
  args:
    - "${prev_node.output}"
    - "--flag"
  output:
    stdout: "${stdout}"
    stderr: "${stderr}"
```

### 7. database_write - 数据库写入
```yaml
- id: db_node
  type: database_write
  config:
    provider: feishu_bitable | sqlite | mysql
    connection: "${secrets.DB_CONNECTION}"
    table: "my_table"
    record:
      field1: "{{prev_node.value1}}"
      field2: "{{prev_node.value2}}"
```

### 8. notify - 发送通知
```yaml
- id: notify_node
  type: notify
  config:
    channel: feishu | telegram | email
    template: |
      处理结果：
      {{prev_node.result}}
```

### 9. log - 记录日志
```yaml
- id: log_node
  type: log
  config:
    level: info | warn | error
    message: "操作完成"
```

### 10. file_read / file_write - 文件操作
```yaml
- id: file_node
  type: file_read  # 或 file_write
  config:
    path: "/path/to/file.txt"
    append: true  # write 时可选
  output:
    content: "${content}"
```

---

## 变量系统

### 输入变量
```yaml
inputs:
  action: check
```
引用：`${inputs.action}`

### 节点输出引用
```yaml
${node_id.output_key}      # 引用其他节点的输出
${inputs.param}             # 引用输入参数
${secrets.SECRET_KEY}       # 引用密钥
${now()}                    # 当前时间
${today()}                  # 当前日期
```

### 变量插值示例
```yaml
config:
  url: "https://api.example.com/${inputs.endpoint}"
  body:
    token: "${secrets.API_TOKEN}"
    data: "${prev_node.result}"
```

---

## 创建新 Skill 的步骤

### 步骤1：创建目录结构
```bash
mkdir -p ~/.openclaw/skills/my-skill
cd ~/.openclaw/skills/my-skill
```

### 步骤2：编写 metadata.json
```bash
cat > metadata.json << 'EOF'
{
  "name": "my-skill",
  "description": "我的Skill描述",
  "version": "1.0",
  "tags": ["#mytag"],
  "trigger": {
    "keywords": ["#mytag"]
  },
  "workflow": {
    "enabled": true,
    "file": "workflow.yaml"
  }
}
EOF
```

### 步骤3：编写 workflow.yaml
```bash
cat > workflow.yaml << 'EOF'
name: 我的工作流
trigger:
  - keyword: "#mytag"

nodes:
  - id: step1
    type: code
    name: 第一步
    config:
      language: python
      code: |
        outputs['result'] = "Hello World"

  - id: step2
    type: notify
    name: 发送结果
    depends_on: [step1]
    config:
      message: "{{step1.result}}"
EOF
```

### 步骤4：编写 SKILL.md
```bash
cat > SKILL.md << 'EOF'
---
name: my-skill
description: 我的Skill
---

# My Skill v1.0

## 使用
```
#mytag
```
EOF
```

### 步骤5：测试
```bash
# 在 OpenClaw 中输入
#mytag
```

---

## 最佳实践

### 1. 节点设计原则
- **单一职责**：每个节点只做一件事
- **可复用**：通用逻辑抽离为独立节点
- **可测试**：节点可单独测试

### 2. 错误处理
```yaml
on_error:
  - type: notify
    message: "执行失败: ${error.message}"
  - type: log
    level: error
```

### 3. 超时控制
```yaml
- id: slow_node
  type: api_call
  config:
    timeout: 30000  # 30秒超时
```

### 4. 重试机制
```yaml
- id: retry_node
  type: api_call
  config:
    retries: 3      # 重试3次
    retry_delay: 1000  # 间隔1秒
```

---

## 示例：完整审批 Skill

见 `eap3-approval-flow/` 目录：
- `metadata.json` - 定义触发器和参数
- `workflow.yaml` - 5个节点编排审批流程
- `SKILL.md` - 详细使用文档

---

## 参考资源

- **Coze 工作流设计**: https://www.coze.cn/docs/guides/workflow
- **OpenClaw 文档**: https://docs.openclaw.ai
- **示例 Skills**: https://github.com/lusanjiang/openclaw-skills

---

**版本**: v2.0  
**作者**: Kimi Claw  
**日期**: 2026-03-10
