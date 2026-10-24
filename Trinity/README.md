# Halloween Rotary Phone (Trinity)

A Raspberry Pi–powered haunted rotary phone. When motion is detected, the phone “rings” from a speaker inside the phone. Picking up the handset stops the ring, sends a UDP message to another device (Morpheus), and plays a spooky voice. After each ring, answered or not, a cooldown starts. During the cooldown, picking up the handset again pauses the timer and plays a different clip; the timer resumes once the handset is set down.

## Features

* Motion on **BOARD pin 8** that stays HIGH for at least **1s** (`MOTION_HOLD_SECONDS`) starts the ring: `rotary_ringing.mp3` plays **twice** in the **left** channel only.
* Handset pickup on **BOARD pin 10** while ringing immediately:

  1. stops ringing
  2. sends UDP `PHONE_ANSWERED` to **morpheus.local:5005**
  3. waits **1.5s**, then plays `man_behind_you.mp3` in the **right** channel (blocking)
  4. starts a **30s** cooldown.
* **No answer:** if both rings finish without a pickup, the 30s cooldown starts anyway. Motion is not checked again until the cooldown ends.
* **Cooldown behavior:** during the cooldown, if the handset is set down and then picked up again, the cooldown **pauses** and `girl_behind_you.mp3` plays in the **right** channel; the cooldown **continues** once the handset is set down.

## Hardware & Wiring

* Raspberry Pi using **BOARD** numbering:

  * **Pin 8** → PIR output (pull-down enabled)
  * **Pin 10** → switchhook input (pull-up enabled); other side of switchhook to **GND**. Handset **down** closes the switch (reads LOW); handset **up** opens it (reads HIGH). Pickups are debounced for 50ms.
* **Audio topology:** the Pi’s stereo output feeds two speakers in the phone:

  * A **mono speaker inside the rotary phone body** is fed from the **left channel** and is used for the ringing sound (50% volume).
  * The **handset speaker** is wired to the **right channel**, used for the voice clips (10% volume).

## Behavior Flow

1. **Idle → Motion:** once motion has been HIGH for 1s, play `rotary_ringing.mp3` twice (left channel).
2. **Pickup during ring:** stop ring → send UDP to `morpheus.local:5005` → 1.5s pause → play `man_behind_you.mp3` (right) → start 30s cooldown.
3. **No pickup:** when the second ring ends, start the 30s cooldown.
4. **During cooldown:** if handset goes LOW (down) then HIGH (pickup), **pause** cooldown and play `girl_behind_you.mp3` (right). When handset returns LOW (down), **resume** the remaining cooldown.
5. **Cooldown expires:** return to Idle.

## Configuration

Constants at the top of `rotary_phone.py`:

| Constant              | Default          | Meaning                                       |
| --------------------- | ---------------- | --------------------------------------------- |
| `MOTION_PIN`          | `8`              | PIR input (BOARD)                             |
| `SWITCHHOOK_PIN`      | `10`             | Switchhook input (BOARD)                      |
| `COOLDOWN_SECONDS`    | `30`             | Cooldown after each ring                      |
| `MOTION_HOLD_SECONDS` | `1`              | How long motion must stay HIGH (0 = immediate) |
| `SOCKET_HOST` / `SOCKET_PORT` | `morpheus.local` / `5005` | Where `PHONE_ANSWERED` is sent |

Requires `pygame` and `RPi.GPIO`.
