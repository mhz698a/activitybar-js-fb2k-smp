# stop_radio_metadata_daemon.py
import time
import win32event
import win32con

EVENT_NAME = "Global\\RadioMetadataDaemon_Stop"

try:
    event = win32event.OpenEvent(
        win32con.EVENT_MODIFY_STATE,
        False,
        EVENT_NAME
    )
    win32event.SetEvent(event)
    print("✔ Señal de cierre enviada")
except Exception as e:
    print("❌ No se pudo enviar la señal:", e)

time.sleep(3)