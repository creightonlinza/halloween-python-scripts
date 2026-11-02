# Halloween Rotary Phone (Trinity)

A Raspberry Pi–powered haunted rotary phone. When motion is detected, the phone “rings” from a speaker inside the phone. Picking up the handset stops the ring, sends a UDP message to another device (Morpheus), and plays a spooky voice. Picking up the handset when the phone *isn't* ringing plays a jump scare instead. After every ring and every hang-up, a cooldown keeps the phone quiet for a while.

## Features

* Motion on **BOARD pin 8** that stays HIGH for at least **1s** (`MOTION_HOLD_SECONDS`) starts the ring: `rotary_ringing.mp3` plays **twice** on the **body** speaker (left channel).
* **Answering:** handset pickup on **BOARD pin 10** while ringing immediately:

  1. stops ringing
  2. sends UDP `PHONE_ANSWERED` to **morpheus.local:5005**
  3. waits **1.5s**, then plays the answer clip in the **handset** (right channel), to the end
  4. starts a **30s** cooldown.
* **No answer:** if both rings finish without a pickup, the 30s cooldown starts anyway.
* **Jump scare:** picking up the handset when the phone isn't ringing (idle *or* during a cooldown) plays the jump-scare clip in the handset. It's audio only, and Morpheus is **not** triggered.
* **Off the hook = quiet:** while the handset is up, motion is ignored. When it's hung up, the **full** 30s cooldown restarts, so the phone never rings the moment it's put down.

## Hardware & Wiring

* Raspberry Pi using **BOARD** numbering:

  * **Pin 8** → PIR output (pull-down enabled)
  * **Pin 10** → switchhook input (pull-up enabled); other side of switchhook to **GND**. Handset **down** closes the switch (reads LOW); handset **up** opens it (reads HIGH). Changes must hold for 50ms to count (debounce).
* **Audio topology:** the Pi’s stereo output feeds two speakers in the phone:

  * A **mono speaker inside the rotary phone body** is fed from the **left channel** and is used for the ringing sound (50% volume).
  * The **handset speaker** is wired to the **right channel**, used for the voice clips (10% volume).

## Behavior Flow

1. **Idle (handset down, no cooldown) → Motion:** once motion has been HIGH for 1s, ring twice (body speaker).
2. **Pickup during ring:** stop ring → send UDP to `morpheus.local:5005` → 1.5s pause → play answer clip (handset) → start 30s cooldown.
3. **No pickup:** when the second ring ends, start the 30s cooldown.
4. **Pickup while not ringing** (idle or cooldown): play the jump scare (handset). Motion is ignored while the handset is up.
5. **Hang-up** (after any pickup, including answering): restart the full 30s cooldown.
6. **Cooldown expires:** return to Idle.

If the handset is already off the hook when the script starts, nothing plays; the phone just waits for it to be hung up.

## Audio

| Clip       | Setting           | Current file           |
| ---------- | ----------------- | ---------------------- |
| Ring       | `RING_FILE`       | `rotary_ringing.mp3`   |
| Answer     | `ANSWER_FILE`     | `laugh.mp3`            |
| Jump scare | `JUMP_SCARE_FILE` | `scream.mp3`           |

To swap a clip, drop the new mp3 in `audio/` and change the setting. Keep new handset clips close to the old ones in length and loudness, or adjust `HANDSET_VOLUME`.

## Configuration

Constants at the top of `rotary_phone.py`:

| Constant               | Default          | Meaning                                         |
| ---------------------- | ---------------- | ----------------------------------------------- |
| `MOTION_PIN`           | `8`              | PIR input (BOARD)                               |
| `SWITCHHOOK_PIN`       | `10`             | Switchhook input (BOARD)                        |
| `COOLDOWN_SECONDS`     | `30`             | Quiet time after a ring or a hang-up            |
| `MOTION_HOLD_SECONDS`  | `1`              | How long motion must stay HIGH (0 = immediate)  |
| `RING_COUNT`           | `2`              | Times the ring clip plays                       |
| `ANSWER_DELAY_SECONDS` | `1.5`            | Pause between pickup and the answer clip        |
| `BODY_VOLUME` / `HANDSET_VOLUME` | `0.50` / `0.10` | Speaker volumes                       |
| `MORPHEUS_HOST` / `MORPHEUS_PORT` | `morpheus.local` / `5005` | Where `PHONE_ANSWERED` is sent |

Requires `pygame` and `RPi.GPIO`.
