$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = 'C:\Users\pawan\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$log = Join-Path $root 'data\raw\scin\download.log'
$err = Join-Path $root 'data\raw\scin\download.error.log'
Start-Process -FilePath $python -ArgumentList 'scripts\download_scin_images.py --workers 4' -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput $log -RedirectStandardError $err
Write-Output "SCIN downloader started in background. Log: $log; errors: $err"
