
# ⚙️ VPTK — Wave Gear with Rolling Elements Calculator

**Compact-size design calculator for wave gears with intermediate rolling elements (ВПТК / BWG). Enter any two parameters — get the full geometry, torques and a ready-to-use DXF.**


[![Python](https://img.shields.io/badge/python-3.14-%233776AB?logo=python)](https://www.python.org/)
[![NiceGUI](https://img.shields.io/badge/NiceGUI-local%20web%20UI-5898D4)](https://nicegui.io/)
[![NumPy](https://img.shields.io/badge/NumPy-013243?logo=numpy)](https://numpy.org/)
[![SciPy](https://img.shields.io/badge/SciPy-8CAAE6?logo=scipy&logoColor=white)](https://scipy.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-11557c)](https://matplotlib.org/)
[![ezdxf](https://img.shields.io/badge/DXF-ezdxf-orange)](https://ezdxf.mozman.at/)
[![Windows](https://img.shields.io/badge/Windows-exe%20build-0078D6?logo=windows)](#-quick-start)
[![License](https://img.shields.io/badge/license-GNU-yellow)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](#-contributing)
[![Donate XMR](https://img.shields.io/badge/Donate-Monero%20(XMR)-FF6600?logo=monero&logoColor=white)](#-support-the-project)

---

**English** • [Русский](README.ru.md)

[Features](#-features) • [Why this one](#-why-this-project) • [Quick Start](#-quick-start) • [Usage](#-usage) • [Methodology](#-methodology) • [DXF export](#-dxf-export) • [Architecture](#-architecture) • [Contributing](#-contributing) • [Support](#️-support-the-project)

---

## 🚀 Features

| Capability | Description |
| --- | --- |
| **Any-two-of-four input** | Fill exactly two of: gear ratio `q`, outer diameter `D`, output torque `M_out`, input torque `M_in` — the rest is solved automatically |
| **Load-based sizing** | Rolling-element diameter `d_RE` is derived from the torque, shear strength of the cage `[τ]`, row non-uniformity `k_N` and contact type |
| **Balls / Rollers** | Rollers carry 2× the torque of balls at the same diameter (≈ 21 % smaller diameter for the same torque) |
| **GOST rounding** | Rounds `d_RE` **up** to the nearest standard size (balls — GOST 3722, rollers — GOST 22696) and recomputes everything |
| **Efficiency-aware** | `M_in = M_out / (q·η)`, default `η = 0.85`, editable, with reference values in a tooltip |
| **Live geometry plot** | Rigid-wheel profile, cage, eccentric, rolling elements and outline — each toggled independently |
| **DXF export (mm)** | Correct `$INSUNITS = 4`, so the drawing opens at real size in any CAD |
| **PNG export** | One-click plot export |
| **Calculation log** | Every run is logged; export as TXT / JSON / CSV |
| **RU / EN interface** | Switch language on the fly, entered values are kept |
| **Design sanity check** | Warns when the outer radius is below the minimum allowed by the geometry |
| **Fully offline** | Local server bound to `127.0.0.1` only — nothing leaves your machine |
| **Standalone `.exe`** | Built by GitHub Actions, no Python needed on the user's PC |

### Project Boundaries

- ✅ Sizing and geometry of a single-row, single-wave ВПТК (`n = 1`, `u = 1`)
- ✅ Based on a published methodology (Podshibnev, 2022)
- ❌ Not a FEM / contact-stress solver — it gives a design starting point, not a certification

---

## 🆚 Why this project

The idea of a geometry calculator for ball wave gears was inspired by
[TrashRobotics/BallsWaveGearingGenerator](https://codeberg.org/TrashRobotics/BallsWaveGearingGenerator)
([YouTube channel](https://www.youtube.com/@trashrobotics)). Related community projects exist as well:
[Jkl88/BallsWaveGearingGenerator](https://github.com/Jkl88/BallsWaveGearingGenerator) (a PyQt6 front-end built on top of the TrashRobotics script that generates a profile DXF) and
[hadzaki/wave-gear](https://github.com/hadzaki/wave-gear) (a tkinter profile visualiser with self-intersection detection).

Those tools work from **geometry** — you already have to know the ball size, eccentricity and number of cavities. VPTK goes one step earlier: **you start from the requirements** (ratio, envelope, torque) and get the geometry out.

| | **VPTK (this project)** | hadzaki/wave-gear |
| --- | --- | --- |
| Input | Any 2 of `q`, `D`, `M_out`, `M_in` | Generator Ø, ball Ø, eccentricity, cavities, points |
| Sizing from load (torque → `d_RE`) | ✅ | ❌ (stress calc listed as planned) |
| Material strength `[τ]`, `k_N`, `η` | ✅ | ❌ (efficiency listed as planned) |
| Balls **and** rollers | ✅ | not mentioned |
| GOST standard-size rounding | ✅ (up, then full recalculation) | ❌ |
| Output `D`, `L`, `W`, `z_sh`, `z_g`, `M_in` | ✅ | profile only |
| Plot layers | profile, cage, eccentric, elements, outline | profile + zoom |
| Self-intersection check | ⚠ outer-radius warning only | ✅ |
| DXF | `ezdxf`, units explicitly **mm**, all elements | `dxfwrite` |
| UI | NiceGUI (local web), **RU / EN** | tkinter |
| Calculation log (TXT/JSON/CSV) | ✅ | ❌ |
| Distribution | CI-built `.exe` artifact | `.exe` committed to the repo |
| Source of formulas | Podshibnev 2022, referenced per formula | generic |


**In short:** if you already know your profile and want to inspect it for defects — use the visualisers above. If you need to *choose* the gear — what ball diameter, what outer diameter, what torque it holds — use VPTK.

---

## ⚡ Quick Start

### Option A: Windows `.exe` (no Python needed)

1. Open **Actions → Build Windows EXE** (or **Releases**) and download the `VPTK-windows` artifact.
2. Run `GeometryCalculationVPTK-v<version>-<sha>.exe`.
3. A console window opens (it shows the log and keeps the server alive) and your default browser opens the interface.

> 💡 Close the program with the **Exit** button in the UI or by closing the console window / `Ctrl+C`. Closing only the browser tab does **not** stop the server.

### Option B: From source

Requires **Python 3.14+** and [Poetry](https://python-poetry.org/).

```bash
git clone https://github.com/<your-username>/vptk.git
cd vptk
poetry install --no-root
poetry run python main.py
```

The app picks the first free port starting from `8000` and opens `http://127.0.0.1:<port>` automatically.

### Option C: Build the `.exe` yourself

```bash
poetry install --no-root --with dev
poetry run nicegui-pack --onefile --name GeometryCalculationVPTK main.py
```

`nicegui-pack` is a PyInstaller wrapper that bundles NiceGUI's static files — without it the packaged app answers *Internal Server Error*. `--windowed` is intentionally **not** used: the console shows the log.

If something goes wrong in a frozen build, the app prints its environment (Python, library versions, presence of NiceGUI templates) and writes errors to the console (or to `vptk.log` when no console is available).

---

## 🖥️ Usage

1. **Fill exactly two** of the four fields: `q`, `D`, `M_out`, `M_in`.

   | Pair | Result |
   | --- | --- |
   | `q` + `M_out` | `d_RE`, `D`, `L`, `W` |
   | `q` + `D` | `M_out` |
   | `D` + `M_out` | `q` (solved numerically on `q ∈ [4.1; 100]`) |
   | `q` + `M_in` | `M_out` through `η` |
   | `M_in` + `M_out` | `q` from the torque ratio; **`q` is rounded to an integer** and `M_in` is recomputed (the deviation is shown) |

2. Choose **Balls** or **Rollers**, tick **Round to GOST** if needed.
3. Adjust `τ`, `k_N`, `η` (or keep defaults: `150 MPa`, `0.56`, `0.85`).
4. Pick which elements to draw and press **Save DXF** / **Save PNG**.
5. Save the calculation log as TXT / JSON / CSV if you need a record.

### Inputs

| Parameter | Symbol | Default | Meaning |
| --- | --- | --- | --- |
| Shear stress of the cage | `[τ]` | 150 MPa | Higher `[τ]` → smaller rolling element, higher ratio. Tooltip lists typical steels |
| Non-uniformity in a row | `k_N` | 0.56 | Depends on `q`: 0.50…0.56 for `q = 10…30` (Podshibnev, Table 1.1); 0.6 is suggested for rough engineering estimates |
| Efficiency | `η` | 0.85 | Experimental maximum 0.92, calculated 0.95 (Stepanov 2009); typical 0.80…0.90. Real `η` falls at low torque (see note below) |
| Rolling-element type | `k` | roller | Ball `k = 1`, roller `k = 2` |
| GOST rounding | — | on | Always rounds **up** to keep strength margin |

### Simplifications

- **One row** (`n = 1`, `k_H = 1`) and **one wave** (`u = 1`) are fixed in this version — the simplest and most common configuration. The formulas themselves support `n > 1`.
- Stepanov (2009) shows the smallest outer diameter at moderate ratios; Podshibnev cites `q ≈ 8…15` for minimum `D`. Torque ripple decreases as `q` grows, so very low ratios are not always the best choice.
- Efficiency is a constant. Stepanov's measurements give `η(M) = 0.92·(1 − e^(−0.57·M))` (`M` in N·m), i.e. `η ≈ 0.92` from roughly 10–20 N·m upwards but much lower at small torque — treat results for tiny torques with care.

---

## 📐 Methodology

Formulas follow V. A. Podshibnev, *"Methodology of designing an actuator based on a wave gear with rolling elements with a given vibration-acceleration level"* (2022).

Material coefficient (eq. 3.14, values for steels — Table 3.3):

$$k_M = \frac{33.8\cdot 10^{3}}{[\tau]}$$

Rolling-element diameter (Podshibnev, eq. 3.15):

$$d_{RE} = \sqrt[3]{\frac{k_M \cdot M_{out} \cdot \sin\!\big(\pi/(q-1)\big)}{k_N \cdot k \cdot k_H \cdot n \cdot (q-1)}}$$

Overall dimensions (eq. 3.16–3.18):

$$D = \left(\frac{2.06}{\sin(\pi/q)} + 1.8\right) d_{RE},\qquad L = (1.2\,n + 1.8)\,d_{RE},\qquad W = \frac{\pi}{4}D^{2}L$$

Torques and counts:

$$M_{in} = \frac{M_{out}}{q\,\eta},\qquad z_{sh} = \lfloor q \rfloor,\qquad z_g = z_{sh} + 1$$

Minimum outer radius of the rigid wheel (used for the warning):

$$R_{out,min} = \frac{1.03\, d_{RE}}{\sin(\pi/z_g)} + 0.4\, d_{RE}$$

The `R_out,min` condition keeps the chord of a cavity at least `2.06·d_RE`; if it is violated the rigid-wheel profile gets cusps ("whiskers") that cannot be machined, and some elements lose contact (Stepanov 2009, p. 9).

Profile construction uses eccentricity `e = 0.2·d_RE`, cage thickness `h_c = 2.2·e` and generator radius `r_d = R_out − 2e − d_RE`.

### GOST rounding

1. Compute the exact `d_RE`.
2. Find the nearest **larger** size in the standard series (balls — GOST 3722, rollers — GOST 22696).
3. Recalculate `D`, `L`, `W`, `M_out`, `M_in` for the rounded size.

Rounding down would make the element smaller than required; rounding up keeps a strength margin. If `d_RE` exceeds the largest standard size, a clear error is shown.

### Balls vs rollers

| | Balls (`k = 1`) | Rollers (`k = 2`) |
| --- | --- | --- |
| Contact | Point | Line |
| Torque at same `d_RE` | Base | **2× more** |
| `d_RE` at same torque | Base | **≈ 21 % smaller** |
| Wear | Higher (spalling) | Lower |
| Recommendation | Light-duty | **Power drives** |

Sources: Stepanov 2009 (abstract, pp. 10–11: `k_p = 2` for rollers of length `l = d`); Podshibnev 2022, eq. 3.15.

---

## 📤 DXF export

The file is saved in **millimetres** (`doc.units = MM`, `$INSUNITS = 4`). Many generators omit the units, so CAD systems may read the numbers as metres or inches — this one does not.

| Layer content | DXF entity |
| --- | --- |
| Rigid-wheel profile | `LWPOLYLINE` |
| Cage (outer and inner) | 2 × `CIRCLE` |
| Eccentric | `CIRCLE` + `POINT` + axis line |
| Rolling elements | `CIRCLE` per element |
| Outline (overall Ø) | `CIRCLE` |

Which entities are exported is controlled by the same checkboxes as the plot.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│  main.py   — entry point: free port, logging, ui.run()   │
└───────────────┬──────────────────────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────┐
│  ui.py + local.py  — NiceGUI interface, RU/EN strings    │
│  (no formulas inside)                                    │
└───────────────┬──────────────────────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────┐
│  core/                                                   │
│   solver.py   — picks the solving mode, returns result   │
│   formula.py  — pure formulas (no UI, no state)          │
│   constans.py — GOST series, material hints              │
│   geometry.py — profile / cage / eccentric / elements    │
│   export.py   — DXF (ezdxf, mm)                          │
│   logger.py   — in-memory log, TXT / JSON / CSV          │
└──────────────────────────────────────────────────────────┘
```

### Tech Stack

| Category | Technologies |
| --- | --- |
| **Language** | Python 3.14 |
| **UI** | NiceGUI (FastAPI + Uvicorn under the hood) |
| **Math** | NumPy, SciPy (root finding) |
| **Plots** | Matplotlib |
| **CAD export** | ezdxf |
| **Packaging** | Poetry, `nicegui-pack` (PyInstaller) |
| **CI** | GitHub Actions (`windows-latest`) |

### Repository Structure

```
vptk/
├── .github/workflows/build-exe.yml   # Windows .exe build, versioned artifact
├── core/
│   ├── __init__.py
│   ├── solver.py
│   ├── formula.py
│   ├── constans.py
│   ├── geometry.py
│   ├── export.py
│   └── logger.py
├── literature/                       # source PDFs
├── local.py                          # RU / EN strings
├── main.py
├── ui.py
├── pyproject.toml
├── README.md                         # English (default)
├── README.ru.md                      # Русская версия
└── LICENSE
```

---

## 🤝 Contributing

Issues and PRs are welcome.

```bash
poetry install --no-root --with dev
poetry run python main.py
```

**Adding a language:** copy the `"en"` block in `local.py`, translate the values (keep the keys and `{placeholders}`), add the code to `LANGUAGES`.



---

## ❤️ Support the Project

VPTK is free and open source. If it saved you time, you can support development with Monero:

**XMR:** `<86CuofuVXfoUBb6tHufqHXZG4fbniEhmMUumNfBst2f7S2vpQrVJ69Bd7LqiLqDWz2VZ1Gxj2ePa2355Gc68CyZd7jXpjpS>`

<sub>Monero keeps donations private — no need to leave a name. Stars and bug reports help just as much ⭐</sub>

---
## 🙏 Acknowledgments
 
- [TrashRobotics](https://www.youtube.com/@trashrobotics) — the original idea and calculator that inspired this project
- V. A. Podshibnev — dissertation (2022), the basis of all sizing formulas
- V. S. Stepanov — thesis abstract (2009): original `d_RE`, `D`, `L` relations, GOST 3722-81 size series, efficiency measurements
---


## 📜 License

[GNU GPLv3](LICENSE) — feel free to use, modify, and distribute.

---

**Built with ❤️ for engineers who need a gear, not just a profile.**