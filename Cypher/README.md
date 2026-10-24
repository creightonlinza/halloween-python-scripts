# Axworthy Ghost Wiper Motor (Cypher)

> **Status: work in progress, largely untested.** Right now this is a bench-test script for checking the motor driver wiring, not a finished prop.

A Raspberry Pi named **Cypher** drives a 12V **wiper motor** through an **IBT-4 H-bridge** board. The goal is to use the motor to animate the Axworthy ghost prop. For now, `axworthy_ghost.py` runs a single demo pattern so you can confirm the motor spins both ways, ramps smoothly, and brakes.

---

## What the demo does

`axworthy_ghost.py` runs `pattern_demo()` once and exits:

1. **Ramp forward** from 0 up to `--max-duty` over 2s, then back down over 1.5s.
2. **Pulse forward** 10 times (0.25s on / 0.25s off, capped at 60% duty).
3. **Brake test**: drive forward at up to 50% duty for 1s, then actively brake for 0.2s.
4. **Ramp reverse** up and back down, the same as step 1.

Between steps the motor coasts. On exit, `Ctrl+C` or `SIGTERM` (e.g. `systemctl stop`), both outputs go to 0% and the GPIO pins are released.

### Motor control notes

- **Coast**: both inputs at 0%.
- **Drive**: PWM on one input, the other held at 0%. The direction is set by which input gets the PWM.
- **Brake**: both inputs at 100% for a moment. This can spike current, so use it sparingly.
- **Deadtime**: when reversing while the motor is driven, both inputs drop to 0% for 50ms first to avoid shoot-through. Changing duty in the same direction (as during a ramp) has no extra delay.
- PWM is RPi.GPIO **software PWM** at 1000 Hz by default. It's fine for a motor, but expect some jitter.

---

## Hardware

- **Raspberry Pi**
- **IBT-4 H-bridge** motor driver board (IN1 / IN2 / GND logic inputs)
- **12V wiper motor** plus a separate 12V supply for the motor side of the IBT-4

### Wiring (BCM numbering)

| IBT-4 | Pi GPIO | Physical pin |
| ----- | ------- | ------------ |
| IN1   | GPIO18  | 12           |
| IN2   | GPIO19  | 35           |
| GND   | GND     | 6 (or any GND) |

The Pi and the IBT-4 logic side must share a ground.

---

## Running

```bash
python3 axworthy_ghost.py --max-duty 0.4 --verbose
```

| Flag         | Default | Meaning                                   |
| ------------ | ------- | ----------------------------------------- |
| `--in1`      | `18`    | BCM GPIO for IN1                          |
| `--in2`      | `19`    | BCM GPIO for IN2                          |
| `--pwm-hz`   | `1000`  | PWM frequency in Hz                       |
| `--max-duty` | `0.7`   | Maximum duty cycle, 0.0–1.0               |
| `--verbose`  | off     | Debug-level logging                       |

> Tip: start with a low `--max-duty` the first time. A wiper motor at full duty has a lot of torque.

When launched by `autorun.py` (see the top-level README), the script runs with the defaults above, and logs go to the journal (`sudo journalctl -u autorun.service -f`).

---

## Setup

Cypher uses the systemd boot method described under **Deployment** in the [top-level README](../README.md). Its only extra dependency is RPi.GPIO:

```bash
sudo apt install -y python3-rpi.gpio
```

---

## TODO

- Verify the wiring and the demo pattern on real hardware.
- Replace the demo with the actual ghost motion sequence.
- Decide on a trigger (a sensor, or a UDP message like Morpheus uses).
