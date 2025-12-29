# Checks if has admin permission 
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    $arguments = "& '" + $myinvocation.mycommand.definition + "'"
    Start-Process powershell -Verb runAs -ArgumentList $arguments
    break
}

# Gets path
$RepoPath = $PSScriptRoot

# Checks if is already in path to avoid duplicates
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($CurrentPath -notlike "*$RepoPath\interp*") {
    $NewPath = "$CurrentPath;$RepoPath\interp"
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    Write-Host "Your User PATH has been configured." -ForegroundColor Green
    Write-Host "Restart the terminal to use the command 'dr'." -ForegroundColor Yellow
} else {
    Write-Host "dr already in PATH." -ForegroundColor Cyan
}

pause