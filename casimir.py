python3 << 'EOF'
import numpy as np
import subprocess
import os
import sys

# Resolution and Timing Parameters
NX, NY = 256, 256
SCALE = 2
WIDTH, HEIGHT = NX * SCALE, NY * SCALE
FPS = 30
DURATION_SEC = 10
TOTAL_FRAMES = FPS * DURATION_SEC

c = 1.0
dt = 0.05
dx = 1.0

# QED Vacuum Field Initialization
field = np.zeros((NY, NX), dtype=np.float32)
field_prev = np.zeros((NY, NX), dtype=np.float32)

np.random.seed(42)
vacuum_noise = np.random.normal(0, 0.08, (NY, NX)).astype(np.float32)
field += vacuum_noise
field_prev += vacuum_noise

# Oscillating Conducting Boundary (Mirror) Parameters
mirror_center_x = NX // 4
omega_mirror = 2.4
amp_mirror = 6.0

output_file = "casimir_effect_10s.mp4"
ffmpeg_cmd = [
    'ffmpeg',
    '-y',
    '-f', 'rawvideo',
    '-vcodec', 'rawvideo',
    '-s', f'{WIDTH}x{HEIGHT}',
    '-pix_fmt', 'rgb24',
    '-r', str(FPS),
    '-i', '-',
    '-c:v', 'libx264',
    '-preset', 'fast',
    '-pix_fmt', 'yuv420p',
    output_file
]

try:
    process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
except FileNotFoundError:
    print("ERROR: FFmpeg binary not found! Please ensure FFmpeg is installed and in your PATH.")
    sys.exit(1)

x_coords = np.arange(NX)

print(f"[QED Simulation]: Rendering {DURATION_SEC}-second video ({TOTAL_FRAMES} frames)...")

for frame in range(TOTAL_FRAMES):
    t = frame * dt * 4.0
    x_mirror = mirror_center_x + amp_mirror * np.sin(omega_mirror * t)

    # 2D Discrete Spatial Laplacian
    laplacian = (
        np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) +
        np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) -
        4.0 * field
    ) / (dx * dx)

    # Leapfrog wave propagation
    field_next = 2.0 * field - field_prev + ((c * dt) ** 2) * laplacian
    field_next *= 0.9985

    # Mirror boundary condition
    mirror_mask = (x_coords >= int(x_mirror - 2)) & (x_coords <= int(x_mirror + 2))
    field_next[:, mirror_mask] = 0.0

    # Outer boundaries
    field_next[0, :] = field_next[-1, :] = field_next[:, 0] = field_next[:, -1] = 0.0

    field_prev[:] = field
    field[:] = field_next

    # Color mapping
    energy_density = np.clip(np.abs(field) * 8.0, 0.0, 1.0)
    r_channel = (energy_density ** 1.5 * 180).astype(np.uint8)
    g_channel = (energy_density * 220).astype(np.uint8)
    b_channel = (np.sqrt(energy_density) * 255).astype(np.uint8)

    r_channel[:, mirror_mask] = 255
    g_channel[:, mirror_mask] = 215
    b_channel[:, mirror_mask] = 0

    rgb = np.stack([r_channel, g_channel, b_channel], axis=-1)
    rgb_upscaled = rgb.repeat(SCALE, axis=0).repeat(SCALE, axis=1)

    process.stdin.write(rgb_upscaled.tobytes())

stdout, stderr = process.communicate()
if process.returncode != 0:
    print("FFmpeg encoding error:", stderr.decode())
    sys.exit(1)

print(f"[Done]: Generated {output_file} successfully.")

if sys.platform == "darwin":
    os.system(f"open {output_file}")
elif sys.platform.startswith("linux"):
    os.system(f"xdg-open {output_file} 2>/dev/null || vlc {output_file} 2>/dev/null")
EOF
