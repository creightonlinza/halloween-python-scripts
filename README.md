# Halloween Python Pi Scripts

A single repo for my Raspberry Pi–powered Halloween props. Each device has its own folder with code, assets, and notes.

- **Morpheus** → animates the **skeleton** prop
- **Neo** → runs the **servo sweep** in the attic window
- **Trinity** → drives the **rotary phone** gag

> Hardware is mostly Raspberry Pi + Python + simple GPIO peripherals.

---

## Devices at a glance

### Morpheus — Skeleton

- Controls servo/relay outputs for a skeleton prop.
- Intended to run idle loops plus triggered sequences.
- Listens for a network socket trigger to start an animation.
- Plays well with simple sensors (PIR, reed switches) if needed.

### Neo — Attic Servo Sweep

- Raspberry Pi named **Neo** lives in the attic.
- A servo with a 3D-printed arm sweeps in front of a red light to fake movement in the attic window.
- Uses an easing function and randomized timing for a natural, unsettling motion profile.

### Trinity — Rotary Phone

- Raspberry Pi named **Trinity** is mounted inside a vintage rotary phone.
- Connected to a **stereo speaker inside the phone**:

  - **Left channel** is used for the ringer on the internal speaker.
  - **Right channel** is soldered to the handset speaker for voice effects.

- Implements call/handset logic, cooldowns, and one-off stings.
  For example: during a cooldown, if the handset is picked up and set down again, cooldown pauses and a right-channel whisper clip can play, then cooldown resumes only after the handset is set down.
- When the handset is picked up while ringing, sends a socket message over the network to Morpheus to trigger the skeleton animation.

---

## Getting started

1. **Clone** this repo on your workstation or directly on each Pi.
2. **Choose a project folder** (`morpheus`, `neo`, or `trinity`) and follow its local README for wiring, GPIO pins, and run commands.

> Tip: keep each Pi’s hostname aligned with its folder name (morpheus, neo, trinity) so logs and network discovery stay obvious.

---

## Conventions

- **Python 3.11+** preferred.
- **pigpio** for precise PWM/servo where needed.
- **Logging** to stdout by default; services redirect to journald.
- **Env/config**: favor simple `.env` or a `config.py` per device.

---

## License

Personal project. If you reuse parts, be cool and credit where appropriate.
