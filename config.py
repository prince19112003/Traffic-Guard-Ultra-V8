import os

# --- SYSTEM SETTINGS ---
DEFAULT_MODE = "SIMULATION" # 'LIVE' or 'SIMULATION'

# --- VIDEO PATHS (For Simulation) ---
# Apni test videos 'videos' folder me dalein
VIDEO_DIR = "videos"
SIMULATION_SOURCES = {
    'north': os.path.join(VIDEO_DIR, 'north.mp4'),
    'south': os.path.join(VIDEO_DIR, 'south.mp4'),
    'east':  os.path.join(VIDEO_DIR, 'east.mp4'),
    'west':  os.path.join(VIDEO_DIR, 'west.mp4')
}

# --- LIVE CAMERA INDICES ---
# USB Cameras ke numbers (0 = Webcam)
LIVE_SOURCES = {
    'north': 0,
    'south': 1,
    'east':  2,
    'west':  3
}

# --- SIGNAL TIMINGS (Seconds) ---
MIN_GREEN_TIME = 10
MAX_GREEN_TIME = 60
YELLOW_TIME = 3