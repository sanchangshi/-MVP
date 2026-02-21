# -*- coding: utf-8 -*-
"""
华为云 FunctionGraph 代码包构建脚本
运行此脚本生成可上传到华为云的代码包
"""
import os
import subprocess
import shutil
import zipfile

def build_deployment_package():
    """
    构建华为云函数部署包
    """
    # 获取当前目录
    current_dir = os.path.dirname(os.path.realpath(__file__))
    
    # 创建临时目录
    build_dir = os.path.join(current_dir, 'build')
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    
    # 复制代码文件
    files_to_copy = [
        'app.py',
        'backtest.py',
        'data_fetcher.py',
        'huawei_handler.py',
        'requirements.txt'
    ]
    
    for f in files_to_copy:
        src = os.path.join(current_dir, f)
        if os.path.exists(src):
            shutil.copy(src, build_dir)
            print(f"复制: {f}")
    
    # 复制策略模块
    strategies_src = os.path.join(current_dir, 'strategies')
    strategies_dst = os.path.join(build_dir, 'strategies')
    if os.path.exists(strategies_src):
        shutil.copytree(strategies_src, strategies_dst)
        print("复制: strategies/")
    
    # 安装依赖到构建目录
    print("\n安装依赖...")
    requirements_file = os.path.join(current_dir, 'requirements.txt')
    
    # 使用 pip 安装依赖到 build 目录
    subprocess.run([
        'pip', 'install',
        '-r', requirements_file,
        '-t', build_dir,
        '--quiet'
    ], check=True)
    
    # 创建 zip 包
    print("\n创建部署包...")
    output_zip = os.path.join(current_dir, 'deployment_package.zip')
    if os.path.exists(output_zip):
        os.remove(output_zip)
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, build_dir)
                zipf.write(file_path, arcname)
    
    # 清理临时目录
    shutil.rmtree(build_dir)
    
    # 显示结果
    package_size = os.path.getsize(output_zip) / 1024 / 1024
    print(f"\n✅ 部署包创建成功!")
    print(f"📦 文件: {output_zip}")
    print(f"📊 大小: {package_size:.2f} MB")
    print("\n请将此文件上传到华为云 FunctionGraph")


if __name__ == '__main__':
    build_deployment_package()