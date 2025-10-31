import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'true'

import socket
import time
import pigpio
import pygame
import sys
import RPi.GPIO as GPIO
import threading
import math

# -----------------------------
# EYES (try-me button)
# -----------------------------
EYES_PIN = 18
EYES_START_PERIOD = 0.25  # seconds (slow at start)
EYES_END_PERIOD   = 0.06  # seconds (fast near the end)

# -----------------------------
# CONFIG
# -----------------------------
UDP_PORT = 5005
EXPECTED_MSG = b'PHONE_ANSWERED'

# Servo (pigpio uses BCM numbering)
SERVO_PIN = 17
SERVO_MIN = 500
SERVO_MID = 1500
SERVO_MAX = 2500
HOLD_SECONDS = 6  # time to hold head turn after trigger
SERVO_MOVE_DURATION = 1.0  # seconds for edge-edge sweep
SWEEPS = 4

# Audio files on Desktop
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
LOOK_FILE = 'look_behind_you.mp3'
LAUGH_FILE = 'crypt_laugh.mp3'
AUDIO_BEHIND = os.path.join(AUDIO_DIR, LOOK_FILE)
AUDIO_LAUGH = os.path.join(AUDIO_DIR, LAUGH_FILE)

# -----------------------------
# INIT
# -----------------------------
print('***** Halloween Rocking Chair Skeleton *****')

# pigpio
pi = pigpio.pi()
if not pi.connected:
    print('[error] pigpio daemon not running. Start with: sudo pigpiod')
    sys.exit(1)
pi.set_mode(SERVO_PIN, pigpio.OUTPUT)

# pygame audio
pygame.mixer.init()
pygame.mixer.music.set_volume(0.25)

# GPIO for eyes (ON by default)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(EYES_PIN, GPIO.OUT)
GPIO.output(EYES_PIN, GPIO.HIGH)

# UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', UDP_PORT))
sock.settimeout(1.0)  # allows Ctrl+C responsiveness

print('[ready] listening on UDP port', UDP_PORT)

# -----------------------------
# SERVO HELPERS (all motion stepped)
# -----------------------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def ease_in_out_sine(t: float) -> float:
    # t in [0,1] -> eased in [0,1]
    return 0.5 * (1 - math.cos(math.pi * t))

def get_pulsewidth():
    try:
        pw = pi.get_servo_pulsewidth(SERVO_PIN)
        return pw if SERVO_MIN <= pw <= SERVO_MAX else 0
    except pigpio.error:
        return 0

def sweep(start: int, end: int, duration: float, steps: int = 100, easing=ease_in_out_sine):
    """
    Step from start to end over 'duration' with 'steps' using easing.
    All pulses are clamped and sent as ints.
    """
    steps = max(2, int(steps))
    duration = max(0.01, float(duration))

    start = clamp(int(start), SERVO_MIN, SERVO_MAX)
    end   = clamp(int(end),   SERVO_MIN, SERVO_MAX)

    sleep_time = duration / (steps - 1)
    delta = end - start

    for i in range(steps):
        t = i / (steps - 1)
        eased = easing(t)
        pos = clamp(int(round(start + eased * delta)), SERVO_MIN, SERVO_MAX)
        pi.set_servo_pulsewidth(SERVO_PIN, pos)
        time.sleep(sleep_time)

def move_to(target: int, duration: float = 1.0, steps: int = 100):
    """
    Smoothly move from current (or best-guess) position to 'target'.
    If current is unknown (pigpio returns 0), wake gently near MID first.
    """
    current = get_pulsewidth()
    if current == 0:
        # Wake with a tiny nudge around MID to avoid the initial static click
        nudge = 50
        sweep(SERVO_MID - nudge, SERVO_MID + nudge, duration=0.25, steps=40)
        sweep(SERVO_MID + nudge, SERVO_MID, duration=0.15, steps=30)
        current = SERVO_MID

    sweep(current, target, duration, steps)

def move_to_center(duration: float = 1.0, steps: int = 100):
    move_to(SERVO_MID, duration, steps)

# -----------------------------
# EYES HELPERS
# -----------------------------
def eyes_on():
    GPIO.setup(EYES_PIN, GPIO.OUT)
    GPIO.output(EYES_PIN, GPIO.HIGH)

def eyes_off():
    GPIO.setup(EYES_PIN, GPIO.IN)

def blink_eyes_ramp(duration, stop_event: threading.Event):
    """
    Blink eyes for up to 'duration' seconds with a ramp from slow to fast.
    Duty ~50%. Ends with eyes ON.
    """
    t_end = time.time() + duration
    while time.time() < t_end and not stop_event.is_set():
        remaining = t_end - time.time()
        progress = 1.0 - max(0.0, min(1.0, remaining / duration))
        period = EYES_START_PERIOD + (EYES_END_PERIOD - EYES_START_PERIOD) * progress
        half = period * 0.5

        eyes_on()
        time.sleep(half)
        if stop_event.is_set() or time.time() + half >= t_end:
            break
        eyes_off()
        time.sleep(half)

    eyes_on()  # leave ON

# -----------------------------
# EFFECT
# -----------------------------
def do_effect():
    """Hold at MIN while 'look_behind_you' plays (>= HOLD_SECONDS), blinking; then do sweeps with 'crypt_laugh'."""

    # Step to HOLD (MIN) instead of a raw pulse
    move_to(SERVO_MIN, duration=SERVO_MOVE_DURATION, steps=120)

    # Start 'look behind you' (non-blocking) and blink for at least HOLD_SECONDS
    pygame.mixer.music.stop()
    pygame.mixer.music.load(AUDIO_BEHIND)
    pygame.mixer.music.play()

    hold_start = time.time()
    stop_blink = threading.Event()
    blinker = threading.Thread(target=blink_eyes_ramp, args=(HOLD_SECONDS, stop_blink), daemon=True)
    blinker.start()

    # Wait until BOTH: audio finished AND at least HOLD_SECONDS elapsed
    while True:
        elapsed = time.time() - hold_start
        if elapsed >= HOLD_SECONDS and not pygame.mixer.music.get_busy():
            break
        time.sleep(0.02)

    # stop blinking thread and ensure eyes stay ON
    stop_blink.set()
    blinker.join(timeout=0.2)
    eyes_on()
    pygame.mixer.music.stop()

    # Start 'crypt_laugh' and do stepped sweeps
    pygame.mixer.music.load(AUDIO_LAUGH)
    pygame.mixer.music.play()

    for _ in range(SWEEPS):
        move_to(SERVO_MIN, duration=SERVO_MOVE_DURATION, steps=120)
        move_to(SERVO_MAX, duration=SERVO_MOVE_DURATION, steps=120)

    # Recenter, stop audio, and keep eyes ON
    move_to_center(duration=1.2, steps=120)
    pygame.mixer.music.stop()
    eyes_on()

# -----------------------------
# MAIN LOOP
# -----------------------------
try:
    busy = False

    move_to_center(duration=0.8, steps=80)

    while True:
        try:
            data, addr = sock.recvfrom(4096)  # blocks up to 1s due to settimeout
        except socket.timeout:
            continue

        if busy:
            # already active, ignore
            continue

        msg = data.strip()
        print(f'[message] {msg!r} from {addr}')

        if msg == EXPECTED_MSG:
            busy = True
            try:
                do_effect()
            finally:
                busy = False

except KeyboardInterrupt:
    pass
finally:
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass
    try:
        eyes_off()
        GPIO.cleanup()
    except Exception:
        pass
    pygame.mixer.quit()
    move_to_center(duration=1.2, steps=120)
    pi.stop()
    print('[stopped]')
