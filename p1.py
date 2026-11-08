"""AI Snake - steer a snake with your fingertip using webcam hand tracking.

The tip of the player's index finger (MediaPipe landmark 8) acts as the
snake's head.  Moving the finger draws the snake's body; eating the apple
grows the snake and increases the score.

Usage:
    python p1.py

Press Q or Esc to quit.
"""

from __future__ import annotations

import argparse
import math
import random
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector

WINDOW_NAME = "AI Snake - Hand Tracking"
FONT = cv2.FONT_HERSHEY_SIMPLEX
FINGERTIP_ID = 8

SNAKE_COLOR = (0, 0, 255)
SNAKE_OUTLINE = (0, 0, 90)
HEAD_COLOR = (200, 0, 200)
TEXT_COLOR = (255, 255, 255)

HEAD_RADIUS = 20
SEGMENT_THICKNESS = 20
INITIAL_LENGTH = 250.0
GROWTH_PER_FOOD = 25.0
MAX_JUMP_PX = 250.0

DEFAULT_FOOD_IMAGE = Path(__file__).resolve().parent / "pi.png"


@dataclass(frozen=True)
class GameConfig:
    """Tunable game-play values."""

    initial_length: float = INITIAL_LENGTH
    growth_per_food: float = GROWTH_PER_FOOD
    max_jump: float = MAX_JUMP_PX


def load_food_image(path: Path):
    """Load an RGBA food sprite, or return ``None`` if it is unusable."""
    if not path.exists():
        print(f"[warn] Food image not found: {path}")
        print("[warn] Falling back to a drawn apple.")
        return None

    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None:
        print(f"[warn] Could not read food image: {path}")
        print("[warn] Falling back to a drawn apple.")
        return None

    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGRA)
    elif image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

    return image


