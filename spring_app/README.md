# Spring Generator — Local Web App

A self-hosted replacement for MakerWorld's Parametric Model Maker spring tool.
No cloud, no credits, no Fusion 360 required.

## Requirements

- Python 3.8+
- `flask` and `numpy` (both standard / easy to install)

## Setup

```bash
# 1. Install dependencies (one time)
pip install flask numpy

# 2. Run the server
python3 app.py

# 3. Open your browser
#    http://localhost:5000
```

## Parameters

| Parameter      | Description                              |
|----------------|------------------------------------------|
| Coils          | Number of coils                          |
| Thickness (mm) | Wire cross-section height                |
| Width (mm)     | Wire cross-section width (radial)        |
| Pitch (mm)     | Axial distance per coil                  |
| Inside Dia (mm)| Inner diameter of the spring             |
| Chamfer (mm)   | Edge chamfer on the wire cross-section   |

Click **Generate & Download** to get your STL, ready to slice.

## Notes

- Output is a binary STL. Import into PrusaSlicer, Bambu Studio, Orca, etc.
- For 95A TPU springs: use 3-4 walls, 15% gyroid infill, slow speeds (~25 mm/s).
- The geometry engine is pure Python + numpy — no CAD kernel needed.
- Tested on Python 3.10/3.11. Should work on Windows, Mac, and Linux.

## File Structure

```
spring_app/
├── app.py          ← Flask server (run this)
├── spring_gen.py   ← Geometry engine
└── templates/
    └── index.html  ← Web UI
```
