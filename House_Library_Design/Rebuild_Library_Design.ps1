param([Parameter(Mandatory=$true)][string]$BlenderPath,[switch]$Render)
& $BlenderPath -b --disable-autoexec --python-exit-code 1 --python (Join-Path $PSScriptRoot 'scripts/build_library_design.py')
if ($LASTEXITCODE -ne 0) {throw 'Build failed'}
& $BlenderPath -b --disable-autoexec --python-exit-code 1 --python (Join-Path $PSScriptRoot 'scripts/verify_library.py')
if ($LASTEXITCODE -ne 0) {throw 'Verification failed'}
if ($Render) {& $BlenderPath -b --disable-autoexec --python-exit-code 1 --python (Join-Path $PSScriptRoot 'scripts/render_library.py')}