def put_text(frame, text, origin, scale, color=TEXT_COLOR, thickness=2):
    """Draw text with a dark shadow so it stays readable on any background."""
    cv2.putText(frame, text, origin, FONT, scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
    cv2.putText(frame, text, origin, FONT, scale, color, thickness, cv2.LINE_AA)


def draw_hud(frame, score, fps):
    """Render the score, frame rate and control hint."""
    put_text(frame, f"Score: {score}", (30, 60), 1.4, thickness=3)
    put_text(frame, f"FPS: {fps:4.0f}", (30, 105), 0.8)

    hint = "Move your index fingertip to steer  |  Q / Esc to quit"
    put_text(frame, hint, (30, frame.shape[0] - 25), 0.7)


class Snake:
    """Snake body built from the recent trajectory of the player's finger."""

    def __init__(
        self,
        food_image,
        frame_width: int,
        frame_height: int,
        config: GameConfig = GameConfig(),
    ):
        self.config = config
        self.frame_width = frame_width
        self.frame_height = frame_height

        self.food_image = food_image
        if food_image is not None:
            self.food_height, self.food_width = food_image.shape[:2]
        else:
            self.food_width = self.food_height = 40

        self.points: list[tuple[int, int]] = []
        self.segment_lengths: list[float] = []
        self.current_length = 0.0
        self.allowed_length = config.initial_length
        self.previous_head: tuple[int, int] | None = None
        self.score = 0

        self.food_position = (0, 0)
        self.spawn_food()

    def spawn_food(self):
        """Place the apple at a random spot that keeps the sprite on screen."""
        margin_x = self.food_width // 2 + 8
        margin_y = self.food_height // 2 + 8
        max_x = max(margin_x, self.frame_width - margin_x)
        max_y = max(margin_y, self.frame_height - margin_y)
        self.food_position = (
            random.randint(margin_x, max_x),
            random.randint(margin_y, max_y),
        )

    def reset_path(self):
        """Clear the trail without resetting the score or the snake's length."""
        self.points.clear()
        self.segment_lengths.clear()
        self.current_length = 0.0
        self.previous_head = None

    def update(self, frame, head):
        """Advance the snake to ``head``, handle food and draw everything."""
        head = (int(head[0]), int(head[1]))

        # A missing hand or a large jump would otherwise draw a line across
        # the whole frame, so start a fresh trail in that case.
        if self.previous_head is None:
            self.reset_path()
        elif (
            math.hypot(head[0] - self.previous_head[0], head[1] - self.previous_head[1])
            > self.config.max_jump
        ):
            self.reset_path()

        previous = self.previous_head or head
        self.points.append(head)
        segment = math.hypot(head[0] - previous[0], head[1] - previous[1])
        self.segment_lengths.append(segment)
        self.current_length += segment
        self.previous_head = head

        # Trim the oldest segments until the snake fits its allowed length.
        while (
            self.current_length > self.allowed_length
            and self.segment_lengths
            and self.points
        ):
            self.current_length -= self.segment_lengths.pop(0)
            self.points.pop(0)

        self._eat_if_needed(head)
        self.draw(frame)
        return frame

    def _eat_if_needed(self, head):
        food_x, food_y = self.food_position
        food_radius = min(self.food_width, self.food_height) / 2
        hit_radius = food_radius + HEAD_RADIUS * 0.5

        if math.hypot(head[0] - food_x, head[1] - food_y) <= hit_radius:
            self.score += 1
            self.allowed_length += self.config.growth_per_food
            self.spawn_food()

    def draw(self, frame):
        self._draw_body(frame)
        self._draw_food(frame)

    def _draw_body(self, frame):
        if not self.points:
            return

        for start, end in zip(self.points, self.points[1:]):
            cv2.line(
                frame, start, end, SNAKE_OUTLINE, SEGMENT_THICKNESS + 4, cv2.LINE_AA
            )
            cv2.line(frame, start, end, SNAKE_COLOR, SEGMENT_THICKNESS, cv2.LINE_AA)

        cv2.circle(
            frame,
            self.points[-1],
            HEAD_RADIUS + 2,
            SNAKE_OUTLINE,
            cv2.FILLED,
            cv2.LINE_AA,
        )
        cv2.circle(
            frame, self.points[-1], HEAD_RADIUS, HEAD_COLOR, cv2.FILLED, cv2.LINE_AA
        )

    def _draw_food(self, frame):
        food_x, food_y = self.food_position

        if self.food_image is not None:
            x = food_x - self.food_width // 2
            y = food_y - self.food_height // 2
            cvzone.overlayPNG(frame, self.food_image, (x, y))
            return

        # Drawn fallback used when the sprite is missing or unreadable.
        cv2.circle(frame, (food_x, food_y), 18, (0, 0, 220), cv2.FILLED, cv2.LINE_AA)
        cv2.circle(frame, (food_x, food_y), 18, (0, 0, 90), 2, cv2.LINE_AA)
        cv2.circle(
            frame, (food_x - 5, food_y - 5), 5, (90, 90, 255), cv2.FILLED, cv2.LINE_AA
        )
        cv2.ellipse(
            frame,
            (food_x + 6, food_y - 22),
            (9, 4),
            -30,
            0,
            360,
            (40, 160, 60),
            cv2.FILLED,
            cv2.LINE_AA,
        )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Control a snake with your index fingertip using a webcam."
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Camera index to open (default: 0).",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Requested capture width (default: 1280).",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="Requested capture height (default: 720).",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.6,
        help="Minimum hand-detection confidence, 0-1 (default: 0.6).",
    )
    parser.add_argument(
        "--food",
        type=Path,
        default=DEFAULT_FOOD_IMAGE,
        help="Path to an RGBA food sprite (default: pi.png).",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    food_image = load_food_image(args.food)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise SystemExit(
            f"Could not open camera {args.camera}.\n"
            "Close other apps that use the webcam, check camera permissions, "
            "or try a different index with --camera 1."
        )

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    detector = HandDetector(detectionCon=args.confidence, maxHands=2)
    game = None
    fps = 0.0
    previous_time = time.perf_counter()

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("[error] Failed to read a frame from the camera.")
                break

            # Mirror the feed so moving right on screen matches moving right
            # in front of the camera.
            frame = cv2.flip(frame, 1)

            if game is None:
                game = Snake(food_image, frame.shape[1], frame.shape[0])

            hands, frame = detector.findHands(frame, flipType=False)

            if hands and len(hands[0]["lmList"]) > FINGERTIP_ID:
                fingertip = hands[0]["lmList"][FINGERTIP_ID][:2]
                game.update(frame, fingertip)
            else:
                # Keep the current snake and food visible while no hand is seen.
                game.draw(frame)

            now = time.perf_counter()
            elapsed = now - previous_time
            previous_time = now
            if elapsed > 0:
                instant_fps = 1.0 / elapsed
                fps = instant_fps if fps == 0 else 0.9 * fps + 0.1 * instant_fps

            draw_hud(frame, game.score, fps)
            cv2.imshow(WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
