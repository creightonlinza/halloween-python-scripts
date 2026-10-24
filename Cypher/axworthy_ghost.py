#!/usr/bin/env python3
"""
Cypher - IBT-4 (IN1/IN2/GND) wiper motor test script (RPi.GPIO version)

Wiring (BCM):
- IN1 -> GPIO18 (physical pin 12)
- IN2 -> GPIO19 (physical pin 35)
- GND -> Pi GND (physical pin 6 or any GND)
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time

import RPi.GPIO as GPIO

LOG = logging.getLogger("cypher")


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


class IBT4Motor:
    def __init__(self, in1: int, in2: int, pwm_hz: int = 1000, deadtime_s: float = 0.05):
        self.in1 = in1
        self.in2 = in2
        self.pwm_hz = pwm_hz
        self.deadtime_s = deadtime_s

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.in1, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.in2, GPIO.OUT, initial=GPIO.LOW)

        self.pwm1 = GPIO.PWM(self.in1, self.pwm_hz)
        self.pwm2 = GPIO.PWM(self.in2, self.pwm_hz)
        self.pwm1.start(0.0)
        self.pwm2.start(0.0)

        self._direction: str | None = None  # last driven direction; None while stopped
        self._cleaned_up = False

        LOG.info("Initialized IBT-4 on IN1=GPIO%d IN2=GPIO%d @ %d Hz", self.in1, self.in2, self.pwm_hz)

    def _both_zero(self) -> None:
        self.pwm1.ChangeDutyCycle(0.0)
        self.pwm2.ChangeDutyCycle(0.0)
        self._direction = None

    def coast(self) -> None:
        self._both_zero()

    def brake(self, duration_s: float = 0.2) -> None:
        # Brief active brake. Use sparingly - can spike current.
        self.pwm1.ChangeDutyCycle(100.0)
        self.pwm2.ChangeDutyCycle(100.0)
        time.sleep(max(0.0, duration_s))
        self._both_zero()

    def drive(self, direction: str, duty: float) -> None:
        if direction not in ("fwd", "rev"):
            raise ValueError("direction must be 'fwd' or 'rev'")
        duty = clamp(duty, 0.0, 1.0) * 100.0

        # Deadtime to reduce shoot-through, only when reversing while moving.
        # Same-direction calls (e.g. during a ramp) just update the duty cycle.
        if self._direction is not None and direction != self._direction:
            self._both_zero()
            time.sleep(self.deadtime_s)

        if direction == "fwd":
            self.pwm2.ChangeDutyCycle(0.0)
            self.pwm1.ChangeDutyCycle(duty)
        else:
            self.pwm1.ChangeDutyCycle(0.0)
            self.pwm2.ChangeDutyCycle(duty)
        self._direction = direction

    def cleanup(self) -> None:
        if self._cleaned_up:
            return
        self._cleaned_up = True
        try:
            self._both_zero()
            self.pwm1.stop()
            self.pwm2.stop()
        finally:
            GPIO.cleanup()


def ramp(m: IBT4Motor, direction: str, start: float, end: float, seconds: float, step_hz: float = 40.0) -> None:
    start = clamp(start, 0.0, 1.0)
    end = clamp(end, 0.0, 1.0)
    seconds = max(0.0, seconds)

    steps = max(1, int(seconds * step_hz))
    for i in range(steps + 1):
        t = i / steps
        duty = start + (end - start) * t
        m.drive(direction, duty)
        time.sleep(seconds / steps)


def pattern_demo(m: IBT4Motor, max_duty: float) -> None:
    LOG.info("Pattern: demo")
    LOG.info("Ramp FWD up/down")
    ramp(m, "fwd", 0.0, max_duty, 2.0)
    time.sleep(0.8)
    ramp(m, "fwd", max_duty, 0.0, 1.5)
    m.coast()
    time.sleep(0.8)

    LOG.info("Pulse FWD x10")
    for _ in range(10):
        m.drive("fwd", min(0.6, max_duty))
        time.sleep(0.25)
        m.coast()
        time.sleep(0.25)
    time.sleep(0.8)

    LOG.info("Brief brake test")
    m.drive("fwd", min(0.5, max_duty))
    time.sleep(1.0)
    m.brake(0.2)
    time.sleep(0.8)

    LOG.info("Ramp REV up/down")
    ramp(m, "rev", 0.0, max_duty, 2.0)
    time.sleep(0.8)
    ramp(m, "rev", max_duty, 0.0, 1.5)
    m.coast()
    time.sleep(0.8)


def setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in1", type=int, default=18, help="BCM GPIO for IN1 (default 18)")
    ap.add_argument("--in2", type=int, default=19, help="BCM GPIO for IN2 (default 19)")
    ap.add_argument("--pwm-hz", type=int, default=1000, help="PWM freq Hz (default 1000)")
    ap.add_argument("--max-duty", type=float, default=0.7, help="Max duty 0.0-1.0 (default 0.7)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    setup_logging(args.verbose)

    motor = IBT4Motor(args.in1, args.in2, pwm_hz=args.pwm_hz)
    max_duty = clamp(args.max_duty, 0.0, 1.0)

    def _stop(_signum, _frame):
        # Cleanup happens in the finally block below.
        LOG.warning("Stopping motor (coast) and cleaning up.")
        sys.exit(0)

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    try:
        pattern_demo(motor, max_duty=max_duty)
    finally:
        motor.cleanup()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
