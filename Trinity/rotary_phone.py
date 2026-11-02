import os
import time
import socket
import RPi.GPIO as GPIO

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'true'
import pygame

# -----------------------------
# CONFIG
# -----------------------------
MOTION_PIN = 8
SWITCHHOOK_PIN = 10
COOLDOWN_SECONDS = 30       # quiet time after a ring, or after the handset is hung up
MOTION_HOLD_SECONDS = 1     # seconds motion must stay HIGH to trigger (0 = immediate)
RING_COUNT = 2              # times the ring clip plays before giving up
ANSWER_DELAY_SECONDS = 1.5  # pause between pickup and the answer clip
SWITCH_DEBOUNCE_SEC = 0.05  # 50 ms
POLL_SECONDS = 0.02

# Body speaker (left channel) rings; handset speaker (right channel) plays voices
BODY_VOLUME = 0.50
HANDSET_VOLUME = 0.10

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
RING_FILE = 'rotary_ringing.mp3'
ANSWER_FILE = 'laugh.mp3'
JUMP_SCARE_FILE = 'scream.mp3'

# Morpheus (skeleton) is told when a ringing phone is answered
MORPHEUS_HOST = 'morpheus.local'
MORPHEUS_PORT = 5005
ANSWERED_MESSAGE = b'PHONE_ANSWERED'

# -----------------------------
# SETUP
# -----------------------------
print('***** Halloween Rotary Phone *****')

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

GPIO.setup(MOTION_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(SWITCHHOOK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

pygame.mixer.init()
pygame.mixer.set_num_channels(4)

BODY_CH = pygame.mixer.Channel(0)
HANDSET_CH = pygame.mixer.Channel(1)

def load_sound(filename: str) -> pygame.mixer.Sound:
    return pygame.mixer.Sound(os.path.join(AUDIO_DIR, filename))

RING_SND = load_sound(RING_FILE)
ANSWER_SND = load_sound(ANSWER_FILE)
JUMP_SCARE_SND = load_sound(JUMP_SCARE_FILE)

# -----------------------------
# HELPERS
# -----------------------------
def read_handset(last_up: bool) -> bool:
    """
    Debounced handset state (True = off hook). The switchhook opens (HIGH) when
    the handset is lifted. A change is only reported once it holds for
    SWITCH_DEBOUNCE_SEC; otherwise 'last_up' is returned.
    """
    up = GPIO.input(SWITCHHOOK_PIN) == GPIO.HIGH
    if up == last_up:
        return last_up
    time.sleep(SWITCH_DEBOUNCE_SEC)
    if (GPIO.input(SWITCHHOOK_PIN) == GPIO.HIGH) == up:
        return up
    return last_up

def motion_detected() -> bool:
    if GPIO.input(MOTION_PIN) != GPIO.HIGH:
        return False
    if MOTION_HOLD_SECONDS <= 0:
        return True
    t0 = time.time()
    while (time.time() - t0) < MOTION_HOLD_SECONDS:
        if GPIO.input(MOTION_PIN) != GPIO.HIGH:
            return False
        time.sleep(0.01)
    return True

def notify_morpheus():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(ANSWERED_MESSAGE, (MORPHEUS_HOST, MORPHEUS_PORT))
        print(f'[message] sent to {MORPHEUS_HOST}')
    except Exception as e:
        print(f'[message] failed: {e}')

def play_on_body(sound: pygame.mixer.Sound, loops: int = 0):
    BODY_CH.stop()
    BODY_CH.set_volume(BODY_VOLUME, 0.0)
    BODY_CH.play(sound, loops=loops)

def play_on_handset(sound: pygame.mixer.Sound):
    HANDSET_CH.stop()
    HANDSET_CH.set_volume(0.0, HANDSET_VOLUME)
    HANDSET_CH.play(sound)

def ring() -> bool:
    """
    Ring RING_COUNT times. If the handset is picked up, stop ringing, notify
    Morpheus, and play the answer clip to the end. Returns True if answered.
    """
    play_on_body(RING_SND, loops=RING_COUNT - 1)

    while BODY_CH.get_busy():
        if read_handset(False):
            BODY_CH.stop()
            notify_morpheus()
            time.sleep(ANSWER_DELAY_SECONDS)
            play_on_handset(ANSWER_SND)
            while HANDSET_CH.get_busy():
                time.sleep(POLL_SECONDS)
            return True
        time.sleep(POLL_SECONDS)

    return False

# -----------------------------
# MAIN LOOP
# -----------------------------
# States:
#   off hook  -> motion ignored; a fresh pickup plays the jump scare
#   hung up   -> full cooldown restarts
#   cooldown  -> motion ignored
#   idle      -> motion rings the phone, then cooldown
try:
    print('[ready] waiting for motion')
    cooldown_until = 0.0
    handset_up = read_handset(False)  # already off hook at boot: no jump scare

    while True:
        was_up = handset_up
        handset_up = read_handset(was_up)

        if handset_up:
            if not was_up:
                print('[handset] picked up -> jump scare')
                play_on_handset(JUMP_SCARE_SND)
            time.sleep(POLL_SECONDS)
            continue

        if was_up:
            print(f'[handset] hung up -> {COOLDOWN_SECONDS}s cooldown')
            cooldown_until = time.time() + COOLDOWN_SECONDS

        if time.time() < cooldown_until:
            time.sleep(POLL_SECONDS)
            continue

        # Re-check the handset so a pickup during the motion hold isn't treated as answering
        if motion_detected() and not read_handset(False):
            print('[motion] ringing')
            answered = ring()
            print('[ring] answered' if answered else '[ring] no answer')
            cooldown_until = time.time() + COOLDOWN_SECONDS
            # Still off hook after answering: cooldown restarts once it's hung up
            handset_up = read_handset(False)
        else:
            time.sleep(POLL_SECONDS)

except KeyboardInterrupt:
    pass
finally:
    time.sleep(0.2)
    try:
        BODY_CH.stop(); HANDSET_CH.stop()
    except Exception:
        pass
    pygame.mixer.quit()
    GPIO.cleanup()
    print('[stopped]')
