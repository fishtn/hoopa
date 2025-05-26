#!/bin/bash

# 自动化发布脚本
set -e

echo "🚀 开始发布流程..."

# 1. 检查工作目录是否干净
# if [[ -n $(git status --porcelain) ]]; then
#     echo "❌ 工作目录不干净，请先提交所有更改"
#     exit 1
# fi

# 2. 运行测试
# echo "🧪 运行测试..."
# pytest

# 3. 代码格式化和检查
# echo "🔍 代码格式化和检查..."
# black hoopa/
# isort hoopa/
# flake8 hoopa/

# 4. 清理之前的构建
echo "🧹 清理构建目录..."
rm -rf build/ dist/ *.egg-info/

# 5. 构建包
echo "📦 构建包..."
python -m build

# 6. 检查包
echo "✅ 检查包..."
twine check dist/*

# 7. 询问是否发布
read -p "是否发布到 PyPI? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 发布到 PyPI..."
    twine upload dist/*
    echo "✅ 发布完成！"
else
    echo "❌ 取消发布"
fi
