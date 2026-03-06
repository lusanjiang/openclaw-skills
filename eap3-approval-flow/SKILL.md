# EAP3 XZ38审批自动化技能

## 功能
自动完成EAP3系统中XZ38-定制及新产品需求审批流程。

## 审批流程
1. 登录EAP3获取SID
2. 访问工作台获取待办列表
3. 点击待办进入详情页
4. 点击"接收办理"
5. 确认对话框（确定）
6. 选择审批结论"已核实请后台支持"
7. 点击"办理"提交
8. 确认提交完成

## 使用方法

### 方式1: 定时任务（自动 - 每20分钟）
已配置定时任务，每20分钟自动检查并审批XZ38待办：
```bash
# 查看定时任务
crontab -l

# 查看日志
tail -f /root/.openclaw/logs/eap3_cron.log

# 手动执行一次
/root/.openclaw/skills/eap3-approval-flow/cron_runner.sh
```

### 方式2: #审批 标签（手动）
在对话中输入 `#审批` 自动触发：
```
#审批
```

### 方式3: 一键运行
```bash
cd /root/.openclaw/skills/eap3-approval-flow
python3 eap3_auto.py
```

## 定时任务配置（工作时间9:00-19:00）

### 执行时间
- **周期**: 每20分钟执行一次
- **时段**: 每天 9:00-19:00（晚上和早上不执行）
- **任务**: `*/20 9-18 * * * /root/.openclaw/skills/eap3-approval-flow/cron_runner.sh`

### 执行计划示例
```
09:00  - 第一次执行
09:20  - 第二次执行
09:40  - 第三次执行
...
18:40  - 当天最后一次执行
19:00+ - 停止执行，直到次日9:00
```

### 资源清理优化
为确保系统不卡顿，定时任务做了以下优化：
- **单次执行**: 一次任务处理完所有待办，不会并发
- **自动清理**: 任务结束后强制关闭浏览器、清理进程
- **防重复**: 检查是否已有任务在运行，避免重叠
- **超时保护**: 单任务超时600秒强制终止

### 记录方式
- **本地记录**: 审批记录保存到 `/root/.openclaw/logs/approval_record_YYYYMMDD_HHMMSS.md`
- **飞书记录**: 需要手动使用 `#审批` 标签或通过其他方式触发飞书工具写入

### 执行流程
```
检查是否有运行中的任务 → 执行审批 → 关闭浏览器 
→ 清理残留进程 → 记录内存使用 → 退出
```

### 查看日志
```bash
# 实时查看
tail -f /root/.openclaw/logs/eap3_cron.log

# 查看最近执行结果
tail -50 /root/.openclaw/logs/eap3_cron.log | grep -E "(启动|结束|处理|完成)"
```

### 执行周期
- **频率**: 每20分钟执行一次
- **任务**: `*/20 * * * * /root/.openclaw/skills/eap3-approval-flow/cron_runner.sh`

### 记录内容
定时任务会自动提取并记录以下信息到飞书文档：
- **执行时间**: 每次运行的具体时间
- **处理数量**: 本次处理了多少条待办
- **单据编号**: XZ38-2026xxxxxx
- **申请人**: 桑欣冉、潘金航等
- **物料信息**: 定制产品详情（如TGRS32-DQ方形熔断器）
- **审批状态**: ✓ 成功 / ✗ 失败

### 记录格式
```markdown
## 定时审批执行记录

**执行时间**: 2026-03-06 15:00:00
**处理数量**: 2 条

| 时间 | 单据 | 申请人 | 物料 | 状态 |
|---|---|---|---|---|
| 15:00:01 | XZ38-2026002512 | 赖佳 | TGRS32-DQ 方形... | ✓ |
| 15:00:45 | XZ38-2026002505 | 郑威 | TGM3-1600M2... | ✓ |

*自动记录 by 定时任务 #审批*
```

## 飞书记录集成

审批执行后会自动记录到飞书文档：
- **文档名称**: EAP3审批记录
- **文档链接**: https://feishu.cn/docx/Otlxd1AllogLYAxzPq4casnRnpb
- **记录内容**: 执行时间、时长、结果、SID、物料详情

审批执行后会自动记录到飞书文档：
- **文档名称**: EAP3审批记录
- **文档链接**: https://feishu.cn/docx/Otlxd1AllogLYAxzPq4casnRnpb
- **记录内容**: 执行时间、时长、结果、SID

### 记录格式
```markdown
## 审批执行记录

**执行时间**: 2026-03-06 14:34:00
**执行时长**: 45.2秒
**执行结果**: ✓ 成功
**SID**: a1b2c3d4...

*自动记录 by #审批*
```

## 自修复能力

### 自动检查项
1. **依赖检查**: 自动检测并安装缺失的Python包
2. **浏览器检查**: 自动安装Playwright Chromium浏览器
3. **目录检查**: 自动创建必要的日志目录
4. **登录检查**: 自动处理登录失败重试

### 错误恢复机制
- 浏览器启动失败 → 自动重新初始化
- 元素点击超时 → 截图记录并继续处理下一条
- 页面加载失败 → 重试3次后跳过

### 前置/后置验证
```
[前置检查] 获取待办列表...
当前待办: N 条XZ38

[执行审批]
...

[后置验证] 重新获取待办...
剩余待办: M 条XZ38

✓ 全部完成 / ⚠ 还有 M 条待处理
```

