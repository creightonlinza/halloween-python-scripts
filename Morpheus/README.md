# Rocking Chair Skeleton (Morpheus)

A lightweight control script for a Halloween prop running on a Raspberry Pi, paired with a DIY **wiper-motor rocking-chair skeleton**. When a companion device (**Trinity**) signals that the rotary phone has been answered, Morpheus:

* **Sweeps the head** with a servo (smooth, stepped motion with easing)
* **Flashes the eyes** (GPIO "try-me" button) with a ramp that speeds up over time
* **Plays spooky audio** (first “look_behind_you.mp3”, then “crypt_laugh.mp3”), at a set music volume

---

## How it works

1. **Idle / Ready**

   * Listens on UDP port **5005** for the message `PHONE_ANSWERED`.
   * Eyes are **ON** by default.

2. **On trigger (`PHONE_ANSWERED`)**

   * **Head move (hold)**: Steps the servo to the “hold” position (in this code, `SERVO_MIN`) using a smooth eased sweep.
   * **Audio A**: Plays `look_behind_you.mp3` (music volume set to **0.25**).
   * **Blink ramp**: For `HOLD_SECONDS`, eyes blink with a 50% duty cycle, **ramping** from a slow period (`0.25s`) to fast (`0.06s`) while holding the head position.
   * The script waits **at least `HOLD_SECONDS`** (here `6s`) and until Audio A finishes. If the audio runs longer than `HOLD_SECONDS`, the eyes stay ON for the rest of it.

3. **Sweeps + Audio B**

   * **Audio B**: Plays `crypt_laugh.mp3`.
   * Performs **`SWEEPS`** back-and-forth head sweeps (here, 4 cycles) between `SERVO_MIN` and `SERVO_MAX`, using eased stepping (`SERVO_MOVE_DURATION`, 1s per edge-to-edge move).

4. **Finish**

   * **Recenters** the head smoothly to `SERVO_MID`.
   * Stops audio (Audio B is cut off if it's still playing) and leaves eyes **ON**.

---

## Hardware

* **Raspberry Pi** running the `pigpiod` daemon (`sudo pigpiod`)
* **Servo motor**: BCM **GPIO 17** (pigpio servo control)
* **Skeleton Skull with Powered Eyes** (controlled via the "try-me" button cord): BCM **GPIO 18**. Eyes **ON** = pin driven HIGH; eyes **OFF** = pin switched to an input (released).

> The **wiper-motor rocking chair** motion is a separate DIY mechanism the Pi is paired with; this script controls the **head servo** and **eyes** and coordinates audio with Trinity’s phone event.

Requires `pigpio`, `pygame`, and `RPi.GPIO`.

---

## Graceful startup & shutdown

* **On boot**: Parks the head **to center** via a small nudge + stepped motion (avoids initial “energize click”).
* **On exit / Ctrl+C**: Stops audio, turns the eyes **OFF** (releases GPIO 18), recenters head smoothly, and **stops pigpio**.

---

## Testing locally

Trigger the effect without Trinity by sending the UDP message from the Pi itself:

```bash
echo -n "PHONE_ANSWERED" > /dev/udp/127.0.0.1/5005
```
