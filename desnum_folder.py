import sys
import re
import uuid
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox,
    QProgressDialog
)

INVALID_CHARS = r'[\\/:*?"<>|]'

def is_valid_windows_name(name: str) -> bool:
    return not re.search(INVALID_CHARS, name)

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


    QMessageBox.information(
        None,
        "Aviso",
        "Cierra cualquier archivo abierto de esta carpeta antes de continuar."
    )

    mp3s = [p for p in folder.iterdir() if p.suffix.lower() == ".mp3"]

    if not mp3s:
        QMessageBox.information(None, "Info", "No se encontraron mp3")
        sys.exit(0)

    locked = [p.name for p in mp3s if is_file_locked(p)]

    if locked:
        QMessageBox.critical(
            None,
            "Archivos abiertos",
            "Estos archivos están en uso:\n\n" + "\n".join(locked)
        )
        sys.exit(2)

    progress = QProgressDialog(
        "Quitando numeración...",
        "Cancelar",
        0,
        len(mp3s) * 2
    )

    progress.setWindowTitle("Procesando")
    progress.setMinimumDuration(0)

    temps = []
    step = 0

    # =========================
    # FASE 0: SIMULACIÓN
    # =========================
    mapping = []
    errors = []
    seen = set()

    for p in mp3s:

        clean = strip_leading_number(p.stem).strip()

        if not clean:
            errors.append(f"{p.name} -> nombre vacío")
            continue

        if not is_valid_windows_name(clean):
            errors.append(f"{p.name} -> caracteres inválidos")
            continue

        new_name = f"{clean}{p.suffix}"

        if new_name in seen:
            errors.append(f"{p.name} -> nombre duplicado: {new_name}")
            continue

        if (folder / new_name).exists():
            errors.append(f"{p.name} -> ya existe: {new_name}")
            continue

        seen.add(new_name)
        mapping.append((p, folder / new_name))


    # =========================
    # FASE 1: VALIDACIÓN
    # =========================
    if errors:
        QMessageBox.critical(
            None,
            "Errores detectados",
            "Se canceló la operación:\n\n" + "\n".join(errors[:20])
        )
        sys.exit(4)


    # =========================
    # FASE 2: EJECUCIÓN REAL
    # =========================
    progress = QProgressDialog(
        "Renombrando...",
        "Cancelar",
        0,
        len(mapping)
    )

    progress.setWindowTitle("Procesando")
    progress.setMinimumDuration(0)

    step = 0

    for src, dst in mapping:

        if progress.wasCanceled():
            sys.exit(3)

        src.rename(dst)

        step += 1
        progress.setValue(step)

    progress.close()
    
    QMessageBox.information(
        None,
        "Completado",
        f"Se elimino la enumeracion de {len(mp3s)} archivos"
    )

if __name__ == "__main__":
    main()