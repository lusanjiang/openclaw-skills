#!/usr/bin/env python3
"""
即梦AI图片生成 - 电商运营技能包
配置完成，等待API开通
"""

import os
import sys

# 当前状态
STATUS = {
    "api_key_configured": True,
    "service_ready": False,
    "waiting_for": "火山引擎控制台开通即梦AI服务"
}

# 提示词模板
PROMPT_TEMPLATES = {
    "蓝牙耳机_白底": "白色背景，无线蓝牙耳机，极简设计，银色金属质感，45度角展示，柔和自然光，细腻阴影，8K超高清，电商主图风格，专业商业摄影，纯净白色背景，产品居中构图，studio lighting，高端电子产品",
    "智能手表_白底": "白色背景，智能手表，极简设计，黑色表盘，金属表带，45度角展示，柔和自然光，8K超高清，电商主图风格，专业商业摄影，纯净白色背景，产品居中构图，科技感",
    "保温杯_白底": "白色背景，不锈钢保温杯，极简设计，金属质感，45度角展示，柔和自然光，8K超高清，电商主图风格，专业商业摄影，纯净白色背景，产品居中构图"
}

def get_prompt(product, style="白底"):
    """获取提示词"""
    key = f"{product}_{style}"
    return PROMPT_TEMPLATES.get(key, f"白色背景，{product}，极简设计，专业产品摄影，45度角展示，柔和自然光，8K超高清，电商主图风格")

def main():
    print("🎨 即梦AI图片生成 - 电商运营技能包")
    print("=" * 50)
    print()
    print("📋 当前状态:")
    print(f"  API密钥: {'✅ 已配置' if STATUS['api_key_configured'] else '❌ 未配置'}")
    print(f"  服务状态: {'✅ 已就绪' if STATUS['service_ready'] else '⏳ 等待开通'}")
    print()
    print("📝 立即可用的提示词:")
    print()
    for name, prompt in PROMPT_TEMPLATES.items():
        print(f"【{name}】")
        print(f"{prompt}")
        print()
    print("=" * 50)
    print()
    print("使用方式:")
    print("1. 访问 https://jimeng.jianying.com")
    print("2. 登录后点击「图片生成」")
    print("3. 复制上面的提示词粘贴")
    print("4. 选择 1:1 比例，点击生成")

if __name__ == "__main__":
    main()
