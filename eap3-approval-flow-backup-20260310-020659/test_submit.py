#!/usr/bin/env python3
"""
EAP3 纯 API 审批 - 尝试模拟表单提交
"""

import requests
import re
from datetime import datetime

EAP3_URL = 'https://eap3.tengen.com.cn'
USER_ID = 'lusanjiang'
ENCRYPTED_PWD = '345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39'

def main():
    session = requests.Session()
    
    # 登录
    print('登录中...')
    resp = session.post(f'{EAP3_URL}/r/w', data={
        'userid': USER_ID, 'pwd': ENCRYPTED_PWD, 'cmd': 'com.actionsoft.apps.tengen.login',
        'deviceType': 'pc', 'lang': 'cn', 'pwdEncode': 'RSA', 'timeZone': '8',
        '_CACHE_LOGIN_TIME_': str(int(datetime.now().timestamp() * 1000))
    }, headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=30)
    sid = resp.json()['data']['sid']
    print(f'✓ 登录成功')
    
    # 获取通知
    resp2 = session.post(f'{EAP3_URL}/r/jd', params={'sid': sid, 'cmd': 'com.actionsoft.apps.notification_load_unread_msg'}, timeout=30)
    data2 = resp2.json()
    
    # 获取第一个待办
    for item in data2.get('data', {}).get('list', []):
        content = item.get('content', '')
        if 'XZ38' in content and '定制' in content:
            task_inst_id = item.get('sourceId', '')
            process_inst_id = item.get('notifyContent', {}).get('processInstId', '')
            user_name = item.get('userName', '')
            
            print(f'\n申请人: {user_name}')
            print(f'taskInstId: {task_inst_id}')
            
            # 尝试直接调用 /r/jd 接口提交
            # 参考 VBA 代码中的格式
            submit_data = {
                'sid': sid,
                'cmd': 'CLIENT_BPM_FORM_SUBMIT',
                'processInstId': process_inst_id,
                'taskInstId': task_inst_id,
                'buttonId': 'BTN_TRANSACT',
                'NEED_RESULT': '已核实请后台支持',
                'DISTRIBUTE_TYPE': '已核实请后台支持'
            }
            
            print(f'\n尝试提交审批...')
            resp_submit = session.post(f'{EAP3_URL}/r/jd', data=submit_data, timeout=30)
            print(f'状态码: {resp_submit.status_code}')
            print(f'Content-Type: {resp_submit.headers.get("Content-Type", "")}')
            
            # 检查是否是 JSON 响应
            try:
                result = resp_submit.json()
                print(f'响应: {result}')
            except:
                print(f'响应(前200字): {resp_submit.text[:200]}')
            
            break

if __name__ == '__main__':
    main()
