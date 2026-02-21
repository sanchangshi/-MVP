# -*- coding: utf-8 -*-
"""
华为云 FunctionGraph 代码包构建脚本（精简版）
运行此脚本生成可上传到华为云的代码包
"""
import os
import subprocess
import shutil
import zipfile

def build_deployment_package():
    """
    构建华为云函数部署包（精简版）
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
        'requirements.txt'
    ]
    
    for f in files_to_copy:
        src = os.path.join(current_dir, f)
        if os.path.exists(src):
            shutil.copy(src, build_dir)
            print(f"复制: {f}")
    
    # 复制 huawei_handler.py 并重命名为 index.py（华为云HTTP函数要求）
    src_handler = os.path.join(current_dir, 'huawei_handler.py')
    dst_index = os.path.join(build_dir, 'index.py')
    if os.path.exists(src_handler):
        shutil.copy(src_handler, dst_index)
        print("复制: huawei_handler.py -> index.py")
    
    # 复制 bootstrap 文件（华为云HTTP函数要求）
    src_bootstrap = os.path.join(current_dir, 'bootstrap')
    if os.path.exists(src_bootstrap):
        shutil.copy(src_bootstrap, build_dir)
        print("复制: bootstrap")
    
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
        '--quiet',
        '--no-deps'  # 先安装主包
    ], check=False)
    
    # 再安装所有依赖
    subprocess.run([
        'pip', 'install',
        '-r', requirements_file,
        '-t', build_dir,
        '--quiet'
    ], check=True)
    
    # 排除的目录和文件模式（减小包大小）
    exclude_patterns = [
        'tests',
        'test',
        'testing',
        'examples',
        'example',
        'docs',
        'doc',
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '*.dist-info',
        '*.egg-info',
        '*.data',
        'bin',
        'mypy',
        'py.typed',
        'LICENSE',
        'COPYING',
        'README',
        'CHANGELOG',
        'AUTHORS',
        'Makefile',
    ]
    
    # 清理不必要的文件
    print("\n清理不必要的文件...")
    for root, dirs, files in os.walk(build_dir, topdown=False):
        # 删除匹配的目录
        for d in dirs:
            for pattern in exclude_patterns:
                if pattern in d.lower():
                    dir_path = os.path.join(root, d)
                    if os.path.exists(dir_path):
                        shutil.rmtree(dir_path, ignore_errors=True)
                        break
        
        # 删除匹配的文件
        for f in files:
            for pattern in exclude_patterns:
                if pattern.replace('*', '') in f.lower():
                    file_path = os.path.join(root, f)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    break
    
    # 创建 zip 包
    print("\n创建部署包...")
    output_zip = os.path.join(current_dir, 'deployment_package.zip')
    if os.path.exists(output_zip):
        os.remove(output_zip)
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(build_dir):
            # 跳过测试目录
            dirs[:] = [d for d in dirs if d not in ['tests', 'test', '__pycache__', 'examples', 'docs']]
            
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, build_dir)
                zipf.write(file_path, arcname)
    
    # 清理临时目录
    shutil.rmtree(build_dir)
    
    # 显示结果
    package_size = os.path.getsize(output_zip) / 1024 / 1024
    print(f"\n[OK] 部署包创建成功!")
    print(f"文件: {output_zip}")
    print(f"大小: {package_size:.2f} MB")
    
    if package_size > 40:
        print("\n[警告] 包大小超过40MB，建议使用OBS上传")
    else:
        print("\n可以直接上传到华为云 FunctionGraph")


if __name__ == '__main__':
    build_deployment_package()