## 详细技术流程

### 1. API登录获取SID
```python
POST https://eap3.tengen.com.cn/r/w
{
    "userid": "lusanjiang",
    "pwd": "<encrypted_password>",
    "cmd": "com.actionsoft.apps.tengen.login",
    "deviceType": "pc",
    "lang": "cn",
    "pwdEncode": "RSA",
    "timeZone": "8"
}

Response: { "data": { "sid": "xxx" } }
```

### 2. 访问工作台
```
https://eap3.tengen.com.cn/r/w?sid=<sid>&cmd=com.actionsoft.apps.workbench_main_page
```

### 3. 点击"待办任务"
- 等待页面加载iframe
- Frame 1中包含firstPageData变量

### 4. 获取待办数据
```javascript
// 从firstPageData提取XZ38待办
const data = window.firstPageData || [];
const todos = data.filter(item => item.title && item.title.includes('XZ38'));
```

### 5. 打开详情页
```
https://eap3.tengen.com.cn/r/w?sid=<sid>&cmd=CLIENT_BPM_FORM_MAIN_PAGE_OPEN&processInstId=<pid>&taskInstId=<tid>&openState=1
```

### 6. 点击"接收办理"
- 查找按钮: `.aws-form-main-toolbar button`
- 或包含文字: `button:has-text("接收办理")`

### 7. 处理确认对话框
- 查找: `.awsui-dialog button.blue:has-text("确定")`
- 点击确认后等待页面刷新（约8秒）

### 8. 选择审批结论
```javascript
// 方法1: 点击label文字
const labels = document.querySelectorAll('label');
for (let label of labels) {
    if (label.innerText.includes('已核实请后台支持')) {
        label.click();
        break;
    }
}

// 方法2: 点击radio按钮
const radios = document.querySelectorAll('input[type="radio"]');
for (let r of radios) {
    const lbl = r.nextElementSibling;
    if (lbl && lbl.innerText?.includes('已核实')) {
        r.click();
        lbl.click();
        break;
    }
}
```

### 9. 点击"办理"
- 查找: `button.blue:has-text("办理")`
- 或: `.aws-form-toolbar button.blue`

### 10. 确认提交
- 查找确认对话框并点击"确定"
- 可能需要多次确认

### 11. 完成验证
- 返回工作台
- 重新获取待办列表
- 确认待办已消失

## 关键API端点

| 功能 | API |
|------|-----|
| 登录 | `com.actionsoft.apps.tengen.login` |
| 工作台 | `com.actionsoft.apps.workbench_main_page` |
| 打开表单 | `CLIENT_BPM_FORM_MAIN_PAGE_OPEN` |

## 关键选择器

| 元素 | 选择器 |
|------|--------|
| 接收办理 | `.aws-form-main-toolbar button` |
| 确定按钮 | `.awsui-dialog button.blue:has-text("确定")` |
| 已核实选项 | `label:has-text("已核实请后台支持")` |
| 办理按钮 | `button.blue:has-text("办理")` |

## 自我审核机制

### 审核步骤
1. **前置检查**: 获取当前待办数量
2. **流程执行**: 按步骤执行审批
3. **后置验证**: 再次获取待办，确认已减少
4. **截图记录**: 每步截图保存到 `/root/.openclaw/logs/`

### 审核代码
```python
# 执行前检查
todos_before = await get_todos()
print(f"执行前: {len(todos_before)} 条待办")

# 执行审批
await process_all_todos()

# 执行后验证
todos_after = await get_todos()
print(f"执行后: {len(todos_after)} 条待办")

# 确认完成
if len(todos_after) == 0:
    print("✓ 所有待办已处理完成")
else:
    print(f"⚠ 还有 {len(todos_after)} 条待办未处理")
```

## 注意事项

1. **并发审批**: XZ38可能是并签任务，允许多个审批人同时处理
2. **确认对话框**: 不同步骤可能有多个确认对话框，需要循环处理
3. **页面刷新**: 点击"接收办理"后页面会刷新，需要等待
4. **选择器优先级**: 优先使用class选择器，其次使用文字匹配

## 关键特性

### 自修复能力
```python
# 1. 依赖自动安装
REQUIRED_PACKAGES = ["playwright", "requests"]
for pkg in REQUIRED_PACKAGES:
    try:
        __import__(pkg)
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", pkg])

# 2. 浏览器自动安装
try:
    await p.chromium.launch()
except:
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])

# 3. 三重验证机制
- 前置检查: 获取待办数量
- 执行过程: 逐条处理+截图
- 后置验证: 确认待办已清空
```

### 健壮性设计
- **元素查找**: 多种选择器备选
- **超时处理**: 每个步骤独立超时
- **错误隔离**: 单条失败不影响其他
- **状态保存**: 每步截图记录

## 文件位置
- 主脚本: `/root/.openclaw/skills/eap3-approval-flow/eap3_auto.py`
- 检查脚本: `/root/.openclaw/skills/eap3-approval-flow/check_todos.py`
- 日志截图: `/root/.openclaw/logs/eap3_*.png`

## 更新记录
- 2026-03-06: 完成完整审批流程开发和测试
  - 成功处理5条初始待办
  - 成功处理2条新增待办
  - 实现完整的自我审核机制
