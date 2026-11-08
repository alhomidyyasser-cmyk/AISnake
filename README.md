# 🐍 AI Snake — Hand-Tracked Snake Game

> Control a snake with your index fingertip using only a webcam. No keyboard, no controller.

[![Python](https://img.shields.io/badge/Python-3.9--3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Hand%20Tracking-0097A7)](https://developers.google.com/mediapipe)
[![cvzone](https://img.shields.io/badge/cvzone-1.6%2B-2E8B57)](https://github.com/cvzone/cvzone)

AI Snake is a real-time computer-vision game. A webcam feed is mirrored on screen, MediaPipe detects your hand, and the tip of your index finger becomes the snake's head. Guide the snake to the apple to grow longer and increase your score.

---

## Features

- **Touch-free controls** — steer the snake by moving your index fingertip.
- **Real-time hand tracking** — MediaPipe + cvzone, no special hardware required.
- **Snake-style growth** — the snake gets longer every time it eats an apple.
- **Random food placement** — the apple always spawns fully inside the play area.
- **Live HUD** — current score and smoothed FPS counter.
- **Robust trail handling** — the snake resets its trail when tracking is lost or the finger jumps, so no lines are drawn across the screen.
- **Configurable** — camera index, capture resolution, detection confidence, and food sprite can be set from the command line.
- **Graceful fallback** — if the food sprite is missing or unreadable, a drawn apple is used instead.
- **Clean shutdown** — releases the camera and closes windows on exit.

---

## Requirements

| Requirement | Details |
| --- | --- |
| Python | 3.9 – 3.12 |
| Webcam | Any camera OpenCV can access |
| OS | Windows, macOS, or Linux with a desktop session |
| Dependencies | OpenCV, MediaPipe, cvzone, NumPy |

> Tested with Python 3.11, OpenCV 4.11, MediaPipe 0.10.21, and cvzone 1.6.1 on Windows 11.

---

## Installation

```bash
git clone https://github.com/<your-username>/aisnake.git
cd aisnake
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

**Windows**

```powershell
.venv\Scripts\activate
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> **Linux note:** if OpenCV cannot open a window, install the GUI libraries for your distribution, for example `sudo apt install libgl1 libglib2.0-0`.

---

## Usage

Start the game:

```bash
python p1.py
```

A window titled **AI Snake - Hand Tracking** opens with the mirrored camera feed. Move your index fingertip to steer the snake toward the apple.

### Command-line options

| Option | Default | Description |
| --- | --- | --- |
| `--camera` | `0` | Camera index to open. Use `1`, `2`, … for additional cameras. |
| `--width` | `1280` | Requested capture width in pixels. |
| `--height` | `720` | Requested capture height in pixels. |
| `--confidence` | `0.6` | Minimum hand-detection confidence (`0`–`1`). Lower values detect more hands but may produce false positives. |
| `--food` | `pi.png` | Path to an RGBA food sprite. |

Examples:

```bash
# Use a second camera
python p1.py --camera 1

# Lower resolution for better performance on slower machines
python p1.py --width 640 --height 480

# Require more confident hand detections
python p1.py --confidence 0.75

# Use a custom apple sprite
python p1.py --food assets/my_apple.png
```

---

## Controls

| Input | Action |
| --- | --- |
| Move your index fingertip | Steer the snake |
| `Q` | Quit |
| `Esc` | Quit |

---

## How It Works

1. **Capture and mirror** — OpenCV reads frames from the webcam and flips them horizontally so on-screen movement matches real-world movement.
2. **Hand detection** — `cvzone.HandTrackingModule.HandDetector` runs MediaPipe Hands and returns 21 landmarks per hand.
3. **Fingertip as the head** — landmark `8` (the index fingertip) is used as the snake's current head position.
4. **Trail and length** — every head position is appended to a trail. The distance between consecutive points is accumulated; once the snake exceeds its allowed length, the oldest segments are removed.
5. **Food and growth** — when the head overlaps the apple, the score increases, the allowed length grows by 25 pixels, and a new apple is placed at a random valid position.
6. **Rendering** — the snake body, head, apple sprite, and HUD are drawn on each frame and displayed with `cv2.imshow`.

The snake's trail is reset automatically when the fingertip reappears far from its last position (for example, after tracking is lost) or when it moves more than `MAX_JUMP_PX` between frames. This keeps the game stable without penalizing the player.

---

## Project Structure

```text
aisnake/
├── p1.py              # Main game: hand tracking, snake logic, rendering, CLI
├── pi.png             # 64×64 RGBA apple sprite used as the food
├── requirements.txt   # Python dependencies
├── .gitignore         # Python, virtualenv, IDE, and OS ignores
└── README.md          # This file
```

---

## Configuration

Game-play constants live at the top of [`p1.py`](p1.py):

| Constant | Default | Purpose |
| --- | --- | --- |
| `FINGERTIP_ID` | `8` | MediaPipe landmark used as the snake's head. |
| `HEAD_RADIUS` | `20` | Radius of the head circle in pixels. |
| `SEGMENT_THICKNESS` | `20` | Thickness of the snake body. |
| `INITIAL_LENGTH` | `250` | Starting snake length in pixels. |
| `GROWTH_PER_FOOD` | `25` | Length added after eating an apple. |
| `MAX_JUMP_PX` | `250` | Jump distance that resets the trail. |
| `SNAKE_COLOR` | `(0, 0, 255)` | Body color (BGR). |
| `HEAD_COLOR` | `(200, 0, 200)` | Head color (BGR). |

For more involved changes, the `GameConfig` dataclass groups the length and jump settings.

---

## Troubleshooting

| Problem | Suggested fix |
| --- | --- |
| `Could not open camera 0` | Close apps using the webcam, check OS camera permissions, or try `--camera 1`. |
| `ModuleNotFoundError: cv2` / `mediapipe` / `cvzone` | Activate the virtual environment and run `pip install -r requirements.txt`. |
| MediaPipe fails to install | Use Python 3.10–3.12 (3.11 is the most tested); check that the wheel matches your OS and architecture. |
| Hand is not detected | Improve lighting, keep your whole hand in frame, and lower `--confidence` (for example `0.4`). |
| Low FPS or lag | Use `--width 640 --height 480`, close background apps, or reduce camera resolution. |
| Food image warning in the console | The sprite path is wrong or the file is unreadable; the game continues with a drawn apple. |
| MediaPipe prints TensorFlow Lite / inference warnings | These are normal MediaPipe log messages and do not affect the game. |
| Window is black | Make sure the script is not running in a headless environment and that the camera is not in use elsewhere. |

---

## Tips for Best Results

- Use a well-lit room with a plain background behind your hand.
- Keep your hand roughly 40–80 cm from the camera.
- Move your index finger smoothly; very fast movements may trigger a trail reset.
- If multiple hands are in frame, the first detected hand is used.
- Start with the default resolution and lower it only if performance is poor.

---

## Roadmap

Ideas for extending the project:

- Persistent high-score table
- Sound effects for eating and growth
- Obstacles and multiple food items
- Pause and restart keys
- On-screen difficulty selection
- Two-player mode using both hands

---

## Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/my-improvement`.
3. Commit your changes with a clear message.
4. Open a pull request describing what changed and why.

Please keep changes focused and test the game with a real webcam before submitting.

---

## Acknowledgments

- [OpenCV](https://opencv.org/) for video capture, drawing, and image processing.
- [MediaPipe](https://developers.google.com/mediapipe) for real-time hand tracking.
- [cvzone](https://github.com/cvzone/cvzone) for the hand-detector wrapper and PNG overlay helper.
- Inspired by the classic Nokia Snake game.

---

## License

No license has been specified for this repository yet. If you intend to share or reuse the code, add a `LICENSE` file (for example, the MIT License) so the terms are clear.
