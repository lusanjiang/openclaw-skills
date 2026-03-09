#!/usr/bin/env python3
"""
EAP3 纯 API 审批研究脚本
分析表单提交机制
"""

import requests
import re
import json
from datetime import datetime

EAP3_URL = 'https://eap3.tengen.com.cn'
USER_ID = 'lusanjiang'
ENCRYPTED_PWD = '345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39'

def main():
    # 登录
    url = f'{EAP3_URL}/r/w'
    post_data = {
        'userid': USER_ID,
        'pwd': ENCRYPTED_PWD,
        'cmd': 'com.actionsoft.apps.tengen.login',
        'rememberMeUid': '',
        'rememberMePwd': '',
        'sid': '',
        'token': '',
        'deviceType': 'pc',
        'ssoId': '',
        'phone': '',
        '_CACHE_LOGIN_TIME_': str(int(datetime.now().timestamp() * 1000)),
        'redirect_url': 'null',
        'lang': 'cn',
        'pwdEncode': 'RSA',
        'timeZone': '8'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest'
    }

    session = requests.Session()
    resp = session.post(url, data=post_data, headers=headers, timeout=30)
    data = resp.json()
    sid = data['data']['sid']
    print(f'✓ 登录成功')

    # 获取通知
    params = {'sid': sid, 'cmd': 'com.actionsoft.apps.notification_load_unread_msg'}
    resp2 = session.post(f'{EAP3_URL}/r/jd', params=params, headers=headers, timeout=30)
    data2 = resp2.json()

    # 获取第一个待办
    for item in data2.get('data', {}).get('list', []):
        content = item.get('content', '')
        if 'XZ38' in content and '定制' in content:
            task_inst_id = item.get('sourceId', '')
            process_inst_id = item.get('notifyContent', {}).get('processInstId', '')
            
            print(f'\n申请人: {item.get("userName", "")}')
            print(f'taskInstId: {task_inst_id}')
            
            # 获取表单页面
            form_params = {
                'sid': sid,
                'cmd': 'CLIENT_BPM_FORM_MAIN_PAGE_OPEN',
                'processInstId': process_inst_id,
                'taskInstId': task_inst_id,
                'openState': '1'
            }
            resp3 = session.get(f'{EAP3_URL}/r/w', params=form_params, headers=headers, timeout=30)
            html = resp3.text
            
            # 查找JavaScript中的提交函数
            submit_funcs = re.findall(r'function\s+(\w+[Ss]ubmit\w*)\s*\(', html)
            print(f'\n提交函数: {submit_funcs[:5]}')
            
            # 查找ajax调用
            ajax_pattern = r'\.ajax\s*\(\s*\{[^}]*url\s*:\s*["\']([^"\']+)["\']'
            ajax_calls = re.findall(ajax_pattern, html, re.DOTALL)
            print(f'Ajax URL: {ajax_calls[:3]}')
            
            # 查找form提交目标
            form_targets = re.findall(r'action\s*=\s*["\']([^"\']*)["\']', html)
            print(f'Form targets: {list(set(form_targets))[:3]}')
            
            # 查找隐藏字段
            hidden_pattern = r'<input[^>]*type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']'
            hidden_fields = re.findall(hidden_pattern, html)
            print(f'\n隐藏字段: {hidden_fields[:5]}')
            
            # 查找可能的审批结果字段
            result_pattern = r'(auditResult|result|NEED_RESULT|DISTRIBUTE_TYPE)'
            result_fields = re.findall(result_pattern, html)
            print(f'\n审批相关字段: {list(set(result_fields))}')
            
            break

if __name__ == '__main__':
    main()
