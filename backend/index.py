"""
Flask 应用入口 - Fly.io 部署
"""
import os
from app import app

if __name__ == '__main__':
    # Fly.io 使用 PORT 环境变量，默认 8080
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)