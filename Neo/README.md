# Halloween Attic Light Sweep (Neo)

This project runs on a Raspberry Pi located in my attic, and powers a servo-driven silhouette that swings in front of a glowing red light. The effect, when viewed from the outside through an attic window, gives the illusion that something is **moving inside**. It's designed to subtly disturb passersby using only a shadow, a servo, and some code.

---

## Device Overview

- **Hardware**:
  - Raspberry Pi running `pigpiod`
  - Servo motor
  - 3D-printed arm or other shadow-casting figure attached to the servo
  - External bright red LED placed behind the figure
  - Mounted on some scrap wood and placed in a window-facing portion of the attic

- **Behavior**:
  - On boot, the servo smoothly centers.
  - It then begins an endless loop of casting a shadow across the window at randomized speeds and intervals.
  - Upon shutdown or keyboard interrupt (`Ctrl+C`), it smoothly returns to center before stopping.

---

## How It Works

This Python script uses the `pigpio` library to control servo motion with **eased sweeping** and **randomized timing**. The result is lifelike, ghostly movement rather than robotic motion.

### Key Features:
- **Smooth Easing** via `ease_in_out_sine()` for natural motion
- **Random Durations** for pauses and sweeps to avoid pattern detection
- **Wake-up Nudge** to prevent servo dead-zone issues
- **Graceful Centering** on shutdown
