$ErrorActionPreference = "Stop"

$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $AppDir ".venv\Scripts\python.exe"
$AppName = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("5YWJ5LyP6Lef6Liq5pSv5p625Zyw6ISa6J665qCT6K6h566X56iL5bqP"))

if (!(Test-Path $Python)) {
    throw "Local virtual environment was not found. Create .venv and install PyInstaller, python-docx, and Pillow first."
}

Push-Location $AppDir
try {
    & $Python -m PyInstaller `
        --noconfirm `
        --onefile `
        --windowed `
        --name $AppName `
        --icon "assets\anchor_plate.ico" `
        --add-data "assets;assets" `
        --add-data "tkinter;tkinter" `
        --add-data "runtime_tcl;runtime_tcl" `
        --add-data "runtime_tcl\tcl8.6;_tcl_data" `
        --add-data "runtime_tcl\tk8.6;_tk_data" `
        --add-binary "C:\Users\cheny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\DLLs\_tkinter.pyd;." `
        --add-binary "C:\Users\cheny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\DLLs\tcl86t.dll;." `
        --add-binary "C:\Users\cheny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\DLLs\tk86t.dll;." `
        --hidden-import "_tkinter" `
        --hidden-import "PIL._tkinter_finder" `
        app.py
}
finally {
    Pop-Location
}
