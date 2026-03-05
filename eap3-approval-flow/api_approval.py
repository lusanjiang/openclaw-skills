#!/usr/bin/env python3
"""
EAP3 纯 API 审批 - 模拟页面加载分析
不启动浏览器，直接请求页面并解析
"""

import requests
import re
import json
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
            print(f'processInstId: {process_inst_id}')
            
            # 获取表单页面 HTML
            print('\n获取表单页面...')
            form_params = {
                'sid': sid,
                'cmd': 'CLIENT_BPM_FORM_MAIN_PAGE_OPEN',
                'processInstId': process_inst_id,
                'taskInstId': task_inst_id,
                'openState': '1'
            }
            resp3 = session.get(f'{EAP3_URL}/r/w', params=form_params, timeout=30)
            html = resp3.text
            
            # 解析 HTML 提取关键信息
            print('\n解析表单数据...')
            
            # 提取单据编号
            doc_no = re.search(r'单据编号\s*XZ38-(\d+)', html)
            if doc_no:
                print(f'单据编号: XZ38-{doc_no.group(1)}')
            
            # 提取申请人
            applicant = re.search(r'申请人员\s*([^<]+)', html)
            if applicant:
                print(f'申请人员: {applicant.group(1).strip()}')
            
            # 提取客户名称
            customer = re.search(r'客户名称\s*([^<]+)', html)
            if customer:
                print(f'客户名称: {customer.group(1).strip()}')
            
            # 提取物料信息
            materials = re.findall(r'TGM\w+[^<]+', html)
            if materials:
                print(f'物料信息: {materials[:2]}')
            
            # 查找审批按钮相关的 JavaScript
            print('\n查找审批操作...')
            
            # 查找是否有接收办理按钮
            if 'BTN_RECEIVE_TRANSACT' in html or '接收办理' in html:
                print('✓ 需要接收办理')
                
                # 尝试调用接收办理接口
                receive_data = {
                    'sid': sid,
                    'cmd': 'CLIENT_BPM_TASK_RECEIVE',
                    'processInstId': process_inst_id,
                    'taskInstId': task_inst_id
                }
                
                print('\n尝试接收办理...')
                resp_receive = session.post(f'{EAP3_URL}/r/jd', data=receive_data, timeout=30)
                print(f'状态: {resp_receive.status_code}')
                
                if 'json' in resp_receive.headers.get('Content-Type', ''):
                    try:
                        result = resp_receive.json()
                        print(f'响应: {result}')
                    except:
                        print(f'响应: {resp_receive.text[:200]}')
            
            # 查找是否有办理/提交按钮
            if 'BTN_TRANSACT' in html or '办理' in html:
                print('✓ 可以办理/提交')
                
                # 尝试直接提交
                submit_data = {
                    'sid': sid,
                    'cmd': 'CLIENT_BPM_FORM_SUBMIT',
                    'processInstId': process_inst_id,
                    'taskInstId': task_inst_id,
                    'buttonId': 'BTN_TRANSACT',
                    'NEED_RESULT': '已核实请后台支持',
                    'DISTRIBUTE_TYPE': '已核实请后台支持',
                    'formData': json.dumps({
                        'NEED_RESULT': '已核实请后台支持',
                        'DISTRIBUTE_TYPE': '已核实请后台支持'
                    })
                }
                
                print('\n尝试提交审批...')
                resp_submit = session.post(f'{EAP3_URL}/r/jd', data=submit_data, timeout=30)
                print(f'状态: {resp_submit.status_code}')
                
                if 'json' in resp_submit.headers.get('Content-Type', ''):
                    try:
                        result = resp_submit.json()
                        print(f'响应: {result}')
                        
                        if result.get('result') == 'ok':
                            print('\n✅ 审批成功!')
                        else:
                            print(f'\n❌ 审批失败: {result.get("msg", "未知错误")}')
                    except:
                        print(f'响应: {resp_submit.text[:200]}')
                else:
                    print(f'返回HTML: {resp_submit.text[:200]}')
            
            break

if __name__ == '__main__':
    main()
