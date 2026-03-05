---
name: tengen-knowledge-base
description: 天正电气产品知识库，包含断路器、接触器、继电器等全系列产品资料、技术参数、选型手册、价格信息。当用户需要查询天正电气任何产品信息、技术资料、选型指导时使用。
---

# 天正电气产品知识库

完整的天正电气产品资料库，支持全系列产品查询。

## 产品系列

### 低压电器
- **万能式断路器** - TGW1N系列、TGWD系列
- **塑料外壳式断路器** - TGM1系列、TGM3系列
- **小型断路器** - TGB1N系列、TGB1系列
- **接触器** - TGC1系列、TGC2系列
- **继电器** - TGR1系列、TGR2系列
- **双电源** - TGQ1系列、TGQ2系列

### 配电电器
- **隔离开关** - TGH1系列
- **熔断器** - TGR1系列
- **电涌保护器** - TGDY系列

### 控制电器
- **按钮开关** - TGLA系列
- **指示灯** - TGLD系列
- **转换开关** - TGLW系列

## 知识库结构

```
references/
├── circuit-breakers/       # 断路器系列
│   ├── tgw1n.md           # TGW1N万能式断路器
│   ├── tgwd.md            # TGWD万能式断路器
│   ├── tgm1.md            # TGM1塑壳断路器
│   └── tgm3.md            # TGM3塑壳断路器
├── contactors/            # 接触器系列
├── relays/                # 继电器系列
├── dual-power/            # 双电源系列
├── technical-specs/       # 技术规格
└── price-lists/           # 价格信息
```

## 使用方式

根据用户查询的产品系列，加载对应的参考文件：
- 万能式断路器 → 读取 `references/circuit-breakers/` 下对应文件
- 接触器 → 读取 `references/contactors/` 下对应文件
- 技术参数 → 读取 `references/technical-specs/` 下对应文件

## 数据来源

- 天正电气官网：www.tengen.com.cn
- EAP3系统：eap3.tengen.com.cn
- 产品样本和技术手册
