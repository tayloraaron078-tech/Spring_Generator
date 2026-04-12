# Spring Generator

Generate downloadable, parametric spring STL files for 3D printing using a local web app.

## Overview

This repository contains a lightweight Flask application that builds spring geometry directly in Python and exports binary STL files.

- No cloud dependency
- No CAD license requirement
- Fast parameter-driven spring generation

## Repository Layout

```text
.
├── README.md                 # Repository overview (this file)
└── spring_app/
    ├── README.md             # App-specific documentation
    ├── app.py                # Flask server
    ├── spring_gen.py         # Spring geometry and STL generation
    └── templates/index.html  # Browser UI
```

## Quick Start

1. Move into the app directory:
   ```bash
   cd spring_app
   ```
2. Install dependencies:
   ```bash
   pip install flask numpy
   ```
3. Start the web app:
   ```bash
   python3 app.py
   ```
4. Open `http://localhost:5000` in your browser.

For parameter details, usage notes, and troubleshooting, see `spring_app/README.md`.

## License

See `License` for licensing details.
