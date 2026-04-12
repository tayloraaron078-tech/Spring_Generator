"""
app.py  –  Spring Generator local web app
Run:  python3 app.py
Open: http://localhost:5000
"""

import os
import uuid
import tempfile
from flask import Flask, request, send_file, jsonify, render_template

from spring_gen import generate_spring_stl

app = Flask(__name__)
TMP = tempfile.gettempdir()


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
    print("Spring Generator running at http://localhost:5000")
    app.run(debug=False, port=5000)
