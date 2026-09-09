# Mplay

> *"We hack the baseline. We amplify the signal. Music is the ultimate system exploit."* — **DEDSEC**

**Mplay** is a lightweight, high-performance terminal music player and native YouTube downloader package. It serves as a fully integrated, zero-configuration alternative to `ncmpcpp` and `cava` that runs flawlessly inside any terminal environment.

---

## ⚡ Core Features

- **Textured Equalizer Visualizer**: Bottom-up reactive spectrum rendering using smooth analog physical drop-decay math.
- **Native Non-Blocking Downloader**: Integrated asynchronous `yt-dlp` library backend that handles video and playlist URLs in a separate background worker thread without pausing audio streams.
- **Flicker-Free Canvas**: Employs an intelligent double-buffered window refresh layer that completely eliminates standard Curses grid flickering.
- **Adaptive Layout Engine**: Seamlessly adjusts between side-by-side or stacked orientation structures depending on terminal grid dimensions.
- **Auto Workspace Syncing**: Instantly re-scans, syncs, and updates track listings the millisecond background network streams wrap up.

---

## 🎹 Global Control Interface

| Hotkey Keybind | Action Description |
| :--- | :--- |
| `SPACE` / `ENTER` | Play Selected Track / Toggle Audio Pause |
| `S` | Stop Audio Stream Playback Completely |
| `UP` / `DOWN` / `k` / `j` | Navigate and Scroll Local Tracks Library Listing |
| `LEFT` / `RIGHT` | Incremental Volume Controls Down/Up (±5%) |
| `D` | Shift Layout Control to Interactive Download Entry Field |
| `ESC` | Exit Text Input Field Focus Layer |
| `q` | Close Hardware Mixer Channels and Safely Exit |

---

## 🚀 Automated Installation & Setup

### 📦 Prerequisites
Your system requires `ffmpeg` installed to allow python libraries to decode audio formats into a high-fidelity native `.mp3` format workspace.

* **Debian/Ubuntu/Mint:** `sudo apt install ffmpeg`
* **Arch Linux:** `sudo pacman -S ffmpeg`
* **macOS:** `brew install ffmpeg`

### 💻 Deploying Mplay
Run the wrapper setup launcher engine. It builds a virtual sandboxed container workspace environment automatically, downloads the `pygame-ce`, `pydub`, and `yt-dlp` packages inside the `venv`, and boots up your application:

```bash
git clone https://github.com/Unknownx007/Mplay
cd Mplay
chmod +x run_music.sh
./run_music.sh { your music (.mp3 or files) directory path }
```
*Note: If no folder parameter is supplied, it defaults target indexes to look directly inside your local system `~/Music` directory.*

---
