$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$TargetDir = Join-Path $HOME ".local\bin"
$TargetPath = Join-Path $TargetDir "aniworld.cmd"

New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

$launcher = @"
@echo off
call "$RepoRoot\aniworld.cmd" %*
"@

Set-Content -Path $TargetPath -Value $launcher -Encoding ASCII

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (-not $userPath) {
    $userPath = ""
}

$pathParts = $userPath -split ";" | Where-Object { $_ -ne "" }
if ($pathParts -notcontains $TargetDir) {
    $newPath = if ($userPath.Trim()) { "$userPath;$TargetDir" } else { $TargetDir }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
}

if (($env:Path -split ";") -notcontains $TargetDir) {
    $env:Path = "$TargetDir;$env:Path"
}

Write-Host "Installed launcher:" $TargetPath
Write-Host "You can now use 'aniworld' in new terminals."
Write-Host "If the current terminal does not resolve it yet, open a new terminal and test with: aniworld --help"
