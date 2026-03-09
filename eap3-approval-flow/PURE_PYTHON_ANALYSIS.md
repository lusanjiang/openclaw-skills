# EAP3 纯Python实现方案分析

## 现状分析

### 当前实现（v2.0）
```
API登录 → Playwright浏览器 → 点击待办 → 打开表单 → 提取物料 → 审批提交
```
**依赖**: Playwright + Chromium浏览器

### 目标实现（v3.0）
```
API登录 → 直接调用EAP3 API → JSON数据 → 审批API
```
**依赖**: 仅requests

---

## 需要逆向的关键点

### 1. 待办列表API

**当前**: 通过浏览器访问工作台页面，从window.firstPageData提取

**需要找到**:
```
GET/POST /r/w?cmd=XXX 
Response: JSON格式的待办列表
```

**逆向方法**:
1. Chrome DevTools → Network → XHR
2. 刷新工作台页面
3. 查找返回待办数据的请求
4. 分析请求参数和响应结构

### 2. 表单详情API

**当前**: 通过浏览器打开表单页面，JavaScript提取表格数据

**需要找到**:
```
GET/POST /r/w?cmd=XXX
Params: processInstId, taskInstId
Response: JSON格式的表单数据
```

**逆向方法**:
1. 点击一个待办进入表单
2. Network中查找加载表单数据的请求
3. 分析响应中的物料字段

### 3. 审批提交API

**当前**: 浏览器点击"办理"→"确定"→"提交"

**需要找到**:
```
POST /r/w?cmd=XXX
Body: taskInstId, processInstId, opinion, 其他参数
```

**逆向方法**:
1. 执行一次审批（测试环境）
2. Network中抓包记录完整的审批流程
3. 分析每个步骤的API调用

---

## 可能遇到的加密/签名

### 情况1: 无加密（最简单）
- API直接返回JSON
- 直接requests调用即可

### 情况2: Cookie/Session验证
- 需要携带sid cookie
- 可能需要额外的token

### 情况3: 参数签名
- 类似京东h5st、抖音a_bogus
- 需要逆向JS找到签名算法

### 情况4: 表单数据嵌套在HTML
- 需要用BeautifulSoup解析HTML
- 提取表单字段

---

## 实施步骤

### 第一步：抓包分析（30分钟）
1. 登录EAP3，打开工作台
2. Chrome DevTools → Network → XHR
3. 记录所有API调用
4. 分析待办、表单、审批的API端点

### 第二步：API验证（30分钟）
1. 用curl/Postman测试发现的API
2. 验证参数和响应格式
3. 确认是否需要额外签名

### 第三步：纯Python实现（1小时）
1. 替换Playwright为requests
2. 实现纯API调用的审批流程
3. 测试并调试

### 第四步：异常处理（30分钟）
1. 添加重试机制
2. 处理登录过期
3. 处理API限流

---

## 预期收益

| 指标 | 当前(Playwright) | 目标(纯Python) | 提升 |
|:---|:---|:---|:---:|
| 启动时间 | 10-15秒 | 1-2秒 | 80% |
| 内存占用 | 200-300MB | 50-100MB | 70% |
| 依赖复杂度 | 高(Chromium) | 低(requests) | - |
| 稳定性 | 中(浏览器崩溃) | 高(纯API) | - |

---

## 风险提示

1. **API变动风险**: EAP3升级可能导致API变化
2. **反爬加强**: 如果EAP3增加签名验证，需要额外逆向
3. **测试环境**: 务必在测试环境验证后再上生产

---

## 建议

**分阶段实施**:
1. **第一阶段**: 保持现有Playwright实现，作为fallback
2. **第二阶段**: 实现纯Python版本，与现有版本并行运行
3. **第三阶段**: 验证稳定后，切换为主版本

**今日是否实施？**
- 如果时间充裕（2-3小时），可以立即开始抓包分析
- 如果时间有限，建议明天专门安排时间实施
