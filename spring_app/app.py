"""
app.py  -  Spring Generator local web app
Run:  python3 app.py
Open: http://localhost:5000
"""

import os
import sys
import uuid
import socket
import threading
import tempfile
import webbrowser
from flask import Flask, request, send_file, jsonify, render_template

from spring_gen import generate_spring_stl

# When bundled by PyInstaller, data files live in sys._MEIPASS; otherwise
# they are alongside this script.
if getattr(sys, "frozen", False):
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=os.path.join(_base, "templates"))
TMP = tempfile.gettempdir()


def _free_port():
    """Return an available TCP port on localhost."""
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)

    try:
        coils       = float(data.get("coils",       15))
        thickness   = float(data.get("thickness",   1.7))
        width       = float(data.get("width",        2.0))
        pitch       = float(data.get("pitch",        4.0))
        inside_dia  = float(data.get("inside_dia",   6.0))
        chamfer     = float(data.get("chamfer",      0.5))
        support_gap = float(data.get("support_gap",  0.25))
        fmt         = data.get("format", "stl").lower()
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid parameter: {e}"}), 400

    # Sanity clamp
    coils       = max(1,   min(coils,       50))
    thickness   = max(0.2, min(thickness,   20))
    width       = max(0.2, min(width,       20))
    pitch       = max(0.5, min(pitch,       50))
    inside_dia  = max(1,   min(inside_dia,  200))
    chamfer     = max(0,   min(chamfer,     min(thickness, width) / 2))
    support_gap = max(0,   min(support_gap, 5))

    fname = f"spring_{uuid.uuid4().hex[:8]}.stl"
    out_path = os.path.join(TMP, fname)

    try:
        generate_spring_stl(
            coils=coils,
            thickness=thickness,
            width=width,
            pitch=pitch,
            inside_dia=inside_dia,
            chamfer=chamfer,
            n_per_coil=72,
            closed_ends=True,
            support_gap=support_gap,
            output_path=out_path,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    dl_name = f"spring_c{coils}_id{inside_dia}_p{pitch}.stl"
    return send_file(
        out_path,
        as_attachment=True,
        download_name=dl_name,
        mimetype="application/octet-stream",
    )


if __name__ == "__main__":
    port = _free_port()
    url  = f"http://localhost:{port}"
    print(f"Spring Generator running at {url}")
    print("Press Ctrl+C to stop.")
    # Auto-open the browser when running as a bundled executable
    if getattr(sys, "frozen", False):
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    app.run(debug=False, port=port)
