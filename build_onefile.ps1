$ErrorActionPreference = "Stop"

$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $AppDir ".venv\Scripts\python.exe"
$AppName = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("5YWJ5LyP6Lef6Liq5pSv5p625Zyw6ISa6J665qCT6K6h566X56iL5bqP"))
$AppVersion = "1.1.0"
$ReleaseExeName = "$($AppName)_v$AppVersion.exe"
$ReleaseAssetName = "solar-tracker-anchor-bolt-calculator_v$AppVersion.exe"

if (!(Test-Path $Python)) {
    throw "Local virtual environment was not found. Create .venv and install PyInstaller, python-docx, and Pillow first."
}

$PythonRoot = (& $Python -c "import sys; print(sys.base_prefix)").Trim()
$PythonDllDir = Join-Path $PythonRoot "DLLs"
$TkinterPyd = Join-Path $PythonDllDir "_tkinter.pyd"
$TclDll = Join-Path $PythonDllDir "tcl86t.dll"
$TkDll = Join-Path $PythonDllDir "tk86t.dll"
foreach ($PathToCheck in @($TkinterPyd, $TclDll, $TkDll)) {
    if (!(Test-Path $PathToCheck)) {
        throw "Required Tcl/Tk runtime file was not found: $PathToCheck"
    }
}

Push-Location $AppDir
try {
    & $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --windowed `
        --name $AppName `
        --icon "assets\anchor_plate.ico" `
        --version-file "version_info.txt" `
        --add-data "assets;assets" `
        --add-data "tkinter\*.py;tkinter" `
        --add-data "runtime_tcl\tcl8.6;_tcl_data" `
        --add-data "runtime_tcl\tk8.6;_tk_data" `
        --additional-hooks-dir "packaging_hooks" `
        --add-binary "$TkinterPyd;." `
        --add-binary "$TclDll;." `
        --add-binary "$TkDll;." `
        --hidden-import "_tkinter" `
        --hidden-import "PIL._tkinter_finder" `
        app.py

    $BuiltExe = Join-Path $AppDir "dist\$AppName.exe"
    $ReleaseExe = Join-Path $AppDir "dist\$ReleaseExeName"
    $ReleaseAssetExe = Join-Path $AppDir "dist\$ReleaseAssetName"
    if (Test-Path $BuiltExe) {
        Copy-Item -LiteralPath $BuiltExe -Destination $ReleaseExe -Force
        Write-Host "Release executable copied to $ReleaseExe"
        Copy-Item -LiteralPath $BuiltExe -Destination $ReleaseAssetExe -Force
        Write-Host "GitHub release asset copied to $ReleaseAssetExe"
        Remove-Item -LiteralPath $BuiltExe -Force
        Write-Host "Unversioned build executable removed from dist."
    }
}
finally {
    Pop-Location
}
