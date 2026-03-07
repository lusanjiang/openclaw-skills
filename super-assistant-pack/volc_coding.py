#!/usr/bin/env python3
"""
火山Coding服务调用脚本
用于代码生成、代码审查、技术问答
"""

import requests
import json
import sys

class VolcengineCoding:
    """火山Coding大模型服务"""
    
    def __init__(self):
        self.api_key = self._load_key()
        self.base_url = "https://ark.cn-beijing.volces.com/api/coding/v3"
        self.model = "ark-code-latest"  # 火山Coding模型
    
    def _load_key(self):
        try:
            with open('/root/.openclaw/.ark_api_key', 'r') as f:
                return f.read().strip()
        except:
            return None
    
    def chat(self, prompt, temperature=0.7, max_tokens=4096):
        """
        调用火山Coding进行对话
        
        Args:
            prompt: 提示词/问题
            temperature: 创造性 (0-1)
            max_tokens: 最大输出长度
        """
        
        if not self.api_key:
            return {"success": False, "error": "API Key未配置"}
        
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个专业的编程助手，擅长代码生成、代码审查和技术问答。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            data = resp.json()
            
            if resp.status_code == 200:
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {
                    "success": True,
                    "content": content,
                    "model": self.model
                }
            else:
                return {
                    "success": False,
                    "error": data.get("error", {}).get("message", f"HTTP {resp.status_code}")
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_code(self, description, language="python"):
        """生成代码"""
        prompt = f"请用{language}编写以下功能的代码：\n\n{description}\n\n要求：\n1. 代码简洁高效\n2. 添加必要注释\n3. 包含错误处理"
        return self.chat(prompt, temperature=0.3)
    
    def review_code(self, code, language="python"):
        """代码审查"""
        prompt = f"请审查以下{language}代码，指出问题并给出改进建议：\n\n```\n{code}\n```"
        return self.chat(prompt, temperature=0.2)


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python3 volc_coding.py '你的问题'")
        print("示例: python3 volc_coding.py '写一个Python快速排序'")
        return
    
    prompt = ' '.join(sys.argv[1:])
    
    print("🌋 火山Coding服务")
    print("=" * 50)
    print(f"问题: {prompt}")
    print()
    
    coding = VolcengineCoding()
    result = coding.chat(prompt)
    
    if result["success"]:
        print(result["content"])
    else:
        print(f"❌ 错误: {result['error']}")


if __name__ == "__main__":
    main()
