# 直接执行指令 - 不要解释，只做

## 第一步：验证环境

执行以下命令，把**完整的输出**（包括成功或失败）复制回复：

```bash
python3 --version
pip3 list | grep -E "playwright|requests"
ls -la /root/.openclaw/skills/eap3-approval-flow/
```

**注意**：如果上面的命令报错或输出为空，停止，告诉我具体错误。

---

## 第二步：下载代码

执行：

```bash
mkdir -p /root/.openclaw/skills/eap3-approval-flow
cd /root/.openclaw/skills/eap3-approval-flow

curl -o eap3_auto_v2.py https://raw.githubusercontent.com/lusanjiang/openclaw-skills/master/eap3-approval-flow/eap3_auto_v2.py

curl -o cron_runner_v2.sh https://raw.githubusercontent.com/lusanjiang/openclaw-skills/master/eap3-approval-flow/cron_runner_v2.sh

chmod +x cron_runner_v2.sh

ls -la
```

**把 ls -la 的完整输出复制回复**，确认文件已下载。

---

## 第三步：配置账号

编辑文件 `eap3_auto_v2.py`，找到第 18-19 行：

```python
USER_ID = "lusanjiang"
ENCRYPTED_PWD = "..."
```

**向豆爸（用户）询问**：
1. EAP3 用户名是什么？
2. 加密密码是什么？

**不要自己编密码**，必须问用户获取真实值。

修改后执行：

```bash
grep "USER_ID\|ENCRYPTED_PWD" eap3_auto_v2.py | head -2
```

**把输出复制回复**，确认配置已修改。

---

## 第四步：测试运行（最关键）

执行：

```bash
cd /root/.openclaw/skills/eap3-approval-flow
python3 eap3_auto_v2.py 2>&1
```

**把完整的输出（从头到尾）复制回复**，不要删减。

---

## 第五步：如果测试成功

输出应该包含：
- `✓ 登录成功，SID: xxxx`
- `当前待办: X 条XZ38`
- 如果有福建/江西待办，会显示物料详情

**只有看到上述输出，才能说"技能已就绪"**。

---

## 重要规则（违反就错了）

1. **不要解释你在做什么** — 直接执行命令，给我看结果
2. **不要编造输出** — 如果命令执行失败，给我看真实错误
3. **不要问"你要审核什么"** — 用户说 `#审核流程` 时，直接执行上面的测试命令
4. **每步必须验证** — 执行完命令后，把输出给我确认，再进行下一步

---

## 现在开始

执行第一步的命令，把输出给我。
