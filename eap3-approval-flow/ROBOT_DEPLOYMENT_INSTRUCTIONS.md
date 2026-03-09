# 给另一个机器人的精确部署指令

## 重要警告

**不要解释、不要编造、直接执行代码。**
如果你不懂，就说"我需要配置"，而不是瞎编答案。

---

## 第一步：确认环境（必须做）

在终端执行以下命令，确认每一项都成功：

```bash
# 1. 检查 Python
python3 --version
# 应该输出 Python 3.8+，如果不是，安装 Python3

# 2. 检查 pip
pip3 --version

# 3. 安装依赖
pip3 install playwright requests

# 4. 安装 Chromium 浏览器
python3 -m playwright install chromium
# 这一步会下载约 100MB 的浏览器，等待完成

# 5. 验证安装
python3 -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
# 应该输出 Playwright OK，如果报错，重新执行第3-4步
```

**如果以上任何一步失败，停止部署，报告问题。**

---

## 第二步：获取代码文件

从 GitHub 下载以下文件到本地目录 `/root/.openclaw/skills/eap3-approval-flow/`：

```bash
mkdir -p /root/.openclaw/skills/eap3-approval-flow
cd /root/.openclaw/skills/eap3-approval-flow

# 下载主程序
curl -O https://raw.githubusercontent.com/lusanjiang/openclaw-skills/master/eap3-approval-flow/eap3_auto_v2.py

# 下载定时任务脚本
curl -O https://raw.githubusercontent.com/lusanjiang/openclaw-skills/master/eap3-approval-flow/cron_runner_v2.sh

# 设置执行权限
chmod +x cron_runner_v2.sh
```

**验证文件存在**：
```bash
ls -la /root/.openclaw/skills/eap3-approval-flow/
# 应该看到 eap3_auto_v2.py 和 cron_runner_v2.sh
```

---

## 第三步：修改配置（关键！）

编辑 `eap3_auto_v2.py`，修改以下配置：

### 3.1 EAP3 账号配置
```python
# 第 18-19 行
USER_ID = "你的EAP3用户名"  # 例如：lusanjiang
ENCRYPTED_PWD = "你的加密密码"  # 需要向原部署者获取
```

**如何获取加密密码？**
- 询问原部署者（豆爸）提供加密后的密码
- 或者自己在浏览器登录 EAP3，从网络请求中复制 pwd 字段

### 3.2 区域人员名单
```python
# 第 25-26 行
FUJIAN_USERS = ["茅智伟", "谢品", "林志伟", "吴国强", 
                "黄丽萍", "何超阳", "唐悠梅"]
JIANGXI_USERS = ["肖培坤", "程明锦", "李志辉", "江伟康", 
                 "熊澄伟", "刘荣德", "胡洪箭", "朱海平", "陈毅"]
```

根据实际业务需求修改名单。

### 3.3 飞书配置（可选，如果不记录到飞书可跳过）
```python
# 在文件末尾添加飞书配置
FEISHU_APP_TOKEN = "你的飞书AppToken"
FEISHU_TABLE_ID = "你的表格ID"
FEISHU_APP_ID = "你的飞书AppID"
FEISHU_APP_SECRET = "你的飞书AppSecret"
```

---

## 第四步：首次测试运行（必须成功才能继续）

```bash
cd /root/.openclaw/skills/eap3-approval-flow
python3 eap3_auto_v2.py
```

**期望的输出**：
```
[xx:xx:xx] [INFO] ==================================================
[xx:xx:xx] [INFO] EAP3 XZ38审批自动化 v2.0 - 区域筛选+确认模式
[xx:xx:xx] [INFO] ==================================================
[xx:xx:xx] [INFO] 检查依赖环境...
[xx:xx:xx] [INFO] ✓ 依赖环境就绪
[xx:xx:xx] [INFO] 登录EAP3...
[xx:xx:xx] [INFO] ✓ 登录成功，SID: xxxxxxxx...
...
[前置检查] 获取待办列表...
[xx:xx:xx] [INFO] 当前待办: X 条XZ38
```

**如果输出包含以下任何错误，停止并修复**：
- `登录失败` → 检查账号密码
- `ModuleNotFoundError` → 重新安装 pip 依赖
- `playwright not found` → 重新执行 `playwright install chromium`
- `TimeoutError` → 检查网络是否能访问 eap3.tengen.com.cn

