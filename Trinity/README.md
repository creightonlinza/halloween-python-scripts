# Halloween Rotary Phone (Trinity)

A Raspberry Pi–powered haunted rotary phone. When motion is detected, the phone “rings” from a speaker inside the phone. Picking up the handset stops the ring, sends a UDP message to another device (Morpheus), and plays a spooky voice. During cooldown, picking up the handset again pauses the timer and plays a different clip; the timer resumes once the handset is set down.

## Features

* Motion on **BOARD pin 8** starts the ring clip `rotary_ringing.mp3` in the **left** channel only.
* Handset pickup on **BOARD pin 10** immediately:

  1. stops ringing
  2. sends UDP `PHONE_ANSWERED` to **morpheus.local:5005**
  3. plays `man_behind_you.mp3` in the **right** channel (blocking), then starts a **30s** cooldown.
* **Cooldown behavior:** during the cooldown, if the handset is set down and then picked up again, the cooldown **pauses** and `girl_behind_you.mp3` plays in the **right** channel; the cooldown **continues** once the handset is set down.
* Ringing plays one full file at a time; when a file finishes, it checks motion again and repeats if motion is still present (no mid-file cutoffs).

## Hardware & Wiring

* Raspberry Pi using **BOARD** numbering:

  * **Pin 8** → PIR output (pull-down enabled)
  * **Pin 10** → switchhook input (pull-up enabled); other side of switchhook to **GND**
* **Audio topology:** the Pi’s stereo output feeds two speakers in the phone:

  * A **mono speaker inside the rotary phone body** is fed from the **left channel** and is used for the ringing sound.
  * The **handset speaker** is wired to the **right channel**, used for the voice clips.

## Behavior Flow

1. **Idle → Motion:** play `rotary_ringing.mp3` (left channel); when the file ends, re-check motion and repeat if still HIGH.
2. **Pickup during ring:** stop ring → send UDP to `morpheus.local:5005` → short pause → play `man_behind_you.mp3` (right) → start 30s cooldown.
3. **During cooldown:** if handset goes LOW (down) then HIGH (pickup), **pause** cooldown and play `girl_behind_you.mp3` (right). When handset returns LOW (down), **resume** the remaining cooldown.
4. **Cooldown expires:** return to Idle.
