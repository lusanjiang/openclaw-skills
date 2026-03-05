#!/usr/bin/env python3
import requests
import re
from datetime import datetime

EAP3_URL = 'https://eap3.tengen.com.cn'
USER_ID = 'lusanjiang'
ENCRYPTED_PWD = '345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39'

session = requests.Session()
resp = session.post(f'{EAP3_URL}/r/w', data={
    'userid': USER_ID, 'pwd': ENCRYPTED_PWD, 'cmd': 'com.actionsoft.apps.tengen.login',
    'deviceType': 'pc', 'lang': 'cn', 'pwdEncode': 'RSA', 'timeZone': '8',
    '_CACHE_LOGIN_TIME_': str(int(datetime.now().timestamp() * 1000))
}, headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=30)
sid = resp.json()['data']['sid']

resp2 = session.post(f'{EAP3_URL}/r/jd', params={'sid': sid, 'cmd': 'com.actionsoft.apps.notification_load_unread_msg'}, timeout=30)
data2 = resp2.json()

for item in data2.get('data', {}).get('list', []):
    content = item.get('content', '')
    if 'XZ38' in content and '定制' in content:
        task_inst_id = item.get('sourceId', '')
        process_inst_id = item.get('notifyContent', {}).get('processInstId', '')
        
        print(f'申请人: {item.get("userName", "")}')
        
        resp3 = session.get(f'{EAP3_URL}/r/w', params={
            'sid': sid, 'cmd': 'CLIENT_BPM_FORM_MAIN_PAGE_OPEN',
            'processInstId': process_inst_id, 'taskInstId': task_inst_id, 'openState': '1'
        }, timeout=30)
        html = resp3.text
        
        # 查找所有script标签
        scripts = re.findall(r'<script[^>]*>([\s\S]*?)</script>', html)
        
        for i, script in enumerate(scripts[:10]):  # 只查前10个脚本
            if len(script) > 100 and ('submit' in script.lower() or 'transact' in script.lower()):
                # 查找URL模式
                urls = re.findall(r'url\s*[:=]\s*["\']([^"\']+)["\']', script)
                cmds = re.findall(r'cmd\s*[:=]\s*["\']([^"\']+)["\']', script)
                if urls or cmds:
                    print(f'\\nScript {i}:')
                    if urls: print(f'  URLs: {urls[:2]}')
                    if cmds: print(f'  CMDs: {cmds[:2]}')
        
        break
