# EAP3 XZ38 审批 Skill v2.0 - 工作流架构

基于 Coze 工作流设计理念重构，支持 YAML 可视化编排。

## 架构变化

### v1.0 → v2.0

| 维度 | v1.0 (代码驱动) | v2.0 (工作流驱动) |
|:---|:---|:---|
| **流程定义** | 硬编码在 Python 中 | YAML 配置文件 |
| **可读性** | 需读代码理解流程 | 看 YAML 即可 |
| **修改流程** | 改 Python 代码 | 改 YAML 配置 |
| **节点复用** | 复制粘贴 | 拖拽复用 |
| **可视化** | 无 | 未来可支持 |

## 工作流结构

```yaml
name: EAP3 XZ38 审批流程
version: "2.0"

# 输入参数
inputs:
  action:
    type: string
    enum: [check, approve, approve_pending]

# 节点编排
nodes:
  - id: login              # 节点ID
    type: api_call         # 节点类型
    name: EAP3登录
    depends_on: []         # 依赖节点
    
  - id: check_todos
    type: browser_action
    name: 检测待办
    depends_on: [login]    # 依赖login节点完成
    
  - id: region_selector
    type: selector         # 条件分支
    condition: "${parse.regional.length > 0}"
    branches:
      - case: true         # 有福建/江西待办
        nodes: [...]
      - case: false        # 无福建/江西待办
        nodes: [...]
```

## 支持的节点类型

| 类型 | 说明 | 示例 |
|:---|:---|:---|
| `api_call` | HTTP API 调用 | EAP3 登录 |
| `browser_action` | 浏览器自动化 | 打开表单、提取数据 |
| `code` | 执行 Python/JS 代码 | 解析申请人、区域判断 |
| `selector` | 条件分支（if/else） | 福建/江西 vs 其他 |
| `notify` | 发送通知到用户 | 发送待办详情 |
| `python_script` | 执行外部 Python 脚本 | 审批执行 |
| `database_write` | 写入数据库 | 飞书多维表格记录 |
| `log` | 记录日志 | 调试信息 |

## 变量系统

### 输入变量
```yaml
inputs:
  action: check  # 用户传入
```

### 节点输出引用
```yaml
${login.sid}           # login节点的sid输出
${parse.regional}      # parse节点的regional输出
${inputs.action}       # 输入参数
```

### 密钥引用
```yaml
${secrets.EAP3_USER}   # 从安全存储读取
```

## 使用方式

### 方式1：直接执行工作流
```bash
cd /root/.openclaw/skills/eap3-approval-flow
python3 workflow_engine.py
```

### 方式2：传统方式（兼容）
```bash
python3 eap3_auto_v2.py
```

### 方式3：标签触发
```
#审核流程 立即
```

## 扩展新节点

在 `workflow_engine.py` 中添加：

```python
async def _execute_new_node(self, node: Node) -> Dict:
    """执行新节点类型"""
    config = self.interpolate(node.config)
    # 实现节点逻辑
    return {'result': 'success'}
```

## 迁移指南

### 从 v1.0 迁移到 v2.0

1. 理解原有代码逻辑
2. 将流程映射为 YAML 节点
3. 测试工作流执行
4. 逐步替换旧代码

### 优势

- ✅ 流程可视化（看 YAML 就知道流程）
- ✅ 易于修改（改配置不改代码）
- ✅ 节点复用（通用节点可共享）
- ✅ 错误隔离（单节点失败不影响其他）

## 未来规划

1. **Web 可视化编辑器** - 拖拽编排节点
2. **节点市场** - 共享通用节点
3. **调试模式** - 单步执行、查看变量
4. **版本管理** - 工作流版本回滚

## 参考

学习自 [Coze 扣子](https://www.coze.cn) 的工作流设计理念，
应用于 OpenClaw 的代码优先架构。

---

**更新日期**: 2026-03-10  
**版本**: v2.0  
**作者**: Kimi Claw
