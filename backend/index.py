"""
阿里云函数计算入口 - Custom Runtime 模式
"""
import os
from app import app

# 初始化函数（可选）
def initializer(context):
    """
    函数初始化，在实例启动时执行一次
    """
    print("Function initialized")

# 事件处理函数（用于事件触发）
def handler(event, context):
    """
    阿里云函数计算入口函数（事件触发模式）
    """
    return {
        'statusCode': 200,
        'body': 'Use HTTP trigger for this API'
    }

# Custom Runtime 模式：直接运行 Flask
if __name__ == '__main__':
    # 阿里云 Custom Runtime 默认监听 9000 端口
    port = int(os.environ.get('FC_SERVER_PORT', 9000))
    print(f"Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
