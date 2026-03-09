#!/usr/bin/env python3
"""
EAP3 纯 API 审批 - 尝试所有可能的提交接口
"""

import requests
from datetime import datetime

EAP3_URL = 'https://eap3.tengen.com.cn'
USER_ID = 'lusanjiang'
ENCRYPTED_PWD = '345f9bd110a90cba3aba5b913b5870e044a2e0e28d01a7c9dc6ba122abd6e6fa160f356800c908b76895a385e5ff8c03f5b3e5c39b797c2aba017449a406b3f7ae94832155f28f62118e58bab758d5dc546b71d757310e8a945056ed65e2c40493a450f186b70d9bda92495a0cdcc888bf2e87e22587ea59f29bcb30e22a3d39'

def main():
    session = requests.Session()
    
    # 登录
    resp = session.post(f'{EAP3_URL}/r/w', data={
        'userid': USER_ID, 'pwd': ENCRYPTED_PWD, 'cmd': 'com.actionsoft.apps.tengen.login',
        'deviceType': 'pc', 'lang': 'cn', 'pwdEncode': 'RSA', 'timeZone': '8',
        '_CACHE_LOGIN_TIME_': str(int(datetime.now().timestamp() * 1000))
    }, headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=30)
    sid = resp.json()['data']['sid']
    
    # 获取通知
    resp2 = session.post(f'{EAP3_URL}/r/jd', params={'sid': sid, 'cmd': 'com.actionsoft.apps.notification_load_unread_msg'}, timeout=30)
    data2 = resp2.json()
    
    # 获取第一个待办
    for item in data2.get('data', {}).get('list', []):
        content = item.get('content', '')
        if 'XZ38' in content and '定制' in content:
            task_inst_id = item.get('sourceId', '')
            process_inst_id = item.get('notifyContent', {}).get('processInstId', '')
            
            print(f'申请人: {item.get("userName", "")}')
            print(f'taskInstId: {task_inst_id}')
            
            # 尝试所有可能的接口
            cmds = [
                'com.actionsoft.apps.workbench.task_transact',
                'com.actionsoft.apps.workbench.task_submit',
                'com.actionsoft.apps.workbench.task_complete',
                'CLIENT_BPM_TASK_TRANSACT',
                'CLIENT_BPM_TASK_SUBMIT',
                'CLIENT_BPM_TASK_COMPLETE',
                'CLIENT_BPM_FORM_SAVE_AND_SUBMIT',
                'CLIENT_BPM_FORM_COMPLETE',
            ]
            
            for cmd in cmds:
                submit_data = {
                    'sid': sid,
                    'cmd': cmd,
                    'processInstId': process_inst_id,
                    'taskInstId': task_inst_id,
                    'NEED_RESULT': '已核实请后台支持'
                }
                
                resp = session.post(f'{EAP3_URL}/r/jd', data=submit_data, timeout=10)
                
                if 'json' in resp.headers.get('Content-Type', ''):
                    try:
                        result = resp.json()
                        if result.get('result') == 'ok':
                            print(f'✓ {cmd}: 成功!')
                            print(f'  响应: {result}')
                            return
                        else:
                            print(f'✗ {cmd}: {result.get(\"msg\", \"错误\")[:50]}')
                    except:
                        print(f'? {cmd}: 无法解析响应')
                else:
                    print(f'- {cmd}: 返回HTML')
            
            break

if __name__ == '__main__':
    main()
