import sys
import re
import uuid
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox,
    QProgressDialog
)

try:
    import msvcrt
except Exception:
    msvcrt = None


def strip_leading_number(name: str) -> str:
    pattern = re.compile(r"^\s*\d+\s*[\.\-_:)]*\s*")
    return pattern.sub("", name)


def is_file_locked(path: Path) -> bool:
    if msvcrt is None:
        try:
            fh = open(path, "r+b")
            fh.close()
            return False
        except Exception:
            return True

    try:
        fh = open(path, "r+b")
    except Exception:
        return True

    try:
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        fh.close()
        return False
    except Exception:
        try:
            fh.close()
        except Exception:
            pass
        return True


def main():

    if len(sys.argv) != 2:
        sys.exit(1)

    file_path = Path(sys.argv[1])
    folder = file_path.parent

    app = QApplication([])

    # aviso inicial
    QMessageBox.information(
        None,
        "Aviso",
        "Cierra cualquier archivo abierto de esta carpeta antes de continuar."
    )

    mp3s = [p for p in folder.iterdir() if p.suffix.lower() == ".mp3"]

    if not mp3s:
        QMessageBox.information(None, "Info", "No se encontraron mp3")
        sys.exit(0)

    # verificar bloqueos
    locked = [p.name for p in mp3s if is_file_locked(p)]

    if locked:
        QMessageBox.critical(
            None,
            "Archivos abiertos",
            "Estos archivos están en uso:\n\n" + "\n".join(locked)
        )
        sys.exit(2)

    # ordenar por last_modified
    mp3s.sort(key=lambda p: p.stat().st_mtime)

    width = max(2, len(str(len(mp3s))))

    final_names = []

    for i, p in enumerate(mp3s, 1):
        clean = strip_leading_number(p.stem)
        new_name = f"{i:0{width}d}. {clean}{p.suffix}"
        final_names.append(new_name)

    progress = QProgressDialog(
        "Renumerando archivos...",
        "Cancelar",
        0,
        len(mp3s) * 2
    )

    progress.setWindowTitle("Procesando")
    progress.setMinimumDuration(0)

    # fase 1: temporales
    temps = []
    step = 0

    for p in mp3s:

        if progress.wasCanceled():
            sys.exit(3)

        tmp = folder / f"enumtmp_{uuid.uuid4().hex}{p.suffix}"
        p.rename(tmp)

        temps.append(tmp)

        step += 1
        progress.setValue(step)

    # fase 2: nombres finales
    for tmp, final in zip(temps, final_names):

        if progress.wasCanceled():
            sys.exit(3)

        tmp.rename(folder / final)

        step += 1
        progress.setValue(step)

    progress.close()

    QMessageBox.information(
        None,
        "Completado",
        f"Se renumeraron {len(mp3s)} archivos"
    )


if __name__ == "__main__":
    main()