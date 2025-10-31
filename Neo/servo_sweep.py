import pigpio
import random
import time
import math

# -----------------------------
# CONFIG
# -----------------------------
SERVO_PIN = 17
SERVO_MIN = 500
SERVO_MID = 1500
SERVO_MAX = 2500
MIN_WAIT_TIME = 1

# -----------------------------
# Setup
# -----------------------------
pi = pigpio.pi()
if not pi.connected:
    raise RuntimeError("pigpio daemon not running. Start with: sudo pigpiod")
pi.set_mode(SERVO_PIN, pigpio.OUTPUT)
pi.set_servo_pulsewidth(SERVO_PIN, 0)  # explicit stop; needed to fix bug with state


def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def ease_in_out_sine(t: float) -> float:
    # t in [0,1] -> eased in [0,1]
    return 0.5 * (1 - math.cos(math.pi * t))

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

def move_to(target: int, duration: float = 1.0, steps: int = 80):
    """
    Smoothly move from the current (or best-guess) position to 'target'.
    If the current position is unknown (pigpio returns 0), do a tiny wake nudge first
    so we never issue a single static pulse.
    """
    current = pi.get_servo_pulsewidth(SERVO_PIN)

    if current == 0:
        # Wake the servo gently with a micro-sweep around mid; then go to target.
        # This avoids the initial 'click with no motion' from a static pulse.
        nudge_span = 40  # micro range ~0.04 ms
        sweep(SERVO_MID - nudge_span, SERVO_MID + nudge_span, duration=0.25, steps=40)
        sweep(SERVO_MID + nudge_span, SERVO_MID, duration=0.15, steps=30)
        current = SERVO_MID

    sweep(current, target, duration, steps)

def move_to_center(duration: float = 1.2, steps: int = 100):
    move_to(SERVO_MID, duration, steps)

print('***** Halloween Attic Light Sweep *****')

try:
    move_to_center(duration=0.8, steps=60)
    print('[sweeping]')

    while True:
        loop_wait_time = random.randint(MIN_WAIT_TIME, 20)
        move_duration  = random.randint(MIN_WAIT_TIME, 5)

        move_to(SERVO_MAX, duration=move_duration, steps=100)
        time.sleep(MIN_WAIT_TIME)
        move_to(SERVO_MIN, duration=move_duration, steps=100)
        time.sleep(loop_wait_time)

except KeyboardInterrupt:
    pass
finally:
    move_to_center(duration=1.5, steps=120)
    pi.stop()
    print('[stopped]')