---

## 第五步：配置定时任务（可选）

```bash
crontab -e
```

添加：
```
*/20 9-18 * * * /root/.openclaw/skills/eap3-approval-flow/cron_runner_v2.sh
```

**验证定时任务**：
```bash
crontab -l | grep eap3
# 应该看到上面添加的那一行
```

---

## 第六步：处理用户指令（关键！）

当用户发送 `#审核流程` 或 `#审核流程 立即` 时：

### 6.1 你必须执行的操作

1. **执行脚本**：
   ```bash
   cd /root/.openclaw/skills/eap3-approval-flow
   python3 eap3_auto_v2.py 2>&1 | tail -100
   ```

2. **解析输出**：
   - 如果有福建/江西待办，输出会包含 `📋 检测到福建/江西区域XZ38待办`
   - 此时保存待办信息到 pending 文件，并询问用户是否审批
   - 如果只有其他省份，会自动审批，输出 `✓ 全部完成`

3. **根据结果回复用户**：
   - 有待办 → 显示物料详情，等待用户确认
   - 无待办 → 告诉用户当前没有待审批的 XZ38

### 6.2 禁止做的事

❌ **禁止编造** 流程ID、审批状态、不存在的待办
❌ **禁止问** "你要审核什么类型" —— XZ38 审批就是 XZ38 定制流程
❌ **禁止解释** 你不确定的逻辑 —— 直接执行代码看结果
❌ **禁止返回** 类似 "已提交到EAP3系统，等待审批" 这种虚假状态

### 6.3 正确的回复示例

**场景1：有待办（福建/江西）**
```
检测到福建/江西区域XZ38待办，请确认是否审批：

【1】单据编号: XZ38-2026002699
    申请人: 唐悠梅 (福建)
    客户名称: SDS-福建泉州苏东生
    物料详情:
      1. 系列: 互感器类-浇注式互感器-LMZD
         描述: LMZ3D-TGH1 600/5 10-3.75VA 0.5
         生产公司: IO_电源二车间

💡 如需审批，请回复：#审核
💡 如需跳过，请回复：#跳过
```

**场景2：无待办**
```
当前没有 XZ38 待审批流程。
```

**场景3：执行出错**
```
执行出错，错误信息：
[粘贴具体的错误日志]
需要检查：[根据错误提示给出建议]
```

---

## 第七步：用户确认后执行审批

当用户回复 `#审核` 时：

```bash
cd /root/.openclaw/skills/eap3-approval-flow
python3 eap3_auto_v2.py --approve-pending
```

**期望输出**：
```
[待确认审批] 加载 X 条记录...
...
✓ 完成
待确认审批完成: X/X 条
```

---

## 故障排查速查表

| 问题 | 排查方法 |
|:---|:---|
| 登录失败 | 检查账号密码；确认网络能访问 eap3.tengen.com.cn |
| 浏览器启动失败 | 执行 `python3 -m playwright install chromium` |
| 提取不到物料 | EAP3页面结构可能变化，需要更新 JavaScript 选择器 |
| 飞书写入失败 | 检查 App Token 和权限；tenant_access_token 可能过期 |
| 定时任务不执行 | 检查 crontab；查看 `/root/.openclaw/logs/eap3_cron.log` |

---

## 验证清单（部署完成后勾选）

- [ ] Python 3.8+ 已安装
- [ ] Playwright 和 requests 已安装
- [ ] Chromium 浏览器已下载
- [ ] 代码文件已下载到正确目录
- [ ] EAP3 账号密码已配置
- [ ] 手动执行测试成功（能看到登录成功和待办数量）
- [ ] 能正确识别福建/江西人员
- [ ] 能提取物料详情（定制系列、描述、生产公司）
- [ ] 定时任务已配置（可选）

**全部勾选完成，才能向用户宣布部署成功。**

---

## 最终警告

**如果你无法完成上述任何一步，直接告诉用户：**
> "部署遇到问题：[具体问题]。需要协助解决。"

**不要编造** "部署成功"、"技能已加载" 这种虚假状态。

**你的任务是执行代码，不是解释代码。** 如果代码执行失败，用户看到的是真实错误，而不是你编造的"流程ID"。

---

**部署者确认签名**：________________
**部署日期**：________________
**测试结果**：通过 / 未通过
