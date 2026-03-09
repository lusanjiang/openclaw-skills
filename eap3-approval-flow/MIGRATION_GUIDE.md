# EAP3 XZ38 智能审批 Skill 迁移指南

## 概述

本 Skill 实现 EAP3 系统中 XZ38 定制及新产品需求流程的自动化审批，支持：
- 区域筛选（福建/江西需确认，其他自动审批）
- 物料详情提取与记录
- 飞书多维表格同步
- 人工确认机制

## 核心架构

```
用户触发/定时任务 → 登录EAP3 → 检测待办 → 区域判断
    ├── 福建/江西 → 提取物料 → 发送通知 → 等待确认 → 执行审批
    └── 其他省份 → 自动审批 → 直接记录
```

## 依赖环境

### 系统依赖
- Python 3.8+
- Playwright（浏览器自动化）
- requests（HTTP请求）

### 安装命令
```bash
pip install playwright requests
python -m playwright install chromium
```

## 核心实现步骤

### 步骤1：EAP3 登录获取 SID

**API 端点**：`POST https://eap3.tengen.com.cn/r/w`

**请求参数**：
```python
data = {
    "userid": "lusanjiang",
    "pwd": "<RSA加密后的密码>",
    "cmd": "com.actionsoft.apps.tengen.login",
    "deviceType": "pc",
    "lang": "cn",
    "pwdEncode": "RSA",
    "timeZone": "8"
}
```

**响应**：
```json
{
    "data": {
        "sid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    }
}
```

**关键代码**：
```python
def api_login(self):
    session = requests.Session()
    resp = session.post(
        f"{EAP3_URL}/r/w",
        data={...},
        timeout=30
    )
    data = resp.json()
    self.sid = data.get("data", {}).get("sid")
```

### 步骤2：浏览器初始化与待办检测

**访问工作台**：
```python
await page.goto(
    f"{EAP3_URL}/r/w?sid={sid}&cmd=com.actionsoft.apps.workbench_main_page"
)
```

**点击"待办任务"**：
```python
await page.click('text=待办任务', timeout=5000)
```

**提取 XZ38 待办**（从 iframe 中的 firstPageData）：
```javascript
// 在浏览器中执行
const data = window.firstPageData || [];
const todos = data.filter(item => 
    item.title && item.title.includes('XZ38')
);
```

### 步骤3：申请人提取与区域判断

**从标题解析申请人**：
```python
def extract_applicant(self, title):
    # 格式：(区域OPS)XZ38-定制及新产品需求-姓名-...
    parts = title.split('-')
    if len(parts) >= 3:
        return parts[2].strip()
    return "未知"
```

**区域名单配置**：
```python
FUJIAN_USERS = ["茅智伟", "谢品", "林志伟", "吴国强", 
                "黄丽萍", "何超阳", "唐悠梅"]
JIANGXI_USERS = ["肖培坤", "程明锦", "李志辉", "江伟康", 
                 "熊澄伟", "刘荣德", "胡洪箭", "朱海平", "陈毅"]
REGIONAL_USERS = set(FUJIAN_USERS + JIANGXI_USERS)

def get_region(self, applicant):
    if applicant in FUJIAN_USERS:
        return "福建"
    elif applicant in JIANGXI_USERS:
        return "江西"
    else:
        return "其他"
```

### 步骤4：表单详情提取（关键！）

**打开表单**：
```python
open_url = f"{EAP3_URL}/r/w?sid={sid}&cmd=CLIENT_BPM_FORM_MAIN_PAGE_OPEN&processInstId={pid}&taskInstId={tid}&openState=1"
await page.goto(open_url)
```

**提取物料表格**（JavaScript 注入）：
```javascript
const materials = [];
const tables = document.querySelectorAll('table');

for (let table of tables) {
    const headers = table.querySelectorAll('th, td');
    let hasCustomSeries = false;
    let hasCustomDesc = false;
    
    // 检查表头是否包含关键字段
    for (let h of headers) {
        if (h.textContent.includes('定制系列')) hasCustomSeries = true;
        if (h.textContent.includes('定制描述')) hasCustomDesc = true;
    }
    
    // 提取数据行
    if (hasCustomSeries && hasCustomDesc) {
        const rows = table.querySelectorAll('tr');
        for (let i = 1; i < rows.length; i++) {
            const cells = rows[i].querySelectorAll('td');
            materials.push({
                series: cells[0]?.textContent?.trim(),
                company: cells[1]?.textContent?.trim(),
                env: cells[2]?.textContent?.trim(),
                description: cells[3]?.textContent?.trim()
            });
        }
    }
}
```

### 步骤5：确认模式实现

**Pending 文件机制**：
```python
PENDING_FILE = "/tmp/eap3_pending_approval.json"

def save_pending_approval(self, todos):
    """保存待确认列表到文件"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "todos": todos,
        "count": len(todos)
    }
    with open(PENDING_FILE, 'w') as f:
        json.dump(data, f)

def load_pending_approval(self):
    """加载待确认列表"""
    if not os.path.exists(PENDING_FILE):
        return None
    with open(PENDING_FILE, 'r') as f:
        return json.load(f)
```

