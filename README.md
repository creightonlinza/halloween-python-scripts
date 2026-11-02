# Halloween Python Pi Scripts

A single repo for my Raspberry Pi–powered Halloween props. Each device has its own folder with code, assets, and notes.

- **[Morpheus](Morpheus/)** → animates the **skeleton** prop
- **[Neo](Neo/)** → runs the **servo sweep** in the attic window
- **[Trinity](Trinity/)** → drives the **rotary phone** gag
- **[Cypher](Cypher/)** → drives a **wiper motor** for the Axworthy ghost *(work in progress)*

> Hardware is mostly Raspberry Pi + Python + simple GPIO peripherals.

---

## Devices at a glance

### Morpheus — Skeleton

- Controls the head servo and light-up eyes of a skeleton in a rocking chair.
- Plays spooky audio along with the animation.
- Listens on UDP port 5005 for a `PHONE_ANSWERED` message from Trinity to start the sequence.

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
  For example: picking up the handset when the phone isn't ringing plays a jump scare in the handset, and hanging up restarts the full cooldown.
- When the handset is picked up while ringing, sends a socket message over the network to Morpheus to trigger the skeleton animation.

### Cypher — Wiper Motor *(work in progress)*

- Raspberry Pi named **Cypher** drives a 12V wiper motor through an IBT-4 H-bridge.
- Currently a bench-test script (ramps, pulses, brake, reverse) to validate wiring before building the real motion sequence.

---

## Getting started

1. **Clone** this repo on your workstation or directly on each Pi.
2. **Choose a project folder** (`Morpheus`, `Neo`, `Trinity`, or `Cypher`) and follow its local README for wiring, GPIO pins, and run commands.

> Tip: keep each Pi’s hostname aligned with its folder name (morpheus, neo, trinity, cypher) so logs and network discovery stay obvious. Trinity reaches Morpheus at `morpheus.local`.

### Dependencies

| Device   | Python modules              | Notes                                  |
| -------- | --------------------------- | -------------------------------------- |
| Morpheus | `pigpio`, `pygame`, `RPi.GPIO` | needs the `pigpiod` daemon running (`sudo pigpiod`) |
| Neo      | `pigpio`                    | needs the `pigpiod` daemon running     |
| Trinity  | `pygame`, `RPi.GPIO`        |                                        |
| Cypher   | `RPi.GPIO`                  |                                        |
| all (autorun) | `smbprotocol`          | provides `smbclient`, used by `autorun.py` |

---

## Deployment

The device code doesn't live on the Pis. Each Pi runs [`autorun.py`](autorun.py) at boot, which:

1. Waits (up to 60s) for the SMB server to answer on port 445 and for the share to be readable.
2. Copies that Pi's folder from the share into a temp directory.
3. Runs the folder's entry script.

So updating a prop means updating its folder on the share and rebooting (or restarting the service).

### 1. Provision the Pi

```bash
ssh pi@<NAME>.local

sudo apt update
sudo apt full-upgrade -y
sudo apt install -y python3-venv python3-pip git tmux
pip3 install smbprotocol --break-system-packages
```

Then install the device's own dependencies (see the table above).

### 2. Configure `autorun.py`

Copy `autorun.py` to `/home/pi/autorun.py` on the Pi and fill in the `CONFIG` block:

| Setting      | Example                       |
| ------------ | ----------------------------- |
| `SERVER`     | SMB server hostname (`*.local`) |
| `SHARE`      | `Raspberry Pi`                |
| `REMOTE_DIR` | `Morpheus`                    |
| `ENTRYPOINT` | `skeleton.py`                 |
| `USERNAME` / `PASSWORD` | SMB credentials    |

> **Only put real credentials in the Pi's copy.** The committed `autorun.py` must keep its placeholders.

### 3. Start it at boot

**systemd (recommended, used by Cypher)**: create `/etc/systemd/system/autorun.service`:

```ini
[Unit]
Description=Python App
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/bin/python3 /home/pi/autorun.py
Restart=on-failure
RestartSec=2
Environment=PYTHONUNBUFFERED=1

# Logs go to the system journal (view with journalctl)
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Then enable it and check on it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now autorun.service
sudo systemctl status autorun.service
sudo journalctl -u autorun.service -f
```

**Desktop autostart (older method)**: opens a terminal window on login so the output is visible on screen. Install `xterm` (`sudo apt-get install -y xterm`), put `autorun.py` at `/home/pi/Desktop/autorun.py`, and create `/home/pi/.config/autostart/autorun.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=Autorun Script
Exec=xterm -hold -e '/usr/bin/python3 /home/pi/Desktop/autorun.py'
```

---

## Conventions

- **Python 3.11+** preferred.
- **pigpio** for precise PWM/servo where needed.
- **Logging** to stdout by default; services redirect to journald.
- **Config**: constants at the top of each script.

---

## License

Personal project. If you reuse parts, be cool and credit where appropriate.
