# render_domains.pyw
# first release: 2026-06-23 20:35:00

from pathlib import Path
import sys
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from domain_visor.scene_view import VasculumApp

APP_DIR = Path(__file__).resolve().parent.as_posix()
ICON_WIN = f"{APP_DIR}/assets/online.ico"
JSON_DOMAINS = f"{APP_DIR}/__structure__/domains.json"
CONTAINER_DOMAINS = f"{APP_DIR}/__structure__/container.json"

myappid = 'etudetools.year_struct.render_domains.1.0'
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        app.setWindowIcon(QIcon(ICON_WIN))
    except Exception:
        pass

    window = VasculumApp(JSON_DOMAINS, CONTAINER_DOMAINS)
    window.show()
    sys.exit(app.exec())
