#!/usr/bin/env pwsh
# -*- coding: utf-8 -*-
<#
.SYNOPSIS
    zzgz-autoto-core Git Upload Script

.DESCRIPTION
    Auto execute git add, commit and push
    Usage:
        .\git_push.ps1                    # Use default commit message
        .\git_push.ps1 "your message"     # Use custom commit message

.NOTES
    Author: Auto-generated
    Date: 2026-03-09
#>

param(
    [string]$Message = ""
)

# Set error preference
$ErrorActionPreference = "Stop"

# Color definitions
$ColorSuccess = "Green"
$ColorInfo = "Cyan"
$ColorWarning = "Yellow"
$ColorError = "Red"

Write-Host "========================================" -ForegroundColor $ColorInfo
Write-Host "  zzgz-autoto-core Git Upload Script" -ForegroundColor $ColorInfo
Write-Host "========================================" -ForegroundColor $ColorInfo
Write-Host ""

# Check correct directory
$repoPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoPath

Write-Host "Work Dir: $repoPath" -ForegroundColor $ColorInfo

# Check git repo
if (-not (Test-Path ".git")) {
    Write-Host "Error: Not a Git repository" -ForegroundColor $ColorError
    exit 1
}

# Show current status
Write-Host ""
Write-Host "Git Status:" -ForegroundColor $ColorInfo
Write-Host "----------------------------------------"
git status
Write-Host "----------------------------------------"
Write-Host ""

# Check for changes
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "No changes to commit" -ForegroundColor $ColorSuccess
    exit 0
}

# Use default message if not provided
if ([string]::IsNullOrWhiteSpace($Message)) {
    $Message = "Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Host "Using default message: $Message" -ForegroundColor $ColorWarning
}

# Execute git add
Write-Host ""
Write-Host "Execute: git add ." -ForegroundColor $ColorInfo
git add . 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "git add failed (exit code: $LASTEXITCODE)" -ForegroundColor $ColorError
    exit 1
}
Write-Host "git add OK" -ForegroundColor $ColorSuccess

# Execute git commit
Write-Host ""
Write-Host "Execute: git commit -m '$Message'" -ForegroundColor $ColorInfo
git commit -m "$Message" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "git commit failed (exit code: $LASTEXITCODE)" -ForegroundColor $ColorError
    exit 1
}
Write-Host "git commit OK" -ForegroundColor $ColorSuccess

# Execute git push
Write-Host ""
Write-Host "Execute: git push" -ForegroundColor $ColorInfo
git push 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "git push failed (exit code: $LASTEXITCODE)" -ForegroundColor $ColorError
    exit 1
}
Write-Host "git push OK" -ForegroundColor $ColorSuccess

Write-Host ""
Write-Host "========================================" -ForegroundColor $ColorSuccess
Write-Host "  Upload Success!" -ForegroundColor $ColorSuccess
Write-Host "========================================" -ForegroundColor $ColorSuccess
