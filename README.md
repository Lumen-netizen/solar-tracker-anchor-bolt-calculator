# 光伏跟踪支架地脚螺栓计算程序

Windows desktop calculator for a four-anchor photovoltaic tracker support base plate, based on the ACI 318-19 Chapter 17 workflow in the reference spreadsheet.

## Scope

- Standalone calculation engine; Excel is not required at runtime.
- Four cast-in J- or L-bolts.
- Chinese user interface with engineering symbols and units.
- ACI-style plan/elevation diagrams in the GUI.
- English Word calculation report export (`.docx`).

## Run From Source

```powershell
cd "D:\Users\cheny\Documents\Codex projects\Engineering\光伏跟踪支架地脚螺栓计算程序\anchor_bolt_app"
& "C:\Users\cheny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" app.py
```

## Test

```powershell
& "C:\Users\cheny\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s tests -v
```

## Package

The final deliverable is intended to be a single-file Windows exe built with PyInstaller. The source includes a local `runtime_tcl` folder because the bundled Python environment needs explicit Tcl/Tk resources for Tkinter.

```powershell
.\build_onefile.ps1
```

The packaged file is written to `dist\光伏跟踪支架地脚螺栓计算程序.exe`.
