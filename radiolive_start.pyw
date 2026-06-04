# radio_metadata_daemon.py
# Ejecutar en background. Escribe títulos nuevos a radio_panel_external_history.txt
# y estado a radio_panel_external_state.txt
#
# Requiere:
#   pip install requests pywin32

import win32event
import win32api
import winerror
import win32con
import requests
import time
import sys
import os
from datetime import datetime

# ============================================================
# SINGLE INSTANCE (WINDOWS MUTEX)
# ============================================================

MUTEX_NAME = "Global\\RadioMetadataDaemon"
STOP_EVENT_NAME = "Global\\RadioMetadataDaemon_Stop"

mutex = win32event.CreateMutex(None, False, MUTEX_NAME)
if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
    print("❌ El daemon ya está en ejecución")
    sys.exit(0)

# Evento de parada
stop_event = win32event.CreateEvent(
    None,   # seguridad
    True,   # manual reset
    False,  # no señalado al inicio
    STOP_EVENT_NAME
)

# Asegurarse de que el evento no quedó señalado de antes
win32event.ResetEvent(stop_event)


def should_stop():
    return win32event.WaitForSingleObject(
        stop_event, 0
    ) == win32event.WAIT_OBJECT_0


# ============================================================
# CONFIGURACIÓN
# ============================================================

RADIO_URL = "http://s01.digitalserver.org:9268/stream"
OUT_DIR = r"C:\Users\miche\OneDrive\foobar2000\profile"

HISTORY_FILE = os.path.join(OUT_DIR, "radio_panel_external_history.txt")
STATE_FILE = os.path.join(OUT_DIR, "radio_panel_external_state.txt")

RECONNECT_DELAY = 5.0
READ_CHUNK = 1024


# ============================================================
# UTILIDADES
# ============================================================

def ensure_out_dir():
    os.makedirs(OUT_DIR, exist_ok=True)


def write_state(s):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write(s + "\n")
    except:
        pass


def get_last_history_title():
    try:
        if not os.path.exists(HISTORY_FILE):
            return None
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
            if not lines:
                return None
            last = lines[-1]
            parts = last.split(" - ", 1)
            return parts[1].strip() if len(parts) == 2 else last
    except:
        return None


def append_history_line_if_new(line):
    try:
        parts = line.split(" - ", 1)
        title = parts[1].strip() if len(parts) == 2 else line.strip()
        last_title = get_last_history_title()
        if last_title and title == last_title:
            return False
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        return True
    except Exception as e:
        write_state("ERROR: escribir historial -> " + str(e))
        return False


def parse_icy_metadata_block(block_bytes):
    try:
        s = block_bytes.decode("utf-8", errors="ignore")
        for part in s.split(";"):
            if part.strip().startswith("StreamTitle="):
                val = part.split("=", 1)[1].strip()
                if (val.startswith("'") and val.endswith("'")) or \
                   (val.startswith('"') and val.endswith('"')):
                    val = val[1:-1]
                return val
    except:
        pass
    return None


# ============================================================
# BUCLE PRINCIPAL
# ============================================================

def run_loop():
    last_title = get_last_history_title()

    while not should_stop():
        write_state("CONNECTING")
        try:
            headers = {
                "Icy-MetaData": "1",
                "User-Agent": "Python-Radio-Metadata/1.0",
            }

            r = requests.get(
                RADIO_URL,
                headers=headers,
                stream=True,
                timeout=10,
            )
            r.raise_for_status()

            icy_metaint = int(r.headers.get("icy-metaint", 0) or 0)
            radio_name = r.headers.get("icy-name", "Radio desconocida")

            write_state("RUNNING - " + radio_name)
            print(f"[{datetime.now().isoformat()}] Conectado a {radio_name}")

            stream = r.raw

            if icy_metaint <= 0:
                buf = stream.read(65536)
                possible = parse_icy_metadata_block(buf)
                if possible and possible != last_title:
                    ts = datetime.now().strftime("%H:%M")
                    if append_history_line_if_new(f"{ts} - {possible}"):
                        last_title = possible
                r.close()
                time.sleep(RECONNECT_DELAY)
                continue

            while not should_stop():
                remaining = icy_metaint
                while remaining > 0:
                    if should_stop():
                        r.close()
                        return
                    chunk = stream.read(min(READ_CHUNK, remaining))
                    if not chunk:
                        raise IOError("stream ended")
                    remaining -= len(chunk)

                size_byte = stream.read(1)
                if not size_byte:
                    raise IOError("stream ended")
                size = size_byte[0] * 16

                if size > 0:
                    metadata_bytes = stream.read(size)
                    titulo = parse_icy_metadata_block(metadata_bytes)
                    if titulo and titulo != last_title:
                        ts = datetime.now().strftime("%H:%M")
                        if append_history_line_if_new(f"{ts} - {titulo}"):
                            last_title = titulo
                            print(f"[{datetime.now().isoformat()}] {titulo}")

                time.sleep(0.01)

            r.close()

        except Exception as e:
            write_state("ERROR: " + str(e))
            time.sleep(RECONNECT_DELAY)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 30 + " RADIO METADATA DAEMON " + "=" * 30)
    ensure_out_dir()
    write_state("INIT")

    try:
        run_loop()
    finally:
        write_state("STOPPED")
        win32event.ReleaseMutex(mutex)
        print("Daemon detenido correctamente")
