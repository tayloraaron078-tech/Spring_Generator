"""
spring_gen.py
Generates a 3D-printable coil spring as a binary STL.

Parameters mirror the MakerWorld Parametric Model Maker:
  coils          – number of coils
  thickness      – wire cross-section height (mm)
  width          – wire cross-section width (mm)
  pitch          – axial distance per coil (mm)
  inside_dia     – inner diameter of the spring (mm)
  chamfer        – chamfer size on wire edges (mm)

The approach:
  1. Build a chamfered rectangular cross-section profile in 2-D.
  2. Sweep it along a helix path using Frenet-Serret frames.
  3. Cap both ends flat.
  4. Write binary STL.
"""

import math
import struct
import numpy as np


# ---------------------------------------------------------------------------
# Cross-section profile (chamfered rectangle, in local XY)
# ---------------------------------------------------------------------------

def chamfered_rect_profile(w, h, chamfer):
    """
    Returns an (N, 2) array of vertices for a chamfered rectangle.
    Centred at origin, width=w (X), height=h (Y).
    chamfer is clipped to half the shorter side.
    """
    c = min(chamfer, w / 2 - 0.01, h / 2 - 0.01)
    hw, hh = w / 2, h / 2
    pts = np.array([
        [-hw + c,  -hh     ],
        [ hw - c,  -hh     ],
        [ hw,      -hh + c ],
        [ hw,       hh - c ],
        [ hw - c,   hh     ],
        [-hw + c,   hh     ],
        [-hw,       hh - c ],
        [-hw,      -hh + c ],
    ])
    return pts


# ---------------------------------------------------------------------------
# Helix path + Frenet frames
# ---------------------------------------------------------------------------

def helix_frames(coils, pitch, radius, n_per_coil=64, closed_ends=True):
    """
    Returns positions (N,3) and rotation matrices (N,3,3) along the helix.
    radius = inside_dia/2 + width/2  (centreline radius)

    When closed_ends=True one extra coil is added at each end where the pitch
    smoothly ramps between 0 and the main pitch using a half-cosine curve.
    This makes the wire lie flat at both ends so the spring sits level and
    compresses evenly between parallel surfaces.

    Frame convention (analytical, exact for any pitch):
      T = (-R·sin θ, R·cos θ, h(θ)) / |...|
      N = (-cos θ, -sin θ, 0)          radially inward
      B = T × N
    """
    h_main = pitch / (2 * math.pi)   # rise per radian at full pitch
    two_pi = 2 * math.pi

    if closed_ends:
        # θ layout:
        #   [0,           2π]            bottom ramp   h: 0 → h_main
        #   [2π,          2π(1+coils)]   main coils    h: h_main (constant)
        #   [2π(1+coils), 2π(2+coils)]  top ramp      h: h_main → 0
        total_turns = coils + 2
        N = int(total_turns * n_per_coil)
        t = np.linspace(0, total_turns * two_pi, N, endpoint=True)

        main_start = two_pi
        main_end   = two_pi * (1 + coils)

        # Half-cosine pitch ramps (C1-smooth at both joints)
        # Bottom: h(θ) = h_main·(1 − cos(θ/2))/2  for θ∈[0, 2π]
        # Top:    h(θ) = h_main·(1 + cos(φ/2))/2  for φ=θ−main_end ∈[0, 2π]
        h_bot = h_main * (1 - np.cos(t / 2)) / 2
        h_top = h_main * (1 + np.cos((t - main_end) / 2)) / 2
        h_arr = np.where(t <= main_start, h_bot,
                np.where(t <= main_end,   h_main,
                                          h_top))

        # z by cumulative-trapezoid integration of h(θ)
        dt  = np.diff(t)
        z   = np.concatenate([[0.0], np.cumsum((h_arr[:-1] + h_arr[1:]) / 2 * dt)])
    else:
        total_turns = coils
        N = int(total_turns * n_per_coil)
        t = np.linspace(0, total_turns * two_pi, N, endpoint=True)
        h_arr = np.full(N, h_main)
        z = h_main * t

    x = radius * np.cos(t)
    y = radius * np.sin(t)
    pos = np.stack([x, y, z], axis=1)  # (N,3)

    # Analytical frame — N stays radially inward for any pitch
    denom  = np.sqrt(radius ** 2 + h_arr ** 2)
    tang   = np.stack(
        [-radius * np.sin(t), radius * np.cos(t), h_arr], axis=1
    ) / denom[:, None]
    norm   = np.stack([-np.cos(t), -np.sin(t), np.zeros(N)], axis=1)
    binorm = np.cross(tang, norm)  # unit length (T⊥N, both unit)

    R = np.stack([norm, binorm, tang], axis=2)  # (N,3,3)
    return pos, R


# ---------------------------------------------------------------------------
# Sweep & mesh
# ---------------------------------------------------------------------------

def sweep_profile(profile_2d, positions, rotations):
    """
    Maps each 2-D profile point through each Frenet frame.
    Returns (N_frames, N_pts, 3) world-space positions.
    """
    N = len(positions)
    P = len(profile_2d)
    # Extend profile to 3-D: (x, y, 0)
    prof3 = np.zeros((P, 3))
    prof3[:, :2] = profile_2d

    rings = np.zeros((N, P, 3))
    for i in range(N):
        # rotations[i] : (3,3) where col0=norm, col1=binorm, col2=tang
        # We want to place the profile in the (norm, binorm) plane
        rings[i] = positions[i] + (rotations[i] @ prof3.T).T

    return rings


