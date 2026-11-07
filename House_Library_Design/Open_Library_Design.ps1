param([string]$BlenderPath)
if (-not $BlenderPath) {
 $candidate = Join-Path $PSScriptRoot '..\..\work\tools\blender-4.5.3-windows-x64\blender.exe'
 if (Test-Path -LiteralPath $candidate) {$BlenderPath = (Resolve-Path -LiteralPath $candidate).Path}
 else {$BlenderPath = (Get-Command blender -ErrorAction Stop).Source}
}
Start-Process -FilePath $BlenderPath -ArgumentList @('--disable-autoexec', ('"' + (Join-Path $PSScriptRoot 'House_Library_Design.blend') + '"'))
