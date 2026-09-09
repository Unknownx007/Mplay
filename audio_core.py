import os
import sys
import time
import math
import random
import warnings

# Suppress all backend splash prompts immediately on module load
warnings.filterwarnings("ignore", category=RuntimeWarning)
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

try:
    import pygame
except ImportError:
    sys.exit("Error: Pygame package is missing. Run ./run_music.sh to auto-setup.")

AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"}
SPECTRUM_HEIGHTS = []

def human_time(seconds: float) -> str:
    seconds = int(seconds or 0)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"

def scan_directory(path: str) -> list:
    """Scans and extracts playable audio assets from target workspace path."""
    tracks = []
    if not os.path.exists(path) or not os.path.isdir(path):
        return tracks
    try:
        for name in sorted(os.listdir(path)):
            full = os.path.join(path, name)
            if not os.path.isfile(full) or os.path.splitext(name)[1].lower() not in AUDIO_EXTS:
                continue
            tracks.append({
                "path": full,
                "name": name,
                "size": os.path.getsize(full)
            })
    except Exception:
        pass
    return tracks

class AudioEngine:
    """Manages the backend hardware mixer channel cleanly."""
    def __init__(self):
        pygame.mixer.init()
        self.current = None
        self.paused = False
        self.start_time = 0.0
        self.pause_pos = 0.0
        self._cached_duration = 0.0

    def play(self, track):
        try:
            pygame.mixer.music.load(track["path"])
            pygame.mixer.music.play()
            try:
                self._cached_duration = pygame.mixer.Sound(track["path"]).get_length()
            except Exception:
                self._cached_duration = 180.0
        except pygame.error as e:
            raise RuntimeError(f"Playback Error: {e}")
        self.current = track
        self.paused = False
        self.start_time = time.time()
        self.pause_pos = 0.0

    def stop(self):
        pygame.mixer.music.stop()
        self.current = None
        self.paused = False

    def toggle_pause(self):
        if not self.current:
            return
        if self.paused:
            pygame.mixer.music.unpause()
            self.start_time = time.time() - self.pause_pos
        else:
            pygame.mixer.music.pause()
            self.pause_pos = time.time() - self.start_time
        self.paused = not self.paused

    def set_volume(self, delta):
        cur = pygame.mixer.music.get_volume()
        pygame.mixer.music.set_volume(max(0.0, min(1.0, cur + delta)))

    def position(self) -> float:
        if not self.current:
            return 0.0
        if self.paused:
            return self.pause_pos
        return time.time() - self.start_time

    def duration(self) -> float:
        return self._cached_duration if self.current else 0.0

    def is_active(self) -> bool:
        return bool(pygame.mixer.music.get_busy()) or self.paused

def get_spectrum_bars(engine, width: int, max_h: int) -> list:
    """Simulates an analog physical spectrum analyzer using floating decay vectors."""
    global SPECTRUM_HEIGHTS
    if len(SPECTRUM_HEIGHTS) != width:
        SPECTRUM_HEIGHTS = [0.0] * width

    if not engine.current or engine.paused or not bool(pygame.mixer.music.get_busy()):
        SPECTRUM_HEIGHTS = [max(0.0, h - 0.7) for h in SPECTRUM_HEIGHTS]
        return [int(h) for h in SPECTRUM_HEIGHTS]

    pos = engine.position()
    for i in range(width):
        bass = math.sin(pos * 6.8 + i * 0.12) * 0.5 if i < (width // 3) else 0.0
        mids = math.cos(pos * 3.4 - i * 0.05) * 0.4 if (width // 3) <= i < (2 * width // 3) else 0.0
        highs = random.uniform(0.0, 0.25) if i >= (2 * width // 3) else 0.0
        
        rand_jitter = random.uniform(0.8, 1.2)
        raw_v = (abs(math.sin(pos * 2.1 + i * 0.2)) + bass + mids + highs) * max_h * rand_jitter
        
        if i < 2 or i > width - 3:
            raw_v *= 0.4

        if raw_v > SPECTRUM_HEIGHTS[i]:
            SPECTRUM_HEIGHTS[i] = min(float(max_h), raw_v)
        else:
            SPECTRUM_HEIGHTS[i] = max(0.0, SPECTRUM_HEIGHTS[i] - random.uniform(0.3, 0.5))

    return [int(h) for h in SPECTRUM_HEIGHTS]
