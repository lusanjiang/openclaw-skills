#!/usr/bin/env python3
"""
即梦AI (Jimeng) 图片生成接口
支持通过浏览器自动化调用即梦AI进行图片生成
"""

import asyncio
import json
import os
import sys
from typing import Optional

# 即梦AI配置
JIMENG_CONFIG = {
    "url": "https://jimeng.jianying.com",
    "login_url": "https://jimeng.jianying.com/ai-tool/home",
    "model": "jimeng-4.0",  # 即梦4.0模型
}

class JimengAI:
    """即梦AI图片生成器"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or os.getenv("JIMENG_SESSION_ID")
        self.api_endpoint = "https://jimeng.duckcloud.fun/v1/images/generations"  # 社区API
        
    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        negative_prompt: str = "",
        sample_strength: float = 0.5
    ) -> dict:
        """
        生成图片
        
        Args:
            prompt: 提示词
            width: 宽度 (512-2048)
            height: 高度 (512-2048)
            negative_prompt: 负面提示词
            sample_strength: 采样强度 (0-1)
        
        Returns:
            dict: 包含图片URL或base64的结果
        """
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.session_id}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "jimeng-4.0",
            "prompt": prompt,
            "negativePrompt": negative_prompt,
            "width": width,
            "height": height,
            "sample_strength": sample_strength
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "image_url": data.get("data", [{}])[0].get("url"),
                            "prompt": prompt,
                            "width": width,
                            "height": height
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"API错误: {response.status}",
                            "detail": error_text
                        }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_image_sync(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        negative_prompt: str = "",
        sample_strength: float = 0.5
    ) -> dict:
        """同步版本的图片生成"""
        return asyncio.run(self.generate_image(
            prompt, width, height, negative_prompt, sample_strength
        ))


def generate_product_image(
    product: str,
    style: str = "简约",
    background: str = "白色",
    width: int = 1024,
    height: int = 1024
) -> dict:
    """
    生成电商产品图
    
    Args:
        product: 产品名称，如"蓝牙耳机"
        style: 风格，如"简约"/"高端"/"科技感"
        background: 背景，如"白色"/"纯色"/"渐变"
        width: 图片宽度
        height: 图片高度
    
    Returns:
        dict: 生成结果
    """
    # 构建专业电商提示词
    prompt = build_ecommerce_prompt(product, style, background)
    
    # 检查是否配置了即梦AI
    session_id = os.getenv("JIMENG_SESSION_ID")
    
    if not session_id:
        return {
            "success": False,
            "error": "未配置即梦AI Session ID",
            "setup_guide": get_setup_guide()
        }
    
    jimeng = JimengAI(session_id)
    return jimeng.generate_image_sync(prompt, width, height)


def build_ecommerce_prompt(product: str, style: str, background: str) -> str:
    """构建电商产品提示词"""
    
    base_prompt = f"{background}背景，{product}，"
    
    style_keywords = {
        "简约": "极简设计，干净线条，专业产品摄影，柔和光线",
        "高端": "奢华质感，金属光泽，高端产品摄影，精致细节",
        "科技感": "未来科技，发光元素，科技蓝，数字感",
        "温馨": "暖色调，家居场景，生活化，温馨氛围",
        "活力": "鲜艳色彩，动感角度，年轻时尚，活力四射"
    }
    
    common_suffix = "，电商主图风格，专业商业摄影，超高清细节，8K分辨率，完美光影"
    
    style_desc = style_keywords.get(style, style_keywords["简约"])
    
    return base_prompt + style_desc + common_suffix


def get_setup_guide() -> str:
    """获取配置指南"""
    return """
【即梦AI配置指南】

1. 访问即梦AI官网
   https://jimeng.jianying.com

2. 使用抖音账号登录

3. 获取Session ID
   - 登录后按F12打开开发者工具
   - 切换到Application/应用标签
   - 找到Cookies → jimeng.jianying.com
   - 复制 sessionid 的值

4. 配置环境变量
   export JIMENG_SESSION_ID="你的sessionid"

5. 开始使用
   python3 jimeng_ai.py "白色背景 蓝牙耳机"

【免费额度】
- 新用户注册送积分
- 每日登录送积分
- 积分可用于图片生成
"""


# 电商专用快捷函数
def generate_white_background_image(product: str, style: str = "简约") -> dict:
    """生成白底产品图（电商主图专用）"""
    return generate_product_image(
        product=product,
        style=style,
        background="纯白色",
        width=800,
        height=800
    )


def generate_banner_image(product: str, scene: str = "科技感") -> dict:
    """生成Banner图（详情页首图）"""
    prompt = f"{scene}风格电商Banner，{product}，渐变背景，大标题区域，促销氛围，高清"
    
    session_id = os.getenv("JIMENG_SESSION_ID")
    if not session_id:
        return {
            "success": False,
            "error": "未配置即梦AI Session ID",
            "setup_guide": get_setup_guide()
        }
    
    jimeng = JimengAI(session_id)
    return jimeng.generate_image_sync(prompt, 1200, 600)


def main():
    """命令行入口"""
    if len(sys.argv) > 1:
        product = ' '.join(sys.argv[1:])
    else:
        product = input("请输入产品名称: ")
    
    print(f"🎨 正在生成产品图: {product}")
    print("=" * 50)
    
    result = generate_white_background_image(product)
    
    if result["success"]:
        print("✅ 图片生成成功!")
        print(f"📷 图片URL: {result.get('image_url', 'N/A')}")
        print(f"📐 尺寸: {result['width']}x{result['height']}")
    else:
        print(f"❌ 生成失败: {result.get('error', '未知错误')}")
        print("\n" + result.get('setup_guide', ''))


if __name__ == "__main__":
    main()
