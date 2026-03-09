#!/usr/bin/env pwsh
# -*- coding: utf-8 -*-
<#
.SYNOPSIS
    zzgz-autoto-core Git 上传脚本

.DESCRIPTION
    自动执行 git add、commit 和 push 操作
    使用方法:
        .\git_push.ps1                    # 使用默认提交信息
        .\git_push.ps1 "你的提交信息"      # 使用自定义提交信息

.NOTES
    作者: Auto-generated
    日期: 2026-03-09
#>

param(
    [string]$Message = ""
)

# 设置错误操作偏好
$ErrorActionPreference = "Stop"

# 颜色定义
$ColorSuccess = "Green"
$ColorInfo = "Cyan"
$ColorWarning = "Yellow"
$ColorError = "Red"

Write-Host "========================================" -ForegroundColor $ColorInfo
Write-Host "  zzgz-autoto-core Git 上传脚本" -ForegroundColor $ColorInfo
Write-Host "========================================" -ForegroundColor $ColorInfo
Write-Host ""

# 检查是否在正确的目录
$repoPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoPath

Write-Host "📁 工作目录: $repoPath" -ForegroundColor $ColorInfo

# 检查 git 仓库
if (-not (Test-Path ".git")) {
    Write-Host "❌ 错误: 当前目录不是 Git 仓库" -ForegroundColor $ColorError
    exit 1
}

# 显示当前状态
Write-Host ""
Write-Host "📋 当前 Git 状态:" -ForegroundColor $ColorInfo
Write-Host "----------------------------------------"
git status
Write-Host "----------------------------------------"
Write-Host ""

# 检查是否有变更
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "✅ 没有需要提交的变更" -ForegroundColor $ColorSuccess
    exit 0
}

# 如果没有提交信息，使用默认信息
if ([string]::IsNullOrWhiteSpace($Message)) {
    $Message = "Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Host "使用默认提交信息: $Message" -ForegroundColor $ColorWarning
}

# 执行 git add
Write-Host ""
Write-Host "📝 执行: git add ." -ForegroundColor $ColorInfo
git add . 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ git add 失败 (exit code: $LASTEXITCODE)" -ForegroundColor $ColorError
    exit 1
}
Write-Host "✅ git add 完成" -ForegroundColor $ColorSuccess

# 执行 git commit
Write-Host ""
Write-Host "📝 执行: git commit -m '$Message'" -ForegroundColor $ColorInfo
git commit -m "$Message" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ git commit 失败 (exit code: $LASTEXITCODE)" -ForegroundColor $ColorError
    exit 1
}
Write-Host "✅ git commit 完成" -ForegroundColor $ColorSuccess

# 执行 git push
Write-Host ""
Write-Host "📝 执行: git push" -ForegroundColor $ColorInfo
git push 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ git push 失败 (exit code: $LASTEXITCODE)" -ForegroundColor $ColorError
    exit 1
}
Write-Host "✅ git push 完成" -ForegroundColor $ColorSuccess

Write-Host ""
Write-Host "========================================" -ForegroundColor $ColorSuccess
Write-Host "  ✅ 上传成功!" -ForegroundColor $ColorSuccess
Write-Host "========================================" -ForegroundColor $ColorSuccess
