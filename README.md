# 光伏跟踪支架地脚螺栓计算程序

Windows desktop calculator for a four-anchor photovoltaic tracker support base plate, based on ACI 318-19 Chapter 17 and the internal force workflow from 《钢结构节点设计手册》（第四版）.

Current release: `v1.0.0`

## Download

For normal use, download the Windows executable from GitHub Releases:

https://github.com/Lumen-netizen/solar-tracker-anchor-bolt-calculator/releases

Release asset:

```text
solar-tracker-anchor-bolt-calculator_v1.0.0.exe
```

## Scope

- Standalone calculation engine; Excel is not required at runtime.
- Four cast-in J- or L-bolts.
- Chinese user interface with engineering symbols and units.
- ACI-style plan/elevation diagrams in the GUI.
- English Word calculation report export (`.docx`).

## Run From Source

```powershell
git clone https://github.com/Lumen-netizen/solar-tracker-anchor-bolt-calculator.git
cd solar-tracker-anchor-bolt-calculator
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python app.py
```

If `py` is not available, use `python` instead:

```powershell
python -m venv .venv
```

## Test

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
```

## Package

The final deliverable is a single-file Windows exe built with PyInstaller. The source includes a local `runtime_tcl` folder because the bundled Python environment needs explicit Tcl/Tk resources for Tkinter.

```powershell
powershell -ExecutionPolicy Bypass -File .\build_onefile.ps1
```

The packaged executable is written to:

```text
dist\光伏跟踪支架地脚螺栓计算程序.exe
```

The versioned release copy is written to:

```text
dist\光伏跟踪支架地脚螺栓计算程序_v1.0.0.exe
```

For GitHub Release assets, the uploaded file is renamed in English for compatibility:

```text
solar-tracker-anchor-bolt-calculator_v1.0.0.exe
```
