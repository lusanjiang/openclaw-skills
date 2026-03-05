#!/usr/bin/env python3
"""
天正EAP3自动登录 Skill
使用 #eap 标签调用
"""

from playwright.sync_api import sync_playwright
import time
import sys


def eap3_login():
    """
    登录天正EAP3系统
    
    Returns:
        登录成功后的页面信息
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("🔐 正在登录天正EAP3...")
        
        # 打开登录页面
        page.goto('https://eap3.tengen.com.cn/', timeout=30000)
        time.sleep(2)
        
        # 输入账号密码
        page.fill('input[name=userid]', 'lusanjiang')
        page.fill('input[name=pwd]', 'Lsj123456')
        
        # 调用登录函数
        page.evaluate('() => { loginAccount(); }')
        time.sleep(3)
        
        # 检查登录结果
        current_url = page.url
        title = page.title()
        
        if 'login' not in current_url.lower():
            print("✅ 登录成功！")
            print(f"\n📍 当前页面: {current_url}")
            print(f"📋 页面标题: {title}")
            
            # 截图
            page.screenshot(path='/tmp/eap3_current.png')
            print("📸 截图已保存: /tmp/eap3_current.png")
            
            # 尝试提取用户信息
            try:
                user_info = page.inner_text('.user-info, .user-name, [class*=user]')
                if user_info:
                    print(f"👤 用户信息: {user_info}")
            except:
                pass
            
            browser.close()
            return {
                'success': True,
                'url': current_url,
                'title': title,
                'screenshot': '/tmp/eap3_current.png'
            }
        else:
            print("❌ 登录失败")
            browser.close()
            return {
                'success': False,
                'error': '登录失败，仍在登录页面'
            }


def eap3_check_todo():
    """
    查看待办任务
    
    Returns:
        待办任务列表
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("🔐 登录EAP3并查看待办...")
        
        # 登录
        page.goto('https://eap3.tengen.com.cn/', timeout=30000)
        time.sleep(2)
        page.fill('input[name=userid]', 'lusanjiang')
        page.fill('input[name=pwd]', 'Lsj123456')
        page.evaluate('() => { loginAccount(); }')
        time.sleep(3)
        
        # 截图
        page.screenshot(path='/tmp/eap3_todo.png')
        
        print("\n📸 待办任务截图已保存")
        
        browser.close()
        return {
            'success': True,
            'screenshot': '/tmp/eap3_todo.png'
        }


if __name__ == "__main__":
    # 默认执行登录
    result = eap3_login()
    
    if result['success']:
        print("\n✅ EAP3登录完成")
    else:
        print("\n❌ 登录失败")
        sys.exit(1)
