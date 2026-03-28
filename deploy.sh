#!/bin/bash

# Agentic AI Risk Auditor 部署脚本
# 用于推送到 GitHub 和设置项目

set -e  # 遇到错误时退出

echo "🚀 Agentic AI Risk Auditor 部署脚本"
echo "======================================"

# 检查是否在项目目录中
if [ ! -f "README.md" ] || [ ! -f "requirements.txt" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 检查 Git
if ! command -v git &> /dev/null; then
    echo "❌ 错误: Git 未安装"
    exit 1
fi

# 显示项目信息
echo "📁 项目目录: $(pwd)"
echo "📊 项目大小: $(du -sh . | cut -f1)"
echo "📝 文件数量: $(find . -type f -name "*.py" | wc -l) 个 Python 文件"

# 检查 Git 状态
echo ""
echo "🔍 检查 Git 状态..."
if [ ! -d ".git" ]; then
    echo "❌ 错误: 这不是一个 Git 仓库"
    exit 1
fi

git status

# 询问是否推送到 GitHub
echo ""
read -p "📤 是否推送到 GitHub? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 检查远程仓库
    if git remote | grep -q "origin"; then
        echo "✅ 远程仓库已配置"
        REMOTE_URL=$(git remote get-url origin)
        echo "   URL: $REMOTE_URL"
        
        # 尝试推送
        echo ""
        echo "📤 推送到 GitHub..."
        if git push -u origin main; then
            echo "✅ 推送成功!"
        else
            echo "❌ 推送失败"
            echo ""
            echo "请手动执行:"
            echo "  git push -u origin main"
        fi
    else
        echo "❌ 未配置远程仓库"
        echo ""
        echo "请先执行以下步骤:"
        echo "1. 在 GitHub 创建仓库: https://github.com/new"
        echo "2. 仓库名: agentic-ai-risk-auditor"
        echo "3. 不要初始化 README、.gitignore 或 license"
        echo "4. 创建后运行:"
        echo "   git remote add origin https://github.com/CathySong/agentic-ai-risk-auditor.git"
        echo "   git push -u origin main"
    fi
fi

# 显示项目设置说明
echo ""
echo "📋 项目设置说明"
echo "================"
echo ""
echo "1. 安装依赖:"
echo "   pip install -r requirements.txt"
echo ""
echo "2. 配置环境变量:"
echo "   cp .env.example .env"
echo "   # 编辑 .env 文件添加 API 密钥"
echo ""
echo "3. 运行 Streamlit 应用:"
echo "   streamlit run ui/streamlit_app.py"
echo ""
echo "4. 运行 FastAPI 服务器:"
echo "   uvicorn app.main:app --reload"
echo ""
echo "5. Docker 部署:"
echo "   docker-compose up -d"
echo ""
echo "🔗 项目链接:"
echo "   GitHub: https://github.com/CathySong/agentic-ai-risk-auditor"
echo "   Streamlit: http://localhost:8501"
echo "   FastAPI: http://localhost:8000"
echo ""
echo "🎉 部署完成!"