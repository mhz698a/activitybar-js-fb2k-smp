from pathlib import Path
import traceback
import shutil
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

def clean_path(p: str) -> str:
    return p.replace("\ufeff", "").strip()

def safe_move(src, dst_dir):
    src = Path(src)
    dst_dir = Path(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)
    target = dst_dir / src.name
    if not target.exists():
        shutil.move(str(src), str(target))
        return str(target)

    stem = src.stem
    suffix = src.suffix
    i = 1
    while True:
        candidate = dst_dir / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            shutil.move(str(src), str(candidate))
            return str(candidate)
        i += 1

class MoveWorker(QObject):
    progress = pyqtSignal(int, int, str)
    log = pyqtSignal(str)
    finished = pyqtSignal(object, object, object)  # moved, failed, origin_dirs
    error = pyqtSignal(str)

    def __init__(self, paths, dest_dir):
        super().__init__()
        self.paths = list(paths)
        self.dest_dir = Path(dest_dir)

    @pyqtSlot()
    def run(self):
        moved = []
        failed = []
        origin_dirs = set()

        try:
            total = len(self.paths)

            for i, p in enumerate(self.paths, 1):
                p_clean = clean_path(p)
                src = Path(p_clean)
                origin_dirs.add(str(src.parent))

                try:
                    if not src.exists():
                        failed.append((p_clean, "Origen no existe"))
                        self.log.emit(f"FALLO: {p_clean} -> Origen no existe")
                    else:
                        newp = safe_move(p_clean, self.dest_dir)
                        moved.append(newp)
                        self.log.emit(f"MOVIDO: {p_clean} -> {newp}")
                except Exception as e:
                    failed.append((p_clean, str(e)))
                    self.log.emit(f"FALLO: {p_clean} -> {e}")

                self.progress.emit(i, total, p_clean)

            self.finished.emit(moved, failed, origin_dirs)

        except Exception:
            self.error.emit(traceback.format_exc())