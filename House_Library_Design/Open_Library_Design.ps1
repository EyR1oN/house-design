param([string]$BlenderPath)
if (-not $BlenderPath) {
 $candidate = Join-Path $PSScriptRoot '..\Tools\blender-4.5.3-windows-x64\blender.exe'
 if (Test-Path -LiteralPath $candidate) {$BlenderPath = (Resolve-Path -LiteralPath $candidate).Path}
 elseif ($env:BLENDER_EXE -and (Test-Path -LiteralPath $env:BLENDER_EXE)) {$BlenderPath = $env:BLENDER_EXE}
 else {
  $installed = Get-Command blender -ErrorAction SilentlyContinue
  if (-not $installed) {throw 'Blender not found. Install Blender 4.5.3 LTS, pass -BlenderPath, or set BLENDER_EXE.'}
  $BlenderPath = $installed.Source
 }
}
Start-Process -FilePath $BlenderPath -ArgumentList @('--disable-autoexec', ('"' + (Join-Path $PSScriptRoot 'House_Library_Design.blend') + '"'))
