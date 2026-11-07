param([string]$PythonPath, [string]$OutputPath)
$ErrorActionPreference = 'Stop'
if (-not $PythonPath) {
    if (Get-Command python -ErrorAction SilentlyContinue) { $PythonPath = (Get-Command python).Source }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonPath = (Get-Command py).Source }
    else { throw 'Install Python 3 or pass -PythonPath. See README.md.' }
}
$buildArguments = @((Join-Path $PSScriptRoot 'automation/build_viewer.py'))
if ($OutputPath) { $buildArguments += @('--output', $OutputPath) }
& $PythonPath @buildArguments
if ($LASTEXITCODE -ne 0) { throw 'Viewer build failed; the existing output was not replaced.' }
