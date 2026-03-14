#!/usr/bin/env pwsh
# 推送到 GitHub 和 Gitee

param(
    [string]$Message = ""
)

# 使用默认提交信息
if ([string]::IsNullOrWhiteSpace($Message)) {
    $Message = "Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Push to GitHub & Gitee" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 添加所有变更
git add .

# 提交
git commit -m "$Message"
if ($LASTEXITCODE -ne 0) {
    Write-Host "No changes to commit or commit failed" -ForegroundColor Yellow
}

# 推送到 GitHub
Write-Host ""
Write-Host "[1/2] Pushing to GitHub..." -ForegroundColor Yellow
cmd /c "git push origin master 2>&1"
if ($LASTEXITCODE -eq 0) {
    Write-Host "GitHub OK" -ForegroundColor Green
} else {
    Write-Host "GitHub failed" -ForegroundColor Red
}

# 推送到 Gitee
Write-Host ""
Write-Host "[2/2] Pushing to Gitee..." -ForegroundColor Yellow
cmd /c "git push gitee master 2>&1"
if ($LASTEXITCODE -eq 0) {
    Write-Host "Gitee OK" -ForegroundColor Green
} else {
    Write-Host "Gitee failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Done!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