**用户确认后执行**：
```bash
# 用户回复 #审核 后执行
python3 eap3_auto_v2.py --approve-pending
```

### 步骤6：审批流程自动化

**点击"接收办理"**：
```python
await page.click('.aws-form-main-toolbar button', timeout=10000)
```

**处理确认对话框**：
```python
await page.click('.awsui-dialog button.blue:has-text("确定")', timeout=5000)
```

**选择审批结论**：
```javascript
// 点击"已核实请后台支持"
const labels = document.querySelectorAll('label');
for (let label of labels) {
    if (label.innerText.includes('已核实请后台支持')) {
        label.click();
        break;
    }
}
```

**点击"办理"提交**：
```python
await page.click('button.blue:has-text("办理")', timeout=10000)
```

### 步骤7：飞书多维表格记录

**字段结构**：
| 字段 | 类型 | 说明 |
|:---|:---|:---|
| 单据编号 | Text | XZ38-2026xxxxxx |
| 申请人 | Text | 姓名 |
| 省份 | Text | 福建/江西/其他 |
| 客户名称 | Text | 客户公司 |
| 定制系列 | Text | 产品类别 |
| 定制描述 | Text | 详细规格（关键） |
| 生产公司 | Text | 生产车间 |
| 状态 | Text | 已审批/待确认 |
| 审批时间 | DateTime | 时间戳 |

**API 写入**：
```python
POST https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records

Headers:
  Authorization: Bearer {tenant_access_token}
  Content-Type: application/json

Body:
{
    "fields": {
        "单据编号": "XZ38-2026002699",
        "申请人": "唐悠梅",
        "省份": "福建",
        "定制描述": "LMZ3D-TGH1 600/5 10-3.75VA 0.5",
        ...
    }
}
```

## 关键技巧与注意事项

### 1. SID 缓存优化
- Token 有效期约 25 分钟
- 复用 SID 避免重复登录
- 超时后自动重新获取

### 2. 页面等待策略
```python
# 固定等待（简单但慢）
await page.wait_for_timeout(5000)

# 元素等待（推荐）
await page.wait_for_selector('.some-element', timeout=10000)
```

### 3. 错误处理
```python
try:
    await page.click('button', timeout=5000)
except TimeoutError:
    # 元素不存在或已处理
    pass
```

### 4. 防重复执行
使用 PID 文件锁：
```bash
PID_FILE="/tmp/eap3_cron.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null; then
        echo "任务已在运行，跳过"
        exit 0
    fi
fi
echo $$ > "$PID_FILE"
```

### 5. 资源清理
```python
finally:
    if browser:
        await browser.close()
    if playwright:
        await playwright.stop()
```

## 定时任务配置

```bash
# crontab -e
*/20 9-18 * * * /path/to/cron_runner_v2.sh
```

**cron_runner_v2.sh 内容**：
```bash
#!/bin/bash
LOG_FILE="/var/log/eap3_cron.log"
echo "[$(date)] 启动定时任务" >> $LOG_FILE

cd /path/to/eap3-approval-flow
timeout 300 python3 eap3_auto_v2.py 2>&1 >> $LOG_FILE

# 清理残留进程
pkill -f "chrome.*--headless" 2>/dev/null || true

echo "[$(date)] 任务结束" >> $LOG_FILE
```

## 测试验证清单

- [ ] API 登录能获取 SID
- [ ] 能正确提取待办列表
- [ ] 申请人解析正确
- [ ] 区域判断正确
- [ ] 能打开表单并提取物料
- [ ] 审批流程能正常执行
- [ ] 能写入飞书表格
- [ ] 定时任务能正常触发
- [ ] 防重复机制有效
- [ ] 资源清理正常

## 常见问题

### Q1: 提取不到物料详情？
**A**: 检查页面结构是否变化，调试 JavaScript 选择器。

### Q2: 审批失败？
**A**: 截图保存现场，检查按钮选择器是否匹配。

### Q3: 飞书写入失败？
**A**: 检查 tenant_access_token 是否过期，重新获取。

### Q4: 定时任务不执行？
**A**: 检查 crontab 配置，查看日志文件权限。

## 文件清单

```
eap3-approval-flow/
├── SKILL.md                    # 使用文档
├── eap3_auto_v2.py            # 主程序
├── cron_runner_v2.sh          # 定时任务脚本
├── requirements.txt           # 依赖列表
└── references/
    ├── implementation_notes.md  # 实现笔记
    └── troubleshooting.md      # 故障排除
```

## 联系与更新

- **创建者**: Kimi Claw
- **创建时间**: 2026-03-09
- **版本**: v2.0
- **更新记录**: 见 Git 提交历史

---

**迁移完成标准**: 另一个机器人能独立运行完整审批流程并正确记录到飞书表格。