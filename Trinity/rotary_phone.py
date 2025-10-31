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
COOLDOWN_SECONDS = 30
MOTION_HOLD_SECONDS = 1  # seconds motion must stay HIGH to trigger (0 = immediate)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
RING_FILE = 'rotary_ringing.mp3'
MAN_FILE = 'man_behind_you.mp3'
GIRL_FILE = 'girl_behind_you.mp3'
RING_PATH = os.path.join(AUDIO_DIR, RING_FILE)
MAN_PATH = os.path.join(AUDIO_DIR, MAN_FILE)
GIRL_PATH = os.path.join(AUDIO_DIR, GIRL_FILE)

# Socket notify target
SOCKET_HOST = 'morpheus.local'
SOCKET_PORT = 5005
SOCKET_MESSAGE = b'PHONE_ANSWERED'

# Debounce timings
SWITCH_DEBOUNCE_SEC = 0.05  # 50 ms

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

RING_CH = pygame.mixer.Channel(0)
SFX_CH  = pygame.mixer.Channel(1)

RING_SND = pygame.mixer.Sound(RING_PATH)
MAN_SND = pygame.mixer.Sound(MAN_PATH)
GIRL_SND = pygame.mixer.Sound(GIRL_PATH)

def is_handset_picked_up() -> bool:
    first = GPIO.input(SWITCHHOOK_PIN) == GPIO.HIGH
    if not first:
        return False
    time.sleep(SWITCH_DEBOUNCE_SEC)
    return GPIO.input(SWITCHHOOK_PIN) == GPIO.HIGH

def send_socket_notice():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(SOCKET_MESSAGE, (SOCKET_HOST, SOCKET_PORT))
        print(f'[message] sent to {SOCKET_HOST}')
    except Exception as e:
        print(f'[message] failed: {e}')

def play_left_only(sound: pygame.mixer.Sound, loops: int = 0):
    RING_CH.stop()
    RING_CH.set_volume(.50, 0.0)
    RING_CH.play(sound, loops=loops)

def play_right_only(sound: pygame.mixer.Sound):
    SFX_CH.stop()
    SFX_CH.set_volume(0.0, 0.10)
    SFX_CH.play(sound)

def ring_twice_or_until_answered() -> bool:
    play_left_only(RING_SND, loops=1)

    while RING_CH.get_busy():
        if is_handset_picked_up():
            RING_CH.stop()
            send_socket_notice()
            time.sleep(1.5)
            play_right_only(MAN_SND)
            while SFX_CH.get_busy():
                time.sleep(0.01)
            return True
        time.sleep(0.01)

    return False

def motion_triggered() -> bool:
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

try:
    print('[ready] waiting for motion')
    cooldown_until = 0.0
    cooldown_pickup_armed = False

    while True:
        now = time.time()

        if now < cooldown_until:
            if GPIO.input(SWITCHHOOK_PIN) == GPIO.LOW:
                cooldown_pickup_armed = True
            elif cooldown_pickup_armed and is_handset_picked_up():
                remaining = max(0.0, cooldown_until - time.time())
                play_right_only(GIRL_SND)
                while is_handset_picked_up():
                    time.sleep(0.01)
                cooldown_until = time.time() + remaining
                cooldown_pickup_armed = False
            else:
                time.sleep(0.05)
            continue

        if motion_triggered():
            answered = ring_twice_or_until_answered()
            cooldown_until = time.time() + COOLDOWN_SECONDS
            cooldown_pickup_armed = False
        else:
            time.sleep(0.02)

except KeyboardInterrupt:
    pass
finally:
    time.sleep(0.2)
    try:
        RING_CH.stop(); SFX_CH.stop()
    except Exception:
        pass
    pygame.mixer.quit()
    GPIO.cleanup()
    print('[stopped]')
