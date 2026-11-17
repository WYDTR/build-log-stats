# 上传到新 GitHub 仓库

当前目录已经是独立 Git 仓库，包含实际开发的多个提交与实验标签。
请通过 Git 推送现有历史，使 C0/C1 的完整 SHA 可以在服务器复现。

## 1. 创建空仓库

在你的 GitHub 账号下创建空仓库，建议名称 `build-log-stats`。
创建页面的 README、gitignore 和 license 选项保持未选，使用本地已有历史作为初始内容。
本工具的本地开发不依赖提前创建远端。

## 2. 从本地 PowerShell 推送

下面每一行分别执行。若远端仓库名称不同，替换 origin 地址。

```powershell
Set-Location -LiteralPath 'D:\study\Devops\project\devops\build-log-stats'
git remote add origin https://github.com/WYDTR/build-log-stats.git
git push -u origin main
git push origin --tags
```

首次推送可能要求你通过自己的 GitHub 登录方式完成认证。
GitHub Actions 会构建主分支、运行测试，并重新检查记录的基础版本、实验目标和修复结果。

## 3. 检查历史

```powershell
git log --oneline --decorate -5
git tag
git status --short
```

`e12-base` 指向实际基础实现，`e12-target` 指向功能扩展和明确注入漏依赖的实验版本，
`e12-fixed` 指向修复与回归验证版本。当前 main 保持修复后的状态。
完整提交号见 `integration/commits.json`。

之后按 [E12 接入说明](INTEGRATION.md) 在服务器将新仓库作为被测输入克隆。
