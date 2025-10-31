#!/usr/bin/env python3
# Minimal SMB (python-smbclient) loader with a tiny network/SMB check.

import os, sys, shutil, runpy, tempfile, time, socket
from pathlib import Path, PureWindowsPath
import smbclient

# ===== CONFIG =====
SERVER     = "LOCAL-CLOUD-NAME-HERE.local"
SHARE      = "Raspberry Pi"
REMOTE_DIR = "PI_DEVICE_NAME"
ENTRYPOINT = "SCRIPT-TO-RUN.py"
USERNAME   = "pi"
PASSWORD   = "RaspberryPi"

WAIT_TOTAL_SECS = 60   # total time to wait for network/SMB
WAIT_STEP_SECS  = 3    # delay between retries
# ==================

def unc(*parts: str) -> str:
    p = PureWindowsPath("\\\\" + SERVER) / SHARE
    for part in parts:
        if part:
            p = p / part.replace("/", "\\").strip("\\")
    return str(p)

def wait_for_tcp_445(host: str, total=WAIT_TOTAL_SECS, step=WAIT_STEP_SECS):
    deadline = time.time() + total
    last_err = None
    while time.time() < deadline:
        try:
            # Resolve + attempt TCP connect to port 445
            for fam, _, _, _, addr in socket.getaddrinfo(host, 445, proto=socket.IPPROTO_TCP):
                s = socket.socket(fam, socket.SOCK_STREAM)
                s.settimeout(3)
                try:
                    s.connect(addr)
                    s.close()
                    return
                finally:
                    try: s.close()
                    except: pass
        except OSError as e:
            last_err = e
        time.sleep(step)
    raise RuntimeError(f"SMB host not reachable on 445: {host} (last error: {last_err})")

def wait_for_share(server: str, share: str, total=WAIT_TOTAL_SECS, step=WAIT_STEP_SECS):
    # Assumes session already registered
    path = f"//{server}/{share}"
    deadline = time.time() + total
    last_err = None
    while time.time() < deadline:
        try:
            smbclient.listdir(path)
            return
        except Exception as e:
            last_err = e
            time.sleep(step)
    raise RuntimeError(f"SMB share not accessible: {path} (last error: {last_err})")

def copy_tree(remote_root: str, local_root: Path):
    local_root.mkdir(parents=True, exist_ok=True)
    for entry in smbclient.scandir(remote_root):
        rp = str(PureWindowsPath(remote_root) / entry.name)
        lp = local_root / entry.name
        if entry.is_dir():
            copy_tree(rp, lp)
        else:
            with smbclient.open_file(rp, mode="rb") as src, open(lp, "wb") as dst:
                shutil.copyfileobj(src, dst)

def main():
    # 1) Network/SMB ready checks
    wait_for_tcp_445(SERVER)
    smbclient.register_session(SERVER, username=USERNAME, password=PASSWORD)
    wait_for_share(SERVER, SHARE)

    # 2) Copy folder then run
    try:
        with tempfile.TemporaryDirectory(prefix="temp_") as td:
            local_project = Path(td) / REMOTE_DIR
            copy_tree(unc(REMOTE_DIR), local_project)

            entry = local_project / ENTRYPOINT
            if not entry.exists():
                raise SystemExit(f"ENTRYPOINT not found: {entry}")

            os.chdir(local_project)
            sys.argv = [str(entry)]  # no extra args
            if str(local_project) not in sys.path:
                sys.path.insert(0, str(local_project))
            runpy.run_path(str(entry), run_name="__main__")
    finally:
        smbclient.reset_connection_cache()

if __name__ == "__main__":
    main()
