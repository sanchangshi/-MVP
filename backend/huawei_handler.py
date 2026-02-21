# -*- coding: utf-8 -*-
"""
华为云 FunctionGraph HTTP函数入口
"""
import json
import os
import sys

# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.realpath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app import app

def handler(event, context):
    """
    华为云 FunctionGraph HTTP函数入口
    
    Args:
        event: HTTP 请求事件
        context: 函数上下文
    
    Returns:
        HTTP 响应
    """
    # 解析请求
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    headers = event.get('headers', {})
    query_string = event.get('queryStringParameters', {})
    body = event.get('body', '')
    
    # 构建 WSGI 环境
    environ = {
        'REQUEST_METHOD': http_method,
        'PATH_INFO': path,
        'QUERY_STRING': '&'.join([f'{k}={v}' for k, v in query_string.items()]) if query_string else '',
        'CONTENT_TYPE': headers.get('Content-Type', ''),
        'CONTENT_LENGTH': headers.get('Content-Length', str(len(body) if body else 0)),
        'wsgi.input': None,
        'wsgi.errors': sys.stderr,
        'wsgi.version': (1, 0),
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    # 添加 headers 到 environ
    for key, value in headers.items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            environ[f'HTTP_{key}'] = value
    
    # 处理请求体
    if body:
        from io import BytesIO
        if isinstance(body, str):
            body = body.encode('utf-8')
        environ['wsgi.input'] = BytesIO(body)
    else:
        from io import BytesIO
        environ['wsgi.input'] = BytesIO(b'')
    
    # 调用 Flask 应用
    response_started = False
    response_status = None
    response_headers = []
    response_body = []
    
    def start_response(status, headers):
        nonlocal response_started, response_status, response_headers
        response_status = status
        response_headers = headers
        response_started = True
        return lambda data: response_body.append(data)
    
    # 执行 WSGI 应用
    result = app(environ, start_response)
    for data in result:
        response_body.append(data)
    
    # 构建响应
    response = {
        'statusCode': int(response_status.split()[0]) if response_status else 200,
        'headers': dict(response_headers),
        'body': b''.join(response_body).decode('utf-8') if response_body else ''
    }
    
    return response


# 本地测试
if __name__ == '__main__':
    # 测试健康检查
    test_event = {
        'httpMethod': 'GET',
        'path': '/',
        'headers': {},
        'queryStringParameters': {},
        'body': ''
    }
    result = handler(test_event, None)
    print(f"Status: {result['statusCode']}")
    print(f"Body: {result['body']}")