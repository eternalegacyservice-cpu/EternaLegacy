
<#
  Secure Git Setup Launcher (PowerShell)
  Usage: run in the project root (e.g., EternaLegacy)
#>
$ErrorActionPreference = "Stop"
Write-Host ""
Write-Host "🔒 Secure Git Setup (PowerShell launcher)"

# Ensure Git Bash-like environment for .sh
if (!(Test-Path ".\setup_secure_git.sh")) {
  Write-Error "setup_secure_git.sh not found in current directory."
}

# Use bash if available (Git for Windows includes it)
$bash = "$Env:ProgramFiles\Git\bin\bash.exe"
if (-not (Test-Path $bash)) {
  $bash = "bash"
}

Write-Host "▶ Running setup_secure_git.sh via bash..."
& $bash "./setup_secure_git.sh"