def rings_to_triangles(rings):
    """
    Builds triangles for the lateral (tube) surface from ring array (N,P,3).
    Returns list of (3,3) triangles.
    """
    N, P, _ = rings.shape
    tris = []
    for i in range(N - 1):
        for j in range(P):
            j1 = (j + 1) % P
            a = rings[i,  j ]
            b = rings[i,  j1]
            c = rings[i+1,j ]
            d = rings[i+1,j1]
            tris.append((a, b, d))
            tris.append((a, d, c))
    return tris


def fan_triangles(centre, ring):
    """Triangulate a flat end cap from a centre point + ring."""
    P = len(ring)
    tris = []
    for j in range(P):
        j1 = (j + 1) % P
        tris.append((centre, ring[j], ring[j1]))
    return tris


# ---------------------------------------------------------------------------
# STL writer
# ---------------------------------------------------------------------------

def triangle_normal(t):
    a, b, c = t
    n = np.cross(b - a, c - a)
    l = np.linalg.norm(n)
    return n / l if l > 1e-12 else n


def write_binary_stl(triangles, path):
    header_text = b"Spring STL generated by spring_gen.py"
    header = header_text + b" " * (80 - len(header_text))
    count = len(triangles)
    with open(path, "wb") as f:
        f.write(header)
        f.write(struct.pack("<I", count))
        for tri in triangles:
            n = triangle_normal(tri)
            f.write(struct.pack("<fff", *n))
            for v in tri:
                f.write(struct.pack("<fff", *v))
            f.write(struct.pack("<H", 0))


# ---------------------------------------------------------------------------
# Support structure helpers
# ---------------------------------------------------------------------------

def _support_frames(coils, pitch, radius, n_per_coil, z_main_start):
    """
    Helix frames for the support body.

    Runs for (coils - 1) full turns at the same radius and pitch as the main
    spring, but z-shifted so each pass sits exactly midway between two adjacent
    spring coil passes:

        z_support(θ) = z_main_start  +  pitch/2  +  (pitch/2π)·θ

    Returns (positions, rotation_matrices) — both None if coils < 2.
    """
    turns = coils - 1
    N = int(turns * n_per_coil)
    if N < 2:
        return None, None

    h = pitch / (2 * math.pi)
    t = np.linspace(0, turns * 2 * math.pi, N, endpoint=True)

    z   = z_main_start + pitch / 2 + h * t
    pos = np.stack([radius * np.cos(t), radius * np.sin(t), z], axis=1)

    denom  = math.sqrt(radius ** 2 + h ** 2)
    tang   = np.stack([-radius*np.sin(t), radius*np.cos(t), np.full(N, h)], axis=1) / denom
    norm   = np.stack([-np.cos(t), -np.sin(t), np.zeros(N)], axis=1)
    binorm = np.cross(tang, norm)

    R = np.stack([norm, binorm, tang], axis=2)
    return pos, R


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_spring_stl(
    coils=15,
    thickness=1.7,
    width=2.0,
    pitch=4.0,
    inside_dia=6.0,
    chamfer=0.5,
    n_per_coil=80,
    closed_ends=True,
    support_gap=0.25,
    output_path="spring.stl",
):
    """
    Generate a spring STL and write it to output_path.
    Returns output_path on success.

    closed_ends  – add one extra coil at each end where pitch ramps to zero,
                   giving flat contact faces (default True).
    support_gap  – air gap in mm between supports and the spring coils above/
                   below them.  The support height is
                     pitch - thickness - 2 * support_gap.
                   Set to 0 to omit supports entirely.
    """
    radius = inside_dia / 2 + width / 2

    profile   = chamfered_rect_profile(width, thickness, chamfer)
    positions, rotations = helix_frames(
        coils, pitch, radius, n_per_coil, closed_ends=closed_ends
    )
    rings = sweep_profile(profile, positions, rotations)

    # Shift the whole spring so its lowest point sits exactly at z=0
    z_min = rings[:, :, 2].min()
    rings[:, :, 2]  -= z_min
    positions[:, 2] -= z_min

    triangles = rings_to_triangles(rings)

    # End caps — flip winding on first cap so normals point outward
    for tri in fan_triangles(positions[0], rings[0][::-1]):
        triangles.append(tri)
    for tri in fan_triangles(positions[-1], rings[-1]):
        triangles.append(tri)

    # ---- Support structures ----
    # Each support pass sits midway between two adjacent spring coil passes with
    # `support_gap` mm of clearance above and below.
    support_h = pitch - thickness - 2 * support_gap
    if support_gap > 0 and coils > 1 and support_h > 0:
        # z of the spring centreline at the start of the first main coil
        # (frame index ≈ n_per_coil when closed_ends=True, 0 otherwise)
        z_main = positions[n_per_coil if closed_ends else 0, 2]

        sup_pos, sup_R = _support_frames(coils, pitch, radius, n_per_coil, z_main)
        if sup_pos is not None:
            # Same radial width as the wire; height fills the gap minus clearances
            hw = width / 2
            hh = support_h / 2
            sup_profile = np.array([[-hw, -hh], [hw, -hh], [hw, hh], [-hw, hh]])
            sup_rings = sweep_profile(sup_profile, sup_pos, sup_R)

            sup_tris = rings_to_triangles(sup_rings)
            for tri in fan_triangles(sup_pos[0], sup_rings[0][::-1]):
                sup_tris.append(tri)
            for tri in fan_triangles(sup_pos[-1], sup_rings[-1]):
                sup_tris.append(tri)

            triangles.extend(sup_tris)

    write_binary_stl(
        [np.array(t, dtype=np.float32) for t in triangles],
        output_path,
    )
    return output_path


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    out = generate_spring_stl(output_path="/tmp/test_spring.stl")
    print(f"Written: {out}")
    import os
    print(f"Size: {os.path.getsize(out):,} bytes")
