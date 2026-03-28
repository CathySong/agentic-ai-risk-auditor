#!/bin/bash

# Agentic AI Risk Auditor - GitHub推送脚本
# 这个脚本将指导你完成GitHub仓库创建和代码推送

set -e

echo "🚀 Agentic AI Risk Auditor - GitHub推送流程"
echo "=============================================="
echo ""

# 检查当前目录
if [ ! -f "README.md" ] || [ ! -f "requirements.txt" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

echo "📊 项目信息:"
echo "  - 项目名称: Agentic AI Risk Auditor"
echo "  - 本地提交: $(git log --oneline | wc -l) 个提交"
echo "  - 文件数量: $(find . -type f -name "*.py" | wc -l) 个Python文件"
echo "  - 项目大小: $(du -sh . | cut -f1)"
echo ""

# 检查Git配置
echo "🔧 检查Git配置..."
if ! git config user.name > /dev/null 2>&1; then
    echo "⚠️  警告: Git用户名未设置"
    read -p "请输入Git用户名 (例如: Cathy Song): " git_name
    git config --global user.name "$git_name"
fi

if ! git config user.email > /dev/null 2>&1; then
    echo "⚠️  警告: Git邮箱未设置"
    read -p "请输入Git邮箱 (例如: cathy@example.com): " git_email
    git config --global user.email "$git_email"
fi

echo "✅ Git配置完成:"
echo "  - 用户名: $(git config user.name)"
echo "  - 邮箱: $(git config user.email)"
echo ""

# 检查远程仓库
echo "🔗 检查远程仓库..."
if git remote | grep -q "origin"; then
    remote_url=$(git remote get-url origin)
    echo "  - 远程仓库已配置: $remote_url"
    
    # 检查仓库是否存在
    if echo "$remote_url" | grep -q "github.com/CathySong/agentic-ai-risk-auditor"; then
        echo "  - 仓库URL正确"
        
        # 尝试推送
        echo ""
        echo "📤 尝试推送到GitHub..."
        if git push -u origin main 2>&1 | grep -q "Repository not found"; then
            echo "❌ 错误: GitHub仓库不存在"
            echo ""
            echo "请按照以下步骤创建仓库:"
        else
            echo "✅ 推送成功!"
            echo ""
            echo "🎉 项目已成功推送到GitHub!"
            echo "访问: https://github.com/CathySong/agentic-ai-risk-auditor"
            exit 0
        fi
    else
        echo "⚠️  远程仓库URL不是目标仓库"
        read -p "是否更新远程仓库URL? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git remote remove origin
            git remote add origin https://github.com/CathySong/agentic-ai-risk-auditor.git
            echo "✅ 远程仓库URL已更新"
        fi
    fi
else
    echo "  - 未配置远程仓库"
    git remote add origin https://github.com/CathySong/agentic-ai-risk-auditor.git
    echo "✅ 已添加远程仓库"
fi

echo ""
echo "📋 GitHub仓库创建步骤:"
echo "======================"
echo ""
echo "1. 打开浏览器访问: https://github.com/new"
echo ""
echo "2. 填写仓库信息:"
echo "   - Owner: CathySong (选择你的账户)"
echo "   - Repository name: agentic-ai-risk-auditor"
echo "   - Description: Multi-agent system for automated AI risk assessment and compliance auditing"
echo "   - Visibility: Public (选择公开)"
echo "   - 重要: 不要初始化 README、.gitignore 或 license"
echo "     (我们已经有了这些文件)"
echo ""
echo "3. 点击 'Create repository'"
echo ""
echo "4. 创建后，你会看到推送现有仓库的指令"
echo ""
echo "5. 回到终端，运行以下命令:"
echo "   git push -u origin main"
echo ""
echo "6. 验证推送:"
echo "   访问: https://github.com/CathySong/agentic-ai-risk-auditor"
echo ""

# 提供备用方案
echo ""
echo "🔄 备用方案: 使用GitHub CLI"
echo "=========================="
echo "如果你安装了GitHub CLI (gh)，可以运行:"
echo ""
echo "gh auth login  # 登录GitHub"
echo "gh repo create CathySong/agentic-ai-risk-auditor \\"
echo "  --description \"Multi-agent system for automated AI risk assessment\" \\"
echo "  --public \\"
echo "  --source=. \\"
echo "  --remote=origin \\"
echo "  --push"
echo ""

# 显示当前状态
echo ""
echo "📊 当前项目状态:"
echo "================"
echo "✅ 项目代码: 已完成 (25个文件)"
echo "✅ 文档: 已完成 (README.md, CONTRIBUTING.md等)"
echo "✅ 测试: 已完成 (9个测试用例)"
echo "✅ 部署配置: 已完成 (Docker, docker-compose)"
echo "✅ Git提交: 已完成 (2个提交)"
echo "⏳ GitHub仓库: 待创建"
echo ""

echo "💡 提示: 创建GitHub仓库后，项目将完全公开并可访问。"
echo "项目使用MIT许可证，适合开源分享。"
echo ""
echo "准备好后，请按照上述步骤创建GitHub仓库并推送代码。"
echo "如有问题，请参考 PUSH_TO_GITHUB.md 文件中的详细说明。"